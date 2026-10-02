"""CircuitPython hardware boundary; portable modules remain testable on CPython."""
import time
import board
import analogio
import keypad
import rotaryio
import supervisor
import usb_cdc
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode
from adafruit_hid.mouse import Mouse
import config
from macropad.engine import Engine
from macropad.inputs import Axis, EncoderDelta, ArmGuard
from macropad.framing import Lines, encode, led_colors

class Companion:
    def __init__(self, pixels=None):
        self.port = usb_cdc.data if config.COMPANION_ENABLED else None
        self.pixels, self.lines = pixels, Lines()
        self.pending = []
        self.offset, self.deadline = 0, 0
        self.last_frame = None
        self.dark = False
        if self.port:
            self.port.timeout = 0
            self.port.write_timeout = 0
        self.blackout()

    def blackout(self):
        if self.pixels is not None and not self.dark:
            self.pixels.fill((0, 0, 0))
            self.pixels.show()
        self.dark = True

    def activate(self, index):
        # No offline/stale action replay. Bound memory even on a slow host.
        if self.port and self.port.connected and len(self.pending) < 8:
            self.pending.append((encode({"v": 1, "type": "activate", "index": index}),
                                 time.monotonic() + 0.25))

    def poll(self, now):
        if self.port is None or not self.port.connected:
            self.pending[:] = []
            self.offset = 0
            self.lines = Lines()
            self.last_frame = None
            self.blackout()
            return
        try:
            available = self.port.in_waiting
            if available:
                # Bound work per main-loop iteration; parser retains all frames.
                for frame in self.lines.feed(self.port.read(min(available, 512)) or b""):
                    colors = led_colors(frame)
                    if colors is not None:
                        self.last_frame, self.dark = now, False
                        if self.pixels is not None:
                            for index, color in enumerate(colors):
                                self.pixels[index] = color
                            self.pixels.show()
            if self.pending:
                frame, deadline = self.pending[0]
                if now > deadline:
                    # Terminate any incomplete JSON; receiver discards it.
                    if self.offset:
                        self.port.write(b"\n")
                    self.pending[:] = []
                    self.offset = 0
                else:
                    written = self.port.write(frame[self.offset:]) or 0
                    self.offset += written
                    if self.offset == len(frame):
                        self.pending.pop(0)
                        self.offset = 0
        except (OSError, RuntimeError):
            self.pending[:] = []
            self.offset = 0
            self.last_frame = None
        if self.last_frame is None or now - self.last_frame > config.LED_STALE_SECONDS:
            self.blackout()

class Sink:
    def __init__(self, companion):
        self.keyboard = Keyboard(usb_hid.devices)
        self.media = ConsumerControl(usb_hid.devices)
        self.mouse = Mouse(usb_hid.devices)
        self.companion = companion

    def key_down(self, name):
        self.keyboard.press(getattr(Keycode, name))

    def key_up(self, name):
        self.keyboard.release(getattr(Keycode, name))

    def tap_delay(self):
        # USB host must have an opportunity to observe press before release.
        time.sleep(0.008)

    def consumer(self, name):
        try:
            self.media.press(getattr(ConsumerControlCode, name))
            self.tap_delay()
        finally:
            self.media.release()

    def wheel(self, steps):
        self.mouse.move(wheel=steps)

    def mouse_down(self, button):
        self.mouse.press(button)

    def mouse_up(self, button):
        self.mouse.release(button)

    def agent(self, index):
        self.companion.activate(index)

    def release_all(self):
        # Try every endpoint even if a disconnected host rejects one report.
        for device in (self.keyboard, self.media, self.mouse):
            try:
                if device is self.media:
                    device.release()
                else:
                    device.release_all()
            except (OSError, RuntimeError):
                pass

def pin(name):
    return getattr(board, name)

def validate():
    pins = list(config.ROW_PINS) + list(config.COLUMN_PINS) + [
        config.ENCODER_A, config.ENCODER_B, config.ENCODER_CLICK,
        config.JOYSTICK_CLICK, config.JOYSTICK_X, config.JOYSTICK_Y]
    if config.RGB_ENABLED:
        pins.append(config.RGB_PIN)
    if len(set(pins)) != len(pins):
        raise ValueError("GPIO assigned more than once")
    if config.TRANSPORT not in ("usb", "wifi"):
        raise ValueError("Unknown transport")
    if config.JOYSTICK_MODE not in ("arrows", "mouse", "disabled"):
        raise ValueError("Unknown joystick mode")
    if len(config.MATRIX_TO_KEY) != 13 or len(set(config.MATRIX_TO_KEY.values())) != 13:
        raise ValueError("Expected 13 unique matrix keys")
    if not 0 <= config.RGB_BRIGHTNESS_LIMIT <= 0.25:
        raise ValueError("RGB brightness limit must be 0..0.25")
    for layer in config.LAYERS.values():
        for action in layer.values():
            kind = action[0]
            if kind in ("keys", "tap"):
                for name in action[1]:
                    getattr(Keycode, name)
            elif kind == "consumer":
                getattr(ConsumerControlCode, action[1])
            elif kind in ("momentary", "toggle"):
                if action[1] not in config.LAYERS:
                    raise ValueError("Missing layer")
            elif kind == "agent":
                if config.TRANSPORT == "wifi":
                    raise ValueError("Agent bindings require USB companion mode")
                if type(action[1]) is not int or not 0 <= action[1] < 6:
                    raise ValueError("Invalid agent index")
            elif kind not in ("none", "transparent", "wheel", "mouse_button"):
                raise ValueError("Invalid action")

def run():
    validate()
    resources = []
    sink = None
    companion = None
    try:
        matrix = keypad.KeyMatrix(tuple(pin(x) for x in config.ROW_PINS),
                                  tuple(pin(x) for x in config.COLUMN_PINS),
                                  columns_to_anodes=config.COLUMNS_TO_ANODES,
                                  interval=config.SCAN_INTERVAL,
                                  debounce_threshold=config.DEBOUNCE_SCANS,
                                  max_events=64)
        resources.append(matrix)
        buttons = keypad.Keys((pin(config.ENCODER_CLICK), pin(config.JOYSTICK_CLICK)),
                              value_when_pressed=False, pull=True,
                              interval=config.SCAN_INTERVAL,
                              debounce_threshold=config.DEBOUNCE_SCANS, max_events=16)
        resources.append(buttons)
        encoder = rotaryio.IncrementalEncoder(pin(config.ENCODER_A), pin(config.ENCODER_B),
                                             divisor=config.ENCODER_DIVISOR)
        resources.append(encoder)
        analog_x = analogio.AnalogIn(pin(config.JOYSTICK_X))
        resources.append(analog_x)
        analog_y = analogio.AnalogIn(pin(config.JOYSTICK_Y))
        resources.append(analog_y)
        pixels = None
        if config.RGB_ENABLED:
            import neopixel
            pixels = neopixel.NeoPixel(pin(config.RGB_PIN), 6,
                                      brightness=config.RGB_BRIGHTNESS_LIMIT,
                                      auto_write=False)
            resources.append(pixels)
        companion = Companion(pixels)
        if config.TRANSPORT == "wifi":
            from macropad.wifi_transport import WifiSink
            sink = WifiSink()
        else:
            sink = Sink(companion)
        engine = Engine(config.LAYERS, sink)
        engine.release_all()
        guard = ArmGuard()
        x, y = Axis(**config.AXIS_X), Axis(**config.AXIS_Y)
        rotary = EncoderDelta(encoder.position, config.ENCODER_INVERTED)
        joy_active = set()
        next_joystick = 0
        was_connected = False
        last_session = None
        # Scanner reset re-emits held switches; guard requires release first.
        matrix.reset()
        buttons.reset()
        print("FIELD13 ready; release all keys and center joystick to arm")
        while True:
            now = time.monotonic()
            session_changed = False
            if config.TRANSPORT == "wifi":
                sink.poll(now)
                session_changed = sink.session != last_session
                last_session = sink.session
                connected = sink.connected
            else:
                connected = supervisor.runtime.usb_connected
            if not connected or connected != was_connected or session_changed:
                engine.release_all()
                joy_active.clear()
                rotary.reset(encoder.position)
                guard.disarm()
                was_connected = connected
            if matrix.events.overflowed or buttons.events.overflowed:
                engine.release_all()
                joy_active.clear()
                guard = ArmGuard()
                matrix.events.clear()
                buttons.events.clear()
                matrix.reset()
                buttons.reset()
                rotary.reset(encoder.position)
                print("Input overflow: release all controls to re-arm")
            for scanner, names in ((matrix, config.MATRIX_TO_KEY),
                                   (buttons, {0: "ENC_CLICK", 1: "JOY_CLICK"})):
                while True:
                    event = scanner.events.get()
                    if event is None:
                        break
                    name = names.get(event.key_number)
                    if name is None:
                        continue
                    guard.event(name, event.pressed)
                    if guard.armed:
                        if event.pressed:
                            engine.press(name)
                        else:
                            engine.release(name)
            raw_x, raw_y = analog_x.value, analog_y.value
            dx, dy = x.update(raw_x), y.update(raw_y)
            neutral = config.JOYSTICK_MODE == "disabled" or (dx == 0 and dy == 0)
            guard.update(now, neutral=neutral, connected=connected)
            rotary.update(encoder.position)
            if not guard.armed:
                rotary.reset(encoder.position)
            else:
                # Work bounded per loop; multiple detents are retained.
                for unused in range(4):
                    step = rotary.pop()
                    if not step:
                        break
                    engine.pulse("ENC_CW" if step > 0 else "ENC_CCW")
                if now >= next_joystick:
                    next_joystick = now + config.JOYSTICK_POLL
                    if config.JOYSTICK_MODE == "arrows":
                        wanted = set()
                        if dx:
                            wanted.add("JOY_RIGHT" if dx > 0 else "JOY_LEFT")
                        if dy:
                            wanted.add("JOY_DOWN" if dy > 0 else "JOY_UP")
                        for name in joy_active - wanted:
                            engine.release(name)
                        for name in wanted - joy_active:
                            engine.press(name)
                        joy_active = wanted
                    elif config.JOYSTICK_MODE == "mouse":
                        mx = int(x.normalize(raw_x) * config.MOUSE_MAX_STEP) if dx else 0
                        my = int(y.normalize(raw_y) * config.MOUSE_MAX_STEP) if dy else 0
                        if mx or my:
                            sink.mouse.move(x=mx, y=my)
            companion.poll(now)
            time.sleep(0.001)
    finally:
        # An unhandled config/I/O error exits safely instead of replaying keys.
        if sink is not None:
            sink.release_all()
        if sink is not None and config.TRANSPORT == "wifi":
            sink.close()
        if companion is not None:
            companion.blackout()
        for resource in reversed(resources):
            resource.deinit()
