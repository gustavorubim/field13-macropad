# FIELD13 firmware prototype

Start with [the complete setup and verification guide](../docs/firmware.md).

- `boot.py`, `code.py`, `config.py`, `macropad/`: copy to CIRCUITPY
- `diagnostics.py`: optional non-HID hardware calibration tool
- `settings.example.toml`: placeholders only; Wi-Fi is opt-in
- `companion/wifi_companion.py`: Windows authenticated Wi-Fi HID, dry-run by default
- `companion/microbridge_companion.py`: macOS/Linux USB serial → local Microbridge v0, focus/LED only

USB is the default. No software or services are installed automatically. Real
CircuitPython, GPIO, USB enumeration, Windows input injection and radio operation
have **not** been tested on physical hardware. This is prototype source, not a
factory-ready binary or Bluetooth firmware.
