# OrcaSlicer setup

The slicer owns how each filament prints: temperatures, pressure advance, flow,
retraction, cooling, chamber temperature and the purge volumes between
filaments. The printer only needs three numbers from it, plus the nozzle
size. See "System integration: who owns what" in the modernisation plan.

## Printer settings → Machine G-code

### Machine start G-code

```
M140 S[bed_temperature_initial_layer_single]
MMU_START_SETUP INITIAL_TOOL={initial_tool} REFERENCED_TOOLS=!referenced_tools! TOOL_COLORS=!colors! TOOL_TEMPS=!temperatures! TOOL_MATERIALS=!materials! FILAMENT_NAMES=!filament_names! PURGE_VOLUMES=!purge_volumes!
MMU_START_CHECK
START_PRINT BED=[bed_temperature_initial_layer_single] EXTRUDER={nozzle_temperature_initial_layer[initial_tool]} CHAMBER={overall_chamber_temperature} NOZZLE={nozzle_diameter[0]}
MMU_START_LOAD_INITIAL_TOOL
POST_START_PRINT
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
```

- `M140` comes first, so the bed heats while Happy Hare checks the gates.
- The `!…!` values are filled in by Happy Hare's G-code preprocessor in Moonraker
  when the file is uploaded.
- Keep these as separate lines. Happy Hare can then pause between steps if
  something goes wrong (Happy Hare's slicer setup guide explains why).
- `START_PRINT` refuses files that still use the old `MATERIALS=` / `SIZE=`
  parameters, and files sliced for a different nozzle from the one recorded with
  `NOZZLE_SET`.

### Machine end G-code

```
MMU_END
END_PRINT
```

`MMU_END` cuts and unloads the filament (`unload_tool` is on); `END_PRINT` then
parks and shuts down.

### Change filament G-code

```
T[next_extruder]
```

Happy Hare's preprocessor adds the next print position to each tool change, so
the toolhead goes straight there after purging (`restore_xy_pos: next`).

### Layer change G-code

```
SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}
```

Used by pause-at-layer and Mainsail's layer display.

## Other settings

- **Temperature commands:** the start G-code heats through `START_PRINT`, so Orca
  must not add its own heat-and-wait lines before it. Check a sliced file: nothing
  before `MMU_START_SETUP` except the `M140` line.
- **Label objects** on. Klipper's `exclude_object` uses the labels, and the
  adaptive mesh only probes where the objects are.
- **Prime tower** off, flush into infill or objects off. Blobifier purges the
  full flushing volume.
- **Multi-material moves** off (ramming, cooling moves, load/unload times),
  because the toolhead cutter does the work. Follow
  [Happy Hare's slicer setup](https://moggieuk.github.io/Happy-Hare-Doc/Slicer-Setup/).
- **Filament profiles:** pressure advance enabled and set per filament. Orca
  emits `SET_PRESSURE_ADVANCE` on every filament change. Set a **chamber
  temperature** on filaments that need one (e.g. ABS/ASA), but leave "activate
  temperature control" off; otherwise Orca inserts its own `M191`, which this
  printer doesn't define. `START_PRINT` gets the highest chamber temperature of
  the print's filaments.
- **Filament names** must match the Spoolman filament names exactly. Happy Hare
  maps tools to gates by name.
- **Nozzles (Revo):** one printer preset per nozzle size. Separate filament
  profiles per nozzle where pressure advance or max volumetric speed differ.
- **Machine limits:** don't exceed the printer's (`max_velocity` 400,
  `max_accel` 7000).

## Exported profiles

The printer, process and filament profiles are exported into `slicer/` so the
slicer side is versioned with the config. (To do: export them from Orca.)
