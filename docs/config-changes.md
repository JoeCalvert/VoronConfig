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
