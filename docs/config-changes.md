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
