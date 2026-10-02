"""Opt-in Pico W Wi-Fi output. USB and Wi-Fi never inject simultaneously."""
import os
import time
import binascii
import wifi
import socketpool
from adafruit_hid.keycode import Keycode
from macropad.wire import hello, parse_challenge, pack, MAX_PACKET

class WifiSink:
    def __init__(self):
        secret = os.getenv('ARC13_PSK', '')
        if len(secret) < 32 or secret.startswith('REPLACE_'):
            raise ValueError('Set a private random ARC13_PSK with 32+ characters')
        self.key = secret.encode('utf-8')
        self.host = os.getenv('ARC13_HOST', '')
        if not self.host:
            raise ValueError('Set ARC13_HOST to the companion IPv4 address')
        wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
                           os.getenv('CIRCUITPY_WIFI_PASSWORD'), timeout=15)
        print("Wi-Fi local IP:", str(wifi.radio.ipv4_address))
        self.pool = socketpool.SocketPool(wifi.radio)
        self.socket = self.pool.socket(self.pool.AF_INET, self.pool.SOCK_DGRAM)
        self.socket.settimeout(0)
        self.peer = (self.host, int(os.getenv('ARC13_PORT', '41413')))
        self.boot = binascii.hexlify(os.urandom(16))
        self.session, self.sequence = None, 0
        self.pressed, self.buttons = set(), 0
        self.buffer = bytearray(MAX_PACKET + 1)
        self.last_hello, self.last_send = -10, -10
        self.last_challenge = -10
        self.mouse = self  # same move API as USB Sink.mouse

    @property
    def connected(self):
        return self.session is not None and time.monotonic() - self.last_challenge < 2.5

    def report(self):
        modifiers = 0
        codes = []
        for code in sorted(self.pressed):
            if 224 <= code <= 231:
                modifiers |= 1 << (code - 224)
            else:
                codes.append(code)
        if len(codes) > 6:
            raise ValueError('USB-compatible report supports six ordinary held keys')
        return bytes([modifiers, 0] + codes + [0] * (6 - len(codes)))

    def send(self, event=None):
        if self.connected:
            self.sequence += 1
            payload = {'buttons': self.buttons}
            if event:
                payload.update(event)
            try:
                self.socket.sendto(pack(self.key, self.session, self.sequence,
                                        self.report(), payload), self.peer)
                self.last_send = time.monotonic()
            except OSError:
                pass

    def poll(self, now):
        if now - self.last_hello >= 0.5:
            try:
                self.socket.sendto(hello(self.key, self.boot), self.peer)
            except OSError:
                pass
            self.last_hello = now
        for unused in range(4):
            try:
                size, address = self.socket.recvfrom_into(self.buffer)
            except OSError:
                break
            if address[0] != self.host or address[1] != self.peer[1]:
                continue
            try:
                session = parse_challenge(self.key, self.boot, bytes(self.buffer[:size]))
                if session != self.session:
                    self.session, self.sequence = session, 0
                    self.pressed.clear()
                    self.buttons = 0
                self.last_challenge = now
            except (ValueError, TypeError):
                pass
        if now - self.last_send >= 0.05:
            self.send()

    def key_down(self, name):
        self.pressed.add(getattr(Keycode, name)); self.send()
    def key_up(self, name):
        self.pressed.discard(getattr(Keycode, name)); self.send()
    def tap_delay(self):
        # Redundant snapshots improve short-tap delivery; UDP is not lossless.
        time.sleep(0.025); self.send(); time.sleep(0.025)
    def consumer(self, name):
        self.send({'media': name})
    def wheel(self, steps):
        self.send({'wheel': steps})
    def mouse_down(self, button):
        self.buttons |= button; self.send()
    def mouse_up(self, button):
        self.buttons &= ~button; self.send()
    def move(self, x=0, y=0, wheel=0):
        self.send({'x': x, 'y': y, 'wheel': wheel})
    def agent(self, index):
        # Wireless mode is a keyboard/mouse transport, not a Microbridge client.
        pass
    def release_all(self):
        self.pressed.clear(); self.buttons = 0; self.send()
    def close(self):
        self.release_all(); self.socket.close()
