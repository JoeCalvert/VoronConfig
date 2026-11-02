# PrusaSlicer setup

The PrusaSlicer presets are **generated**, not edited by hand:

```
slicer/profiles.py ─┐
slicer/base/*.ini ──┼─ tools/build_slicer_profiles.py ─► PrusaSlicer presets
config/machine.cfg ─┤                                    (printer, print, filament)
Spoolman filaments ─┘
```

- **Printers, prints:** `slicer/profiles.py`. One entry per nozzle and one per
  print "intent" (Quality, Standard, Draft, PIF…). Each setting lives in one
  place; the generator does the layering that PrusaSlicer can't do for user
  presets (they can only inherit from its built-in vendor profiles).
- **Filaments:** Spoolman is the master copy. One PrusaSlicer filament per
  Spoolman filament, named exactly as in Spoolman (Happy Hare maps tools to
  gates by that name). Temperatures, density, colour and price come from the
  filament itself; tuned values from its extra fields (below); anything not
  set falls back to `MATERIALS` in `slicer/profiles.py`.
- **Machine limits** (`max_accel`, `max_velocity`) come from
  `config/machine.cfg`, so retuning the printer and rebuilding keeps the slicer
  in step.

Don't edit the generated presets in PrusaSlicer: the next build overwrites
them. To try something, "Save as" a new name; the generator never touches
presets it didn't write. If it ever has to replace one of yours with the same
name, it keeps yours as `<name>.ini.bak`.

## The tuning loop

```
CAL_FILAMENT test print ─► pick the best pattern ─► Spoolman filament ─► rebuild ─► PrusaSlicer
```

PA, EM and max flow tests (RETUNE → PA and EM, or `CAL_FILAMENT`) save their
result to the gate's filament in Spoolman (`tools/spoolman_tuning.py`). Rebuild,
restart PrusaSlicer, and the filament preset has it.

## First-time setup

1. **Spoolman fields** (on the Pi, once):
   `python3 ~/printer_data/config/tools/spoolman_tuning.py setup`
2. **Bring over your existing values** from the old hand-made presets. Export
   a config bundle from PrusaSlicer (File → Export → Export Config Bundle),
   then:
   ```
   python3 tools/spoolman_tuning.py --url http://voron.local:7912 import-bundle PrusaSlicer_config_bundle.ini
   ```
   It lists each PrusaSlicer filament, the Spoolman filament it matches (by
   name, with or without the vendor), and the values it would copy: PA per
   nozzle, EM, max flow, fan, retraction, chamber. Fix any "NO MATCH" by
   renaming in Spoolman, then run again with `--apply`.
3. **Filament names:** each Spoolman filament needs a unique name; the build
   reports duplicates.
4. **Build into PrusaSlicer** (on the computer running PrusaSlicer, with
   PrusaSlicer closed; Help → Show Configuration Folder shows the folder):
   ```
   python3 tools/build_slicer_profiles.py --spoolman http://voron.local:7912 \
       --prusaslicer "<configuration folder>" --physical-printer Voron
   ```
   `--physical-printer Voron` adds the new printers to your "Voron" physical
   printer, so "Send to printer" works with them.
5. In PrusaSlicer, pick the printer for the fitted nozzle, e.g. **Voron 2.4 -
   Revo HF 0.60**. Delete the old `V2.4 - Revo …` printers and `Voron (… Nozzle)`
   prints once you're happy.

Rebuild whenever you change `slicer/profiles.py`, add or edit a filament in
Spoolman, or finish a test. Nothing on the printer needs restarting.

## What the presets contain

**Printers** (`Voron 2.4 - <nozzle>`): one per nozzle in `NOZZLES`, 8 tools
(one per ERCF gate), plus a single-tool **(bypass)** twin for printing through
the bypass (MENU → Bypass). The start G-code passes the nozzle size and type to
`START_PRINT`, which refuses a file sliced for a different nozzle.

**Prints** (`0.20mm Standard @0.40`, `0.30mm Standard @0.60 HF`…): shown for
the printers they suit. Brass and ObXidian 0.40 share prints; HF has its own
because its flow limit is twice brass's.

**Filaments:** pressure advance is in each filament's start G-code, one value
per nozzle, chosen by the printer preset (`printer_notes` carries
`NOZZLE=0.60_hf;`). Every nozzle gets a value, so a tool change never keeps the
previous filament's PA.

### Custom G-code (generated; for reference)

Start:
```
M140 S{first_layer_bed_temperature[initial_tool]}
MMU_START_SETUP INITIAL_TOOL={initial_tool} REFERENCED_TOOLS=!referenced_tools! TOOL_COLORS=!colors! TOOL_TEMPS=!temperatures! TOOL_MATERIALS=!materials! FILAMENT_NAMES=!filament_names! PURGE_VOLUMES=!purge_volumes!
MMU_START_CHECK
PREFLIGHT_CHECK
START_PRINT BED=… EXTRUDER=… NOZZLE={nozzle_diameter[0]} NOZZLE_TYPE=hf CHAMBER=<highest chamber temperature of the filaments used>
MMU_START_LOAD_INITIAL_TOOL
POST_START_PRINT
SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]
```
End: `MMU_END`, `END_PRINT`. Tool change: `T[next_extruder]`. After layer
change: `SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}` and
`MMU_UPDATE_HEIGHT`. Pause and colour change: `PAUSE_FOR_USER` (there is no
`M600` on this printer).

- `M140` first, so the bed heats while Happy Hare checks the gates. The `!…!`
  values are filled in by Happy Hare's preprocessor in Moonraker on upload.
- Temperature commands are not emitted (`START_PRINT` heats); there is no
  chamber heater, so no `M141`/`M191`.
- Labels: firmware (`EXCLUDE_OBJECT`, and the adaptive mesh). Wipe tower off:
  Blobifier purges. PrusaSlicer's tip forming and ramming are all zero: Happy
  Hare's cutter shapes the tip.

## Why the settings are what they are

- **Speeds are generous; flow does the limiting.** On a Revo, the hotend runs
  out of melt long before the motion system runs out of speed, so the print
  presets ask for high speeds and PrusaSlicer slows every move to the flow
  limit: the smaller of the nozzle's (`max_flow` in `NOZZLES`: 12 mm³/s brass,
  24 HF, from E3D's figures and the Voron Discord) and the filament's.
- **The outer wall is the exception:** 150 mm/s (100 in Quality) at 45 % of
  `max_accel`, because it's what you see. Top surfaces likewise.
- **Accelerations** are fractions of `max_accel`: walls 45 %, inner walls
  70 %, infill and travel 100 %. Re-tune the input shaper, update `max_accel`,
  rebuild, and every preset follows.
- **Overhangs** slow down with less support: bridging 15 mm/s, 25 % overlap
  25 mm/s, then 40 % and 80 % of the outer-wall speed. (The old presets had
  these reversed: steep overhangs fast, gentle ones at 10 mm/s.)
- **Line widths** are multiples of the nozzle: 1.125× for walls and solid
  infill, 1.25× first layer and sparse infill, 1.0× top surface.
- **Shells** by thickness as well as count (top at least 0.7 mm, bottom
  0.5 mm), so thin layers still get solid skins.
- **Seams** aligned, with scarf joints on smooth walls.
- **Supports** off by default (enable per print); arc fitting off; travel
  capped at `max_velocity`.

## What gets tuned, and how

| Value | Lives in | How to tune it | When |
|---|---|---|---|
| Pressure advance | Spoolman `pa_<nozzle>` | `CAL_FILAMENT TEST=pa`: Ellis's pattern, wide then fine | Each filament, on each nozzle you use it with |
| Extrusion multiplier | Spoolman `extrusion_multiplier` | `CAL_FILAMENT TEST=em`: Ellis's squares, coarse then fine | Each filament (after its PA) |
| Max flow | Spoolman `max_flow`; nozzle limit in `NOZZLES` | `CAL_FILAMENT TEST=flow`: single wall in rising-flow bands; the last clean band, less 10 % | Each filament, on the HF nozzle. Nozzle limit: run it with your fastest filament |
| Nozzle temperature | Spoolman filament (extruder temp) | Start at the maker's range. If the flow test is short of what you need, +10 °C and test again | New filament |
| Bed temperature | Spoolman filament (bed temp) | Maker's value; raise if corners lift | New filament |
| Chamber temperature | Spoolman `chamber_temp`, else `preheat_materials` | ABS/ASA 50 °C. Raise if large parts warp or layers split | Per material |
| Part fan | Spoolman `fan_min` / `fan_max`, else `MATERIALS` | Overhang/bridge test; less fan if layers split, more if overhangs droop | Per material |
| Retraction | `NOZZLES` `retract`; Spoolman `retract_length` overrides | Ellis's retraction test (stringing towers). Direct drive: 0.4–1.0 mm | After PA, if stringing |
| First layer | `variable_hot_nozzle_offset` (`config/hardware/probe.cfg`) | RETUNE → First layer | After a nozzle or bed change |
| Elephant foot | `elefant_foot_compensation` in `PRINT` | Measure the base of a test part against its middle; set the difference | Once |
| Outer wall speed / acceleration | `PRINT` / `ACCEL` | Raise until ringing shows on a test part, then step back | After input shaping |
| Max acceleration | `config/machine.cfg` | RETUNE → Input shaper (the lower recommended value) | After belts or toolhead changes |
| Purge volume | PrusaSlicer purging volumes, `filament_purge_multiplier` | Print a dark → light change; raise until no streaks | Per colour pair, if streaky |
| Seam | `seam_*`, `scarf_seam_*` in `PRINT` | Print a cylinder; adjust `seam_gap_distance` if there's a gap or bump | Once |

Your old presets' PA, EM, flow, fan and retraction values come across with
`import-bundle` (setup step 2), so nothing has to be re-tuned before the first
build. Two to look at afterwards:

- **eono PETG retraction 3 mm.** That's a Bowden-length value. On the Galileo
  2 it pulls molten plastic into the heatbreak; retune it (0.4–1.0 mm).
- **3DXTech CarbonX ASA EM 0.865** and other values far from their material's
  usual range may be right, but are worth a check with the EM test.
