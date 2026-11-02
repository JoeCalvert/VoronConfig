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
