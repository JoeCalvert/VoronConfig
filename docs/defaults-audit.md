# Defaults audit

Every Klipper option that differs from its documented default has to earn its
place: it's a hardware fact, it was measured on this machine, or it's a tuning
choice with a reason. Anything else goes back to the default.

Regenerate the raw list on the Pi (it reads the installed Klipper's own
reference, so the defaults always match the running version):

```
python3 tools/defaults_audit.py ~/klipper/docs/Config_Reference.md printer.cfg
```

Hardware facts (pins, CAN UUIDs, sensor types, rotation distances, gear
ratios) are left out of the list. Happy Hare's options are audited through
`mmu/.mmu_config`: the lines without `#~DEFAULT~#` are the non-default ones
(done in PRs #2 and #3).

## Fixed in this PR

| Option | Was | Now | Why |
|---|---|---|---|
| `[heater_fan electronics_fan]` | heater fan on the **bed** at 80 °C | `[controller_fan electronics_fan]` | Bug: the electronics fan never ran for PLA/PETG prints. A controller fan runs whenever steppers are enabled or a heater is on |
| `[tmc2209 stepper_x/y] driver_SGTHRS` | 125 | removed | Stale copy. Autotune's `sg4_thrs` (109 / 111, the midpoints of your measured ranges) overrides it; autotune's README says values set in the driver sections have no effect |
| `[tmc2209 stepper_z*] stealthchop_threshold` | 999999 | removed | Autotune's `tuning_goal: silent` sets StealthChop on Z itself |

## Legacy values with no recorded reason

Decided in PR #10: `pwm_cycle_time`, `gcode_arcs` resolution and the two bed
mesh split settings go back to the default. `position_min` stays at -15.
`horizontal_move_z` went back to the default in PR #13: Beacon scans at its own
trigger distance, so it had no effect.

| Option | Default | Ours | Proposal |
|---|---|---|---|
| `[heater_bed] pwm_cycle_time` | 0.1 | 0.01612 | **Default.** Looks derived from the 60 Hz mains period (1/60 s), which doesn't apply on UK 50 Hz mains. With a zero-crossing SSR, the default cycle is fine |
| `[gcode_arcs] resolution` | 1.0 | 0.1 | **Default.** 0.1 mm splits each arc into many tiny moves, which loads the MCUs (a Timer Too Close risk) for no visible gain. Irrelevant if PrusaSlicer's arc fitting is off |
| `[stepper_z] position_min` | 0 | -15 | **-5.** Beacon contact and Z offsets need a little negative travel, not 15 mm, which lets a bad offset drive the nozzle deep into the bed |
| `[bed_mesh] move_check_distance` | 5.0 | 3.0 | **Default**, together with `split_delta_z`. Together they decide where moves over the mesh are split; smaller values add planning work for no visible difference |
| `[bed_mesh] split_delta_z` | 0.025 | 0.01 | **Default** (see above) |
| `[bed_mesh] horizontal_move_z` | 5 | 12 | **Check against the Beacon docs.** Beacon scans at its own height; 12 mm travel between points mostly adds time |

## Keep: measured or a hardware need (re-measure in the tuning pass)

| Option | Ours | Reason |
|---|---|---|
| `[extruder] pid_*`, `[heater_bed] pid_*` | measured | **Re-run `PID_CALIBRATE`**: Klipper fixed a PID calibration bug in October 2026 |
| `[input_shaper]` | mzv 47.6 / ei 43.6, damping 0.053 / 0.063 | **Re-run with Shake&Tune**: Klipper redefined the EI shapers in September 2025, so the Y result is out of date |
| `[extruder] max_extrude_only_distance` | 120 | The cutter retracts 53.4 mm in one move (default limit 50) |
| `[extruder] max_extrude_cross_section` | 5 | Blobifier purges in place at high flow |
| `[extruder] pressure_advance` | 0.05 | Only a default for moves outside a print; PrusaSlicer sets it per filament |
| `[stepper_x/y] homing_retract_dist` | 0 | Required for sensorless homing |
| `[stepper_x/y] homing_speed` | 80 | Tuned with the sensorless thresholds |
| `[stepper_z] homing_speed`, `second_homing_speed`, `homing_retract_dist` | 15 / 5 / 0 | Beacon homing |
| `[bed_mesh] algorithm`, `probe_count`, `speed`, `mesh_min/max`, `zero_reference_position` | bicubic, 27×27, 450, 40–310, 300,300 | Bicubic is required above 6 points. `zero_reference_position` must match Beacon's `home_xy_position` |
| `[quad_gantry_level]` `speed`, `horizontal_move_z`, `retries`, `retry_tolerance`, `max_adjust` | 350, 12, 5, 0.005, 15 | Tuning choices. `max_adjust` 15 lets the coarse QGL recover a badly racked gantry |
| `[printer] square_corner_velocity` | 12 | **Re-derive** in the tuning pass (Ellis's guide) rather than carrying it forward |
| `[force_move] enable_force_move` | True | Needed for `STEPPER_BUZZ` / `FORCE_MOVE` when testing motors |
| filter and fan `kick_start_time` / `off_below` | | Measured for those fans |

## Options set to their default

Options written out with the default value (for example `interpolate: True`,
`full_steps_per_rotation: 200`) are harmless. They'll be dropped when each file
is rewritten, rather than in a churn-only change here.

## Plugins (PR #13)

Checked against each plugin's source for its defaults.

| Plugin option | Default | Ours | Decision |
|---|---|---|---|
| Beacon `home_method` | proximity | proximity | Keep (set explicitly in PR #4, with a comment) |
| Beacon `home_method_when_homed` | proximity | proximity | Keep |
| Beacon `home_autocalibrate` | always | never | Keep: it applies to contact homing, which only `START_PRINT` does, and that calibrates explicitly (`CALIBRATE=1`) |
| Beacon `contact_max_hotend_temperature` | 180 | 160 | Keep: a margin above the 150 °C probing temperature, protecting the PEI |
| Beacon `mesh_main_direction` | y | x | Keep (tuning choice) |
| Beacon `mesh_runs` | 1 | 2 | Keep. Now the only place: `START_PRINT` no longer also passes `RUNS=2` |
| Beacon `home_z_hop` / `home_xy_move_speed` / `speed` / `lift_speed` | 0 / 50 / 5 / speed | 15 / 250 / 10 / 15 | Keep: clearance before homing, and faster travel |
| Beacon `x_offset` | 0 | 0 | Keep explicit: hardware fact |
| `[bed_mesh] horizontal_move_z` | 5 | 12 | **Default**: Beacon scans at its trigger distance (2 mm) and doesn't use it |
| `autotune_tmc` X/Y | | `tuning_goal: performance`, measured `sg4_thrs` 109 / 111 | Keep (measured) |
| `autotune_tmc` Z ×4 | | `tuning_goal: silent` | Keep (sets StealthChop on Z) |
| `autotune_tmc extruder` | | motor only (goal `auto` → silent) | Keep; revisit only if the extruder skips at high flow |
| `[shaketune]` | | all defaults | Keep |
| LED Effects | | effects only (PR #11) | Keep |
