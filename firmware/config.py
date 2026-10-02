"""Edit this file on CIRCUITPY. All behavior is code-configured; no GUI."""
from macropad.actions import keys, tap, consumer, wheel, momentary, agent, NONE

# Board connector contract: four row cathodes / four column anodes.
ROW_PINS = ("GP0", "GP1", "GP2", "GP3")
COLUMN_PINS = ("GP4", "GP5", "GP6", "GP7")
COLUMNS_TO_ANODES = True
# K00..K12 in visual reading order. The three absent corners are ignored.
MATRIX_TO_KEY = {1: "K00", 2: "K01", 4: "K02", 5: "K03", 6: "K04",
                 7: "K05", 8: "K06", 9: "K07", 10: "K08", 11: "K09",
                 12: "K10", 13: "K11", 14: "K12"}
ENCODER_A, ENCODER_B = "GP8", "GP9"
ENCODER_CLICK, JOYSTICK_CLICK = "GP10", "GP11"
JOYSTICK_X, JOYSTICK_Y = "GP26", "GP27"
# GP12/13: optional I2C SDA/SCL; GP16/17/18 reserved mic. Not driven here.
SCAN_INTERVAL = 0.005
DEBOUNCE_SCANS = 3
ENCODER_DIVISOR = 4  # adjust for actual encoder detents (typically 4 edges)
ENCODER_INVERTED = False
JOYSTICK_MODE = "arrows"  # "arrows", "mouse", or "disabled"
JOYSTICK_POLL = 0.010
AXIS_X = {"minimum": 0, "center": 32768, "maximum": 65535,
          "enter": 0.35, "leave": 0.22, "inverted": False}
AXIS_Y = {"minimum": 0, "center": 32768, "maximum": 65535,
          "enter": 0.35, "leave": 0.22, "inverted": False}
MOUSE_MAX_STEP = 10
TRANSPORT = "usb"  # "usb" or explicit opt-in "wifi"; never both
TARGET_OS = "windows"  # "windows" / "linux" select CONTROL shortcuts
PRIMARY = "LEFT_GUI" if TARGET_OS == "macos" else "LEFT_CONTROL"

# Base: safe unassigned F13..F24, a held Fn key, media encoder and arrows.
LAYERS = {0: {
    "K00": keys("F13"), "K01": keys("F14"),
    "K02": keys("F15"), "K03": keys("F16"), "K04": keys("F17"), "K05": keys("F18"),
    "K06": keys("F19"), "K07": keys("F20"), "K08": keys("F21"), "K09": keys("F22"),
    "K10": keys("F23"), "K11": keys("F24"), "K12": momentary(1),
    "ENC_CW": consumer("VOLUME_INCREMENT"), "ENC_CCW": consumer("VOLUME_DECREMENT"),
    "ENC_CLICK": consumer("MUTE"), "JOY_CLICK": keys("ENTER"),
    "JOY_LEFT": keys("LEFT_ARROW"), "JOY_RIGHT": keys("RIGHT_ARROW"),
    "JOY_UP": keys("UP_ARROW"), "JOY_DOWN": keys("DOWN_ARROW"),
}, 1: {
    "K00": tap(PRIMARY, "C"), "K01": tap(PRIMARY, "V"),
    "K02": tap(PRIMARY, "X"), "K03": tap(PRIMARY, "Z"),
    "K04": tap(PRIMARY, "LEFT_SHIFT", "Z"), "K05": tap(PRIMARY, "S"),
    "K06": keys("HOME"), "K07": keys("END"),
    "K08": keys("PAGE_UP"), "K09": keys("PAGE_DOWN"),
    "K10": keys("ESCAPE"), "K11": keys("TAB"),
    "ENC_CW": wheel(-1), "ENC_CCW": wheel(1),
}}
# To enable six Microbridge agent keys, replace the bindings you choose:
# for i in range(6): LAYERS[0]["K%02d" % (i + 2)] = agent(i)
# The bridge can focus/open an assigned agent; it cannot approve, reject or type.
COMPANION_ENABLED = False
RGB_ENABLED = False  # six external addressable LEDs; see electrical guide
RGB_PIN = "GP15"
RGB_BRIGHTNESS_LIMIT = 0.15  # hard local power/brightness cap
LED_STALE_SECONDS = 2.0

# Wi-Fi is opt-in: see settings.example.toml and companion/wifi_companion.py.
# USB Microbridge agent/LED integration is separate from Wi-Fi HID mode.
# No BLE HID is implemented on this CircuitPython Pico W target.
