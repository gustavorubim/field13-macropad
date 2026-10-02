# FIELD 13 carrier electronics revision A

Engineering prototype, not a fabrication release. The supplied PCB is a real editable two-layer KiCad design with connected nets, routed copper, plated vias, manufacturer-derived footprints and an antenna cutout. Electrical and physical review gates are distinct: an ERC/DRC pass does not certify the new footprints, RF performance, USB budget, or printed assembly fit.

## Verification snapshot

The final KiCad 9 check includes all severities and schematic parity. `reports/DRC.rpt` and `DRC.json` report 0 violations, 0 unconnected pads and 0 footprint/parity errors under 0.20 mm trace/clearance and 0.50 mm edge rules. `reports/ERC.rpt` and `ERC.json` report 0 violations. The exported netlist was independently compared against all 137 electrical pin mappings. Physical review gates below remain open.

## Open and inspect

Open `electronics/macropad.kicad_pro` in KiCad 9. The main schematic is `macropad.kicad_sch`; the final PCB is `macropad.kicad_pcb`. Project-local symbol and footprint libraries are included. `net_manifest.json` gives the exact component/pin/net contract. `exports/` contains schematic SVG, PNG, PDF and native/XML netlists. `previews/` contains PCB top and mirrored-bottom SVG/PNG. `reports/` contains unfiltered KiCad checks and independent connectivity validation. Manufacturer sources are linked in the BOM; downloaded third-party datasheets are not republished in the repository.

Build scripts are editable. Do not run `build_pcb.py` over an edited PCB: it recreates placement and initial escape tracks; the full routing workflow is described below. The schematic generator also recreates its outputs.

## Geometry and assembly

- Case datum: rear is y=0, front y=122, width 108 mm
- Carrier: x 4..104, y 3.5..116, R6 corners, 1.6 mm thickness, PCB top Z 13.6 and bottom Z 12
- Six unplated Ø2.7 M2.5 clearance holes at (9,9), (99,9), (9,63), (99,63), (9,111), (99,111)
- Key centers: top (44,37),(64,37); rows x 24,44,64,84 at y 59 and 79; bottom x 24,44,64 at y 99
- Encoder shaft center (24,37); bare joystick shaft center (84,37)
- Optional vertical headers J1/J2/J3 are DNP and do not fit the closed case: their pin height exceeds the 3.6 mm PCB-to-plate gap. Use direct-solder insulated wire pigtails to the same pads for fitted options; validate strain relief and cable clearance
- Touch connector J1 runs horizontally from x 91 to 98.62 at y 94; it is a connector for an optional external module, not an onboard touch sensor
- RGB J2 at x 19..24.08,y 15; mic J3 at x 20..32.7,y 23; these and the encoder/joystick are front-side parts
- All 13 hot-swap sockets and diodes, Pico W, RGB buffer and passive parts are on the back
- Optional C2 is a 5.8 mm-tall underside part. It is DNP by default; do not assume the 4 mm socket clearance is sufficient for it

### Pico W mounting and RF

Pico W body outline is x 42..93,y 5..26. USB faces left, antenna right. Solder its castellations directly to carrier bottom pads with its components facing away from the carrier. No plug-in header stack is used. A real 14×9 mm carrier cutout is x 84..93,y 8.5..22.5. Copper rules prevent routing through the antenna window/end region. The underside interior beneath the module is also kept free of copper to avoid shorting exposed module testpoints. Four Ø2 mm unplated relief holes beneath USB shell solder joints reduce the risk of solder bulges holding the module off the carrier.

The rear board edge was extended 0.5 mm from y 4 to y 3.5, retaining R6 corners, to preserve a 0.5 mm copper-to-edge rule beneath the Pico pad row. Two vias near the antenna cutout were moved to y 7.68, with adjacent tracks rechecked.

A minimum mechanical no-metal volume of x 81..96,y 5.5..25.5 is reserved around the antenna. The module's own required castellated pads occupy the flanking rails; the carrier does not add a ground fill there. The right-rear nonmetallic printed boss has a 3.4 mm radius to support the heat-set insert. Its plastic enters the added 3 mm allowance by 0.4 mm; the brass insert (2.1 mm radius) and screw head (2.5 mm radius) stay outside the no-metal region. This nearby plastic is another reason RF performance must be measured. The enclosure is plain polymer near the antenna. This remains an interior-antenna arrangement; Raspberry Pi recommends board-edge placement. Measure wireless range with the final case and compare against a bare Pico W before accepting the arrangement. Avoid conductive filament, metalized paint, a battery, or bundled USB cable in this volume.

Raspberry Pi's datasheet explicitly specifies the 14×9 mm cutout and warns that nearby objects in any dimension reduce antenna effectiveness. The extra 3 mm margin is this prototype's engineering allowance, not a manufacturer guarantee. See the [Pico W datasheet](https://datasheets.raspberrypi.com/picow/pico-w-datasheet.pdf), mechanical section 2.2.1.

### Switch sockets

Kailh CPG151101S11-16 uses two Ø3 mm socket openings, 6.35 mm horizontal and 2.54 mm vertical separation. Custom pads are 2.55×2.5 mm at (-7.385,-2.54) and (6.115,-5.08) relative to key center. Stem hole Ø4 mm; optional five-pin switch locating holes Ø1.7 at x±5.08. Socket pads are on B.Cu. The pads were derived from the [manufacturer drawing](https://www.kailhswitch.com/Content/upload/pdf/202215927/CPG151101S11-16.pdf), matching the supplied earlier prototype reference. Print a footprint/plate coupon and physically insert the actual socket and switch before ordering a full carrier. No manufacturer's solderability or tolerance certification is claimed.

### Encoder

Chosen exact part is [ALPS EC11E15244B2](https://tech.alpsalpine.com/e/products/detail/EC11E15244B2/), 15 pulses, 30 detents, push travel 1.5 mm. Its current catalog uses Drawing 3. PCB mounting plane to tip is 24.5 mm, so the bare tip is Z 38.1 mm; the advertised 20 mm actuator dimension starts at the front of the 4.5 mm-thick encoder body. Shaft Ø6 with 4.5 mm flat dimension; the D-flat extends 10 mm down from the tip. Front body envelope is approximately 11.7×12 mm. The selected footprint is KiCad's EC11E vertical H20 switch footprint, with shaft center offset (7.5,2.5) from its pad-A origin. Verify its mounting tabs and slots against the purchased lot and current manufacturer drawing before fabrication.

### Joystick

Chosen exact part is [ALPS RKJXV1224005](https://tech.alpsalpine.com/e/products/detail/RKJXV1224005/), two 10 k linear pots and push switch. Its body is 17.8×21.3×11.2 mm; bare shaft reaches 18.95 mm above PCB, so tip Z 32.55. Boss projects 0.75 mm below its mounting plane, motion ±23°. The manufacturer's mounting-side diagram is saved next to the dimensional drawing. Pot terminals are at y=-8.73 with x=-2.5,0,2.5 and at x=8.73 with y=-2.5,0,2.5. Switch terminals are at x±4.3,y 0. Manufacturer-prohibited front-side wiring regions are covered conservatively by copper keepouts.

The F.Fab body outline uses approximately x−8.1..+9.7,y−9.4..+11.9 relative to shaft, interpreted from the manufacturer drawing scale. The 17.8×21.3 overall size is dimensioned, but these asymmetric shaft-to-body offsets are not independently dimensioned. They are explicitly provisional; the mechanical aperture includes extra allowance and requires a physical coupon.

This part is officially Not Recommended for New Designs. The exact part was offered by LCSC at the dated BOM check; availability can change. RKJXV122400R is not silently substituted: it has a different stated 18.2×21.7 mm envelope and must be reviewed as a distinct part. The custom joystick footprint, mounting tab drills, and shaft cap fit are first-article review gates.

## Electrical contract

| Function | Pico GPIO | Physical pins / notes |
|---|---|---|
| Rows 0..3 | GP0,1,2,3 | 1,2,4,5; drive one row low |
| Columns 0..3 | GP4,5,6,7 | 6,7,9,10; pull-up inputs |
| Encoder A/B/click | GP8,9,10 | 11,12,14; common and click return GND |
| Joystick click | GP11 | 15; active low |
| Optional touch SDA/SCL | GP12,13 | 16,17; I2C0; 3.3 V only |
| Optional six-pixel RGB | GP15 | 20; TTL-input AHCT buffer shifts to 5 V |
| Optional I²S BCLK/WS/DATA | GP16,17,18 | 21,22,24; reserved connector |
| Joystick X/Y | GP26,27 | 31,32; ADC0/1 |

The matrix positions are r0c1–r0c2; r1c0–r1c3; r2c0–r2c3; r3c0–r3c2. Each electrical path is COL → switch → diode anode → diode cathode → ROW. D1–D13 pin 1 is cathode. Firmware must scan columns with pull-ups while sinking one selected row. Never drive a column high against a selected low row through a pressed key.

Joystick pots are powered from 3V3, not 5 V. Direction and neutral deadband need calibration using the assembled joystick. Mechanical encoder contacts use GPIO pull-ups and firmware debounce; no 5 V signals go directly to Pico GPIO.

U2 is SN74AHCT1G125DBVR powered from USB 5 V, /OE grounded, with 100 nF bypass. Its input uses a 10 k pull-down, output a 330Ω series resistor. J2 pin 1=5V_USB,pin 2=RGB_DOUT,pin 3=GND. This is a low-speed pixel output, not a bidirectional 3.3 V expansion pin.

J1 pin 1=3V3,2=GND,3=SDA,4=SCL; optional 4.7 k pull-ups R1/R2 are DNP if a chosen module already supplies them. J3 pin 1=3V3,2=GND,3=BCLK,4=WS,5=DATA,6=GND. A microphone module must be a compatible 3.3 V I²S device; no microphone is fitted in this carrier revision.

## Power limits

The baseline is USB-only through the Pico W micro-B connector and the selected Adafruit 3258 panel extension. There is no lithium charging, protection, boost stage, battery connector, or battery firmware here. A finished external USB power bank may be used only as a 5 V USB source.

Do not allow six pixels at unrestricted full-white current. Start with all RGB off; target a conservative total pixel budget of 60 mA, then measure total USB draw with wireless transmitting and all options fitted. Confirm USB enumeration/descriptors and available host current. The optional 100 uF C2 is DNP until USB inrush is measured and accepted. Neither successful routing nor ERC measures power consumption or USB compliance.

## PCB manufacture and validation gates

The carrier uses two copper layers, nominal 0.25 mm signal routes, local 0.20 mm finished neckdowns, 0.20 mm clearance, 0.60 mm vias with 0.30 mm drills, and 0.50 mm copper-to-edge minimum. No ground pours were added; ground is explicitly routed. Confirm these limits with the intended fabricator and review current return paths, especially RGB current and ADC noise. This is a conservative first functional prototype, not an RF-optimized layout.

Before an order: read the final DRC report, inspect routed previews, confirm every custom footprint on a 1:1 print against physical parts, inspect the cutout and four USB relief holes, verify case ribs and component underside heights, and obtain a second PCB review. Before full assembly: print the mechanical fit coupon, test the matrix and controls on the bench, check supply polarity and USB draw, then assemble the case and repeat RF/joystick sweep tests.

## Reproducible routing

`build_pcb.py` uses system KiCad 9 pcbnew to create project footprints, placement, keepouts, and initial escapes, then writes Specctra `macropad.dsn`. The supplied routed PCB was made with official Freerouting 2.4.1 headless, followed by `finish_routes.py` to close two remaining connections against actual obstacles and KiCad DRC. Freerouting sources/release: https://github.com/freerouting/freerouting/releases/tag/v2.4.1 . The downloaded runtime is a temporary build tool, not included or installed on the user's computer.

The final PCB must be treated as authoritative. Re-running placement alone destroys its routing. The source scripts and final check reports preserve the reproducible design logic and verification evidence. Temporary `.dsn`, `.ses`, router executables and raw logs are excluded from the published repository; they are regenerated during a fresh routing run. Router-local 'violations' are not presented as KiCad results; the final KiCad report is the relevant geometric check. All reported physical manufacturing limits still require a first-article review.
