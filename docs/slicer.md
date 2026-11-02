# PrusaSlicer setup

The slicer owns how each filament prints: temperatures, pressure advance, flow,
retraction, cooling, chamber temperature, and the purge volumes between
filaments. The printer only needs a few numbers from it: bed, nozzle and
chamber temperatures, and the nozzle size. See "System integration: who owns
what" in the modernisation plan.

The printer preset is a single-extruder multi-material printer with 8
extruders (one per ERCF gate), G-code flavour **Klipper**.

## Printer Settings → Custom G-code

### Start G-code

```
M140 S{first_layer_bed_temperature[initial_tool]}
MMU_START_SETUP INITIAL_TOOL={initial_tool} REFERENCED_TOOLS=!referenced_tools! TOOL_COLORS=!colors! TOOL_TEMPS=!temperatures! TOOL_MATERIALS=!materials! FILAMENT_NAMES=!filament_names! PURGE_VOLUMES=!purge_volumes!
MMU_START_CHECK
PREFLIGHT_CHECK
START_PRINT BED={first_layer_bed_temperature[initial_tool]} EXTRUDER={first_layer_temperature[initial_tool]} NOZZLE={nozzle_diameter[0]} CHAMBER={max(max(max((is_extruder_used[0] ? chamber_temperature[0] : 0), (is_extruder_used[1] ? chamber_temperature[1] : 0)), max((is_extruder_used[2] ? chamber_temperature[2] : 0), (is_extruder_used[3] ? chamber_temperature[3] : 0))), max(max((is_extruder_used[4] ? chamber_temperature[4] : 0), (is_extruder_used[5] ? chamber_temperature[5] : 0)), max((is_extruder_used[6] ? chamber_temperature[6] : 0), (is_extruder_used[7] ? chamber_temperature[7] : 0))))}
MMU_START_LOAD_INITIAL_TOOL
POST_START_PRINT
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
```

- `M140` comes first, so the bed heats while Happy Hare checks the gates.
- `PREFLIGHT_CHECK` compares each tool's material and filament name with its
  gate, and pauses with a dialog if they differ (`macros/print/preflight.cfg`).
- `CHAMBER` is the highest chamber temperature among the filaments this print
  actually uses (`is_extruder_used`). The expression assumes 8 extruders. If
  PrusaSlicer reports an error in it (older versions have no
  `chamber_temperature`), use `CHAMBER={chamber_temperature[initial_tool]}` or
  `CHAMBER=0` instead.
- The `!…!` values are filled in by Happy Hare's G-code preprocessor in Moonraker
  when the file is uploaded.
- Keep these as separate lines. Happy Hare can then pause between steps if
  something goes wrong (Happy Hare's slicer setup guide explains why).
- `START_PRINT` refuses files that still use the old `MATERIALS=` / `SIZE=`
  parameters, and files sliced for a different nozzle from the one recorded with
  `NOZZLE_SET`.

### End G-code

```
MMU_END
END_PRINT
```

`MMU_END` cuts and unloads the filament (`unload_tool` is on); `END_PRINT` then
parks and shuts down.

### Tool change G-code

```
T[next_extruder]
```

Happy Hare's preprocessor adds the next print position to each tool change, so
the toolhead goes straight there after purging (`restore_xy_pos: next`).

### After layer change G-code

```
SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}
```

Used by pause-at-layer and Mainsail's layer display.

## Other settings

- **Temperature commands:** heating is done by `START_PRINT`, so PrusaSlicer must
  not add its own heat-and-wait lines. Turn off "Emit temperature commands
  automatically" in Printer Settings → Custom G-code, then check a sliced file:
  nothing before `MMU_START_SETUP` except the `M140` line, and no `M141`/`M191`.
  This printer has no chamber heater, so those commands would stop the print.
- **Label objects:** Print Settings → Output options → "Firmware-specific".
  Klipper's `exclude_object` uses the labels, and the adaptive mesh only probes
  where the objects are.
- **Wipe tower** off, "wipe into infill/object" off. Blobifier purges the full
  purging volume. The purging volumes matrix still goes into the file, and Happy
  Hare passes it to Blobifier.
- **Single extruder MM settings** (ramming, cooling moves, loading/unloading
  speeds and times) off or zero, because the toolhead cutter does the work.
  Follow [Happy Hare's slicer setup](https://moggieuk.github.io/Happy-Hare-Doc/Slicer-Setup/).
- **Pressure advance:** PrusaSlicer has no pressure advance setting, so it goes
  in each filament's Filament Settings → Custom G-code → Start G-code. That runs
  at the start and after every tool change. With swappable Revo nozzles, make it
  depend on the nozzle:
  ```
  {if nozzle_diameter[0]==0.4}SET_PRESSURE_ADVANCE ADVANCE=0.040
  {elsif nozzle_diameter[0]==0.6}SET_PRESSURE_ADVANCE ADVANCE=0.030
  {endif}
  ```
  (Example values; use your measured ones.) `pressure_advance` in `extruder.cfg`
  is then only the default for moves outside a print.
- **Chamber temperature:** set it on filaments that need a warm chamber (e.g.
  ABS/ASA) in Filament Settings → Temperature. `START_PRINT` waits for it, with
  the filter running.
- **Filament names** must match the Spoolman filament names exactly. Happy Hare
  maps tools to gates by name.
- **Nozzles (Revo):** one printer preset per nozzle size, or the conditional
  pressure advance above.
- **Machine limits:** don't exceed the printer's (`max_velocity` 400,
  `max_accel` 7000).

## Exported profiles

The printer, print and filament profiles will be exported into `slicer/`, so the
slicer side is versioned with the config. (To do: export them from PrusaSlicer.)
