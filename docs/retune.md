# Retune

Every tune, in one menu. On the printer: **MENU → Calibrate → Retune** (or
type `RETUNE`). Pick any tune on its own, or for a full retune go top to
bottom: each one assumes the ones above it. Belts change the resonances, so
input shaping comes after them; the ERCF must load reliably before filament
tests; pressure advance comes before extrusion multiplier. Each tune's dialog
has its instructions, target values and buttons. "Mark done" ticks it (ticks
survive restarts) and the first unticked tune is highlighted.

| Group | Tunes |
|---|---|
| Motion | Mechanical check, Belts, Mesh and QGL edges, Input shaper |
| Heaters | PID |
| ERCF | Selector and servo, Gear/encoder/bowden, Filamentalist tension, Per-gate calibration, Toolhead distances, Soak test |
| Print | Extruder check (optional), First layer, PA and EM per filament |

Results that Klipper calculates (PID, input shaper) are saved by a **Save**
button in the result dialog. That runs `SAVE_CONFIG`, which writes them to the
block at the bottom of `printer.cfg` and restarts Klipper. `tools/deploy.py`
keeps the printer's values in that block when it deploys, so saving on the
printer is safe. Values you type into the repo by hand (`max_accel`, damping
ratios, `hot_nozzle_offset`, rotation distances) are noted in each step.

## 1. Mechanical check

Before anything is measured.

- **Toolhead:** every screw snug: cowl, hotend, extruder, Beacon mount,
  carriage. A cowl screw that has pulled through the plastic no longer clamps
  anything: put a washer under it, or reprint the part. A loose cowl rattles,
  which shows up as noise in the shaper graphs and can move the part-cooling
  duct. Tap the toolhead: nothing should rattle.
- **Gantry:** XY joint and idler screws tight. Nothing loose on the umbilical
  or bowden.
- **BFI tensioners:** turn both screws on a tensioner by the same amount, so
  the idler stays square and the belt runs centred on it rather than riding
  one flange. Lock the screws (threadlocker or nylocs): BFI users report them
  backing off.

The dialog's **Service position** button brings the toolhead to the front and
lifts the gantry.

## 2. Belt tension

With the printed tension meter (PF Makes / Diyshift GT2 RC2 design).

1. **Calibrate the meter first.** On its music-wire jig it should read
   **1.9**. Adjust its preload screw until it does.
2. **Z belts:** **2.5–2.8** on the meter (EPDM belts 2.6–2.9). All four the
   same.
3. **A and B:** printer cold, motors on (homed), toolhead centred. The dialog's
   **Move to the belt-check position** button homes and moves to
   `belt_check_position_xy` (175,175, about 150 mm from the front idlers; set
   in `config/variables.cfg`). Measure the long run of each belt, about 150 mm
   of span. **1.8–2.2** (EPDM 1.9–2.3). Read each one three times.
4. A and B affect each other: tightening one raises the other a little. Go back
   and forth until both read the same.
5. **Belt comparison** (Shake&Tune `COMPARE_BELTS_RESPONSES`): the two curves
   should overlap, with a similarity of **90 % or more**. If not, adjust the
   looser belt slightly and repeat. Graphs are in `ShakeTune_results`.

## 3. Mesh edges and QGL points

From PR #29 (wider mesh and QGL points). Run QGL from the dialog and watch each
of the four probe points: Beacon must be fully over the plate, clear of edges,
clips and magnets. Then **Full bed mesh**: in Fluidd's mesh view there should be
no sudden drop or jump along any edge. If there is, move that `mesh_min` or
`mesh_max` in by 5–10 mm (`config/software/bed_mesh.cfg`).

## 4. Input shaper

Bed at printing temperature (the dialog has a button), because heat changes
belt tension.

- **a) Axes map**, once: `AXES_MAP_CALIBRATION` checks Beacon's accelerometer
  orientation. If it reports something other than what is configured, set
  `accel_axes_map` in `[beacon]`.
- **b) Shaper graphs** (Shake&Tune `AXES_SHAPER_CALIBRATION`): one clean peak
  per axis is the goal. Extra peaks usually mean something loose (back to step
  1). Note the damping ratios the graphs report.
- **c) Measure and apply** (`SHAPER_CALIBRATE`): Klipper picks a shaper and
  frequency per axis and applies them at once. **Save** keeps them.

Then by hand, in the repo:

- `max_accel` (`config/machine.cfg`): the lower of the two recommended maximum
  accelerations Klipper prints in the console.
- `damping_ratio_x` / `damping_ratio_y` (`config/software/input_shaper.cfg`)
  from the Shake&Tune graphs. `SHAPER_CALIBRATE` doesn't save these.

Square corner velocity is 5 (PR #30), and the graphs account for it.

## 5. PID

Nozzle and bed, at the default print temperatures. Each takes a few minutes and
shows the result with a **Save** button. Saving restarts Klipper, so do one,
save, then the other.

## 6. ERCF

Happy Hare v4's order: selector, gear, encoder, bowden, per-gate, toolhead.
Redoing the gear means redoing encoder, bowden and per-gate; selector and
toolhead can be redone any time. Each dialog marks a step done once Happy Hare
has a saved value for it.

Old v3 values, as a sanity check (from `mmu.V3/mmu_vars.cfg`):

| | v3 value |
|---|---|
| Selector offsets | 3.2, 26.6, 50.0, 73.4, 96.8, 120.2, 143.6, 167.0 |
| Gear rotation distance | about 23.0 (gate 0: 23.5984) |
| Encoder resolution | 0.9535 |
| Bowden length | 1198.9 mm |
| Servo angles | down 75, up 155, move 132 |

### Selector and servo

Press **Motors off**, slide the selector by hand until it lines up with gate 0,
then **Calibrate** (`MMU_CALIBRATE_SELECTOR AUTO=1`): it sweeps the full travel
and works out every gate. **Check** homes and goes to gate 7.

Servo: **Up**, **Down** and **Move** show each position. Up lets the filament
slide freely, down grips it, move holds it while clearing everything as the
selector travels. To adjust one: `MMU_SERVO ANGLE=…` until it's right, then
`MMU_SERVO POS=up SAVE=1` (or `down` / `move`).

### Gear, encoder and bowden (gate 0)

1. **Gear:** filament in gate 0. **Advance 50 mm** pushes it out of the ERCF.
   Cut it flush where it leaves the ERCF. **Move 100 mm**
   (`MMU_TEST_MOVE MOVE=100 GRIP=1`) and measure what came out, then type
   `MMU_CALIBRATE_GEAR MEASURED=<mm>` in the console. Move 100 mm again to
   check it now comes out at 100.
2. **Encoder:** automatic (`MMU_CALIBRATE_ENCODER`). Needs the gate 0 filament
   past the encoder, which step 1 leaves it.
3. **Bowden length:** automatic (`MMU_CALIBRATE_BOWDEN`). It loads gate 0 to the
   extruder and records the length.

### Filamentalist tension

The Filamentalist's tension should be as light as will still rewind. The
advice from its designers on the Armchair Heavy Industries Discord: with no
filament loaded, turn the tension screw until it just touches the top washer.
(That advice was given for the EMU build, which uses the same Filamentalist
with the EMU's spring and two washers; check yours uses the same parts.)

Then test each gate (filament unloaded, all gates parked): the gate's button
pushes its filament 300 mm into the bowden, pulls it back, and parks it again
(`MMU_TEST_MOVE MOVE=300`, `MOVE=-300`, `MMU_CHECK_GATE`).

- **Too light:** the spool doesn't take the slack up on the way back; a loose
  loop forms or falls off the spool.
- **Too tight, or a dragging spool:** the console's *measured* distance falls
  well short of 300, because the gear slips.

### Per-gate calibration

After gear and encoder, with filament in every gate. Each gate's gear runs
slightly differently (its BMG gear mesh, its spool's drag), so
`MMU_CALIBRATE_GATE ALL=1` measures each gate against the encoder and saves a
rotation distance per gate. The dialog lists them with the difference from
gate 0; more than about 2 % usually means a misaligned BMG gear, a tight
Filamentalist or a dragging spool, so fix that and recalibrate the gate.

**Check all gates** (`MMU_CHECK_GATE ALL=1`) then parks each gate and marks it
available.

`autotune_rotation_distance` (off, in `mmu_parameters_unit0.cfg`) can keep
refining these from encoder readings during normal use. Leave it off until the
manual values are good.

### Toolhead distances

After a cold pull (clean nozzle), heat the extruder for the filament and run
**Clean**. Then load filament and run **Dirty**, then **Cut**. These measure the
toolhead sensor-to-nozzle distances and the cutter, using the toolhead sensor.

### Soak test

Proves the calibration: `MMU_SOAKTEST_LOAD_SEQUENCE` loads and unloads every
gate in turn. **Quick** (3 rounds, partway down the bowden) or **Full** (1
round, to the extruder each time, slow). Filament in every gate. A failure
pauses with the usual MMU recovery dialog.

## 7. Extruder check (optional)

The Galileo 2 is already calibrated (`rotation_distance` 47.32344). To check:
filament loaded, mark it 120 mm above the extruder entry, press **Heat and
extrude 100 mm slowly**, and measure what's left above the entry. It should be
20 mm. If not: new value = 47.32344 × (100 / actual extruded), in
`config/hardware/extruder.cfg`.

## 8. First layer

Print a one-layer test (Ellis's first-layer squares) the normal way. Beacon's
contact homing sets Z for every print, then `START_PRINT` raises Z by
`hot_nozzle_offset` for the hot nozzle. If the layer is too squashed or too
loose, baby-step Z during the test, note the total change and add it to
`variable_hot_nozzle_offset` in `config/hardware/probe.cfg` (positive = nozzle higher).

## 9. Pressure advance and extrusion multiplier, per filament

Andrew Ellis's methods, generated and printed by the printer itself, so they use
this printer's real start sequence. **PA and EM per filament** (or Calibrate →
PA / EM test print, or `CAL_FILAMENT TEST=pa|em`):

1. Pick the gate holding the filament.
2. Pick a range. PA is two-phase, as in Ellis's method: **Wide** (0–0.08 in
   0.004 steps) finds the area, then **Fine** (±0.01 in 0.001 steps around your
   pick) pins it down; the result dialog offers Fine first after a Wide test. EM: **Coarse** (0.86–1.04 in 0.02 steps), then
   **Fine** (±0.03 in 0.01 steps) around your pick.
3. It prints. `tools/calib_gcode.py` writes the test to
   `gcodes/calibration/` and starts it as a normal print: `START_PRINT` (nozzle
   check, contact Z, adaptive mesh over just the test), Happy Hare loads the
   gate's tool, and `MMU_END` / `END_PRINT` finish it. Pause and cancel work as
   usual.
4. When it finishes, a dialog asks which pattern is best (they're numbered on
   the print, from 1 on the left). Your pick is applied, and kept per filament
   and nozzle size; the PA/EM dialog lists all results.
5. Copy the values into PrusaSlicer: PA into the filament's Start G-code as
   `SET_PRESSURE_ADVANCE ADVANCE=…` (see `docs/slicer.md` for per-nozzle values),
   EM into its **Extrusion multiplier**.

What to look for:

- **PA** (nested chevrons): the sharpest corner, with no gap or bulge where
  the lines start and end.
- **EM** (solid squares, each at a different multiplier): a smooth top surface.
  Gaps between lines mean too low; ridges or rough patches mean too high.

The temperatures come from the gate's filament (Spoolman), and the bed and
chamber from `preheat_materials`. Speed, acceleration, flow limit and fan come
from the `calib_*` settings in `config/variables.cfg`. Set those to your
PrusaSlicer external perimeter speed and acceleration: pressure advance
depends on them. The EM test applies the filament's PA result first, if there
is one. The line widths and flow use PrusaSlicer's formula, so the EM you pick
transfers directly.

**Is Ellis still the method?** On the Voron Discord in 2026 people still tune
PA with Ellis's pattern tool or OrcaSlicer's built-in pattern test, which users
there describe as the same thing. Helpers still link Ellis's extrusion
multiplier page. I found nothing that has replaced either.

Mark the tune done when your usual filaments are tuned.
