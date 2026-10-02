# Optional host companions

Both programs use Python 3's standard library and run in the foreground. Neither
is installed or started by this package. See `../../docs/firmware.md` for pairing,
security boundaries, firmware setup and full bring-up procedure.

## Windows wireless keyboard / mouse

```powershell
# Set ARC13_PSK privately in this process, identical to Pico settings.toml.
# Keep the whole firmware folder so the receiver imports the same config.py.
python firmware/companion/wifi_companion.py --bind 192.168.1.10 --device 192.168.1.20
# Inspect dry-run reports first. Only then explicitly enable OS input:
python firmware/companion/wifi_companion.py --bind 192.168.1.10 --device 192.168.1.20 --enable-input
```

Bind exact trusted-LAN IPv4s; reserve Pico DHCP address. Restrict inbound UDP
41413 to that device in the firewall yourself. Do not expose this port to the
Internet. Authenticated HMAC-SHA256 packets are **not encrypted**. No remote shell,
text command execution, arbitrary hotkey API, or Microbridge routing is provided.
Actual Windows SendInput operation is hardware/OS-untested.

## macOS Microbridge focus and LED mirror

```sh
python3 firmware/companion/microbridge_companion.py \
  --port /dev/cu.usbmodemYOUR_DATA_PORT \
  --socket "$HOME/.microbridge/microbridged.sock"
```

Choose the Pico's **data** CDC port, not its REPL console. No USB VID/PID scanning
or impersonation is used. On Linux the TTY commonly resembles `/dev/ttyACM1`,
but identify it rather than assuming an index. The local daemon must already be
installed and running; this package does not install it or change adapter consent.

Pin inspected: `DevVig/microbridge@fcd0aba7a4fa360ca8690681bd7b049fa3682f10`
(v0.3.10 formula commit). Exact sources:

- [Protocol](https://github.com/DevVig/microbridge/blob/fcd0aba7a4fa360ca8690681bd7b049fa3682f10/docs/protocol.md)
- [Rust message types](https://github.com/DevVig/microbridge/blob/fcd0aba7a4fa360ca8690681bd7b049fa3682f10/crates/mb-protocol/src/lib.rs)
- [Daemon handshake and subscribe implementation](https://github.com/DevVig/microbridge/blob/fcd0aba7a4fa360ca8690681bd7b049fa3682f10/crates/microbridged/src/socket.rs)

Only UI-role `hello` (protocol 0), `subscribe`, and `activate_agent_key` (indices
0–5, `open:true`) go to the daemon. Opening depends on the owning adapter's
`focus_open` capability. No `approve`, `reject`, interrupt, command passthrough,
or encoder injection is present. This is a narrow UI-protocol bridge, not an
upstream custom `Device` implementation and not the full Microbridge hardware.

`snapshot.agent_key_led_frame` and
`event.led_frame` (`kind=agent_keys_changed`) supply six static RGB colors.
Upstream percent brightness and pause are respected; the Pico adds its own local
power cap. Focus/breathing animations are not reproduced. Missing or incompatible
frames fail dark. The companion refreshes its snapshot every two seconds, treats
six seconds without a valid frame as stale, and sends LEDs every 0.5 seconds.
The Pico independently blacks out after two seconds without a valid LED message.

Fragmentation and **all** messages in a serial read are parsed. A bounded FIFO
preserves activation order at five per second, expiring queued input after two
seconds and socket write commands after 0.5 seconds. Disconnection discards
queued activations. This rate cap is intentionally for six agent focus buttons,
not a general keyboard input stream.
