# Machine states and sequences

What the printer does in each state, in order, and where the toolhead ends up.
Happy Hare owns everything between unload and load. Our macros own job start and
end. They meet only through Happy Hare's `user_*` hooks
(`mmu/base/mmu_macro_vars.cfg`), whose handlers live in `macros/mmu_hooks/`.

Two records make the current situation visible at any time (run `_JOB` in the
console to print both):

- **`_SET_STATE STATE=…`** (`macros/state/machine_state.cfg`) is the only place
  the toolhead LEDs, case light and filter are set. Its header has the table of
  what each state looks like. `printer["gcode_macro _SET_STATE"].state` is the
  current machine state.
- **`_JOB`** holds the print job: `phase` (idle → preparing → prepared →
  printing → complete | cancelled) and the chamber target. `POST_START_PRINT`
  refuses to run unless `START_PRINT` reached `prepared`.

| State | Sequence | Ends at | Where |
|---|---|---|---|
| Startup | `CHECK_CONFIG` runs after 5 s; `START_PRINT` is blocked if it finds errors | | `macros/state/startup_check.cfg` |
| Homing (`G28`, `_CG28`) | X then Y, sensorless (X moves right, away from the pin, first). Z by Beacon proximity, safe at any nozzle temperature. LEDs static | Z home point (300,300) | `macros/motion/` |
| `START_PRINT` | Home if needed. Bed to target, nozzle to 150 °C. Heat-soak if the slicer asks for a chamber temperature (filter on), waiting at `soak_position_xyz` (300,300, Z 2). Coarse QGL, wipe, contact home with `CALIBRATE=1`, QGL, contact home, adaptive mesh. Park over the Blobifier tray, heat to print temperature, apply the hot-nozzle offset | Tray | `macros/print/start_print.cfg` |
| First tool load | `MMU_START_LOAD_INITIAL_TOOL`: load, Blobifier purge, wipe | Brush exit (X 70, back row), then the first print move | Happy Hare |
| Printing | `POST_START_PRINT`: filter to working speed, lights, LEDs show the filament colour | | `macros/print/post_start_print.cfg` |
| Toolchange / runout | Z-hop 1 mm, retract 2 mm. Cut (Happy Hare's guarded approach along Y 346), unload and load at the cutter exit (X 90), purge, wipe. Straight to the next print position | Next print position | Happy Hare |
| MMU error | Pause: z-hop, retract, park on the back row (175,355), sideways along the back from the tray. Heater off after 600 s. After you fix it, resume: `BLOBIFIER_CLEAN` wipe, then Happy Hare finishes the toolchange and returns | Back row | Happy Hare + `user_resume_extension` |
| User pause | Same park and resume | Back row | Happy Hare |
| Cancel | Happy Hare: z-hop 10 mm, retract 5 mm, heaters off; filament stays loaded. Then `_CANCEL_PRINT_EXTENSION` → `_END_JOB REASON=cancel`: `PARK` (X before Y), heaters off, mesh cleared, state `cancelled` (lights, LEDs and filter off) | End-of-job point (175,100), high Z | `macros/mmu_hooks/cancel_print.cfg`, `macros/print/end_print.cfg` |
| Complete | Slicer end G-code: `MMU_END` (lift only, then cut and unload), then `END_PRINT` → `_END_JOB REASON=complete`: `PARK`, heaters off, mesh cleared, motors off, state `complete` (end-of-print light; filter runs 10 min after a heated-chamber print) | End-of-job point | `macros/print/end_print.cfg` |

## Fixed positions

Each has one owner; macros read them rather than retyping them.

| Position | Value | Owner |
|---|---|---|
| Cutter pin | 10, 346 | `_MMU_CUT_TIP_VARS.pin_loc_xy` |
| Cutter exit / clearance line | X 90 = pin X + `pin_park_dist` 20 + `safe_margin_x` 60 | derived (checked by `CHECK_CONFIG`) |
| Blobifier tray | X 5 (`purge_x`), back row | `_BLOBIFIER_VARS` |
| Brush | X 90–125 (`brush_start`, `brush_width`) | `_BLOBIFIER_VARS` |
| Pause park | 175, 355 | `_MMU_SEQUENCE_VARS.park_pause` |
| End-of-job park | 175, 100 | `_USER_VARIABLES.park_position_xy` |
| Z home / mesh zero | 300, 300 | Beacon `home_xy_position` = `bed_mesh` `zero_reference_position` |

The only fixed obstacle is the cutter pin: the tray sits directly behind it.
Nothing may move forward from the tray without first moving right; see the
"Motion safety" section of the modernisation plan.
