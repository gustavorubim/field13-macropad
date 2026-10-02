"""Declarative bindings: no USB, filesystem, network or arbitrary eval here."""

NONE = ("none",)
TRANSPARENT = ("transparent",)

def keys(*names):
    return ("keys", tuple(names))

def tap(*names):
    return ("tap", tuple(names))

def consumer(name):
    return ("consumer", name)

def mouse_button(number):
    if type(number) is not int or not 1 <= number <= 7:
        raise ValueError("Mouse button mask must use left/right/middle bits 1..7")
    return ("mouse_button", number)

def wheel(steps):
    return ("wheel", steps)

def momentary(layer):
    return ("momentary", layer)

def toggle(layer):
    return ("toggle", layer)

def agent(index):
    if type(index) is not int or not 0 <= index < 6:
        raise ValueError("Agent index must be 0..5")
    return ("agent", index)
