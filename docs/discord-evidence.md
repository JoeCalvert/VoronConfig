# Discord evidence: what was re-checked, and how it came out

The slicer and firmware notes cite "Discord" for several choices. On
3 November 2026 each claim was checked again, this time to a stricter
standard:

- Searches used one or two distinctive words or setting names (`smooth_time`,
  `adaptive PA`, `thick bridges`, `arachne`, `SAFC`, `overhang overlap`), since
  Discord's search falls apart with longer phrases.
- Each useful hit was opened in place. The surrounding conversation was read,
  reply chains were followed both ways, and threads were opened.
- Who said it (build serials, how often they help) and when (before or after
  relevant Klipper or slicer changes) was noted, along with whether it was a
  real recommendation, a guess or a joke.
- Where an official source exists, it beats Discord: the Klipper docs,
  PrusaSlicer's own Voron profile (`resources/profiles/Voron.ini`) and the
  Filamentalist build guide.

Links open in the Voron Discord (server 460117602945990666).

| Claim | Verdict | Evidence | Change |
|---|---|---|---|
| `pressure_advance_smooth_time` 0.015–0.02 | **Partly right.** 0.02 holds; 0.015 was a misreading | pajtaz (VT.331, V0.1762, VT.1157), 29 Sep 2026, in the thread *Wavey corners throughout different gantry builds*: shorter smoothing needs more extruder torque, slipping makes PA erratic, and *good extruders with adequate torque can do down to 0.02*; nobody was known to print below 0.02. [message](https://discord.com/channels/460117602945990666/1552014442336755903/1554494250538901516). The "0.015–0.02" in that thread were **PA values** being tested, not smoothing times. Reth (a regular helper) advises 0.02 in several threads (e.g. [Jul 2025](https://discord.com/channels/460117602945990666/1397353292492701708/1397454058603937936)), without reasons. Klipper docs: default 0.040, larger is smoother | Kept 0.02; comment and docs corrected; a commissioning check for extruder clicking at high flow |
| Inner and outer walls at the same speed and acceleration | **Supported** | MxBrnr (V0.2633), 27 Oct 2026: *Best results are usually had by using the same speeds/accels across the entire print*; with different ones *somewhere the PA will be wrong, unless you use Adaptive/non-linear PA*. [message](https://discord.com/channels/460117602945990666/461133450636951552/1564476597006762036). Nobody in the thread disagreed. PrusaSlicer has no adaptive PA | None |
| Overhang speeds 50/70/100 %/100 % ("the Orca port author") | **Not found.** Withdrawn | Searches for `overhang overlap`, `dynamic overhang`, `overhang speeds`, `overhang_speed_3` and the author's name found no such message. Confirmed only the direction: moab1, Oct 2024, *should be faster for more overlap/less overhang* ([message](https://discord.com/channels/460117602945990666/461133450636951552/1298711250913591317)). Most other advice says to slow overhangs | Now PrusaSlicer's Voron profile values: 15 / 25 / 30 / 80 %; overhang test added to commissioning |
| Thick bridges off ("hurt more than they help") | **Discord split**; the official profile agrees with "off" | For: CabbageCorp, Sep 2025, V0 help ([message](https://discord.com/channels/460117602945990666/696930677161197640/1419408586832089119)). Against: H4kunaMatata, Feb 2024, *Thick Bridges are the best imo*. Voron.ini: `thick_bridges = 0` in common, `1` for 0.8 mm | Off, on for 0.8 mm (as Voron.ini); reason in docs replaced |
| ABS minimum layer time 8–15 s ("3 too low") | **Not verified** | No message found. Voron.ini: ABS 5 s, PLA 12 s, others 15 s | Now Voron.ini's values (PLA 12, PETG 15, ABS/ASA 5); a small-part check added |
| Arachne outer-wall artefacts, so Classic for Quality/PIF | **Supported** | 🅱ort, 19 Oct 2026 (search `arachne`): Arachne is *recommended against by many here* (the speaker still prefers it for thin parts). Voron.ini uses Arachne generally and Classic for printed parts, the same split as ours | None |
| SAFC is a band-aid | **Rephrased** | The Discord comparison is with OrcaSlicer's adaptive PA: MxBrnr, Aug–Sep 2026, says adaptive PA handles small-area over-extrusion better and that the two don't mix. PrusaSlicer has neither adaptive PA nor built-in SAFC | Docs reworded; your post-processor stays, with its tester still on the list |
| Pressure equalizer is mixed | **Not found** | No usable hits (`equalizer` matches belt talk). PrusaSlicer marks it experimental | Left off; docs no longer quote Discord |
| Revo flow 10–12 standard, ≈23 HF 0.6 | **Roughly right, as starting caps** | Not Discord: a retailer quotes E3D's 13 mm³/s (standard 0.4, PLA); one buyer measured 17 standard / 31 HF at 0.6 | Values kept (deliberately low starting caps; the flow test sets each filament's real one); docs now say so |
| Filamentalist: screw just touching the top washer | **Wrong source for ERCF** | That came from an EMU build on the Armchair Discord. The Filamentalist's own build guide says: start light, then with a tight spool back off until loose filament collects on an unload, and tighten about half a turn | Retune dialog, retune.md and commissioning now use the build guide's method |
| Ellis's PA pattern is the community's preferred PA test | **Supported** | Many independent mentions (search `PA pattern`, 2024–2026), e.g. *PA pattern method is nice*, *PA Pattern wie in Ellis Guide*; helpers point to a pinned PA-check method in #slicers_and_print_help | None |

Also found while searching: DW (the A4T designer), Aug 2026, says some people
now run with no extruder sensors, using the PSF as the homing sensor, and that
he is testing a single sensor placed *after* the extruder gears. That's useful
for the A4T question.

## What this means for earlier claims

Today's motor advice (about 1.1–1.2 A on the A/B motors) was my own rule of
thumb, not a sourced figure. Treat it as a starting point for the motion
retune, checked against motor and driver temperature.
