"""Layered bindings with ownership: release the action captured on press."""
from macropad.actions import NONE, TRANSPARENT

class Engine:
    def __init__(self, layers, sink, base=0):
        if base not in layers:
            raise ValueError("Missing base layer")
        self.layers, self.sink, self.base = layers, sink, base
        self.active = {}  # physical ID -> captured binding
        self.held_layers = []
        self.toggled = []
        self.key_refs = {}
        self.mouse_refs = {}

    def layer_order(self):
        result = []
        for layer in [item[1] for item in reversed(self.held_layers)] + list(reversed(self.toggled)) + [self.base]:
            if layer not in result:
                result.append(layer)
        return result

    def binding(self, physical):
        for layer in self.layer_order():
            value = self.layers[layer].get(physical, TRANSPARENT)
            if value != TRANSPARENT:
                return value
        return NONE

    def _acquire(self, refs, values, down):
        for value in values:
            if not refs.get(value, 0):
                down(value)
            refs[value] = refs.get(value, 0) + 1

    def _release(self, refs, values, up):
        for value in values:
            count = refs.get(value, 0)
            if count <= 1:
                refs.pop(value, None)
                if count:
                    up(value)
            else:
                refs[value] = count - 1

    def press(self, physical):
        if physical in self.active:
            return  # debounce/repeated press must not double-own keys
        action = self.binding(physical)
        self.active[physical] = action
        kind = action[0]
        if kind == "keys":
            self._acquire(self.key_refs, tuple(dict.fromkeys(action[1])), self.sink.key_down)
        elif kind == "tap":
            values = tuple(dict.fromkeys(action[1]))
            self._acquire(self.key_refs, values, self.sink.key_down)
            try:
                self.sink.tap_delay()
            finally:
                self._release(self.key_refs, values, self.sink.key_up)
        elif kind == "consumer":
            self.sink.consumer(action[1])
        elif kind == "wheel":
            self.sink.wheel(action[1])
        elif kind == "mouse_button":
            self._acquire(self.mouse_refs, tuple(bit for bit in (1, 2, 4) if action[1] & bit), self.sink.mouse_down)
        elif kind == "momentary":
            if action[1] not in self.layers:
                raise ValueError("Unknown layer")
            self.held_layers.append((physical, action[1]))
        elif kind == "toggle":
            if action[1] not in self.layers:
                raise ValueError("Unknown layer")
            if action[1] in self.toggled:
                self.toggled.remove(action[1])
            else:
                self.toggled.append(action[1])
        elif kind == "agent":
            self.sink.agent(action[1])
        elif kind not in ("none", "transparent"):
            raise ValueError("Unknown action: " + str(kind))

    def release(self, physical):
        action = self.active.pop(physical, NONE)
        if action[0] == "keys":
            self._release(self.key_refs, tuple(dict.fromkeys(action[1])), self.sink.key_up)
        elif action[0] == "mouse_button":
            self._release(self.mouse_refs, tuple(bit for bit in (1, 2, 4) if action[1] & bit), self.sink.mouse_up)
        elif action[0] == "momentary":
            self.held_layers = [item for item in self.held_layers if item[0] != physical]

    def pulse(self, physical):
        self.press(physical)
        try:
            self.sink.tap_delay()
        finally:
            self.release(physical)

    def release_all(self):
        """Use on disconnect, scan overflow, shutdown or any runtime exception."""
        self.active.clear()
        self.key_refs.clear()
        self.mouse_refs.clear()
        self.held_layers[:] = []
        self.toggled[:] = []
        self.sink.release_all()
