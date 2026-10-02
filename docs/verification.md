# FIELD 13 verification status

**A0 is a design prototype. Hardware and fabrication release are not validated.** This file separates checks performed on generated files from tests requiring physical components.

## Completed checks

- Native FreeCAD assembly generated and reopened successfully; 73 individual part solids valid
- 42 specified component/structure Boolean overlap and stack checks passed in `mechanical/validation.json`
- Main shell/PCB/plate have no volumetric overlap in the evaluated assembly
- Exact 13-key count, 1.5 mm MX retention plate and 5.1 mm PCB-top-to-plate-top stack verified
- Independent KiCad ERC and DRC reruns passed with 0 violations, 0 unconnected pads and 0 schematic parity errors; all severities enabled, 0.20 mm minimum track/clearance and 0.50 mm minimum copper-to-edge rule
- CAD-to-PCB alignment checked: all 13 switch centers, all 6 mounts and the final board envelope match; see `mechanical/cad_pcb_alignment.json`
- Schematic XML connectivity comparison covered 137 pins and 39 components, with 0 mismatches at the recorded checkpoint
- Firmware: 41 CPython tests passed, 5 real Unix-socket/PTY integration tests skipped because the VM disallows Unix socket creation; see `docs/firmware.md`
- Direct CAD rendering checked visually before delivery; cosmetic legends/colors are design choices, not populated hardware features

## Not validated by those checks

Physical hot-swap contact fit, pad durability, print shrinkage/warping, insert retention, screw torque, USB cable body/bend radius, joystick full travel under real loads, electrical current consumption, board bring-up, USB descriptors on real hardware, Windows input injection, actual radio connectivity, RF performance, external LED current, capacitive sensing and microphone audio.

The FreeCAD assembly includes documented envelopes for purchased parts. It does not substitute for importing every manufacturer STEP model or measuring received parts. The fit coupon and physical checks in the assembly guide are required before treating the enclosure as print-ready for a particular printer/material combination.

No physical tests or fabrication approval are implied by an empty ERC/DRC report. Do not order a production quantity from this prototype without an independent review and successful first article.
