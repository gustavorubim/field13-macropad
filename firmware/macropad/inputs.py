"""Hardware-independent debounce, encoder delta and joystick hysteresis."""

class Debouncer:
    """Emit changes after a raw value remains stable for interval seconds."""
    def __init__(self, interval=0.015, initial=False):
        self.interval = interval
        self.value = bool(initial)
        self.candidate = self.value
        self.since = 0.0

    def update(self, raw, now):
        raw = bool(raw)
        if raw != self.candidate:
            self.candidate, self.since = raw, now
        if raw != self.value and now - self.since >= self.interval:
            self.value = raw
            return raw
        return None

class Axis:
    """3-state axis. Calibrate bounds/center in config; no boot auto-centering."""
    def __init__(self, center=32768, minimum=0, maximum=65535,
                 enter=0.35, leave=0.22, inverted=False):
        if not minimum < center < maximum or not 0 <= leave < enter <= 1:
            raise ValueError("Invalid joystick calibration or hysteresis")
        self.center, self.minimum, self.maximum = center, minimum, maximum
        self.enter, self.leave, self.inverted = enter, leave, inverted
        self.state = 0

    def normalize(self, raw):
        span = self.maximum - self.center if raw >= self.center else self.center - self.minimum
        value = max(-1.0, min(1.0, (raw - self.center) / span))
        return -value if self.inverted else value

    def update(self, raw):
        value = self.normalize(raw)
        if value >= self.enter:
            self.state = 1
        elif value <= -self.enter:
            self.state = -1
        elif self.state == 1 and value <= self.leave:
            self.state = 0
        elif self.state == -1 and value >= -self.leave:
            self.state = 0
        return self.state

class EncoderDelta:
    """Consume a cumulative rotaryio position. Keep the entire delta in order."""
    def __init__(self, initial=0, inverted=False, max_pending=64):
        self.position = initial
        self.pending = 0
        self.sign = -1 if inverted else 1
        self.max_pending = max_pending
        self.overflowed = False

    def update(self, position):
        self.pending += (position - self.position) * self.sign
        self.position = position
        if abs(self.pending) > self.max_pending:
            self.overflowed = True
            self.pending = 0  # stale bursts are unsafe; do not replay them later

    def pop(self):
        if not self.pending:
            return 0
        step = 1 if self.pending > 0 else -1
        self.pending -= step
        return step

    def reset(self, position):
        self.position, self.pending, self.overflowed = position, 0, False

class ArmGuard:
    """After reset/overflow/disconnect require a quiet, fully released device."""
    def __init__(self, interval=0.10):
        self.interval = interval
        self.held = set()
        self.idle_since = None
        self.armed = False

    def event(self, key, pressed):
        if pressed:
            self.held.add(key)
        else:
            self.held.discard(key)

    def disarm(self):
        self.armed = False
        self.idle_since = None

    def update(self, now, neutral=True, connected=True):
        if not connected:
            self.disarm()
        if self.armed:
            return True
        if self.held or not neutral or not connected:
            self.idle_since = None
        elif self.idle_since is None:
            self.idle_since = now
        elif now - self.idle_since >= self.interval:
            self.armed = True
        return self.armed
