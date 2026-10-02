# FIELD 13 — mechanical prototype A0

The assembly is original and inspired by the reference control arrangement. It does not copy the original product's dimensions, industrial design files, marks, or electronics.

## Files and editability

- `mechanical/FIELD13_assembly.FCStd`: native FreeCAD document, individual named BRep solids, dimensions sheet, and separately editable design-profile sketches
- `mechanical/FIELD13_assembly.step`: complete neutral CAD assembly
- `mechanical/stl/`: printable parts and fit coupon, each shifted onto Z=0
- `mechanical/parameters.json`: the authoritative mechanical parameters; edit and run `/usr/bin/python3 scripts/generate_mechanical.py` to regenerate all manufacturing files
- `mechanical/FIELD13_studio.blend`: studio scene built from the same exported assembly geometry

The named BRep components can be inspected and modified with ordinary FreeCAD modeling tools. Changing the displayed dimensions sheet alone does not regenerate the BRep components; use the JSON and generator. Purchased-part geometry is a clearance envelope, not the manufacturer's full manufacturing model.

## Stack and fit

| Item | Dimension |
|---|---:|
| Case footprint | 108 × 122 mm |
| Outside corner radius | 8 mm |
| Base floor / nominal walls | 2.4 / 2.4 mm |
| Main PCB underside / top | 12.0 / 13.6 mm |
| Switch-plate underside / top | 17.2 / 18.7 mm |
| MX plate thickness at retention clips | 1.5 mm |
| PCB top → plate top | 5.1 mm |
| Key center pitch | 20 mm (top→middle 22 mm) |
| Initial switch cutout | 14.1 × 14.1 mm |
| Plate-to-case radial gap | 0.25 mm |
| Fasteners | six underside M2.5 screws |

The switch plate has reinforcement webs between rows and columns. Diodes and hot-swap sockets belong below the PCB. Push an MX switch fully into the plate before fitting its pins into a socket; support the socket from below during insertion. Hot-swap describes future switch replacement, not a solderless assembly process: every socket is soldered to the carrier PCB.

## Materials and first print

The user's stated GF-ABS, PETG and TPU options are retained; no printer or nozzle is assumed. Use GF-ABS or PETG for the rigid case, plain PETG for the RF-adjacent region and touch cover if necessary, and TPU for feet/joystick cap. Carbon-filled material is not treated as a substitute for glass-filled material near the antenna. RF behavior needs a real assembled test.

Print both the switch/shaft and control-aperture fit coupons first using the actual printer, nozzle and material. It includes 13.9/14.1/14.3 mm switch apertures and 6.0/6.2/6.4 mm shaft bores. The control coupon contains the encoder body opening and conservative joystick aperture. The joystick’s 17.8 × 21.3 mm overall body is manufacturer-documented, but its asymmetric offset about the shaft was estimated from the drawing; this requires a received-part fit test. Adjust clearances before a full print. Use the filament maker's temperature/drying settings; for abrasive filled materials, use the nozzle manufacturer’s suitable wear-resistant hardware. No slicer profile is certified here.

Base: floor on bed. Plate: flat upper surface down, bosses/ribs up; no supports inside switch openings. Knob: top on bed if the cosmetic surface permits. Feet: flat on bed in TPU. Check whether your slicer creates disconnected islands and rejects any non-manifold mesh before printing.

## Retention, wiring and service

The six mounts clamp the PCB between the base standoffs and upper plate bosses. Brass inserts are installed into the underside of the plate. Use the specified short insert variant; a longer insert can break through the visible face. Heat and hole fit must be calibrated with the actual plastic. The selected Accu SPP-M2.5-16-ST-BZP DIN 7985Z screw has a 5 mm maximum head diameter and 2.12 mm maximum head height. The 5.4 mm pocket is 1.7 mm deep, so the head may project 0.42 mm below the base, still above the 1.7 mm feet. Confirm this in a dry assembly before purchasing a full batch.

The rear port uses Adafruit 3258, a micro-B extension with 17.3 mm mounting-ear pitch. The port opening and body envelope still require measurement of the received cable. Its excess length routes in the floor corridor, secured by the two tie saddles, without loading the Pico USB connector. Do not substitute a power-only cable. The superficially convenient Adafruit 4056 USB-C adapter is deliberately not the baseline because its manufacturer warns of missing Type-C negotiation resistors.

Pico W is directly soldered to the underside carrier pads, with components facing the base. The antenna has the official 14 × 9 mm carrier cutout plus a larger no-copper/no-metal area. The module remains interior-mounted in this compact prototype. Antenna performance and interference are not established by a CAD check.

## Optional features

The touch position is a replaceable dielectric disc. The electrode/controller is optional and must be tested through the selected cover thickness. The optional vertical headers do not fit beneath the closed plate as drawn. Use direct-solder insulated wire pigtails at the same pads for a closed-case prototype; do not populate the listed vertical header variants without redesigning and measuring their mating clearance. The rear/front board connector reservations provide optional RGB and I²S microphone signals; they are not a claim of a working audio implementation. The microphone bay is reserved space only, hidden in finished renders.

## Release gates

This is a design prototype, not a fabrication release. Mechanical Boolean checks do not establish real fit, strength, switch feel, wear, cable bend radius, antenna performance or print shrinkage. Before ordering a PCB or printing the full case:

1. Confirm the selected controller, socket, switch, encoder and joystick drawings against the received parts
2. Print the fit coupon and adjust the parameter file
3. Verify the exact USB cable body, plug length and bend route
4. Verify the final KiCad board outline, drill positions and component envelopes in the FreeCAD assembly
5. Dry-fit the plate/PCB/fasteners, then test every switch socket with power disconnected
6. Perform the electrical bring-up and firmware checks in the assembly guide
