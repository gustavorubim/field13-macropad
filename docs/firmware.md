# FIELD13 firmware and host setup

## What this prototype implements

**Wired:** standard USB keyboard, consumer/media keys and mouse using CircuitPython
on Raspberry Pi Pico W. No host companion is needed for USB shortcuts.

**Wireless:** opt-in 2.4 GHz Wi-Fi to a foreground Python companion on **Windows**.
The companion authenticates the device and injects only the configured key usages,
media actions and bounded mouse events. It defaults to dry-run. This is a host
software bridge, not Bluetooth HID and not a hardware wireless USB receiver.

**Optional Microbridge:** a separate macOS/Linux USB serial bridge mirrors six
agent LEDs and focuses/opens assigned agent slots through the local daemon's UI
socket. It has no approval/rejection action, no general encoder injection and no
full custom Microbridge Device implementation. Microbridge agent bindings are
rejected in Wi-Fi mode rather than silently doing nothing.

**Not implemented:** Pico W CYW43 Bluetooth/BLE support in this CircuitPython
firmware, microphone/audio processing, a component-specific I2C touch driver,
wireless Microbridge agent/LED routing, or a GUI configurator. I2C and microphone
pins are reserved for a future known module. The Pico W silicon having Bluetooth
capability does not make this program a Bluetooth keyboard.

All control logic is editable Python. Hardware has not been assembled or flashed
for these tests. Do the bring-up checklist before relying on macros.

## GPIO and key identity

| Function | Pico W GPIO | Notes |
|---|---|---|
| Matrix rows R0–R3 | GP0, GP1, GP2, GP3 | Diode cathodes/bands toward rows |
| Matrix columns C0–C3 | GP4, GP5, GP6, GP7 | Anodes toward columns; `columns_to_anodes=True` |
| Encoder A/B / click | GP8 / GP9 / GP10 | Click active-low to ground |
| Joystick click / X / Y | GP11 / GP26 / GP27 | 3.3 V analog supply only |
| Optional touch I2C SDA/SCL | GP12 / GP13 | Reserved; not initialized by runtime |
| Optional six-LED data | GP15 | Electrical level shifting/power per board guide |
| Reserved microphone | GP16 / GP17 / GP18 | No driver or assumed signal order |

Thirteen positions are numbered in visual reading order:

```text
            K00 (r0c1)   K01 (r0c2)
K02 (r1c0) K03 (r1c1)   K04 (r1c2) K05 (r1c3)
K06 (r2c0) K07 (r2c1)   K08 (r2c2) K09 (r2c3)
K10 (r3c0) K11 (r3c1)   K12 (r3c2)
```

The remaining matrix positions do nothing. Every switch needs its own correctly
oriented diode. Do not feed 5 V into a GPIO or ADC. Firmware cannot protect an
incorrectly wired power circuit; use the project's electrical guidance.

## Install on Pico W

1. Download the **Pico W**, not plain Pico, stable CircuitPython UF2 from the
   [official board page](https://circuitpython.org/board/raspberry_pi_pico_w/).
   The APIs used here target CircuitPython 9.x/10.x; use the current stable board
   build and its matching major-version library bundle. No UF2 is bundled.
2. Hold BOOTSEL while connecting USB, copy that UF2 to RPI-RP2, and wait for the
   CIRCUITPY drive. Follow the official board page if recovery is necessary.
3. Copy `firmware/boot.py`, `code.py`, `config.py`, and the complete `macropad/`
   directory to CIRCUITPY. Optionally copy `diagnostics.py`. Do **not** copy host
   `companion/`, tests or `__pycache__` directories onto the device.
4. From the official [CircuitPython library bundle](https://circuitpython.org/libraries),
   copy `adafruit_hid/` into CIRCUITPY/lib. For optional LEDs also copy `neopixel.mpy`.
   Dependencies are not downloaded or executed by this project.
5. Power-cycle. `boot.py` enables keyboard, mouse, consumer control, the REPL
   console CDC and a separate data CDC port. Descriptor changes require a real
   reset; editing `boot.py` alone does not update them. Keep the genuine
   CircuitPython VID/PID. Never use an ESPressif VID such as 0x303A.
6. Start with `TRANSPORT = "usb"`, `COMPANION_ENABLED = False` and
   `RGB_ENABLED = False`. Release every key and center the joystick for at least
   100 ms before input arms. The same rule applies after disconnect or overflow.

## Default behavior and editing

K00–K11 hold F13–F24; K12 is momentary Fn. F13–F24 are intended for application
shortcut assignment, though existing host mappings can already use them. Fn
provides copy, paste, cut, undo, redo, save, Home/End, Page Up/Down, Escape and Tab.
The encoder adjusts volume; its click mutes. With Fn held it scrolls. The joystick
holds arrow keys with diagonal combinations and clicks Enter.

`TARGET_OS = "windows"` selects Control shortcuts. Choose `macos` for Command.
The actual macro tuples live in `config.py`:

```python
from macropad.actions import keys, tap, momentary, toggle, mouse_button, consumer
LAYERS[0]["K00"] = keys("LEFT_CONTROL", "LEFT_SHIFT", "A")
LAYERS[0]["K01"] = tap("LEFT_CONTROL", "S")
LAYERS[0]["K12"] = momentary(1)
LAYERS[1]["K11"] = toggle(2)  # also create layer 2
LAYERS[0]["JOY_CLICK"] = mouse_button(1)
```

`keys` remains held until physical release; `tap` sends a short chord. Unspecified
layer entries are transparent. A release always uses the binding captured on
press, even if the layer changes. Shared modifiers are reference-counted. Use
canonical `adafruit_hid.keycode.Keycode` names, not multiple aliases for the same
usage. USB-compatible keyboard output is six ordinary keys plus modifiers.

`JOYSTICK_MODE` can be `arrows`, `mouse` or `disabled`. Calibration is explicit:
set minimum/center/maximum for each axis and change `inverted` if direction is
backward. Enter/leave thresholds default to 0.35/0.22 normalized travel, providing
hysteresis. No automatic boot centering assumes a held stick is centered. Stop
`code.py` with Ctrl-C in the REPL, then run `import diagnostics; diagnostics.run()`
to read raw ADC, matrix and encoder data without emitting HID. Ctrl-C releases
its GPIO objects. Set `ENCODER_DIVISOR` for the actual detent count; invert in
config if required.

## Windows Wi-Fi setup

1. Keep a matching copy of **the whole firmware directory** on the Windows host.
   Its `config.py` is also the receiver allowlist. After editing the Pico keymap,
   copy the same configuration to the host. Custom HID names may need an explicit
   entry in `macropad/hid_codes.py` and a Windows VK mapping.
2. On the device, copy `settings.example.toml` to `settings.toml` and privately
   enter your own Wi-Fi credentials, host IPv4 and random pairing secret. The
   placeholder is rejected. Generate a fresh 32-byte random secret locally, for
   example with `python -c "import secrets; print(secrets.token_hex(32))"`, and
   place that same value in the host process's `ARC13_PSK` environment variable.
   Do not commit secrets or put them in screenshots or support logs.
3. Use a trusted private WPA2/WPA3 LAN with a compatible 2.4 GHz SSID. Reserve the
   Pico's DHCP address. The firmware prints its assigned address at Wi-Fi startup.
   Restrict host UDP 41413 to that exact device IP yourself. No firewall, account,
   permission or startup-service settings are changed by these scripts.
4. Set `TRANSPORT = "wifi"`, leave Microbridge agent bindings disabled, and reboot.
   Wi-Fi connects only in this mode; USB-mode boot never waits for a network.
5. Start in dry-run, using your actual addresses:

   ```powershell
   python firmware/companion/wifi_companion.py --bind 192.168.1.10 --device 192.168.1.20
   ```

   Inspect report changes. With no keys held, the eight-byte keyboard report is
   all zeroes. Test disconnect, wrong PSK, and host restart before OS input.
6. Only after that, opt in to input:

   ```powershell
   python firmware/companion/wifi_companion.py --bind 192.168.1.10 --device 192.168.1.20 --enable-input
   ```

   The receiver uses Windows SendInput. Elevated applications can reject it due
   to Windows integrity isolation; do not disable security protections to force
   it. No macOS/Linux input injection is supplied. Dry-run is portable.

### Wireless safety and limitations

The wire protocol retains the legacy `ARC13/2` identifier and `ARC13_*` settings
names for compatibility; the hardware/project is FIELD13. It uses HMAC-SHA256 for reports **and handshake messages**, a
fresh host session nonce, monotonically increasing report sequence numbers, a
1,536-byte packet limit, and a configured key/media/button allowlist. It carries
full held-key snapshots and releases host-held keys/buttons after 0.5 seconds
without a valid report. That timeout rotates the session nonce, requiring the
Pico to release and re-arm. Host stop also releases input. It rejects general
commands and arbitrary text execution. Only one exact device IP is accepted.

HMAC authenticates data; it does **not encrypt** key reports or hide timing. This
is a local prototype protocol, not a security audit or an Internet-ready service.
A person with the pairing secret can generate the allowed inputs. Never use it
for passwords, security prompts or safety-critical controls. Disable keyboard
injection while debugging. No credentials are included in this repository.

UDP can lose or reorder packets. Held-state heartbeats arrive about every 50 ms;
short taps use redundant snapshots over about 50 ms. A lost short tap, media or
relative mouse event can still be missed; there is no guaranteed event delivery.
Wi-Fi latency is not gaming-grade. USB is the more reliable transport. On failed
initial Wi-Fi connection the runtime stops safely; correct settings and reset.
After a successful connection CircuitPython handles Wi-Fi reconnection, while
session checks keep remote input disarmed until a live companion returns.

## Optional Microbridge / six LEDs

Use USB mode and the matching local daemon on macOS (Unix socket transport also
works on Linux when a compatible daemon is available). It is **independent of the
Windows wireless companion**. Enable `COMPANION_ENABLED`, then deliberately map
six chosen switches to `agent(0)` through `agent(5)` using the commented example
in config. Enable `RGB_ENABLED` only after the external LED electrical interface
has been verified. The local NeoPixel brightness cap defaults to 15%, multiplied
by the daemon's brightness to limit power; do not treat this cap as power-circuit
protection.

Run the explicit data-port command in [companion/README.md](../firmware/companion/README.md).
The wire contract is pinned to Microbridge commit
`fcd0aba7a4fa360ca8690681bd7b049fa3682f10`. It only subscribes to resolved LED frames
and sends `activate_agent_key` for indices 0–5 with `open:true`. Opening requires
adapter support. No approvals, rejects, interrupts, synthetic encoder events,
upstream device impersonation, or third-party integrations are automatically
configured. No upstream software was installed or run during this build.

## Verification performed and remaining

Run from the project directory:

```sh
python -m unittest discover -s tests/firmware -v
python -m compileall -q firmware
```

At this build: **41 tests passed; 5 Unix-socket/PTY integration tests skipped**
because this cloud VM denies Unix socket creation, including after an escalation
attempt. The skipped tests remain runnable on a normal macOS/Linux machine.
Mock-transport tests cover handshake, six activations in one read, snapshot/event
batches, partial writes, stale queues, fail-dark and disconnection paths. Core
tests cover press/release ownership across layers, shared modifiers, debounce,
axis hysteresis, encoder batch preservation, input re-arming, JSON bounds and
LED validation. Wi-Fi tests cover an RFC 4231 HMAC vector, signed handshake,
wrong secret/session, replay/tampering, allowlist, timeout release/session renewal
and Windows usage mapping. Passing CPython tests does not validate GPIO timing,
CircuitPython compatibility on the actual board, or Windows SendInput behavior.

Before treating it as working hardware:

- Inspect diode polarity and 3.3 V joystick wiring before powering
- Run diagnostics: all 13 positions, both clicks, both encoder directions, ADC ranges
- Validate simultaneous switches, bounce, held modifiers and layer changes
- Unplug/replug USB while keys are held; confirm all keys release and require re-arming
- Check encoder divisor and joystick calibration on the actual parts
- Test all USB media and mouse actions in a disposable editor
- Dry-run Wi-Fi first, then test release on lost radio, host exit/restart and wrong PSK
- Verify Windows input and firewall scope on the intended host, with no sensitive apps open
- Test each Microbridge agent slot and LED, fragmented/batched serial input, daemon restart
- Confirm real LED current and logic levels before enabling its connector

## Primary references

- [Official Pico W CircuitPython download](https://circuitpython.org/board/raspberry_pi_pico_w/)
- [CircuitPython keypad polarity, debounce and queue semantics](https://docs.circuitpython.org/en/latest/shared-bindings/keypad/index.html)
- [CircuitPython rotaryio](https://docs.circuitpython.org/en/latest/shared-bindings/rotaryio/index.html)
- [CircuitPython USB CDC](https://docs.circuitpython.org/en/latest/shared-bindings/usb_cdc/index.html)
- [CircuitPython Wi-Fi API](https://docs.circuitpython.org/en/latest/shared-bindings/wifi/index.html)
- [Adafruit HID API](https://docs.circuitpython.org/projects/hid/en/latest/api.html)
- [Microsoft SendInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)
- [Microbridge pinned protocol](https://github.com/DevVig/microbridge/blob/fcd0aba7a4fa360ca8690681bd7b049fa3682f10/docs/protocol.md)
