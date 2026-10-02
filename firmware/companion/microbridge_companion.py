#!/usr/bin/env python3
"""Opt-in six-key Pico USB serial companion for Microbridge protocol v0.

Only hello, subscribe, and activate_agent_key are emitted to Microbridge.
The implementation uses Python's standard library on macOS and Linux.
"""

import argparse
from collections import deque
import errno
import json
import logging
import os
import re
import selectors
import socket
import stat
import termios
import time
import tty

LOG = logging.getLogger("macropad.microbridge")
KEY_COUNT = 6
BLACK = ((0, 0, 0),) * KEY_COUNT
HELLO = {"type": "hello", "adapter": "field13-six-key-companion",
         "protocol_version": 0, "role": "ui"}
SUBSCRIBE = {"type": "subscribe"}
MAX_DAEMON_LINE = 262144
MAX_SERIAL_LINE = 1024
MAX_DAEMON_OUTPUT = 8192


def encode(message):
    return json.dumps(message, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"


def _bad_constant(_value):
    raise ValueError("non-JSON number")


class NDJSON:
    """Bounded streaming decoder. Oversized records are discarded, never truncated.

    All complete messages survive combined reads; partial messages survive reads.
    Invalid UTF-8, non-object JSON, and malformed JSON are discarded individually.
    """

    def __init__(self, limit):
        self.limit = limit
        self.buffer = bytearray()
        self.discarding = False

    def clear(self):
        self.buffer.clear()
        self.discarding = False

    def feed(self, data):
        messages = []
        start = 0
        while start < len(data):
            end = data.find(b"\n", start)
            complete = end >= 0
            end = end if complete else len(data)
            size = end - start
            if not self.discarding:
                if len(self.buffer) + size > self.limit:
                    self.buffer.clear()
                    self.discarding = True
                else:
                    self.buffer.extend(data[start:end])
            if complete:
                if not self.discarding and self.buffer.strip():
                    try:
                        value = json.loads(self.buffer.decode("utf-8"),
                                           parse_constant=_bad_constant)
                        if isinstance(value, dict):
                            messages.append(value)
                    except (ValueError, UnicodeError, RecursionError):
                        pass
                self.clear()
            start = end + 1
        return messages


def led_colors(frame):
    """Validate the pinned AgentKeyLedFrame and pre-scale brightness (percent).

    An unsupported/legacy frame returns None so the caller can fail dark.
    Static RGB only: upstream focus/breathing animation is not synthesized.
    """
    if not isinstance(frame, dict):
        return None
    keys = frame.get("keys")
    brightness = frame.get("brightness", 80)
    paused = frame.get("paused", False)
    if (not isinstance(keys, list) or len(keys) != KEY_COUNT or
            type(brightness) is not int or not 0 <= brightness <= 255 or
            type(paused) is not bool):
        return None
    scale = 0 if paused else min(brightness, 100)
    result = []
    for key in keys:
        if not isinstance(key, dict):
            return None
        color = key.get("color")
        if color is None:
            result.append((0, 0, 0))
        elif isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            # Round to nearest integer instead of scaling a second time on Pico.
            result.append(tuple((int(color[i:i + 2], 16) * scale + 50) // 100
                                for i in (1, 3, 5)))
        else:
            return None
    return tuple(result)


def activation_index(message):
    # Deliberately exact schema: no commands, approval/reject, encoder, or passthrough.
    if (set(message) != {"v", "type", "index"} or
            type(message.get("v")) is not int or message["v"] != 1 or
            message.get("type") != "activate" or
            type(message.get("index")) is not int or
            not 0 <= message["index"] < KEY_COUNT):
        return None
    return message["index"]


class Companion:
    """Single-threaded, non-blocking serial/socket relay with bounded queues."""

    def __init__(self, port, socket_path, *, clock=time.monotonic,
                 reconnect_seconds=1.0, refresh_seconds=2.0,
                 stale_seconds=6.0, led_seconds=0.5,
                 activation_seconds=0.2):
        if (reconnect_seconds <= 0 or refresh_seconds <= 0 or
                stale_seconds <= refresh_seconds or led_seconds <= 0 or
                activation_seconds < 0.2):
            raise ValueError("invalid timing; activations must be at least 0.2s apart")
        self.port = port
        self.socket_path = socket_path
        self.clock = clock
        self.reconnect_seconds = reconnect_seconds
        self.refresh_seconds = refresh_seconds
        self.stale_seconds = stale_seconds
        self.led_seconds = led_seconds
        self.activation_seconds = activation_seconds
        self.selector = selectors.DefaultSelector()
        self.serial_fd = None
        self.serial_attrs = None
        self.daemon = None
        self.connecting = False
        self.ready = False
        self.colors = BLACK
        self.serial_decoder = NDJSON(MAX_SERIAL_LINE)
        self.daemon_decoder = NDJSON(MAX_DAEMON_LINE)
        self.daemon_output = deque()  # [bytes, offset, activation expiry or None]
        self.activations = deque()  # bounded physical input order, never just first in a read
        self.serial_output = b""
        self.serial_offset = 0
        self.serial_pending = None  # only the newest complete LED frame
        self.next_serial = self.next_daemon = self.next_refresh = self.next_led = 0.0
        self.connected_at = self.last_frame = 0.0
        self.last_activation = float("-inf")
        self.closed = False

    def _interest(self, fileobj, kind, writable):
        events = selectors.EVENT_READ | (selectors.EVENT_WRITE if writable else 0)
        try:
            self.selector.modify(fileobj, events, kind)
        except KeyError:
            self.selector.register(fileobj, events, kind)

    def _unregister(self, fileobj):
        try:
            self.selector.unregister(fileobj)
        except (KeyError, ValueError):
            pass

    def _discard_serial_input(self):
        self.serial_decoder.clear()
        if self.serial_fd is not None:
            try:
                termios.tcflush(self.serial_fd, termios.TCIFLUSH)
            except (OSError, termios.error):
                pass

    def _open_serial(self, now):
        self.next_serial = now + self.reconnect_seconds
        fd = None
        attrs = None
        try:
            fd = os.open(self.port, os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
            if not stat.S_ISCHR(os.fstat(fd).st_mode) or not os.isatty(fd):
                raise OSError("--port must identify a serial TTY")
            attrs = termios.tcgetattr(fd)
            tty.setraw(fd, termios.TCSANOW)
            settings = termios.tcgetattr(fd)
            settings[2] &= ~(termios.PARENB | termios.CSTOPB | termios.CSIZE)
            settings[2] |= termios.CS8 | termios.CLOCAL | termios.CREAD
            settings[2] &= ~getattr(termios, "CRTSCTS", 0)
            settings[4] = settings[5] = termios.B115200
            settings[6][termios.VMIN] = 1
            settings[6][termios.VTIME] = 0
            termios.tcsetattr(fd, termios.TCSANOW, settings)
            termios.tcflush(fd, termios.TCIOFLUSH)
            self.serial_fd, self.serial_attrs = fd, attrs
            self.serial_decoder.clear()
            self._interest(fd, "serial", False)
            self._queue_leds(self.colors if self.ready else BLACK)
            LOG.info("Serial connected")
        except (OSError, termios.error):
            if fd is not None:
                if attrs is not None:
                    try:
                        termios.tcsetattr(fd, termios.TCSANOW, attrs)
                    except (OSError, termios.error):
                        pass
                self._unregister(fd)
                os.close(fd)
            self.serial_fd = self.serial_attrs = None
            self.serial_output, self.serial_offset, self.serial_pending = b"", 0, None
            LOG.debug("Serial not available; retrying", exc_info=True)

    def _close_serial(self, now):
        if self.serial_fd is not None:
            fd = self.serial_fd
            self._unregister(fd)
            try:
                if self.serial_attrs is not None:
                    termios.tcsetattr(fd, termios.TCSANOW, self.serial_attrs)
            except (OSError, termios.error):
                pass
            os.close(fd)
            LOG.info("Serial disconnected")
        self.serial_fd = self.serial_attrs = None
        self.serial_output, self.serial_offset, self.serial_pending = b"", 0, None
        self.serial_decoder.clear()
        self.next_serial = now + self.reconnect_seconds
        # Anything waiting for delivery originated on a now-lost serial link.
        if self.daemon is not None:
            self._close_daemon(now)

    def _open_daemon(self, now):
        self.next_daemon = now + self.reconnect_seconds
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.setblocking(False)
        try:
            error = sock.connect_ex(self.socket_path)
            if error not in (0, errno.EINPROGRESS, errno.EWOULDBLOCK, errno.EAGAIN):
                raise OSError(error, os.strerror(error))
            self.daemon = sock
            self.connecting = error != 0
            self.connected_at = now
            self._interest(sock, "daemon", self.connecting)
            if not self.connecting:
                self._daemon_connected(now)
        except OSError:
            sock.close()
            self.daemon = None
            LOG.debug("Daemon not available; retrying", exc_info=True)

    def _daemon_connected(self, now):
        self.connecting = False
        self.connected_at = now
        self._queue_daemon(HELLO)
        self._queue_daemon(SUBSCRIBE)
        self.next_refresh = now + self.refresh_seconds
        LOG.info("Daemon connected; waiting for LED snapshot")

    def _close_daemon(self, now):
        if self.daemon is not None:
            self._unregister(self.daemon)
            self.daemon.close()
            LOG.info("Daemon disconnected; clearing LEDs")
        self.daemon = None
        self.connecting = self.ready = False
        self.colors = BLACK
        self.daemon_decoder.clear()
        self.daemon_output.clear()
        self.activations.clear()
        self._discard_serial_input()
        self._queue_leds(BLACK)
        self.next_daemon = now + self.reconnect_seconds

    def _queue_daemon(self, message, expiry=None):
        if self.daemon is None:
            return False
        data = encode(message)
        queued = sum(len(item[0]) - item[1] for item in self.daemon_output)
        if queued + len(data) > MAX_DAEMON_OUTPUT:
            self._close_daemon(self.clock())
            return False
        self.daemon_output.append([data, 0, expiry])
        self._interest(self.daemon, "daemon", True)
        return True

    def _queue_leds(self, colors):
        if self.serial_fd is None:
            return
        data = encode({"v": 1, "type": "leds", "colors": colors})
        if not self.serial_output or self.serial_offset == 0:
            self.serial_output, self.serial_offset, self.serial_pending = data, 0, None
        else:
            self.serial_pending = data
        self._interest(self.serial_fd, "serial", True)

    def _write_serial(self, now):
        if not self.serial_output:
            return
        try:
            count = os.write(self.serial_fd, self.serial_output[self.serial_offset:])
            if not count:
                raise OSError("serial write returned zero")
            self.serial_offset += count
            if self.serial_offset == len(self.serial_output):
                self.serial_output, self.serial_offset = self.serial_pending or b"", 0
                self.serial_pending = None
            self._interest(self.serial_fd, "serial", bool(self.serial_output))
        except BlockingIOError:
            pass
        except OSError:
            self._close_serial(now)

    def _write_daemon(self, now):
        try:
            while self.daemon_output:
                data, offset, expiry = self.daemon_output[0]
                if expiry is not None and now >= expiry:
                    if offset:
                        # Finishing a partial expired command would execute stale input.
                        self._close_daemon(now)
                        return
                    self.daemon_output.popleft()
                    continue
                count = self.daemon.send(data[offset:])
                if not count:
                    raise OSError("socket write returned zero")
                self.daemon_output[0][1] += count
                if self.daemon_output[0][1] == len(data):
                    self.daemon_output.popleft()
                else:
                    break
            self._interest(self.daemon, "daemon", bool(self.daemon_output))
        except BlockingIOError:
            pass
        except OSError:
            self._close_daemon(now)

    def _handle_serial(self, message, now):
        index = activation_index(message)
        if (index is None or not self.ready or self.daemon is None or
                now - self.last_frame >= self.stale_seconds):
            return
        if len(self.activations) < 16:
            self.activations.append((index, now + 2.0))

    def _pump_activations(self, now):
        if not self.ready or self.daemon is None:
            self.activations.clear()
            return
        while self.activations and now >= self.activations[0][1]:
            self.activations.popleft()
        if self.activations and now - self.last_activation >= self.activation_seconds:
            index, unused = self.activations.popleft()
            if self._queue_daemon({"type": "activate_agent_key", "index": index,
                                   "open": True}, expiry=now + 0.5):
                self.last_activation = now

    def _handle_daemon(self, message, now):
        frame = None
        snapshot = message.get("type") == "snapshot"
        if snapshot and isinstance(message.get("snapshot"), dict):
            frame = message["snapshot"].get("agent_key_led_frame")
        elif message.get("type") == "event" and self.ready:
            event = message.get("event")
            if isinstance(event, dict) and event.get("kind") == "agent_keys_changed":
                frame = event.get("led_frame")
            else:
                return
        else:
            return
        colors = led_colors(frame)
        if colors is None:
            self._close_daemon(now)
            return
        if not self.ready:
            self._discard_serial_input()  # never replay input buffered during startup
        self.ready, self.colors, self.last_frame = True, colors, now
        self._queue_leds(colors)

    def _read_serial(self, now):
        try:
            data = os.read(self.serial_fd, 4096)
            if not data:
                raise OSError("serial EOF")
            for message in self.serial_decoder.feed(data):
                self._handle_serial(message, now)
        except BlockingIOError:
            pass
        except OSError:
            self._close_serial(now)

    def _read_daemon(self, now):
        try:
            data = self.daemon.recv(4096)
            if not data:
                raise OSError("daemon EOF")
            for message in self.daemon_decoder.feed(data):
                self._handle_daemon(message, now)
                if self.daemon is None:
                    break
        except BlockingIOError:
            pass
        except OSError:
            self._close_daemon(now)

    def step(self, timeout=0.1):
        """One event-loop iteration, also usable by deterministic/integration tests."""
        if self.closed:
            return
        now = self.clock()
        if self.serial_fd is None and now >= self.next_serial:
            self._open_serial(now)
        if self.daemon is None and now >= self.next_daemon:
            self._open_daemon(now)
        if self.daemon is not None:
            reference = self.last_frame if self.ready else self.connected_at
            if now - reference >= self.stale_seconds:
                self._close_daemon(now)
            elif not self.connecting and now >= self.next_refresh:
                self._queue_daemon(SUBSCRIBE)
                self.next_refresh = now + self.refresh_seconds
        self._pump_activations(now)
        if now >= self.next_led:
            self._queue_leds(self.colors if self.ready else BLACK)
            self.next_led = now + self.led_seconds
        for key, mask in self.selector.select(min(max(timeout, 0), 0.1)):
            now = self.clock()
            if key.data == "serial" and key.fd == self.serial_fd:
                if mask & selectors.EVENT_READ:
                    self._read_serial(now)
                if self.serial_fd is not None and mask & selectors.EVENT_WRITE:
                    self._write_serial(now)
            elif key.data == "daemon" and key.fileobj is self.daemon:
                if self.connecting:
                    error = self.daemon.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                    if error:
                        self._close_daemon(now)
                        continue
                    self._daemon_connected(now)
                if mask & selectors.EVENT_READ:
                    self._read_daemon(now)
                if self.daemon is not None and mask & selectors.EVENT_WRITE:
                    self._write_daemon(now)

    def close(self):
        """Best-effort dark frame, bounded shutdown, then restore the serial TTY."""
        if self.closed:
            return
        self.closed = True
        self._close_daemon(self.clock())
        deadline = time.monotonic() + 0.2
        while self.serial_fd is not None and self.serial_output and time.monotonic() < deadline:
            self._write_serial(self.clock())
            if self.serial_output:
                time.sleep(0.005)
        self._close_serial(self.clock())
        self.selector.close()

    def run(self):
        try:
            while not self.closed:
                self.step()
        finally:
            self.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", required=True,
                        help="explicit Pico data CDC serial TTY, e.g. /dev/ttyACM0 or /dev/cu.usbmodem...")
    parser.add_argument("--socket", default=os.environ.get(
        "MICROBRIDGE_SOCKET", "~/.microbridge/microbridged.sock"),
        help="local Microbridge Unix socket (default: MICROBRIDGE_SOCKET or ~/.microbridge/microbridged.sock)")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)
    if not os.path.isabs(args.port):
        parser.error("--port must be an explicit absolute serial device path")
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(levelname)s: %(message)s")
    companion = Companion(args.port, os.path.expanduser(args.socket))
    try:
        companion.run()
    except KeyboardInterrupt:
        pass
    finally:
        companion.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
