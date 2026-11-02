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
| `macros/print/job_recovery.cfg` (new) | `_JOB_FAILED`: when a print stops with an error (in `START_PRINT` or while printing), job phase `failed`, machine state `failed`, and a dialog with the error, the step it was on, Reprint / Turn the heaters off / Unload | Klipper just stops with the heaters on. Klipper has no error hook, but Happy Hare reports print state `error`, so no polling is needed |
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
