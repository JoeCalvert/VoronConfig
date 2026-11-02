# Retune

The whole retune, in order. On the printer: **MENU → Calibrate → Retune** (or
type `RETUNE`). It lists the steps below, ticks them off as you mark them done
(the ticks survive restarts) and highlights the next one. Each step's dialog
has the buttons for that step and a Back button to the list.

Do the steps in order: each one assumes the ones before it. Belts change the
resonances, so input shaping comes after them, and pressure advance comes after
the first layer is right.

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

## 6. ERCF calibration

Happy Hare v4's order. Redoing an earlier step means redoing the ones after it.
The dialog marks each step done once Happy Hare has a saved value for it.

Old v3 values, as a sanity check (from `mmu.V3/mmu_vars.cfg`):

| | v3 value |
|---|---|
| Selector offsets | 3.2, 26.6, 50.0, 73.4, 96.8, 120.2, 143.6, 167.0 |
| Gear rotation distance | about 23.0 (gate 0: 23.5984) |
| Encoder resolution | 0.9535 |
| Bowden length | 1198.9 mm |
| Servo angles | down 75, up 155, move 132 |

1. **Selector:** press **Motors off**, slide the selector by hand until it lines
   up with gate 0, then **Calibrate selector** (`MMU_CALIBRATE_SELECTOR
   AUTO=1`). It sweeps the full travel and works out every gate. Check it after
   with `MMU_HOME` and `MMU_SELECT GATE=7`. If a servo position needs touching
   up: `MMU_SERVO POS=up`, `MMU_SERVO ANGLE=…`, then `MMU_SERVO POS=up SAVE=1`
   (same for `down` and `move`).
2. **Gear (gate 0):** filament in gate 0. **Advance 50 mm** pushes it out of the
   ERCF. Cut it flush where it leaves the ERCF. **Move 100 mm**
   (`MMU_TEST_MOVE MOVE=100 GRIP=1`) and measure what came out. Then type
   `MMU_CALIBRATE_GEAR MEASURED=<mm>` in the console. Move 100 mm again to
   check it now comes out at 100.
3. **Encoder:** automatic (`MMU_CALIBRATE_ENCODER`). Needs gate 0 filament past
   the encoder, which step 2 leaves it.
4. **Bowden length:** automatic (`MMU_CALIBRATE_BOWDEN`). It loads gate 0 to the
   extruder and records the bowden length.
5. **All gates:** filament in every gate, then `MMU_CALIBRATE_GATE ALL=1`. It
   calibrates each gate's rotation distance against the encoder.
6. **Toolhead:** after a cold pull (clean nozzle), heat the extruder for your
   filament and run **Clean**. Then load filament and run **Dirty**, then
   **Cut**. These measure the toolhead sensor-to-nozzle distances and the
   cutter, using the toolhead sensor.

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

Ellis's method is still the usual one on the Voron Discord: pressure advance
first, then extrusion multiplier. Orca's built-in PA test gives equivalent
results, but you use PrusaSlicer.

Load the filament's gate from the MMU panel before printing a test. The test
G-code doesn't select a tool, so it prints with whatever is loaded.

### Pressure advance: Ellis's pattern tool

Settings for this printer in the generator (ellis3dp.com, Pressure Advance
tool):

- Firmware **Klipper**, bed **350 × 350**, nozzle: what's fitted.
- Retraction and fan: copy from your PrusaSlicer filament and printer profiles.
- PA range for a direct-drive extruder: start 0, end 0.08, step 0.005. Narrow
  it on a second run.
- **Start G-code** (replace the tool's default entirely):

  ```
  START_PRINT BED=[BED_TEMP] EXTRUDER=[HOTEND_TEMP] NOZZLE=0.60
  POST_START_PRINT
  ```

  `[BED_TEMP]` and `[HOTEND_TEMP]` are the tool's own placeholders. Set
  `NOZZLE` to the fitted nozzle, or `START_PRINT` refuses the file. Add
  `CHAMBER=…` for ABS/ASA.
- **End G-code:** `END_PRINT`

Pick the pattern with the sharpest corners and no gap or bulge at the start and
end of lines.

### Extrusion multiplier: Ellis's cubes

Slice a few 30 × 30 × 3 mm cubes in PrusaSlicer with the filament's normal
settings and the PA from above, changing the extrusion multiplier by 2 % between
them. Pick the one whose top surface is smooth with no gaps between lines and
no ridging. Then fine-tune in 1 % steps.

### Where the values go

- **PA:** the PrusaSlicer filament's start G-code,
  `SET_PRESSURE_ADVANCE ADVANCE=…` (per nozzle size; see `docs/slicer.md`).
- **EM:** the filament's **Extrusion multiplier**.

Mark the step done when your usual filaments are tuned.
