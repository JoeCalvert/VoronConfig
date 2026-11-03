# Commissioning checklist

Everything to do and verify after the modernisation PRs, in the order to do it.
It replaces working through the per-PR checks in `docs/config-changes.md`
one by one: those are merged here, de-duplicated, with the ones later PRs
made unnecessary listed at the end. Tags in brackets are the original check
IDs, as `#PR/ID`.

## 1. Get the printer running on the new config

- [ ] On the Pi: `python3 ~/VoronConfig/tools/deploy.py --dry-run`, read the plan (especially files it removes), then run it for real. If Klipper is still halted afterwards, `FIRMWARE_RESTART` [#28/D2, D3]
- [ ] Klipper starts, no config errors [#36/K1, #8/D1, #15/T2, #16/Y1, #17/V1, #29/T7]
- [ ] `CHECK_CONFIG` runs clean and shows the Happy Hare version [#38/K2, #7/K1, #21/U4, #27/M9]
- [ ] `printer.cfg` still ends with the `#*# [beacon model default]` block, now with PID and input shaper sections above it; `SET_INPUT_SHAPER` reports mzv 47.6 / ei 43.6 [#31/R1]
- [ ] Record the fitted nozzle: MENU → Change the nozzle → "I've already swapped it" → pick it (or `NOZZLE_SET DIAMETER=0.6 TYPE=hf`). Until then the printer assumes brass and refuses HF files [#34/S1, #5/S4]
- [ ] Console after restart: no `SET_LED` errors [#11/E4]
- [ ] Electronics fan runs when motors or a heater are on, stops ~30 s after both are off [#9/F1]

One-off housekeeping on the Pi:
- [ ] klipper-backup: `github_repository` in `~/klipper-backup/.env` is not VoronConfig [#28/D1]
- [ ] Nothing still runs `autocommit.sh` (crontab, systemd timers, Moonraker) [#6/A1]
- [ ] `python3 ~/VoronConfig/tools/check_deps.py --happy-hare ~/Happy-Hare` prints OK [#21/U5]
- [ ] (Optional) disable the `klipper-mcu` service; nothing uses it now [#29/T7]
- [ ] GitHub → Actions: `check` passes on main [#28/D4]

## 2. Hardware before tuning

- [ ] Fix the cowl screw that pulled through (washer or reprinted part)
- [ ] Read the label on the A/B motors: if it says `17HS19-2004S-AB` (Fysetc's 2.4 kit motor), change `motor:` for `stepper_x`/`stepper_y` in `config/software/motors_autotune.cfg` from `fysetc-17HS19-2004S-C` (their Trident motor) to `fysetc-17HS19-2004S-AB`
- [ ] Measure the toolhead clearance (radius around the nozzle; nozzle tip to the gantry) and set `extruder_clearance_*` in `slicer/profiles.py`; only needed before using the Stencil intent [#35/V4]

## 3. Homing, levelling, positions

- [ ] Cold, after a restart: home-all homes Z without touching the bed [#4/H1]
- [ ] Hot (nozzle > 160 °C), after a restart: `MMU_LOAD` homes by itself first, no contact error [#4/H2]
- [ ] X/Y sensorless homing behaves as before [#9/F2]
- [ ] Cutter: after `G28`, a dry cut approaches the pin along Y 346 and backs out to X 90 [#2/C1]
- [ ] Blobifier: `BLOBIFIER_PARK` puts the nozzle just clear over the tray [#2/B2]; `BLOBIFIER_CLEAN` wipes across the real brush and dips into the bristles without hitting the base [#2/B1, B3]
- [ ] Parking: `BLOBIFIER_PARK` then `MMU_PAUSE` moves sideways along the back to 175,355 [#2/P1]; `RESUME` wipes then returns [#2/P2]; `CANCEL_PRINT` from the tray lifts Z, X to 175, then Y to 100 [#2/P3]

## 4. Retune (MENU → Calibrate → Retune, top to bottom; guide: docs/retune.md)

Motion and heaters:
- [ ] Mechanical check
- [ ] Belts with the tension meter, then Shake&Tune belt comparison ≥ 90 % similar
- [ ] Mesh and QGL edges: full mesh has no drop/jump at any edge; Beacon fully on the plate at all four QGL points [#29/T1, T2]
- [ ] (Optional, with the motion retune) A/B `run_current` 0.9 → about 1.1 A, then check motor and driver temperatures after a long hot-chamber print. This is my rule of thumb, not a sourced figure; it adds torque at speed
- [ ] Input shaper with the bed hot: axes map, graphs (one clean peak per axis), measure and apply → Save. Set `max_accel` and the damping ratios from the results [#9/F4, #27/M8, #30/E2]
- [ ] Update Klipper first if it's older than 18 Oct 2026: before that, `PID_CALIBRATE` suggested values about twice too high (Klipper Config_Changes). Then: PID nozzle and bed → Save; Klipper restarts with the values in SAVE_CONFIG. Deploy again later: they're kept [#31/R3, #9/F4, #10/L1]

ERCF:
- [ ] Selector and servo: re-seat the servo arm at DOWN as the v4 ERCF guide describes, set up/down/move angles and save [#3/S1]; calibrate the selector (motors off, gate 0, Calibrate); calibrate the bypass position
- [ ] Gear, encoder, bowden on gate 0 [#3/K1]
- [ ] Filamentalist tension, the build guide's way: tight spool, back off until loose filament collects on an unload, then half a turn tighter; out-and-back test on each gate [#41/D3, #32/P7]
- [ ] Per-gate calibration; gates more than 2 % off gate 0 investigated [#3/K1]
- [ ] Toolhead distances: Clean, Dirty, Cut [#3/T1]
- [ ] A real cut leaves a clean tip and reloads without jamming [#2/C2]
- [ ] Soak test, all 8 gates. No slips with the 20 mm delta [#3/L1]; no selector drag on parked filament with `gate_parking_distance` -23 (else back to -12) [#3/G1]
- [ ] Toolchanges, purges and loads run without "Extrude only move too long" / "Move exceeds maximum extrusion" [#30/E3]

- [ ] First layer: even across the bed, height right; adjust `hot_nozzle_offset` if not [#5/S6, #10/L2]

## 5. Spoolman, NFC and the PrusaSlicer presets (docs/slicer.md → First-time setup)

- [ ] `python3 ~/printer_data/config/tools/spoolman_tuning.py setup`; Spoolman shows the new filament fields [#34/S2]
- [ ] Export a PrusaSlicer config bundle; `spoolman_tuning.py --url http://voron.local:7912 import-bundle <bundle>`; fix any NO MATCH names in Spoolman, then `--apply` [#34/S3]
- [ ] Every Spoolman filament has a unique name
- [ ] Bind each spool's NFC tag: spool in the gate, then `MMU_SPOOLMAN_TAG REGISTER=1 SPOOLID=<id> GATE=<gate>`
- [ ] `MMU_ENDLESS_SPOOL` shows enabled with same-filament gates grouped (else `MMU_ENDLESS_SPOOL ENABLE=1` once) [#29/T5]
- [ ] Build into PrusaSlicer with PrusaSlicer closed: `build_slicer_profiles.py --spoolman http://voron.local:7912 --prusaslicer "<config folder>" --physical-printer Voron`; printers, prints and filaments appear under User presets; Send to printer works [#34/S4]
- [ ] Quality/PIF prints show "Classic" walls; a carbon-fibre filament only appears with the ObXidian printer [#35/V2]
- [ ] Slice a two-filament part on the fitted nozzle's printer and look in the file: nothing before `MMU_START_SETUP` but `M140`, no `M141`/`M191`; `NOZZLE_TYPE=` right; `CHAMBER=` your target for ABS/ASA, 0 for PLA (if PrusaSlicer reports an error in the chamber expression, tell me); a `SET_PRESSURE_ADVANCE` after each tool change [#34/S5, #5/S2, S3]
- [ ] Remove the old `V2.4 - Revo …` printers and `Voron (… Nozzle)` prints once happy

## 6. Filament tuning (RETUNE → PA and EM)

- [ ] PA for your main filament on the fitted nozzle, Wide then Fine (smoothing is now 0.02, so old PA values are stale): prints 21 numbered chevrons; the pick dialog appears at the end; the pick is applied and saved to Spoolman [#35/V1, #32/P2, P3, #33/Q1]
- [ ] Cancel one test partway: PA and max_accel go back to before [#32/P4]
- [ ] EM test: squares go from gappy to rough; pick, then fine [#32/P5]
- [ ] Max flow test on the HF nozzle: wall turns rough partway up; pick the band; saved to Spoolman [#34/S8]
- [ ] During the HF max-flow test, listen at the extruder: clicking or skipping before the wall turns rough means smoothing 0.02 is too short for it; set `pressure_advance_smooth_time: 0.03`, redo PA [#41/D1]
- [ ] Rebuild the presets; the filament preset has the new values
- [ ] Repeat PA (and EM) for your other common filaments and nozzles over time
- [ ] (Later) Small Area Flow Compensation tester; turn SAFC off if PA leaves no small-area blobs
- [ ] Overhang test (any overhang test model with 30–70° steps), Standard preset: if the 30–50 % overlap steps look fine, try raising `overhang_speed_1`/`_2` in `slicer/profiles.py` towards the walls' speed; slower if they droop [#41/D2]
- [ ] Small-part layer time: a 15 mm cube in ABS and in PLA. If the top deforms or curls, raise that material's `slowdown_below_layer_time` (now Voron's 5 s ABS, 12 s PLA) [#41/D2]
- [ ] Look at eono PETG's 3 mm retraction (too long for direct drive) and CarbonX ASA's EM 0.865

## 7. First real prints: watch these happen

Print start and end:
- [ ] Start: homing, bed soak only from cold (10 min) [#29/T4], QGL, contact Z, mesh over the objects only, heat over the tray, first tool load purges there [#5/S5]
- [ ] Right after a MENU → Preheat: the bed soak is skipped [#24/P4]; Preheat itself: bed heats, nozzle 150, filter on for ABS/ASA, heaters stay on past 15 min, Heaters off works [#24/P3]
- [ ] ABS/ASA print: chamber soak at the centre 80 mm up, filter running, until target, sustained flattening, or the warm-up time limit, then a full timed chamber soak (see [chamber-soak.md](chamber-soak.md)) [#29/T3, #19/H4]
- [ ] Preflight: a tool mapped to a gate holding different filament shows "Check the filament" and waits [#24/P5]; a matching print starts without it [#24/P6]; tools map to gates by name [#3/M1]
- [ ] LEDs static during homing and start; logo follows the loaded filament colour and changes on tool change [#11/E1, E2]
- [ ] Completed print: lights, filter run-on (10 min after a chamber print), LEDs to part-ready once the bed is below 40 °C [#18/M1, #26/N3]
- [ ] Spoolman's active spool changes on a tool change [#8/D2]
- [ ] No false clog pauses over a few prints (else `flowguard_encoder_mode: 1`) [#29/T6]
- [ ] Print quality: a part with overhangs and a cylinder at Standard; compare speed and quality with the old preset [#35/V3, #34/S6]

When stopping or failing:

- [ ] Run the warm-up, soak, cancellation, warm-restart and parking checks in [chamber-soak.md](chamber-soak.md)
- [ ] Cancel with filament loaded: park, lights/LEDs/filter off, "Unload the filament?" offered [#18/M2, #23/J1]
- [ ] Make a print fail (a file sliced for the wrong nozzle): heaters off, then the "Print stopped" dialog with the reason; Reprint works; MENU shows "Why did the last print stop?"; LEDs show the error; "Turn the heaters off" works [#30/E1, #23/J2, J3, J4]
- [ ] An MMU error: the "MMU paused" dialog replaces Happy Hare's, reason and position right; error LEDs, print colours back after resume [#22/R1, #11/E3]
- [ ] In that dialog when it happens: reload + Preload + Load then Resume [#22/R2]; Resume refused with the wrong tool [R3]; Keep hot after 10 min [R4]; Cancel asks first [R5]; Service position only lifts Z and Resume carries on [R6]; Use another gate [R8]

Workflows:
- [ ] MENU from KlipperScreen and Fluidd; summary shows nozzle, chamber, loaded tool; buttons work [#21/U1, U2, U3]
- [ ] Planned pause from a PrusaSlicer pause; MENU → Pause at the next layer [#26/N1, N2]
- [ ] MMU check-up lists gates; "Check every gate" works [#22/R7]
- [ ] Nozzle change: unloads, heater off, front; records the nozzle [#25/W1]
- [ ] Spool swap: unload, eject, scan + preload shows the new spool; "Try again" if not pushed in [#25/W2, W3]
- [ ] Bypass: select, load, print with a "(bypass)" printer, unload [#34/S7]
- [ ] Maintenance: set your intervals in `maintenance_items`; hours added after a print; Done resets [#27/M5, M6]
- [ ] Adaptive mesh still runs two Beacon passes, similar time [#13/P4]

## 8. Optional

- [ ] Firmware updates with UKAM: install, first run with `-m` checking each board's menuconfig (SB2040 especially), all boards and Beacon on the new version, Octopus flash via Katapult [#12/U1-U4]
- [ ] Notifications: set up a notifier; test message, MMU error and part-ready reach your phone [#26/N4]
- [ ] Defaults audit on the Pi matches `docs/defaults-audit.md` [#9/F3]
- [ ] Break-the-config test: `park_pause` to `50, 50, 5, 0, 2`, restart, `CHECK_CONFIG` reports it and `START_PRINT` refuses; put it back [#7/K2]
- [ ] `POST_START_PRINT` alone refuses; `_JOB` prints phase and state [#18/M3, M4]
- [ ] Mainsail macro descriptions; no "without a description" warning for our macros [#19/H5]

## No longer needed (done by later changes)

- Pasting start/end/layer/pause G-code into PrusaSlicer, adding `PREFLIGHT_CHECK`, per-filament PA lines, and fixing `M600` [#5/S1, S7, #24/P1, #8/D3, #26/N1 setup]: the generated presets contain them
- Copying PID values into `extruder.cfg` [#27/M7]: the result dialog's Save puts them in SAVE_CONFIG
- Setting the `calib_*` values to the slicer's walls [#32/P1]: done in PR #35, and the build warns if they drift
- "RETUNE shows nine steps", "four groups" [#31/R2, #32/P6]: it's now a 14-tune menu; just check ticks survive a restart
- ERCF step buttons [#31/R4]: covered by doing the ERCF tunes in section 4
