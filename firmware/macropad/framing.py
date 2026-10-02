"""Bounded NDJSON. Preserve every frame in a batch and partial tails."""
import json

class Lines:
    def __init__(self, maximum=2048):
        self.maximum = maximum
        self.buffer = bytearray()
        self.discarding = False

    def feed(self, chunk):
        frames = []
        for byte in chunk:
            if byte == 10:
                if not self.discarding and self.buffer:
                    try:
                        value = json.loads(self.buffer.decode("utf-8"))
                        if isinstance(value, dict):
                            frames.append(value)
                    except (ValueError, UnicodeError):
                        pass
                self.buffer = bytearray()
                self.discarding = False
            elif not self.discarding:
                self.buffer.append(byte)
                if len(self.buffer) > self.maximum:
                    self.buffer = bytearray()
                    self.discarding = True
        return frames

def encode(value):
    return (json.dumps(value) + "\n").encode("utf-8")

def led_colors(value):
    if type(value.get("v")) is not int or value.get("v") != 1 or value.get("type") != "leds":
        return None
    colors = value.get("colors")
    if not isinstance(colors, list) or len(colors) != 6:
        return None
    for rgb in colors:
        if not isinstance(rgb, (list, tuple)) or len(rgb) != 3:
            return None
        if any(type(x) is not int or not 0 <= x <= 255 for x in rgb):
            return None
    return [tuple(rgb) for rgb in colors]
