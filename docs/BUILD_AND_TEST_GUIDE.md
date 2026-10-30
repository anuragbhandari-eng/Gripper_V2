# Gripper V2: build and test guide

This guide takes you from a box of parts to a working, portable gripper. Each step ends with a check, so a problem shows up where it starts. Work through it in order and tick the boxes as you go.

**If a check fails,** stop. Copy what the Thonny shell printed, or describe what you see, and ask Claude before going on.

The reference documents behind this guide are:
- [DESIGN_REPORT.md](../gripper_fabrication_rev7/DESIGN_REPORT.md): numbers, print list and the full assembly sequence.
- [BOM.csv](../gripper_fabrication_rev7/BOM.csv): every part.
- [AMAZON_CART_2026-10-24.md](AMAZON_CART_2026-10-24.md): what to buy.

## Safety rules (read once, keep in mind)

1. **Never plug or unplug the motor, or the driver, while the power is on.** That kills the TMC2209 instantly. Unplug the USB-C power first.
2. **The driver current is a safety setting.** Set VREF to 0.99 V before the motor is ever connected, and never higher. At full current the motor can push about 259 N, far more than the printed parts are designed for.
3. **Use 9 V only.** Set the trigger board to 9 V and measure it before it touches the board.
4. **Tighten every M3 screw only until snug,** using the short arm of the key (0.15 N·m). More than that crushes the ABS.
5. **Keep fingers out of the jaws while it's powered.** When the driver is off, the jaws go limp and can be pushed by hand. That is normal: the screw back-drives.

## What you need besides the parts

| Tools | Consumables |
|---|---|
| Soldering iron (a spare or conical tip for heat-set inserts) | Solder, heat-shrink |
| Multimeter | Hookup wire: thin (24 AWG) for signals, thicker (20 AWG) for 9 V and the motor |
| Calipers | 30-minute epoxy, CA (super) glue |
| Hex keys 2, 2.5, 4 and 5 mm, plus a 2.5 mm ball-end | Light grease (fablab) |
| 4.0 mm drill bit, turned by hand | Zip ties |
| Hacksaw or Dremel cut-off wheel, small file | 2 M8 hex nuts (fablab or hardware store) |
| Flush cutters, pliers | A little wax or grease as a release agent |
| Optional: M5 tap | |

Also: a USB-C cable from the laptop to the Pico, a USB-C cable from the power bank to the trigger board, and a 20 W USB-C PD power bank.

---

> **Rev 7.2 (2026-10-26):**
> - The jaws now open to 60.5 mm, just past the firmware's 60 mm limit; the last few millimetres were never used.
> - The lead screw is cut shorter (73.0 mm).
> - A printed cover protects the controller.
> - **Compact controller:** the protoboard is cut to 48 × 60 mm, sits on 4 mm spacers, and its cover is 38% smaller.
> - **Flush dowels:** the dowels are cut to 38.5 mm and pressed through the base, flush top and bottom.
> - 28 heat-set inserts in all.

## Part A. When the parts arrive

### A1. Check the parts

| Part | Check | If it's wrong |
|---|---|---|
| Motor | Body 42 × 42 mm and at most 40 mm long. Pilot Ø22 × 2. M3 holes on a 31 mm square. Screw usable length at least 73 mm | Tell Claude the measurements |
| Brass nut (on the motor screw) | Flange Ø22 × 3.5, body Ø10.2, 4 holes | If it's missing, buy a Tr8x8 flange nut. If the size differs, Claude updates the carriage |
| AS5600 board | At most 23 × 23 mm, with the chip centred. Parts on the chip side within a 19.6 mm square | Tell Claude the board size |
| Shoulder screws | Shoulder Ø4 × 12, thread M3 at most 6 mm long, head at most Ø7.5 × 3.5 | — |
| Dowels | Ø4.0 × 40. A bronze bushing slides onto a dowel with no play | — |
| Lock collar | Bore 8 mm, OD at most 14 mm, width at most 7 mm | — |
| 608ZZ | Spins freely | Use another from the pack |

- [ ] All parts checked

### A2. Print the fit tests first

These small test prints check every fit that depends on your printer. Print them in ABS on the printer you'll use for the real parts. They take a few hours, and they save a full reprint if a fit is off.

1. **13b Fit test gripper.stl (ABS).** Install its 2 heat-set inserts (see D2 for how), then check:
   - [ ] The tongue stub slides into the tip-block pocket stub with no play and no forcing.
   - [ ] The 2 M3×10 screws go in and hold.
   - [ ] An AS5600 board slides into the slot.
   - [ ] An M6 nut drops into its pocket.
   - [ ] The 2020 extrusion fits its socket.
   - [ ] The magnet fits its puck, and the puck fits inside a 608.
2. **13c Fit test pad.stl (TPU).**
   - [ ] It snaps into the pocket-stub groove and doesn't pull out by hand.
3. **13 Fit test coupons.stl (ABS).**
   - [ ] Pin bores: a dowel presses into the Ø3.9 hole, is snug in Ø4.1, and turns freely in Ø4.2.
   - [ ] The stacked test plates move freely in their 0.2 / 0.3 mm gaps.
   - [ ] A 608 sits in the cradle with no rattle and no forcing, against the front lip.
   - [ ] The 11.6 mm tongue slides along the 12.0 mm channel.

Tell Claude the results. If a fit is off, one number in `design.py` changes and the parts are re-exported before you print them.

### A3. Magnet test (before printing the base and cover)

The magnet sits inside the steel 608, which can weaken its field. This 5-minute test confirms the encoder still reads well there.

1. Install MicroPython on the Pico (C1 below).
2. Glue the magnet into the puck from 13b, and push the puck into a 608.
3. Wire the AS5600 to the Pico: VCC → 3V3 (pin 36), GND → GND (pin 38), SDA → GP0 (pin 1), SCL → GP1 (pin 2), DIR → GND.
4. Open [as5600_bench_test.py](../gripper_fabrication_rev7/firmware/as5600_bench_test.py) in Thonny, run it, and turn the 608's inner ring slowly by hand.

- [ ] It prints "magnet: OK" the whole time.
- [ ] AGC sits roughly between 30 and 100.
- [ ] The angle runs smoothly through 0–360° once per turn.

If it says "too weak" or AGC sits at 128, stop and tell Claude. The magnet would then move in front of the bearing, which needs a longer block.

---

## Part B. Print everything

The print list with orientations is in the [design report, section 6](../gripper_fabrication_rev7/DESIGN_REPORT.md), and the files are in `gripper_fabrication_rev7/stl/`.

**Settings:**
- ABS in an enclosed printer, part fan low or off, 0.2 mm layers.
- 4 perimeters, 30–40% gyroid infill, 100% around insert holes.
- Brim on the base, cover and all stand parts. No supports anywhere.

**Order:**
1. Base and cover. These are the largest and most likely to warp.
2. The small parts: carriage, adapter, cranks, conrods and fingers.
3. Both tip sets, the encoder puck, the 4 controller spacers and the electronics cover (26 Electronics cover, top face on the bed).
4. The 4 pads, in TPU.
5. The stand parts. ABS is preferred; PLA is fine if the big base warps.

- [ ] **Flatness check:** lay the base, cover and stand base on a flat surface (glass). Reprint any that rock.
- [ ] Quantities: the cranks, conrods, pads and spacers come in 2s and 4s (see the Qty column).

---

## Part C. Electronics on the bench (while parts print)

### C1. Install MicroPython and Thonny

1. Install [Thonny](https://thonny.org) on your laptop.
2. Download the latest MicroPython UF2 for the **Raspberry Pi Pico (RP2040)** from micropython.org.
3. Hold the Pico's BOOTSEL button while plugging it into the laptop. Drag the UF2 onto the RPI-RP2 drive that appears.
4. In Thonny: Tools → Options → Interpreter → "MicroPython (Raspberry Pi Pico)".
5. Copy [bench.py](../gripper_fabrication_rev7/firmware/bench.py) to the Pico: open it in Thonny, then File → Save as → Raspberry Pi Pico → `bench.py`.

- [ ] Typing `import bench` in the Thonny shell prints the list of tests. Errors about missing hardware are fine at this point.

### C2. Solder the controller board

First cut the 50 × 70 mm protoboard down to **48 × 60 mm**: score along a row of holes and snap it, or saw it. Then drill 4 mounting holes to 3.2 mm, 3 mm in from the long edges (54 mm apart):
- one pair 3 mm from the driver end;
- the other pair 36.5 mm from the driver end, so they land between the Pico's two socket rows.

Screw the board down before plugging the Pico in.

**Layout** (it matches the model, so the cover fits):
- Pico sockets along one long edge, with the USB end at a short edge.
- Driver sockets beside the Pico, toward the other short edge.
- The trigger board taped flat at the USB end, next to the Pico, with its socket just over the edge.
- The 7805 lying flat beside it, legs bent down 90°, tab toward the same edge but 6–7 mm in from it, clear of the corner screw.
- The 100 µF capacitor standing between the 7805 and the driver.
- Keep the 9 V wires short and thick.

| From | To | Notes |
|---|---|---|
| Trigger board + | 9 V line: driver **VM**, 7805 **IN**, 100 k (divider top), 100 µF **+** | Thick wire |
| Trigger board − | Common GND | Thick wire |
| 100 µF 35 V | Across VM and GND, right next to the driver | **Mind the polarity** (stripe = −) |
| 7805 | IN = 9 V, GND, OUT → 1N5817 anode. 100 nF from IN to GND, 100 nF from OUT to GND | Pins left to right, label facing you: IN, GND, OUT |
| 1N5817 | Anode at the 7805 OUT, cathode (the band) → Pico **VSYS** (pin 39) | Lets USB and the 9 V be connected together |
| Divider | 100 k from 9 V to Pico **GP26** (pin 31); 27 k from GP26 to GND | 9 V reads 1.91 V. Optional 100 nF across the 27 k |
| Pico GND (pin 38 and others) | Common GND | |
| Pico **3V3** (pin 36) | Driver **VIO**, AS5600 VCC | |
| Pico GP2 (pin 4) | Driver **STEP** | |
| Pico GP3 (pin 5) | Driver **DIR** | |
| Pico GP4 (pin 6) | Driver **EN** | Plus 10 k from EN to 3V3: keeps the driver off while the Pico starts |
| Pico GP8 (pin 11) | **1 k** resistor → driver **UART/PDN** pin | |
| Pico GP9 (pin 12) | Driver **UART/PDN** pin, directly | Same pin as the 1 k |
| Pico GP5 (pin 7) | Driver **DIAG** | Optional (stall backup) |
| Pico GP0 (pin 1), GP1 (pin 2) | AS5600 SDA, SCL | 4-wire lead; also AS5600 DIR → GND |
| Driver 1A, 1B, 2A, 2B | Motor coils (C6) | |

- **Driver pins:** use the labels printed on the driver board. Leave MS1 and MS2 unconnected; that sets UART address 0.
- **Sockets:** solder a 2 × 20 female socket for the Pico and a 2 × 8 for the driver. Check which way round the driver goes (EN pin to EN) *before* soldering its socket.

### C3. Power check with the boards out of their sockets

1. Set the trigger board to **9 V**. Some boards use a button, some a solder jumper. Plug it into the power bank, and measure **9.0 V ± 0.3** at its output before connecting it to the board.
2. Connect it to the board, with neither the Pico nor the driver plugged in, and measure:
   - [ ] 9 V between the driver socket's VM and GND.
   - [ ] 5.0 V at the 7805 OUT.
   - [ ] 4.6–4.8 V between Pico socket pins 39 (VSYS) and 38 (GND).
   - [ ] About 1.9 V between pin 31 (GP26) and GND.
   - [ ] Nothing gets warm.
3. Unplug the power.

### C4. Pico in: test 1

Plug the Pico into its socket, with the driver still out. Connect the laptop, then the 9 V. In the Thonny shell:

```
import bench
bench.t1_power()
```

- [ ] It prints about 9 V and "OK". With the 9 V unplugged, it prints "none".

### C5. Driver in: set the current, then test 3

1. **Unplug the power.** Plug the driver into its socket. **The motor stays disconnected.**
2. Plug in the 9 V. Measure between the small potentiometer on the driver and GND, and turn the pot with a plastic or ceramic screwdriver until it reads **0.99 V**. That sets a 0.70 A ceiling on the BTT TMC2209 V1.3. On a different driver board, ask Claude for its value first.
3. In Thonny:

```
bench.t3_driver()
```

- [ ] It prints "version 0x21" and "Settings taken … 1/16".

### C6. Make the motor cable

The motor has 4 wires in 2 coil pairs. Find the pairs with the multimeter on ohms: wires of the same pair read about 2.2 Ω; wires from different pairs read open.
- Connect one pair to 1A/1B and the other to 2A/2B.
- If the motor later turns the wrong way, the software fixes it (test 4). There's no need to swap wires.
- **Don't connect the motor to the board yet.**

- [ ] Coil pairs found and the cable made

---

## Part D. Mechanical assembly

The numbers match the [design report's assembly sequence (section 8)](../gripper_fabrication_rev7/DESIGN_REPORT.md), which has more detail.

### D1. Clean up the prints

- [ ] Turn a 4.0 mm drill by hand through every pivot bore in the cranks, conrods, fingers and carriage. **Don't** drill the Ø3.9 dowel press holes in the base. The cover's dowel holes are oversize on purpose.
- [ ] Remove the brims and any strings. Check that the carriage tongue slides along the base channel.

### D2. Heat-set inserts (28)

Set the iron to about 230 °C. Rest the insert on its hole and let it sink in under its own weight plus light pressure until it's **flush with the top face**. Keep it straight.

| Part | Inserts |
|---|---|
| BellCrank Lower U and L | 2 each (F1, D) |
| FrontCrank Lower ×2 | 1 each (F2) |
| Carriage | 2 (lower ears) |
| Fingers ×2 | 2 each, in the tongue underside |
| Base | 6: 2 at the motor-wall joint, 2 at the bearing-block ears, 2 posts |
| Adapter | 4 side holes |
| Cover top | 6: 4 for the controller board, 2 for the electronics cover |

- [ ] 28 inserts in, all flush and straight

### D3. Pins, dowels and bushings

1. **Locating pins:** cut the heads off two M3×16 screws. Screw them into the bearing-block half of the base, 8 mm deep.
2. **Dowels:** cut each 4 × 40 dowel to **38.5 mm**. They are hardened, so use an abrasive cut-off disc (a Dremel or similar), not a hacksaw. Deburr the cut end with a file. Press them up through the base from underneath at O1 and O2 on both sides, square to the plate, until flush with the underside. A bench vise with soft jaws works well. Their tops end flush with the cover top.
3. Smear wax or grease on the top 8 mm of each dowel. This stops the epoxy sticking to the dowel in D10. Then slide a bronze bushing onto each.

- [ ] Pins and dowels in, bushings on

### D4. Prepare the lead screw

1. **Collar pull test:** tighten the lock collar's set screw on the end of the screw. Pull hard by hand: it must not slip. Then take it off.
2. **Cut the screw to 73.0 mm from the motor's mounting face** (71.0 mm past the round pilot), tolerance −0.5 / +0. Never long: the encoder puck fills the last 3 mm.
3. File a small chamfer on the cut end, clean off the chips, and grease the thread.

- [ ] Screw cut to length (measure twice) and greased

### D5–D6. Drive into the base

1. Slide the nut into the carriage from the front: body into the bore, flange into the front recess, holes at 3 and 9 o'clock. Fit 2× M3×8, snug only.
2. Spin the carriage onto the screw from its rear. Slide on the lock collar (set screw loose), then the 608.
3. Lay it all into the base with the motor connector facing **up**:
   - the pilot goes in the wall recess;
   - the carriage tongue goes in the channel;
   - the 608 sits in its cradle against the front lip, with the collar behind it.
4. Fit the 2 lower motor screws (M3×8) through the access slots with the 2.5 mm ball-end.
5. Push the collar forward until it **just touches** the 608 inner ring, with no preload, and tighten its set screw.
6. Turn the motor shaft by hand: the carriage must run end to end without binding. Then tighten the 2 nut screws.

- [ ] The carriage runs the full length smoothly

### D7. Encoder

1. Glue the magnet into the puck, flush. Push the puck into the 608 bore against the screw end, and fix it to the screw end with a drop of CA.
2. Solder 4 wires (VCC, GND, SDA, SCL) to the AS5600 pad row, plus a short link from DIR to GND.
3. Drop the board into the slot in front of the 608, chip toward the magnet and pads up. Lead the wires up through the slit in the cover.

### D8. Linkage (each side)

1. BellCrank Lower on O1 and FrontCrank Lower on O2, bosses up.
2. Finger onto F1/F2. Conrod onto D, and between the carriage ears at C.
3. BellCrank Upper and FrontCrank Upper on top.
4. Shoulder screws at F1, F2, D and C, into the inserts. Snug only.

- [ ] Pushing a finger moves both jaws together smoothly over the full range

### D9. Tip blocks and pads (narrow set first)

1. Slide a TPU pad into a tip block's groove from the rear, and press until its barb snaps past the step. A drop of soapy water helps.
2. Push the tip block up onto the finger tongue from below, and fit 2× M3×10 from below.

### D10. Cover (epoxy: leave it overnight)

1. Put a little epoxy into the 4 oversize dowel holes in the cover.
2. Lower the cover over the bushings and dowels.
3. Fit all its screws: 2× M3×20 at the motor wall, 2× M3×20 at the bearing-block ears, 2× M3×8 at the posts, then the 2 upper motor screws (M3×8) through the cover slots.
4. **Let it cure fully** (overnight) with everything assembled. The bushings bond exactly where the dowels are.

- [ ] Next day: with the power off, push the jaws open and closed by hand over the full range. Smooth, no clicks, no rubbing.

---

## Part E. Controller onto the gripper

1. Unplug the Pico and the driver from their sockets. Put the 4 printed spacers (4 mm) on the cover-top inserts, set the board on them, and fit 4× M3×10 through the board and spacers into the inserts. Then plug the Pico and the driver back in.
2. **Power off:** connect the motor cable to the driver and the AS5600 lead to the board.
3. Zip-tie each cable (USB, power, motor, encoder) to the board as strain relief.
4. **Electronics cover:** lower it over the board, with the cables in the notches at its rim:
   - USB-C to the trigger board and USB-C to the Pico through the two notches on the long side next to the USB sockets;
   - motor cable at the motor end;
   - encoder wires at the jaw end.

   Fit 2× M3×8 through its flanges into the cover-top inserts. The window in its top leaves the Pico's BOOTSEL button reachable for the demo.

---

## Part F. First powered tests (in order)

Set the gripper on the bench, or clamp it in its stand (Part G) first. Plug in the laptop, then the 9 V. Each test tells you what it expects. Run `import bench` once per session.

| Step | Command | Pass when |
|---|---|---|
| F1 | `bench.t1_power()` | About 9 V, "OK" |
| F2 | `bench.t2_encoder()`, pushing the jaws by hand | "magnet OK", and the angle and turns change as the jaws move |
| F3 | `bench.t3_driver()` | "version 0x21", settings taken |
| F4 | `bench.t4_direction()` | Follow the prompts: jaws half open, it moves 2 mm, answer y/n. Ends with "Saved: dir_close=…, enc_sign=…" |
| F5 | `bench.t5_tracking()` | Both moves "OK" (encoder within 0.1 mm of the steps) |
| F6 | `bench.t6_home()` | "Homed". Then the pads open to 30 mm: measure with calipers, within 1 mm |

Then try the gripper:

```
bench.goto(40)     # open to 40 mm
bench.grip()       # put an object between the pads first
bench.goto(40)     # release
```

- [ ] **Grip test:** grip a 500 ml water bottle (about 550 g) by its body and let go of it. It should hang without slipping, even when shaken gently.
- [ ] **Wide tips:** run `bench.off()`. Swap to the wide tip blocks (2 screws each side, slide down). Run `bench.tips('wide')`, `bench.home()`, then `bench.goto(60)`. The pads should be 60 mm apart.

---

## Part G. Bench stand and desk clamps

1. Push the column into the base socket. Fit 2× M5×12 through the socket walls into T-nuts. Optional: M5×12 from below into the column end, if you tapped it M5.
2. Drop an M8 nut into the slot of each desk clamp, and thread a star knob in from below.
3. Put the base on the desk with its front edge flush with the desk's front edge. Hook a clamp over each front corner (its boss drops into the corner counterbore), and tighten the knobs by hand under the black edge.
4. Slide the head bracket onto the column and lock it with 2× M5×12 into T-nuts. Drop 4 M6 nuts into the bracket pockets from the back.
5. Bolt the adapter to the bracket with 4× M6×20. Slide the gripper onto the adapter (the U-slot is open at the rear), and fit 4× M3×8 through the side walls.

- [ ] The stand doesn't move when you push the gripper sideways. It tips over if it's not clamped, so always clamp it.

---

## Part H. Demo mode and taking it with you

**Stand-alone demo (no laptop):** save [main.py](../gripper_fabrication_rev7/firmware/main.py) on the Pico next to `bench.py`. From then on, plugging the USB-C cable into a power bank makes the gripper home itself, open, and grip or release on each press of the Pico's **BOOTSEL** button. To stop the demo, connect Thonny, or delete `main.py` from the Pico.

**Portable kit checklist:**
- [ ] Gripper on its stand, or the stand in pieces
- [ ] 2 desk clamps (they work on edges 24–49 mm thick)
- [ ] Power bank (charged) and its USB-C cable
- [ ] Spare plan for power: any USB-C laptop or phone charger of 18 W or more also gives 9 V
- [ ] A few objects to grip, and the wide tips with 4 M3×10 screws
- [ ] Laptop and USB cable, if you want to show ROS 2 control

**A power bank that switches itself off:** some banks turn off when little current is drawn. The driver stays on at hold current while powered, which normally keeps the bank awake. If yours still switches off, press its button, or use another bank or a wall charger.

---

## Part I. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `t1_power` reads 0 V with power plugged in | Trigger board not at 9 V, or a divider wiring error | Measure the trigger output; check the 100 k / 27 k to GP26 |
| `t1_power` reads 5 V | The trigger board fell back to 5 V: the bank or charger isn't PD, or the trigger isn't set | Use a PD source; set the trigger to 9 V |
| "AS5600 not found" | Wiring | VCC to 3V3, SDA to GP0, SCL to GP1, DIR to GND; check solder joints |
| "magnet too weak / not detected" | Board not centred on the magnet, or too far away | Board fully down in its slot, chip side toward the magnet |
| `t3_driver`: "No reply" | UART wiring or no 9 V | 1 k from GP8 to the UART pin, GP9 straight to the same pin; 9 V present; driver the right way round |
| Motor buzzes but doesn't turn | A coil pair is split across 1A/2A | Redo C6: each pair on 1A/1B or 2A/2B (**power off**) |
| Motor turns, encoder doesn't count | Encoder cable or magnet | `t2_encoder()` while turning the jaws by hand |
| `t5_tracking` off by a lot | Steps lost: binding in the mechanism, or the current too low | Power off and check the hand movement; check VREF is 0.99 V |
| Homing never stops | Encoder not counting | `t2_encoder()`, then `t4_direction()` again |
| Jaws open by themselves when the power is off | Normal: the screw back-drives | Keep the power on to hold a grip |
| Driver very hot | VREF set too high | Set VREF to 0.99 V; the driver normally runs warm, not too hot to touch |
| Gripper slips on objects | Low current at large gaps, or a dry screw | Grease the screw; tell Claude the gap and object |
