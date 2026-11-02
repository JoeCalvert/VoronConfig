# Config changes and machine checks

Every value changed by the modernisation pull requests is listed here, with
where it came from and what to check on the printer. Each pull request adds its
own rows, so this file is reviewed alongside the change itself.

Sources: **v3** = the measured value in `mmu.V3/`; **default** = the Happy Hare
v4 installer default; **plan** = a decision recorded in the modernisation plan.

## PR #2: stop the toolhead hitting the cutter pin

| File | Setting | Was | Now | Source and reason |
|---|---|---|---|---|
| `mmu/base/mmu_macro_vars.cfg` (`_MMU_CUT_TIP_VARS`) | `pin_loc_xy` | 14, 250 | 10, 346 | v3; confirmed physical pin position |
| same | `pin_loc_compressed_xy` | 0.5, 250 | 0.5, 346 | v3; same pin |
| same | `pin_park_dist` | 5.0 | 20.0 | v3 |
| same | `blade_pos` | 37.5 | 61.22 | v3; measured for this toolhead |
| same | `retract_length` | 32.5 | 53.4 | v3; measured |
| same | `safe_margin_xy` | 30, 30 | 60, 50 | v3; real toolhead size |
| same (`_BLOBIFIER_VARS`) | `purge_x` | 10 | 5 | v3; tray position |
| same | `tray_top` | 0.7 | 0.8 | v3 |
| same | `brush_start` | 67 | 90 | v3; **see check B1** |
| same | `brush_top` | 6 | -2 | v3 |
| same | `clearance_z` | 2 | 10 | v3 |
| same | `eject_hop` | 6.0 | 1.0 | v3 |
| same | `enable_shaker` | 1 | 0 | No shaker arm fitted |
| same (`_MMU_SEQUENCE_VARS`) | `park_pause` | 50, 50, 5, 0, 2 | 175, 355, 5, 0, 2 | plan; 50,50 crosses the pin from the tray |
| same | `park_complete` | 50, 50, 10, 0, 5 | -999, -999, 10, 0, 5 | plan; lift and retract only (-999 = don't move that axis). `END_PRINT`'s `PARK` does the travel |
| same (`_MMU_CLIENT_VARS`) | `user_resume_extension` | (empty) | `BLOBIFIER_CLEAN` | plan; every resume leaves from the brush exit |
| same | `user_cancel_extension` | (empty) | `_CANCEL_PRINT_EXTENSION` | plan; our cancel steps, run from Happy Hare's hook |
| `macros/base/cancel_print.cfg` | `CANCEL_PRINT` | our own macro (silently replaced by Happy Hare's) | `_CANCEL_PRINT_EXTENSION` | A cancel no longer unloads filament (plan). `SET_VGB` step dropped: VGB isn't included |
| `mmu/.mmu_config` | the menuconfig copies of the values above | | | Kept in step so menuconfig shows what the `.cfg` files use |

Checks on the printer (cold, no filament, slow speed, hand on the e-stop):

- [ ] **C1** Cut: after `G28`, a dry cut approaches the pin along Y 346 and backs out to X 90
- [ ] **C2** `blade_pos` / `retract_length`: a real cut with filament leaves a clean tip, and the reload doesn't jam
- [ ] **B1** `brush_start` 90: v3 used the line commented "For 300mm build"; the 350 mm preset is 84. Check the nozzle wipes across the real brush
- [ ] **B2** `purge_x` 5, `tray_top` 0.8: `BLOBIFIER_PARK` puts the nozzle over the tray, just clear of it
- [ ] **B3** `brush_top` -2, `clearance_z` 10: `BLOBIFIER_CLEAN` dips into the bristles without hitting the brush base
- [ ] **P1** `BLOBIFIER_PARK`, then `MMU_PAUSE`: a sideways move along the back to 175,355
- [ ] **P2** `RESUME` from the pause: wipe, then return
- [ ] **P3** `BLOBIFIER_PARK`, then `CANCEL_PRINT`: Z lift, X to 175, then Y to 100

## PR #3: Happy Hare settings checked against the v4 ERCF guide

Only values with a reason behind them carry over from v3; the rest go back to
Happy Hare v4 defaults.

| File | Setting | Was | Now | Source and reason |
|---|---|---|---|---|
| `mmu/base/mmu_parameters_unit0.cfg` | `bowden_allowable_encoder_delta` | 70.0 | 20.0 | default; 70 mm silently accepted large slips. Gate 1 had 33 load failures under v3 |
| same | `toolhead_homing_max` | 80 | 40 | default; the sensor-to-sensor distance is about 20 mm |
| same | `gate_parking_distance` | -12 | -23 | default, to be tested first; **see check G1** |
| same | `gate_final_eject_distance` | 20 | 50 | v3; your preference for easy spool removal |
| `mmu/base/mmu.cfg` | `toolhead_residual_filament` | 2 | 18.4 | v3, as a starting point; **see check T1** |
| same | `t_macro_color` | slicer | gatemap | plan; tool colours show what is actually loaded |
| `mmu/base/mmu_hardware_unit0.cfg` | gear `run_current` | 0.5 | 0.45 | v3; known good |
| same | selector `run_current` | 0.4 | 0.7 | v3; known good |
| `mmu/base/mmu_macro_vars.cfg` | `automap_strategy` | none | filament_name | plan; tools map to gates by filament name, as in Spoolman |
| same | `restore_xy_pos` | last | next | plan; after a toolchange, go straight to the next print position |
| `mmu/.mmu_config` | the menuconfig copies of the values above | | | Kept in step |

Considered and left unchanged: `servo_duration` (already the 0.4 default),
`gate_homing_max` and `gate_preload_homing_max` (already 100), `sync_gear_current`
(already 100), the servo pulse widths (v4's Savox preset), and
`servo_buzz_gear_on_down` (3 is the v4 default).

**Deferred:** `auto_home: True`. Happy Hare's auto-home runs a plain `G28`, and
the Beacon is set to contact-home on every `G28`, so it would touch the bed with
a hot nozzle. That waits for the Beacon and `PRINT_START` PR, which moves contact
homing into `PRINT_START` only.

Checks on the printer:

- [ ] **S1** Servo: re-seat the arm at DOWN as the v4 ERCF guide describes, then `MMU_SERVO POS=down|move|up` and save each with `SAVE=1`. The v3 angles were set under different pulse widths and no longer apply
- [ ] **G1** `gate_parking_distance` -23: load and unload each gate a few times. If the selector drags on parked filament, go back to -12
- [ ] **T1** `MMU_CALIBRATE_TOOLHEAD`: confirms `toolhead_extruder_to_nozzle`, `toolhead_sensor_to_nozzle` and `toolhead_residual_filament` for this cutter
- [ ] **K1** Re-run selector, gear (per gate), encoder and bowden calibration. v4's saved calibration starts empty; v3's values in `mmu.V3/mmu_vars.cfg` are reference only
- [ ] **L1** Load all 8 gates with the 20 mm delta. A gate that now fails is showing a real slip (gear tension or rotation distance), not a new problem
- [ ] **M1** Re-map the gates by NFC, then slice a two-colour test: `MMU_START_CHECK` should map tools to gates by name

## PR #4: plain G28 homes by proximity; Happy Hare auto-home on

| File | Setting | Was | Now | Source and reason |
|---|---|---|---|---|
| `config/hardware/probe.cfg` (`[beacon]`) | `home_method` | contact | proximity | plan; a plain `G28` (the Mainsail home button, Happy Hare's auto-home) is now safe at any nozzle temperature. Contact homing is unchanged where `START_PRINT` asks for it explicitly (`BEACON_HOME_Z_CONTACT`) |
| `mmu/base/mmu_macro_vars.cfg` (`_MMU_SEQUENCE_VARS`) | `auto_home` | False | True | plan, deferred from PR #3; MMU operations home first if needed instead of failing |
| `mmu/.mmu_config` | `auto_home` | | | Kept in step |

`START_PRINT` already homes with `METHOD=proximity` and then contact-homes
explicitly, so print starts behave the same.

Checks on the printer:

- [ ] **H1** Cold, after a restart: Mainsail's home-all homes Z without touching the bed
- [ ] **H2** Hot (nozzle above 160 °C), after a restart: `MMU_LOAD` homes by itself first, without a contact error
- [ ] **H3** A normal print start still contact-homes after the wipe

## PR #5: slicer integration and a simpler START_PRINT

`START_PRINT` now takes only what the slicer owns, and leaves everything else to
its owner (see `docs/slicer.md`).

| File | Setting | Was | Now | Source and reason |
|---|---|---|---|---|
| `macros/base/start_print.cfg` | `START_PRINT` parameters | `BED`, `HOTEND`, `MATERIALS`, `REFERENCED_TOOLS`, `SOAK`, `SIZE`, `Z_ADJUST` | `BED`, `EXTRUDER` (`HOTEND` still accepted), `CHAMBER`, `NOZZLE`, `Z_ADJUST` | plan; materials come from Happy Hare, the mesh area from object labels, the chamber target from the PrusaSlicer filament settings |
| same | chamber decision | exact `ABS`/`ASA` match sets 40 °C | highest `chamber_temperature` of the filaments used, computed in the PrusaSlicer start G-code | plan; set per filament in PrusaSlicer |
| same | pin avoidance before QGL | X move if left of X 40 | removed | PR #2 removed the causes; nothing leaves the toolhead stranded on the tray |
| same | sequence | coarse QGL, wipe, contact, QGL, mesh, wipe, contact, heat, offset, move to 55,340 | coarse QGL, wipe, contact, QGL, contact, mesh, park on tray, heat, offset | plan; no second wipe (no extrusion at 150 °C); final heat over the tray so ooze falls into it; the first tool load starts there |
| same | hot-nozzle offset | `0.055` inline | `_BEACON_VARS.hot_nozzle_offset` in `config/hardware/probe.cfg` | plan; one value, beside the Beacon settings |
| same | `NOZZLE_SET` | (none) | new | plan; records the fitted nozzle; `START_PRINT` refuses files sliced for another |
| same | old slicer start G-code | accepted | refused with a message | prevents half-updated profiles |
| `macros/base/post_start_print.cfg` | `VORON_PURGE` | called | removed | plan; Blobifier already purged and wiped |
| `docs/slicer.md` | (new) | | | The PrusaSlicer custom G-code and settings to match |

Checks:

- [ ] **S1** Paste the start, end, change-filament and layer-change G-code from `docs/slicer.md` into the PrusaSlicer printer preset (each nozzle preset)
- [ ] **S2** In a sliced file, nothing comes before `MMU_START_SETUP` except the `M140` line and no `M141`/`M191` ("Emit temperature commands automatically" is off)
- [ ] **S3** Slice a part with an ABS/ASA filament (chamber temperature set): the `START_PRINT` line shows `CHAMBER=` with your target. Slice PLA: `CHAMBER=0`. If PrusaSlicer reports an error in the chamber expression, use the fallback in `docs/slicer.md`
- [ ] **S4** Run `NOZZLE_SET DIAMETER=0.6` (the nozzle currently in the config) once; then a file sliced for 0.4 should be refused
- [ ] **S5** Full print start: homing, soak only if needed, QGL, contact, mesh over the objects only, then heats on the tray; the first tool load purges there without moving away first
- [ ] **S6** First layer height looks right; `hot_nozzle_offset` 0.055 is unchanged from before
- [ ] **S7** Pressure advance: each filament's start G-code has its `SET_PRESSURE_ADVANCE` line, and the console shows it after a tool change

## PR #6: remove autocommit.sh

| File | Change | Reason |
|---|---|---|
| `autocommit.sh` | removed | Not used: config backups run through klipper-backup (`update_git` in `macros/miscs/config_backup.cfg`). Its `git pull` before committing would also have deployed every merge straight to the printer |

Checks:

- [ ] **A1** Nothing on the Pi still runs `autocommit.sh` (crontab, systemd timers, Moonraker shell commands)

## PR #7: startup self-check

| File | Change | Reason |
|---|---|---|
| `macros/base/startup_check.cfg` | new: `CHECK_CONFIG`, run automatically 5 s after Klipper starts | plan; pattern from Klippain and klipper-macros. Checks invariants, not copies of values, so each value keeps one owner |
| `macros/base/start_print.cfg` | `START_PRINT` refuses to run if the check found errors or hasn't run | A Happy Hare installer run can silently reset measured values; the printer now refuses to print instead |

Errors (block `START_PRINT`):
- the cutter pin, `brush_start` or `purge_x` back at Happy Hare installer defaults
- cutter `restore_position` True
- `BLOBIFIER_PARK` in the pre-unload or post-form-tip hooks
- any park point left of the cutter's clearance line (pin X + `pin_park_dist` + `safe_margin_x` = 90)
- cancel hook not calling `_CANCEL_PRINT_EXTENSION`
- no Beacon model saved
- Beacon `home_method` not proximity

Warnings: resume hook without `BLOBIFIER_CLEAN`, `z_thermal_adjust` enabled, fitted nozzle not recorded.

Checks:

- [ ] **K1** After a Klipper restart the console shows no `CHECK_CONFIG error` lines. Run `CHECK_CONFIG` by hand: it reports OK (the nozzle warning goes away after `NOZZLE_SET`)
- [ ] **K2** Temporarily set `park_pause` to `50, 50, 5, 0, 2`, restart: the check reports it and `START_PRINT` refuses. Put it back

## PR #8: remove dead and broken config

Nothing here is used by the current macros. Some of it would fail if called.

| Removed | Why |
|---|---|
| `macros/miscs/compatibility.cfg` (and its include) | Its `M204` override passed `ACCEL_TO_DECEL`, which Klipper removed, so any slicer `M204` errored. The `G00`–`G04` aliases are unneeded, and `G03` ran `G2` (the wrong direction). `M701`/`M702`/`M600` pointed at macros that don't exist. Klipper's own `M204` now applies |
| `macros/helpers/nozzle_cleaning.cfg` | `CLEAN_NOZZLE` was only called by the test framework below, and it read `max_accel_to_decel`, which Klipper removed. Blobifier's brush does the wiping |
| `macros/helpers/spoolman.cfg`, `klipper-spoolman.cfg` (and the duplicate include) | Happy Hare v4 sets the active spool on every toolchange |
| `config/software/adaptive_purge.cfg` (`VORON_PURGE`), `macros/calibration/adaptive_bed_mesh.cfg` | Replaced by Blobifier's purge and Klipper's `BED_MESH_CALIBRATE ADAPTIVE=1` (PR #5) |
| `macro_modules/` (and its include) | Unused macro-module test framework |
| `config/software/virtual_gantry_backers.cfg`, `config/vgb_meshes.cfg`, the `SET_VGB` guards in `tilting.cfg` and `end_print.cfg` | VGB wasn't included, so the guards never ran |
| `[include K-ShakeTune/*.cfg]` | Old Shake&Tune macro folder. Current Shake&Tune is the `[shaketune]` section in `config/software/shaketune.cfg`, which stays |
| `variable_mod_mgr_loaded`, `variable_accel_to_decel_factor`, `variable_use_vgb`, the `ercf_enabled` read in `END_PRINT` | Only used by the removed pieces |
| `printer-2024*.cfg`, `printer.cfg.old-*`, `moonraker.conf.old-*`, `mmu_klipperscreen.conf.0*` | Automatic backups. Now in `.gitignore`; still in git history |

Kept for now: `mmu.V3/`, the reference for the measured v3 values, until the
v4 calibration is done.

Checks:

- [ ] **D1** Klipper restarts without config errors, and `CHECK_CONFIG` passes
- [ ] **D2** Spoolman still shows the active spool changing on a toolchange
- [ ] **D3** If PrusaSlicer's "Color change G-code" is `M600`, change it to `PAUSE`. `M600` never worked here: it called a macro that doesn't exist

## PR #9: defaults audit, and three fixes it found

| File | Setting | Was | Now | Source and reason |
|---|---|---|---|---|
| `config/hardware/fans.cfg` | electronics fan | `[heater_fan electronics_fan]` on the bed at 80 °C | `[controller_fan electronics_fan]`, heaters `extruder, heater_bed` | Bug: the fan never ran for PLA/PETG prints |
| `config/hardware/axes_xy.cfg` | `driver_SGTHRS` (X, Y) | 125 | removed | Stale copy; autotune's `sg4_thrs` (109 / 111) is the live value |
| `config/hardware/axes_z.cfg` | `stealthchop_threshold` (Z ×4) | 999999 | removed | Autotune's `tuning_goal: silent` sets StealthChop |
| `tools/defaults_audit.py`, `docs/defaults-audit.md` | (new) | | | Lists every non-default Klipper option against the installed Klipper's own reference, with a class and decision for each |

Waiting on your decision (see `docs/defaults-audit.md`): `pwm_cycle_time`,
`gcode_arcs` resolution, `position_min`, the bed mesh split settings, and bed mesh
`horizontal_move_z`.

Checks:

- [ ] **F1** The electronics fan runs as soon as the motors are enabled or a heater is on, and stops about 30 s after both are off
- [ ] **F2** Sensorless homing of X and Y behaves exactly as before (the thresholds were already coming from autotune)
- [ ] **F3** Run `python3 tools/defaults_audit.py ~/klipper/docs/Config_Reference.md printer.cfg` on the Pi, and check the list matches `docs/defaults-audit.md` for your Klipper version
- [ ] **F4** Tuning pass: `PID_CALIBRATE` for hotend and bed, and Shake&Tune input shaper (EI shapers were redefined in Klipper)

## PR #10: legacy values back to defaults (your decisions from the audit)

| File | Setting | Was | Now | Reason |
|---|---|---|---|---|
| `config/hardware/heated_bed.cfg` | `pwm_cycle_time` | 0.01612 | default (0.1) | Looked like a 60 Hz mains figure; UK mains is 50 Hz |
| `config/machine.cfg` (`[gcode_arcs]`) | `resolution` | 0.1 | default (1.0) | Fewer, longer segments; less MCU load |
| `config/software/bed_mesh.cfg` | `move_check_distance` | 3.0 | default (5.0) | No recorded reason |
| same | `split_delta_z` | 0.01 | default (0.025) | No recorded reason |

`position_min: -15` stays, by your decision.

Checks:

- [ ] **L1** Bed heats and holds temperature as before (`pwm_cycle_time`); the bed's PID re-run (F4) covers it too
- [ ] **L2** First layer is still even across the bed with the default mesh split settings

## PR #11: one LED controller; static while homing; filament colour while printing

| File | Change | Reason |
|---|---|---|
| `macros/hardware_functions/status_leds.cfg` | `_STATUS STATE=…` is the one controller; `STATUS_*` macros are thin wrappers (callers unchanged) | plan (LED decision) |
| same | homing, levelling, Z calibration, meshing, cleaning, busy, ready: **static colours**, no animation | plan; no effect traffic to the CAN toolhead while homing or probing |
| same | printing: logo LEDs follow the **loaded filament's colour** (Happy Hare gate colour from Spoolman) through a Klipper LED template; nozzle LEDs are a white work light | plan; Klipper only resends the template when the colour changes |
| same | animated effects kept only for heating, cooling, part ready, critical error; 24 → 15 fps | plan |
| same | effects stopped with `STOP_LED_EFFECTS LEDS="neopixel:_status_leds"` | Bug: a bare `STOP_LED_EFFECTS` (every status change before) also stopped Happy Hare's gate LED effects |
| same | always-on 24 fps `rainbow` effect removed; idle is a dim static colour | Constant traffic to the toolhead for decoration |
| `mmu/base/mmu_macro_vars.cfg` (`_MMU_STATE_VARS`) | `user_print_state_changed_extension: _STATUS_FROM_MMU` | Happy Hare pauses show the error effect; resuming printing restores the print colours |
| `mmu/.mmu_config` | same value | Kept in step |

Checks:

- [ ] **E1** Homing and a print start show static colours, no animation, and Happy Hare's gate LEDs keep their own effects throughout
- [ ] **E2** While printing, the logo matches the loaded filament's colour and changes after a toolchange
- [ ] **E3** An MMU error shows the error effect; after the resume the print colours come back
- [ ] **E4** No `SET_LED` errors in the console (the logo LEDs are GRB, the nozzle LEDs GRBW)

## PR #12: firmware updates with UKAM

| File | Change | Reason |
|---|---|---|
| `ukam/mcus.ini` | new: Octopus (USB), SB2040 (CAN), MMB (CAN, `mcu unit0`), Pi host MCU, Beacon | plan; one command updates Klipper and flashes only the boards that need it |
| `ukam/config/config.<board>` | moved from `boards/<board>/klipper_*.config` (the variant each flash script actually used) | UKAM keeps each board's Kconfig there, so firmware settings stay versioned with the config |
| `boards/*/flash-klipper.sh` | removed | Replaced by `mcus.ini`. They used Katapult's old `flash_can.py` (now `flashtool.py`) and sent build errors to `/dev/null` |
| `boards/*/*.old`, `mellow_sb2040_v1.bin` | removed | menuconfig backups and a build output |
| `moonraker.conf` | `[update_manager update_klipper_and_mcus]` | UKAM updates itself through Moonraker |

Katapult bootloader Kconfigs and the alternative transport Kconfigs (USB/UART/CAN variants) stay in `boards/` for reference.

Checks:

- [ ] **U1** Install UKAM on the Pi: `cd ~ && git clone https://github.com/fbeauKmi/update_klipper_and_mcus.git ukam`
- [ ] **U2** First run with `~/ukam/ukam.sh -m`, and check each board's menuconfig, especially the SB2040 (UKAM warns that RP2040 configs can be corrupted since Klipper added RP2350 support)
- [ ] **U3** All four boards and the Beacon report the new version after the run; Klipper starts without "MCU protocol" errors
- [ ] **U4** The Octopus flash: if `make flash` doesn't put it into Katapult, switch its `action_command` to Katapult's `flashtool.py` with the board's USB serial, as in UKAM's examples

## PR #13: plugin settings audit

| File | Setting | Was | Now | Reason |
|---|---|---|---|---|
| `config/software/bed_mesh.cfg` | `horizontal_move_z` | 12 | default | Beacon scans at its own trigger distance (2 mm) and doesn't use it |
| `macros/base/start_print.cfg` | `BED_MESH_CALIBRATE RUNS=2` | passed | removed | `mesh_runs: 2` in `[beacon]` is the one owner |
| `docs/defaults-audit.md` | plugin table | | | Beacon, autotune, Shake&Tune and LED Effects checked against each plugin's defaults; everything else kept, with reasons |

Checks:

- [ ] **P4** The adaptive mesh still does two passes (console shows Beacon running two mesh passes) and takes about the same time

## PR #14: line endings

| File | Change | Reason |
|---|---|---|
| `.gitattributes` | new: store text files with LF | The repo had a mix of CRLF and LF files, so an edit could rewrite a whole file and hide the real change |
| 37 files | CRLF → LF only | `git diff --ignore-cr-at-eol` shows no content change |

No check needed on the printer: Klipper reads both.

## PR #15: tidy the layout (no restructure needed)

The plan ended with a moves-only restructure into a Klippain-style layout. The
config already has that layout (`config/boards`, `config/hardware`,
`config/software`, `macros/base`, `macros/hardware_functions`, `macros/helpers`,
`macros/miscs`, plus `docs/`, `tools/`, `ukam/`), so moving files would be churn
without benefit. This removes the leftovers instead.

| Removed | Why |
|---|---|
| `macros/base/pause_resume.cfg`, `config/software/led_effects.cfg`, `config/software/display.cfg`, `config/hardware/display.cfg` (and their includes) | Empty (comments only). The alternative display config `display.cfg.mini12864` stays |
| `config/save_variables.cfg` | Orphan: not the active `save_variables` file (Happy Hare's `mmu/mmu_vars.cfg` is), and nothing reads its two filter values |
| `macros/helpers/temp_check.cfg` | `_LOW_TEMP_CHECK` is not called anywhere |
| includes of `macros/base/probing/`, `macros/calibration/`, `scripts/` | Those folders don't exist |

Checks:

- [ ] **T2** Klipper restarts without config errors and `CHECK_CONFIG` passes

## PR #16: file layout

The layout from the plan, adjusted for what changed since it was written (no
positions file or keep-out macro, and firmware Kconfigs live in `ukam/`). Files
were moved with `git mv` and their contents are unchanged. Only include lines
were edited.

| Was | Now |
|---|---|
| `macros/base/start_print.cfg`, `post_start_print.cfg`, `end_print.cfg` | `macros/print/` |
| `macros/base/park.cfg`, `macros/base/homing/homing_conditional.cfg`, `macros/base/homing/tilting.cfg`, `config/software/sensorless_homing.cfg` | `macros/motion/` |
| `macros/base/cancel_print.cfg` | `macros/mmu_hooks/cancel_print.cfg` |
| `macros/base/startup_check.cfg`, `macros/hardware_functions/status_leds.cfg` | `macros/state/` |
| `macros/hardware_functions/filter.cfg`, `caselights.cfg`, `macros/helpers/heatsoak.cfg` | `macros/accessories/` |
| `macros/miscs/debugging.cfg`, `config_backup.cfg` | `macros/system/` |
| includes spread across `config/machine.cfg`, `lights.cfg`, `nevermore_filter.cfg`, `status_leds.cfg`, `qgl.cfg` | all in `printer.cfg`, grouped and commented |
| (new) | `docs/state-table.md`: states, sequences and fixed positions, with the file each lives in |

Paths in earlier sections of this file are as they were at the time.

Verified before merging: following every include, the old and new trees load
the same 167 sections with identical option values, and no variable is defined
in two places (so the new include order can't change which value wins).

Checks:

- [ ] **Y1** Klipper restarts without config errors and `CHECK_CONFIG` passes

## PR #17: settings in one place

| Change | Reason |
|---|---|
| `_USER_VARIABLES` now lives only in `config/variables.cfg`, grouped and commented (it was split across 9 files) | One page with every setting the macros use |
| 23 variables removed that nothing reads (e.g. `brush_xyz`, `purge_bucket_xyz`, `homing_first`, `zendstop_position`, `probe_dock_speed`, `print_default_chamber_temp`, `print_default_material`) | Dead settings mislead |
| Always-true feature switches removed (`filter_enabled`, `light_enabled`, `status_leds_enabled`, `bed_mesh_enabled`, `chamber_temperature_sensor_enabled`, `qgl_enabled`, `sensorless_homing_enabled`, `purge_and_brush_enabled`, `verbose`), with the 14 branches that tested them | The hardware is fixed, so they only added code to read past |
| Unused LED colour groups removed (`caselight`, `minidisplay`, `thermal`) | Only `logo` and `nozzle` are used |
| Each macro reads the settings once (`{% set v = printer["gcode_macro _USER_VARIABLES"] %}`) instead of one line per value | 32 separate reads before |

**No behaviour change:** 15 scenarios (two print starts, with `POST_START_PRINT` and `END_PRINT`, a cancel, `PARK`, homing homed and unhomed, bed and chamber soaks, every LED state, accessories, `CHECK_CONFIG`, `NOZZLE_SET` and the QGL helpers) were run through a macro simulator, fully expanded to the G-code they send. The output is identical before and after.

Checks:

- [ ] **V1** Klipper restarts without config errors (e.g. no "unknown variable" in a macro), and a print start looks the same as before

## PR #18: one machine-state controller, one end-of-job sequence

| File | Change | Reason |
|---|---|---|
| `macros/state/machine_state.cfg` (new) | `_SET_STATE STATE=…` decides the toolhead LEDs, case light and filter for each state, from one table in its header. `_JOB` holds the job phase and chamber target | Before, the lights, filter and LEDs for each state were set separately in `START_PRINT`, `POST_START_PRINT`, `END_PRINT` and the cancel hook |
| `macros/print/start_print.cfg` | enters states (`preparing`, `soaking`/`heating`, `leveling`, `calibrating_z`, `meshing`, `heating`) instead of setting LEDs, lights and the filter | Says *what* is happening, not how it should look |
| `macros/print/post_start_print.cfg` | refuses to run unless `START_PRINT` finished (job phase `prepared`) | Start-order check (pattern from klipper-macros) |
| `macros/print/end_print.cfg` | new `_END_JOB REASON=complete\|cancel`, used by both `END_PRINT` and the cancel hook | The two end sequences repeated most of the same steps |
| `macros/mmu_hooks/cancel_print.cfg` | calls `_END_JOB REASON=cancel` | |
| `macros/motion/homing_conditional.cfg` | `_CG28` shows the homing state only while it actually homes, then returns to the previous state | It used to flash homing, then "ready", even when no homing was needed, and left the LEDs at "ready" in the middle of a print start |
| `macros/state/status_leds.cfg` | Happy Hare's print-state hook enters `paused` / `printing` through `_SET_STATE` | One path for every state change |
| `macros/motion/park.cfg`, `macros/accessories/heatsoak.cfg` | wrapped in `SAVE_GCODE_STATE` / `RESTORE_GCODE_STATE`, with `G90` set explicitly | They assumed absolute positioning and left `G90` set behind them |
| `END_PRINT`, `POST_START_PRINT` | read `_JOB.chamber_temp`, not `START_PRINT`'s own variable | Job settings stored once |

Expected differences in the expanded G-code (simulator): the filter is
explicitly switched off on entering `leveling` and, for prints without a chamber
target, on entering `printing` (it was already off); a cancel now also runs
`TURN_OFF_HEATERS`/`M107` (Happy Hare had already done both); `M400` moves to the
start of the end-of-job sequence. Everything else is unchanged.

`_POST_SENSORLESS` keeps its explicit `G91` … `G90` rather than saving gcode
state: it runs inside homing, where the original author had commented
save/restore out.

Checks:

- [ ] **M1** A print start, then a completed print: LEDs, case light and filter behave as before (filter on during a chamber soak, off while levelling, working speed while printing an ABS/ASA job, 10-minute run-on afterwards)
- [ ] **M2** Cancel a print: park, lights and LEDs off, filter off
- [ ] **M3** Run `POST_START_PRINT` alone from the console: it refuses with the job-phase message
- [ ] **M4** Run `_JOB` from the console at any point: it prints the job phase and machine state

## PR #19: macro hygiene

| File | Change | Reason |
|---|---|---|
| every public macro | a `description`, with a `Usage:` line where it takes parameters | 21 had none. The description is what Mainsail shows on the button and `HELP` prints |
| `macros/state/startup_check.cfg` | `CHECK_CONFIG` warns about any public macro without a description | Keeps the convention honest (pattern from klipper-macros' `CHECK_MACRO_DOCS`) |
| `macros/motion/tilting.cfg` | removed (`_TILT_CALIBRATE`) | Never called, and it read a variable that doesn't exist |
| `macros/motion/sensorless_homing.cfg` | `_SENSORLESS_HOME_X/Y` removed | Never called; the Beacon homing hooks call `_PRE/_POST_SENSORLESS` directly |
| `macros/motion/park.cfg` | unused `E` parameter removed; description corrected | It promised a retract it never did |
| `macros/accessories/heatsoak.cfg` | chamber wait loop runs `MAXTIME` minutes (was `MAXTIME − 1`) | Off-by-one |
| same | bed and chamber soaks both wait at `soak_position_xyz` (300,300, Z 2), moving XY first then Z, at the configured speeds | Two hardcoded positions (bed max −50 at Z 2, max −10 at Z 15) at a fixed `F6000` |
| `config/variables.cfg` | `soak_position_xyz: 300, 300, 2` | One setting for the soak position, matching `docs/state-table.md` |

`FAST_QGL` stays, by your decision (manual use), now with a description.

Simulator differences from PR #18: the soak moves (new position and speeds, XY
then Z), and one more minute in the chamber-wait loop. Nothing else changed.

Checks:

- [ ] **H4** A chamber soak waits at 300,300 with the nozzle 2 mm above the bed, and stops after `print_default_chamber_max_heating_time` minutes if the chamber never reaches its target
- [ ] **H5** Mainsail's macro buttons show the new descriptions. `CHECK_CONFIG` shows no "without a description" warning (if it lists Happy Hare macros, ignore them)

## PR #20: macro simulator (tools only)

`tools/macro_sim` expands our macros to the G-code they send, for a set of
scenarios. Run `--save` before a change and `--compare` after it. Nothing on the
machine changes.

## PR #21: dialogs, printer menu, dependency check

| File | Change | Reason |
|---|---|---|
| `macros/ui/dialog.cfg` (new) | `_DIALOG`, `_DIALOG_TEXT`, `_DIALOG_BUTTON`, `_DIALOG_ROW`/`_ROW_END`, `_DIALOG_SHOW`, `_DIALOG_CLOSE` | One place that writes the `action:prompt` messages Fluidd, KlipperScreen and Mainsail all render |
| `macros/ui/menu.cfg` (new) | `MENU`: nozzle, chamber and MMU summary; lights, filter, park (homes first if needed), check config | One entry point. Later workflows add their buttons here |
| `KlipperScreen.conf` | a "Menu" button on the main and print screens that runs `MENU` | Plain menu entries only, so KlipperScreen updates can't break them |
| `macros/system/dependencies.cfg` (new) | `_DEPENDENCIES`: every command, `printer.mmu` field, hook and Happy Hare variable we use, plus the Happy Hare version last checked | So updates can be checked instead of discovered |
| `macros/state/startup_check.cfg` | `CHECK_CONFIG` checks that list: missing commands, fields or variables, hooks that no longer call our macros, a Happy Hare version newer than the one checked | Replaces the separate cancel/resume hook checks (same severities: cancel is an error, resume a warning). The status-LED hook is now also checked (warning) |
| `tools/check_deps.py` (new) | Fails if a macro uses something the list leaves out or calls another project's internal macro. With `--happy-hare PATH` it checks the list against that source | Run after updating Happy Hare, before restarting |
| `docs/updating.md` (new) | What to do after an update | |
| `tools/macro_sim` | Parses indented continuation lines that start with `[` correctly. Scenarios for the menu, the park button and a renamed-dependency check | |

Simulator: `check` is unchanged. New scenarios only.

Against Happy Hare's current development branch (4.2), `check_deps.py` finds
nothing missing.

Checks:

- [ ] **U1** KlipperScreen shows a "Menu" button on the main screen and during a print. It opens the printer menu
- [ ] **U2** `MENU` from Fluidd opens the same dialog. The lights, filter and park buttons work, and Close closes it
- [ ] **U3** The summary line shows the nozzle size, chamber temperature and loaded tool
- [ ] **U4** After a Klipper restart, `CHECK_CONFIG` reports no dependency errors (`printer.gcode.commands` lists the Happy Hare, Blobifier and Beacon commands)
- [ ] **U5** On the Pi: `python3 tools/check_deps.py --happy-hare ~/Happy-Hare` prints `OK`

## PR #22: MMU recovery dialog, check-up, service position

| File | Change | Reason |
|---|---|---|
| `mmu/base/mmu_macro_vars.cfg` + `mmu/.mmu_config` | `user_mmu_error_extension: _MMU_RECOVERY` (was empty) | Happy Hare's documented hook for MMU errors in a print |
| `macros/mmu_hooks/recovery.cfg` (new) | `_MMU_RECOVERY`: what failed, where the filament is, what the print needs, the nozzle heater state, and buttons for that situation (table at the top of the file). Each button runs one Happy Hare command, then re-shows the dialog | Replaces Happy Hare's generic RESUME/UNLOCK pop-up, which it shows over. If the hook is ever lost, Happy Hare's pop-up still appears (`show_error_dialog` stays 1) |
| same | Resume only appears, and only resumes, once the needed tool is loaded to the nozzle. Cancel asks first | Resuming with the wrong or no filament prints air. The UI's own Resume still overrides |
| same | `MMU_CHECKUP`: finds the filament (`MMU_RECOVER`), optionally checks every gate, then lists gates, tools, material and state | For after fiddling by hand. When printing it only shows the last known state |
| `macros/motion/service.cfg` (new) | `SERVICE_POSITION`: lift Z to at least 100 (never lower), X then Y to 175,40, lights full | Reach the nozzle. Safe in a pause because it only raises Z |
| `config/variables.cfg` | `service_position_xy: 175, 40`, `service_min_z: 100` | |
| `macros/ui/menu.cfg` | MENU shows "MMU recovery" while the MMU is paused, otherwise "MMU check-up". Also a "Service position" button | |
| `macros/system/dependencies.cfg` | adds the 7 Happy Hare commands and 8 status fields these use, and the new hook (warning if lost) | `check_deps.py` passes against 4.1 and the 4.2 development branch |

Simulator: new scenarios for each filament position, the gate picker, the
refused resume, cancel confirmation, the check-up and the service position.
`MENU` gains the new buttons. Nothing else changed.

Checks (each needs a deliberately caused MMU error during a test print; easiest
is pulling a spool's filament back past the gate before a toolchange):

- [ ] **R1** On an MMU error, the "MMU paused" dialog replaces Happy Hare's, in Fluidd and on KlipperScreen. The reason and filament position look right
- [ ] **R2** Parked-in-gate case (runout): reload the spool, press Preload, then Load. The dialog comes back showing "loaded", and "Resume the print" resumes
- [ ] **R3** Press Resume while the wrong tool is loaded (or none). It says "Not resuming yet" and stays paused
- [ ] **R4** Keep hot turns the nozzle back on after the 10-minute heater timeout
- [ ] **R5** Cancel print asks first. "No, go back" returns to the dialog
- [ ] **R6** `SERVICE_POSITION` during a pause only lifts Z. After Resume, the toolhead returns to the print and carries on normally
- [ ] **R7** `MMU_CHECKUP` when idle lists the gates correctly. "Check every gate" runs Happy Hare's gate check
- [ ] **R8** "Use another gate" lists only gates with filament, and picking one remaps the tool and loads it

## PR #23: failed-print dialog and unload-after-cancel

| File | Change | Reason |
|---|---|---|
| `macros/print/job_recovery.cfg` (new) | `_JOB_FAILED`: when a print stops with an error (in `START_PRINT` or while printing), job phase `failed`, machine state `failed`, and a dialog with the error, the step it was on, Reprint / Turn the heaters off / Unload | Klipper just stops. Happy Hare reports print state `error`, so no polling is needed. *(Corrected in PR #29: Klipper does turn the heaters off by default, via `on_error_gcode`.)* |
| `macros/state/status_leds.cfg` | `_STATUS_FROM_MMU` runs `_JOB_FAILED` on Happy Hare state `error` | |
| `macros/state/machine_state.cfg` | new machine state `failed` (error LED effect, filter off) and job phase `failed` | |
| `macros/print/end_print.cfg` | after a cancel, `_OFFER_UNLOAD` asks whether to unload any loaded filament | `unload_tool_on_cancel` stays off: a cancel may be because of a filament problem, so it asks instead |
| `macros/ui/menu.cfg` | "Why did the last print stop?" after a failure | Re-open the dialog later |
| `macros/state/startup_check.cfg` | warns if Happy Hare's `print_start_detection` is off | The failed-print dialog depends on it |
| `macros/system/dependencies.cfg`, `tools/check_deps.py` | Happy Hare `[mmu]` parameters we read (`disable_heater`, `print_start_detection`) are listed and checked too | |
| `docs/state-table.md` | rows for the unload offer, a failed print and an MMU error | |

Simulator: `cancel` now ends with the unload dialog (T0 loaded). New scenarios
for a failure while starting and while printing, and a cancel with nothing
loaded (no dialog). Nothing else changed.

Checks:

- [ ] **J1** Cancel a print with filament loaded: the "Unload the filament?" dialog appears. Unload cuts and parks the filament, then turns the nozzle off. "Leave it loaded" just closes
- [ ] **J2** Make `START_PRINT` fail, e.g. start a print sliced for the wrong nozzle size. The "Print stopped" dialog shows the error, and Reprint starts the same file again
- [ ] **J3** After a failure, MENU shows "Why did the last print stop?" and the toolhead LEDs show the error effect
- [ ] **J4** "Turn the heaters off" turns off the nozzle, bed and part fan

## PR #24: preheat and preflight check

| File | Change | Reason |
|---|---|---|
| `macros/accessories/preheat.cfg` (new) | `PREHEAT [MATERIAL=]`: bed to the material's temperature, nozzle 150, and for chamber materials the filter on full (state `soaking`). Defaults to the loaded gate's material. Nothing waits. `PREHEAT_OFF` turns it all off. `_PREHEAT_MENU` is the dialog | Warm up while slicing. `START_PRINT` then skips the bed soak |
| same | Preheat stretches the idle timeout to `preheat_max_minutes`. `_RESTORE_IDLE_TIMEOUT` puts it back, from `_END_JOB`, `PREHEAT_OFF` and the failed-print "heaters off" | Otherwise Klipper's 10-minute idle timeout turns a preheat off |
| `config/variables.cfg` | `preheat_materials` (bed, chamber: PLA 60/0, PETG 80/0, ABS 105/50, ASA 105/50, PC 110/55), `preheat_nozzle_temp: 150`, `preheat_max_minutes: 90` | The only temperatures kept on the printer side, and only for warming up. **Check they match your slicer profiles** |
| `macros/print/preflight.cfg` (new) | `PREFLIGHT_CHECK`: for each tool the print uses, the gate must not be empty, and the material and filament name must match the slicer's. If not, it pauses before `START_PRINT` with Check again / Start anyway / Cancel | Catches a tool left on the wrong spool when automap finds no match. Happy Hare's own check only catches empty gates |
| `docs/slicer.md` | `PREFLIGHT_CHECK` goes in the start G-code after `MMU_START_CHECK` | **Slicer change** |
| `macros/ui/menu.cfg` | "Preheat" button (hidden while printing) | |
| `macros/system/dependencies.cfg` | `printer.mmu.slicer_tool_map` | |

Simulator: `_END_JOB` now restores the idle timeout (`cancel`/`start_*`
gain one `SET_IDLE_TIMEOUT TIMEOUT=600` line). New preheat and preflight
scenarios. Nothing else changed.

Checks:

- [ ] **P1** Add `PREFLIGHT_CHECK` to the PrusaSlicer start G-code (docs/slicer.md)
- [ ] **P2** Check `preheat_materials` matches your PrusaSlicer bed and chamber temperatures
- [ ] **P3** MENU → Preheat → the loaded-material button: bed heats, nozzle 150, filter on for ABS/ASA. After 15 minutes the heaters are still on. Heaters off turns them off
- [ ] **P4** Start a print right after a preheat: `START_PRINT` skips the bed soak
- [ ] **P5** Print with a tool mapped to a gate holding a different filament: the "Check the filament" dialog appears and the print waits. Start anyway carries on; Cancel cancels
- [ ] **P6** A print whose tools all match starts without the dialog

## PR #25: nozzle-change and spool-swap workflows

| File | Change | Reason |
|---|---|---|
| `macros/workflows/nozzle_change.cfg` (new) | `NOZZLE_CHANGE`: unload if loaded, nozzle heater off, `SERVICE_POSITION`; pick the new size (runs `NOZZLE_SET`); reminder to switch the PrusaSlicer profile | The Revo swap in one flow. `START_PRINT`'s contact calibration handles the new nozzle's height |
| `config/variables.cfg` | `nozzle_sizes: [0.25, 0.4, 0.5, 0.6, 0.8]` | Buttons offered |
| `macros/workflows/spool_swap.cfg` (new) | `SPOOL_SWAP [GATE=]`: pick the gate, `MMU_EJECT` (it unloads the toolhead first if that gate is loaded), change the spool, scan its tag, `MMU_PRELOAD`, then show what the gate now holds | Today that's three Happy Hare buttons in the right order. Not while printing (Happy Hare refuses) |
| `macros/ui/menu.cfg` | "Change a spool" and "Change the nozzle" (hidden during a print) | |
| `printer.cfg` | `[include macros/workflows/*.cfg]` | |
| `macros/system/dependencies.cfg` | `MMU_EJECT` | |

Simulator: new scenarios for both. MENU gains the two buttons. Nothing else changed.

Checks:

- [ ] **W1** `NOZZLE_CHANGE` with filament loaded: it unloads, turns the heater off and moves to the front. Picking a size records it (`NOZZLE_SET` with no arguments shows it)
- [ ] **W2** `SPOOL_SWAP` on a loaded gate: unload, eject, then after scanning and preloading the dialog shows the new spool's material and name
- [ ] **W3** Preload with the filament not pushed in far enough: "Try again" appears

## PR #26: planned pauses, "safe to remove" and notifications

| File | Change | Reason |
|---|---|---|
| `macros/workflows/pause_for_user.cfg` (new) | `PAUSE_FOR_USER [MSG=]`: pauses with a dialog showing why (the slicer's `M117` message by default): Resume / Service position / Cancel. MENU "Pause at the next layer" uses it through Happy Hare's `SET_PAUSE_NEXT_LAYER` | A planned pause that says what to do |
| `docs/slicer.md` | Pause Print G-code: `PAUSE_FOR_USER` | **Slicer change** |
| `macros/print/part_ready.cfg` (new) | After a completed print, once the bed is below `part_ready_bed_temp` (40), machine state `part_ready` (part-ready LEDs) and a notification | Know when the part can come off |
| `macros/state/machine_state.cfg` | machine state `part_ready` | |
| `macros/system/notify.cfg` (new) | `_NOTIFY MSG=`: console message, and a push notification through Moonraker's notifier when `notifier_name` is set | Off until you configure it (docs/notifications.md) |
| MMU error, failed print, preflight wait, planned pause, part ready | each sends `_NOTIFY` | The moments that need you at the machine |
| `mmu/base/mmu_macro_vars.cfg` + `mmu/.mmu_config` | `user_mmu_error_extension: _MMU_RECOVERY NOTIFY=1` | Only the hook notifies, not Refresh or the menu |
| `macros/ui/confirm.cfg` (new) | `_CONFIRM_CANCEL BACK=<macro>`, used by the recovery, preflight and pause dialogs | One cancel confirmation instead of three |
| `config/variables.cfg` | `part_ready_bed_temp: 40`, `notifier_name: ""` | |
| `docs/notifications.md` (new) | Moonraker notifier set-up (secrets file, two notifier sections) | |

Simulator: `start_*` (completed prints) end by arming the part-ready check.
The recovery cancel goes through `_CONFIRM_CANCEL`. New scenarios for the
error hook, planned pauses, part-ready and a notification. Nothing else changed.

Checks:

- [ ] **N1** Set PrusaSlicer's Pause Print G-code to `PAUSE_FOR_USER`, add a pause with a message to a test print: the dialog shows the message, and Resume carries on
- [ ] **N2** MENU during a print → "Pause at the next layer" pauses at the next layer change with the dialog
- [ ] **N3** After a completed print, the LEDs switch to part-ready once the bed is below 40°C
- [ ] **N4** (Optional) Set up a notifier (docs/notifications.md). `_NOTIFY MSG="Test"` reaches your phone, and so do an MMU error and part-ready

## PR #27: maintenance counters, calibration menu, CHECK_CONFIG dialog

| File | Change | Reason |
|---|---|---|
| `macros/workflows/maintenance.cfg` (new) | `MAINTENANCE`: printing-hour counters per job, with a "Done" button each. `_END_JOB` adds each job's printing time (pauses excluded). The filter only counts jobs with a chamber temperature. Crossing an interval sends a notification, and MENU shows "Maintenance due (n)" | Routine jobs without remembering |
| `config/variables.cfg` | `maintenance_items`: carbon 100 h, rails/belts 200 h, nozzle 300 h | **Starting points: set your own intervals** |
| `macros/workflows/nozzle_change.cfg` | recording a new nozzle restarts its counter | |
| `macros/workflows/calibrate.cfg` (new) | `CALIBRATE`: nozzle PID (at `print_default_extruder_temp`, just above the bed, part fan 25%), bed PID (at `print_default_bed_temp`), Shake&Tune input shaper and belts, full bed mesh. Each homes and runs QGL first if needed | The routine calibrations in one place |
| same | PID results are shown to copy into `config/hardware/*.cfg` | The PID values live in included files, so `SAVE_CONFIG` refuses to override them |
| `macros/state/startup_check.cfg` | `CHECK_CONFIG` also shows its result as a dialog: always when run by hand, and at startup when it finds errors | Errors that block `START_PRINT` are visible on the touchscreen |
| `macros/ui/menu.cfg` | Calibrate and Maintenance buttons. `_CLOSE_AND_PARK` is shared by the workflow dialogs | |
| `macros/system/dependencies.cfg` | Shake&Tune's `AXES_SHAPER_CALIBRATION`, `COMPARE_BELTS_RESPONSES` | |

Simulator: completed and cancelled jobs add to the maintenance counters (one
`SAVE_VARIABLE` line). `check` now also shows the dialog. New scenarios for
maintenance, calibration and the startup dialog. Nothing else changed.

Checks:

- [ ] **M5** Set `maintenance_items` to your own intervals
- [ ] **M6** After a print, `MAINTENANCE` shows its hours added (the filter only for chamber prints). "Done" restarts a counter
- [ ] **M7** CALIBRATE → Nozzle PID: homes, levels, moves to the bed centre at Z 5, tunes, and shows kp/ki/kd. Copy them into `config/hardware/extruder.cfg`
- [ ] **M8** CALIBRATE → Input shaper runs Shake&Tune, and the graphs appear in ShakeTune_results
- [ ] **M9** Run `CHECK_CONFIG` from the console: the dialog lists the result

## PR #28: deploy script and GitHub checks (tools only)

| File | Change | Reason |
|---|---|---|
| `tools/deploy.py` (new) | Run on the Pi from a separate clone. It pulls, refuses during a print, runs `check_deps`, shows the plan (added, changed, and removed files), backs up the whole config folder, and copies. Then it restarts Klipper (and Moonraker or KlipperScreen if their config changed) and prints `CHECK_CONFIG`. `--dry-run`, `--rollback <backup>` | One safe way to get `main` onto the printer |
| same | Keeps what the printer owns: `printer.cfg`'s SAVE_CONFIG block, KlipperScreen.conf's generated section, `mmu/mmu_vars.cfg`, ShakeTune_results | Fresh calibration and Happy Hare state aren't overwritten |
| same | Removes files in our own folders (macros, config, tools, docs, ukam) that the repository no longer has | Klipper includes those folders by wildcard, so a stale copy of a moved file would load twice |
| same | Runs klipper-backup afterwards, unless it backs up to this repository | See below |
| `.github/workflows/check.yml` (new) | On every PR: `check_deps`, all simulator scenarios, and the PR's G-code differences in the run summary. Weekly: `check_deps` against Happy Hare's main and development branches | A coming Happy Hare change shows up before you update |

**klipper-backup.** I read its script. It skips symbolic links, replaces
`.gitignore` with its own, and with the usual `backupPaths` writes everything
under `printer_data/config/`. Pointed at this repository, it would delete the
`mmu/macros` links and restructure the repository. `deploy.py` therefore only
runs it when `~/klipper-backup/.env` points at a different repository.
Earlier I said klipper-backup would "overwrite main". That's only true if it
backs up to this repository, which this repository's layout suggests it
doesn't.

Checks:

- [ ] **D1** Check where klipper-backup backs up to (`github_repository` in `~/klipper-backup/.env`). If it's VoronConfig, point it at a separate repository
- [ ] **D2** On the Pi: clone the repository to `~/VoronConfig` and run `python3 ~/VoronConfig/tools/deploy.py --dry-run`. Check the plan, especially the files it removes
- [ ] **D3** Run it for real. The SAVE_CONFIG block (Beacon model) is kept, and `CHECK_CONFIG` prints OK
- [ ] **D4** GitHub → Actions: the `check` workflow passes on main

## PR #29: chamber soak, bed soak, mesh/QGL area, clog detection, endless spool, clean-up

| File | Change | Reason |
|---|---|---|
| `macros/accessories/heatsoak.cfg`, `config/variables.cfg` | Chamber soak now waits at `chamber_soak_position_xyz: 175, 175, 80` (lifts Z first). The bed soak stays at 300,300, Z 2 | The chamber thermistor is on the toolhead. At Z 2 over a 100 °C bed it read the bed, so the chamber soak ended almost at once. My mistake in PR #19 |
| `config/variables.cfg` | `print_default_soak: 10` (was 2) minutes of bed soak when the bed starts cold | A 350 plate keeps moving well after it reaches temperature. Preheating skips it |
| `config/software/bed_mesh.cfg` | `mesh_min: 15, 20`, `mesh_max: 335, 335` (was 40..310). Stale comments removed | No reason for the 40 mm margins. Beacon reaches X 0–353 and Y 15.6 onwards |
| `config/software/qgl.cfg` | QGL points (nozzle) 25,10 / 25,310 / 325,310 / 325,10. Beacon measures at X 25/325, Y 25.6/325.6 (was 50/300, 40.6/290.6) | Wider points level the gantry more accurately |
| `mmu/base/mmu_parameters_unit0.cfg` + `.mmu_config` | `flowguard_encoder_mode: 2` (was 0) | Encoder clog/tangle detection was off. 2 = auto-tuned detection length |
| `mmu/base/mmu.cfg` + `.mmu_config` | `endless_spool_enabled: 1` | Runout switches to another gate with the same filament |
| `macros/mmu_hooks/endless_spool.cfg` (new) | `_ENDLESS_SPOOL_AUTOGROUP`: puts gates holding the same filament (material and name, from NFC/Spoolman) in one endless spool group. Runs at print start (`PREFLIGHT_CHECK`), after a spool swap and in `MMU_CHECKUP` | Endless spool does nothing until gates are grouped, and groups are otherwise set by hand. Groups set by hand are replaced |
| `config/boards/rpi.cfg` | `[mcu rpi]` removed (the Pi temperature sensor stays) | Nothing used it. The host MCU service could only stop Klipper starting |
| `config/software/settling_probe.cfg`, `test_probe_accuracy.cfg`, `fluidd.cfg` | removed | A Klicky/Tap feature, an empty file and an empty file |
| `config/hardware/extruder.cfg`, `probe.cfg` | stale template comments replaced (Galileo 2, Revo thermistor, why Z homes at 300,300) | |
| `macros/print/job_recovery.cfg`, `docs/state-table.md` | corrected: Klipper's `on_error_gcode` turns the heaters off by default | I said otherwise in PR #23 |

Simulator: the bed soak waits 10 minutes, the chamber soak waits at 175,175,80, and there's a new endless spool scenario. Nothing else changed.

Checks:

- [ ] **T1** **Mesh edges:** run `BED_MESH_CALIBRATE` (non-adaptive, MENU → Calibrate → Full bed mesh) and check the edges of the mesh view. A sudden drop or jump along an edge means Beacon is partly off the plate there: move that `mesh_min`/`mesh_max` value in by 5–10 mm
- [ ] **T2** **QGL points:** run `QUAD_GANTRY_LEVEL` and watch each probe point. Beacon must be fully over the plate, clear of edges, clips and magnets, at all four. It should converge in a few retries
- [ ] **T3** A chamber print: the soak waits at the centre, 80 mm up. The chamber temperature climbs slowly instead of jumping, and the soak runs until the target or the time limit
- [ ] **T4** A cold-bed start soaks the bed 10 minutes
- [ ] **T5** `MMU_ENDLESS_SPOOL` shows endless spool enabled, with gates of the same filament grouped. If it still says disabled, Happy Hare has a saved "off" in `mmu_vars.cfg`: run `MMU_ENDLESS_SPOOL ENABLE=1` once
- [ ] **T6** Encoder clog detection: no false clog pauses over a few prints. If they happen, use `flowguard_encoder_mode: 1` with a larger `flowguard_encoder_max_motion`
- [ ] **T7** Klipper starts without `[mcu rpi]`. You can disable the `klipper-mcu` service afterwards

## PR #30: Klipper's on-error hook, duplicate sections, SCV 5, Happy Hare extrusion limits

| File | Change | Reason |
|---|---|---|
| `config/machine.cfg` | `[virtual_sdcard] on_error_gcode`: `TURN_OFF_HEATERS`, then `_JOB_FAILED_LATER` (a delayed `_JOB_FAILED`, 1 s later) | Klipper's own hook replaces relying on Happy Hare's print detection. Klipper runs it before recording the error message, hence the delay |
| `macros/state/status_leds.cfg`, `startup_check.cfg`, `dependencies.cfg` | Happy Hare state `error` no longer triggers the dialog. The `print_start_detection` warning and dependency are gone | One trigger |
| `config/machine.cfg` | `square_corner_velocity: 5.0` (was 12) | Klipper's default. Higher adds input-shaper smoothing. Per-feature SCV comes after the Monolith/A4T upgrade, from the slicer |
| `mmu/base/mmu_macro_vars.cfg` | `[respond]`, `[display_status]`, `[pause_resume]` removed (still in `config/machine.cfg`) | Defined twice. The installer may add them back on an update, which is harmless |
| `config/hardware/extruder.cfg` | `max_extrude_only_distance: 200` (was 120), `max_extrude_cross_section: 50` (was 5) | **Found while doing the above.** Happy Hare sets these in `mmu_macro_vars.cfg` as MMU requirements, but `extruder.cfg` is included later, so our lower values silently won. Now the same as Happy Hare's |
| `mainsail.cfg` | removed | A broken link to a Mainsail install you don't use |

Simulator: identical (the failure scenarios now call `_JOB_FAILED` directly).

Checks:

- [ ] **E1** Make a print fail (e.g. a file sliced for the wrong nozzle): the heaters go off and, a second later, the "Print stopped" dialog shows the error message
- [ ] **E2** `SET_VELOCITY_LIMIT` with no parameters reports square_corner_velocity 5. Re-tune the shaper with this value (Shake&Tune graphs use it)
- [ ] **E3** Toolchanges, Blobifier purges and loads run without "Extrude only move too long" or "Move exceeds maximum extrusion" errors

## PR #31: retune wizard, PID and input shaper in SAVE_CONFIG

| File | Change | Reason |
|---|---|---|
| `macros/workflows/retune.cfg` (new), `docs/retune.md` (new) | `RETUNE` (MENU → Calibrate → Retune): the whole retune as a checklist, with each step's buttons and the guide's values. Ticks are kept in `retune_done` | One place to work through the retune |
| `macros/workflows/calibrate.cfg` | PID and `SHAPER_CALIBRATE` results shown in a dialog with a Save button. New axes-map, belt and mesh entries usable from the wizard | Saving was a copy-by-hand step |
| `printer.cfg` (SAVE_CONFIG block) | Extruder and bed PID and the shaper types/frequencies moved here, same values | Klipper can only save these where it owns them. Values in an included file can't be overridden by `SAVE_CONFIG` |
| `config/hardware/extruder.cfg`, `heated_bed.cfg`, `config/software/input_shaper.cfg` | `control`, `pid_*`, `shaper_type_*`, `shaper_freq_*` removed. Damping ratios stay (`SHAPER_CALIBRATE` doesn't save them) | Moved above |
| `tools/deploy.py` | The SAVE_CONFIG block is merged: the printer's values win, and anything only the repo has is added | A deploy no longer overwrites what you saved on the printer |
| `config/variables.cfg` | `belt_check_position_xy: 175, 175` | Where the wizard parks for belt measuring, about 150 mm from the front idlers |
| `tools/check_deps.py` | Fails on `;`, `#`, `*` or `\|` in dialog text | Klipper reads them as a comment or separator and cuts the dialog short. It caught four in this PR |

Simulator: four new scenarios (`retune_list`, `retune_steps`, `retune_ercf`, `cal_shaper_klipper`). Nothing else changed.

Checks:

- [ ] **R1** After deploying, `printer.cfg` on the printer still has its `#*# [beacon model default]` block, now with the PID and shaper sections above it. Klipper starts, and `SET_INPUT_SHAPER` reports mzv 47.6 / ei 43.6
- [ ] **R2** `RETUNE` shows nine steps. Mark one done, restart Klipper: it's still ticked
- [ ] **R3** Run one PID from the wizard and press Save: Klipper restarts with the new values in the SAVE_CONFIG block. Deploy again: they're kept
- [ ] **R4** The ERCF step's buttons each run (motors off, selector, advance, move 100 mm) and the dialog comes back afterwards
- [ ] Then work through the retune itself (`docs/retune.md`)

## PR #32: PA/EM test prints, a pick-any tune menu, more ERCF tunes

| File | Change | Reason |
|---|---|---|
| `tools/calib_gcode.py` (new), `macros/workflows/filament_tests.cfg` (new) | `CAL_FILAMENT TEST=pa\|em`: pick a gate and a range, and the printer writes an Ellis-style test (PA chevrons or EM squares) and prints it with our own start/end sequence. At the end you pick the best pattern; it's applied and kept per filament and nozzle (`filament_tuning`) | Ellis's online generator needs its start G-code rewritten for this printer and doesn't load a gate. This one can't get that wrong |
| `config/variables.cfg` | `calib_perimeter_speed: 100`, `calib_perimeter_accel: 4000`, `calib_max_flow: 15`, `calib_fan` per material | The PA result depends on the speed and acceleration of the corners. **Set these to your PrusaSlicer external perimeter values** |
| `macros/print/end_print.cfg` | After a test print in `calibration/`, acceleration and flow are restored, and PA too on a cancel | A cancelled PA test would otherwise leave the last pattern's PA set |
| `macros/workflows/retune.cfg` | `RETUNE` is now a menu of 14 tunes in four groups, any of which can be run on its own. ERCF split into selector and servo, gear/encoder/bowden, Filamentalist tension (per-gate out-and-back test), per-gate calibration (rotation distances against gate 0), toolhead distances, and a load/unload soak test | Pick the tune you want. The per-gate and Filamentalist checks were missing |
| `macros/workflows/calibrate.cfg` | PA and EM test print buttons | |
| `macros/system/dependencies.cfg` | `MMU_HOME`, `MMU_SERVO`, `MMU_SOAKTEST_LOAD_SEQUENCE`, `RUN_SHELL_COMMAND`, `gate_temperature` | Used by the above |

Simulator: new scenarios for the tune menu, per-gate dialog, Filamentalist test, the filament tests, picking a result and cancelling a test. Other scenarios are unchanged.

Checks:

- [ ] **P1** Set the `calib_*` values in `config/variables.cfg` to your PrusaSlicer profile's external perimeter speed and acceleration
- [ ] **P2** `CAL_FILAMENT TEST=pa`, pick a gate, Wide: the console says `calib_gcode: wrote …`, and the print starts, loads that gate, and prints 21 chevrons numbered 1, 6, 11, 16 and 21 in the middle of the bed
- [ ] **P3** At the end, the "Which pattern is best?" dialog appears. Pick one: `SET_PRESSURE_ADVANCE` with no parameters reports it, and the PA/EM dialog lists it
- [ ] **P4** Cancel a test partway: the PA goes back to what it was before (`SET_PRESSURE_ADVANCE` with no parameters reports it) and `SET_VELOCITY_LIMIT` shows max_accel 7000 again
- [ ] **P5** An EM test prints 10 squares. Their top surfaces visibly change from gappy (left) to rough (right)
- [ ] **P6** `RETUNE` shows the four groups; each tune opens on its own
- [ ] **P7** Filamentalist test on one gate: the filament goes 300 mm out, comes back, and the gate parks again

## PR #33: PA test is explicitly two-phase

| File | Change | Reason |
|---|---|---|
| `macros/workflows/filament_tests.cfg` | After a Wide (or Fine 0.01–0.06) PA pick, the result dialog makes "Fine PA test around …" the primary button; after a fine pick, the EM test. `cal_last` records the range | Ellis's PA method is two-phase: find the area, then narrow down |

- [ ] **Q1** After picking from a Wide PA test, the highlighted button is the fine test around your pick

## PR #34: PrusaSlicer presets generated from one source and Spoolman; nozzle type; max flow test; bypass

| File | Change | Reason |
|---|---|---|
| `slicer/profiles.py`, `slicer/base/*.ini` (new), `tools/build_slicer_profiles.py` (new) | All PrusaSlicer printer, print and filament presets are generated. Settings live once, in `profiles.py`; filaments come from Spoolman; machine limits from `config/machine.cfg`. See `docs/slicer.md` | PrusaSlicer user presets can't inherit from each other, so every value was copied by hand, and the copies had drifted apart |
| (presets) | Start G-code is the current one (the old presets' `MATERIALS=` version is refused by `START_PRINT`); no M600 (colour change and pause use `PAUSE_FOR_USER`); `MMU_UPDATE_HEIGHT` instead of the internal `_MMU_UPDATE_HEIGHT`; every tool retracts the same (T0 differed); the 0.60/0.80 "MMU" printers are real 8-tool printers; overhang speeds the right way round; travel within `max_velocity`; machine limits for time estimates from `machine.cfg` (travel was 1500); arc fitting off; supports off by default; chamber temperature set for ABS/ASA (it was 0 everywhere, so no chamber soak ever ran) | Findings from the bundle review |
| (presets) | Pressure advance is generated per nozzle in each filament's start G-code from its Spoolman values; a value for every nozzle, so a tool change never keeps the previous filament's PA. Hard-coded `SET_ACTIVE_SPOOL` removed | The old `;{elsif …}` lines meant to disable values were still evaluated by PrusaSlicer; `SET_ACTIVE_SPOOL` fought Happy Hare's own spool tracking |
| `tools/spoolman_tuning.py` (new) | `setup` creates the Spoolman fields; `set` saves a result to a spool's filament; `import-bundle` copies PA/EM/flow/fan/retraction from an exported bundle into Spoolman | Spoolman is the master copy of filament tuning |
| `macros/workflows/filament_tests.cfg`, `tools/calib_gcode.py` | Results are saved to the gate's filament in Spoolman; PA per nozzle key (`pa_0_60_hf`). New **max flow test** (`CAL_FILAMENT TEST=flow`): single wall in rising-flow bands, saved with a 10 % margin | One place for tuning; flow limits were guesses |
| `macros/print/start_print.cfg`, `nozzle_change.cfg`, `menu.cfg`, `config/variables.cfg` | `NOZZLE_SET DIAMETER= TYPE=brass\|hf\|obxidian`; the nozzle-change dialog offers your nozzles (`variable_nozzles`, replaces `nozzle_sizes`; 0.50 dropped as no preset used it); `START_PRINT NOZZLE_TYPE=` refuses a file sliced for another nozzle type | HF and brass 0.60 need different presets and PA |
| `macros/workflows/bypass.cfg` (new), `menu.cfg`, `retune.cfg` | MENU → Bypass: select, load, unload. RETUNE → Selector: calibrate the bypass position | Easy bypass printing, with the "(bypass)" printer presets |
| `.github/workflows/check.yml`, `slicer/test_spoolman_filaments.json` | CI builds the presets and the three test prints | Catches a broken `profiles.py` |

Checks:

- [ ] **S1** After deploying: `NOZZLE_SET DIAMETER=<fitted> TYPE=<brass/hf/obxidian>` (or MENU → Change the nozzle). Until then the printer assumes brass, and an HF file is refused
- [ ] **S2** On the Pi: `python3 ~/printer_data/config/tools/spoolman_tuning.py setup`; Spoolman shows the new filament fields
- [ ] **S3** `import-bundle` with your exported bundle: check the matches, fix any "NO MATCH" names in Spoolman, then `--apply`
- [ ] **S4** Build into PrusaSlicer (`docs/slicer.md`, step 4); the printers, prints and filaments appear under User presets, and "Send to printer" works
- [ ] **S5** Slice something with two filaments on the HF printer: the file has `NOZZLE_TYPE=hf`, a `CHAMBER=` value for ABS/ASA, and a `SET_PRESSURE_ADVANCE` after each tool change. (Only checked here with PrusaSlicer 2.7 without the chamber expression: the 2.9 chamber line is untested)
- [ ] **S6** A short print from the new presets prints normally; compare speed and quality with the old Standard preset
- [ ] **S7** MENU → Bypass with the bypass calibrated: select, load, print with a "(bypass)" printer, unload
- [ ] **S8** `CAL_FILAMENT TEST=flow` on the HF nozzle: the wall changes from smooth to rough partway up; pick the band; the console shows it saved to Spoolman

## PR #35: every slicer setting reviewed

The full review, setting by setting with sources: `docs/slicer-settings.md`. Key-by-key list: `docs/slicer-reference.md` (CI keeps it current).

| File | Change | Reason |
|---|---|---|
| `slicer/profiles.py` | Inner walls = outer walls: 150 mm/s, 0.5 × max_accel (was 200 / 0.7 and 150 / 0.45). Quality: both 100 at 0.35× | Voron Discord: PA is tuned at one wall speed/acceleration; different inner/outer walls show it |
| same | Overhang speeds 50 / 70 / 100 % / 100 % (bridging → 75 % overlap) | Discord (the author of Orca's port of this feature): slow only near bridging, and not far |
| same | Top surface acceleration 0.3 × max_accel (was 0.45) | PS-Voron 1200, PS-Prusa 800–2000 |
| same | Infill anchors 2.5 / 12 mm (was 600 % / 20); G-code resolution 0.008 (was 0.0125); one skirt loop | PrusaSlicer's Voron and Prusa profiles |
| same | Classic wall generator for Quality and PIF | Discord reports Arachne outer-wall artefacts; PS-Voron printed parts use Classic |
| same | Draft: automatic infill combination | PrusaSlicer 2.9 feature, faster sparse infill |
| same | ABS/ASA/PC minimum layer time 8 s (5 in PR #34); cooling transition 10 mm; fan ramps to full by layer 3; overhang fan per material (dynamic fan on) | Discord: 3 s too low for ABS, 8–15 typical; PS-Voron cooling logic |
| same, `tools/build_slicer_profiles.py`, `tools/spoolman_tuning.py` | Abrasive filaments (Spoolman `abrasive`, or CF/GF/carbon/glass in the name) are flagged and only offered for the hardened ObXidian printer | PrusaSlicer 2.9's abrasive flag; protects brass nozzles |
| same | Toolhead clearance 75 / 33 mm (was 20 / 20); host type moonraker; time-estimate corner speed = square_corner_velocity | One-at-a-time printing (Stencil) needs real clearance |
| `config/hardware/extruder.cfg` | `pressure_advance_smooth_time: 0.02` (was 0.04) | Discord: 0.015–0.02; the default lags speed changes |
| `config/variables.cfg` | PA test walls 150 mm/s, 3500 mm/s² (was 100 / 4000); the build warns if they differ from the presets | PA must be tuned at the walls' speed and acceleration |

Checks:

- [ ] **V1** Retune PA after this (smoothing changed): RETUNE → PA and EM
- [ ] **V2** Rebuild the presets; Quality and PIF prints show "Classic" in PrusaSlicer's wall generator; a carbon-fibre filament only appears with the ObXidian printer
- [ ] **V3** Print a part with overhangs and a cylinder at Standard: no slowdown marks on gentle overhangs, seam hidden on the cylinder
- [ ] **V4** Measure the toolhead clearance (radius around the nozzle, nozzle tip to the gantry) and set `extruder_clearance_*` before using Stencil

## PR #36: Klipper wouldn't start ('#' inside macros)

Klipper's config reader cuts every line at its first `#`, even inside a quoted string (`klippy/configfile.py`). Thirteen macros used `replace('#', '')` to clean text for dialogs, so their lines were cut short and Klipper halted with "Error loading template 'gcode_macro _JOB_FAILED:gcode'" (the first of them).

| File | Change | Reason |
|---|---|---|
| 9 macro files | `replace('#', …)` → `replace('%c' % 35, …)` (the same character, produced at run time) | No `#` in the file for Klipper to cut at |
| `tools/macro_sim/macrosim.py` | Strips comments exactly as Klipper does | It treated `#` as a comment only after a space, so it ran the uncut lines and passed |
| `tools/check_deps.py` | Fails on a `#` inside a quoted string | Clear message for this mistake |
| `tools/klipper_load_check.py` (new), CI | Loads the config with Klipper's own reader and compiles every template in Klipper's Jinja environment (all errors, not just the first) | Catches anything that stops Klipper starting before it reaches the printer |

- [ ] **K1** Deploy, `RESTART`: Klipper starts
