# FIELD 13 assembly and bench test guide

This guide is for a competent hobbyist building the A0 prototype. Read the verification report first. Do not order boards until the selected parts, PCB footprint orientation and remaining release gates have been reviewed. No physical build has been completed from these files.

## 1 Check the parts and print coupon

Confirm every manufacturer part number against the BOM. A hot-swap socket is not a switch: 13 sockets, 13 MX-compatible switches and 13 keycaps are separate items. Do not substitute Kailh Choc sockets for the specified MX socket.

Open the native FreeCAD assembly and final KiCad PCB. Compare the mounting-hole centers and outline. Print the fit coupon with the intended material/nozzle. Test one switch, one keycap and the selected encoder shaft before printing the complete plate. Adjust the JSON clearances if needed and regenerate all CAD exports together. Check the USB extension’s actual body and screw ears against the panel opening.

The user's printer/nozzle is not fixed by this design. The rigid parts may be GF-ABS or PETG after calibration; feet and joystick cap use TPU. Use a suitable wear-resistant nozzle for abrasive filled filament according to its manufacturer. Dry and print the material according to the filament maker's guidance.

## 2 Prepare the PCB without power

Use eye protection, ventilation/fume extraction and a stable heat-resistant work surface. Disconnect USB and every power source while soldering or inserting/removing switches. Work in an ESD-conscious setup.

1. Inspect the bare board against the final Gerber/PCB view. Confirm the antenna cutout, four USB-shell relief holes, switch holes and all mounting holes
2. Solder the small bottom-side resistors, capacitors and diodes. Diode cathode bands face the matrix row nets; verify against the actual silkscreen and schematic, not a photo alone
3. Solder the 5 V AHCT RGB buffer and its decoupling/pull-down if populating that circuit. Leave optional connectors and bulk capacitor unpopulated for the first bring-up. For later closed-case use, direct-solder insulated wire pigtails at the optional connector pads; the listed standard vertical headers would collide with the plate
4. Align and solder all 13 bottom-side hot-swap sockets. Inspect both pads of every socket and check that the spring contacts are unobstructed
5. Test-fit the Pico W on the underside in the orientation shown by KiCad. Components face away from the carrier. Confirm its USB connector shell solder blobs clear the relief holes and its antenna sits above the carrier cutout. Tack opposite pads, verify flush alignment, then finish soldering
6. Solder the encoder and joystick on the top. Confirm joystick X/Y wipers and common rails against the manufacturer drawing. The potentiometers use 3.3 V, never 5 V
7. Clean flux where appropriate and inspect with magnification. Check for bridges and unintended shorts before fitting any case or keycaps

Do not mount a bare lithium battery or charging circuit. The board is designed for USB or a finished external USB power bank only.

## 3 Electrical checks before USB

With no power connected, inspect/measure:

- No metallic debris, lifted pads, solder bridges or reversed diodes
- GND continuity to the intended ground pads and connector shell where specified
- No hard short between VBUS and GND, or 3.3 V and GND; allow meter readings to settle as capacitors charge
- Each switch closes only its intended row/column path through the diode
- Joystick resistance changes smoothly; wipers are not shorted to the supply rails
- Optional RGB and microphone pins match the connector legends and electrical notes

Use the schematic and actual component datasheets to interpret readings. Do not infer a safe power connection solely from a continuity beep. If any reading is ambiguous, stop and find the cause.

## 4 First power and firmware

Use a protected, current-limited USB source or an appropriate USB current monitor for initial bring-up. Keep the board outside the enclosure on an insulating surface. Stop and disconnect if it heats unexpectedly, draws abnormal current or fails to enumerate.

Flash the official CircuitPython build for Raspberry Pi Pico W, then follow [firmware setup](firmware.md), including the required Adafruit HID library. Use diagnostics before the HID application when possible. Leave Wi-Fi, external LEDs and companion integration disabled.

Record the following in a local build log:

| Test | Expected observation | Result |
|---|---|---|
| Power rails | Stable USB input and 3.3 V rail within component limits | Not run |
| Matrix | Exactly 13 intended positions, no phantom keys | Not run |
| Multi-key | Concurrent presses/releases preserve independent keys | Not run |
| Encoder | Correct direction and one desired action per detent after calibration | Not run |
| Encoder click | Press and release register once, no stuck action | Not run |
| Joystick click | Press and release register correctly | Not run |
| Joystick axes | Center, endpoints and polarity calibrated in config | Not run |
| Layer hold | Held actions release correctly while changing layers | Not run |
| USB reconnect | No stuck keys after removal/reconnect | Not run |

Use a disposable text editor for initial HID tests. Default F13–F24 bindings are intended to be configured by the user; the cosmetic render legends are not a guarantee of a particular app’s shortcuts. Avoid destructive shortcuts during bring-up.

## 5 Assemble the enclosure

1. Install the six short M2.5 heat-set inserts into the underside of the plate. Heat and pilot fit depend on the actual plastic. Keep the insert axes square; do not press through the top face
2. Fit the optional touch cover or leave the area unpopulated as described in the mechanical notes
3. Fit switches into the plate and check that both retention clips engage. Keep switch pins straight. Support hot-swap sockets from below while marrying the plate/switch assembly to the PCB
4. Fit the panel USB extension. Route its slack in the reserved floor corridor and secure it with the tie saddles. Nothing should press on the Pico antenna, joystick pins or bottom-side components
5. Place the PCB on the base standoffs. Confirm the upper plate bosses land above the mounting holes and the reinforcement webs miss the components
6. Insert the six underside M2.5 × 16 mm fasteners. Tighten gently and evenly; excessive torque can damage printed bosses or flex the PCB
7. Fit the encoder knob, joystick cap, keycaps and TPU feet. Confirm full key travel, encoder push travel and joystick travel in every direction without rubbing
8. Re-run the complete wired test sequence after closing the case

The screw head pockets permit a small head projection below the base; the TPU feet provide clearance. Confirm the actual head does not touch the desk. Check that the screw tip does not break through the upper face.

## 6 Optional wireless and agent feedback

Configure Wi-Fi only after wired bring-up succeeds. The Windows companion starts in dry-run mode. Set a unique pairing secret locally and never commit the actual settings file. Restrict the host firewall to the intended private network/device; firewall changes are an explicit user setup step. Test wrong-secret, replay, signal loss, host shutdown and reconnect behavior before enabling real input. Wi-Fi control traffic is authenticated but not a substitute for a trusted network.

Microbridge integration uses a separate USB serial data channel and the pinned local daemon protocol. It supports six focus/open slots and LED feedback, with stale frames failing dark. Test it on the intended macOS host; it is not the Windows wireless HID transport. External LEDs require a verified 5 V/current budget and the level-shifted data interface. Do not power a large strip from an unverified USB source.

Touch sensing and microphone audio are optional follow-on validation items. The microphone bay and I²S pins reserve space and signals only. No claim is made for USB microphone enumeration, audio quality or push-to-talk behavior.

## 7 Before a second board revision

Record mechanical interference, RF behavior with the chosen case material, power consumption, key feel and any fixes to the firmware calibration. Update the board, CAD and parameter source together; re-run ERC, DRC, firmware tests and all critical collision checks. Keep the failed prototype files or photos as evidence rather than silently declaring the first revision production-ready.
