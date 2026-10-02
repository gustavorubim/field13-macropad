"""Copy to CIRCUITPY root, then power-cycle (soft reload is insufficient)."""
import usb_cdc
import usb_hid
# Keep the REPL console; separate data CDC is exclusively the optional bridge.
usb_cdc.enable(console=True, data=True)
usb_hid.enable((usb_hid.Device.KEYBOARD, usb_hid.Device.MOUSE,
                usb_hid.Device.CONSUMER_CONTROL))
# Keep CircuitPython's legitimate USB VID/PID. Never impersonate ESPressif 303A.
