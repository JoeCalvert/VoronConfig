# Updating Happy Hare, KlipperScreen, Fluidd and the rest

Our macros only use other projects through their public surface:

- **G-code commands** they document (`MMU_RECOVER`, `BLOBIFIER_CLEAN`, `BEACON_HOME_Z_CONTACT`…)
- **status fields** (`printer.mmu.*`)
- **hook and setting variables** in Happy Hare's `mmu_macro_vars.cfg` (`user_*_extension`, `park_*`…)

We never copy or override another project's macros, and never call their
`_underscore` internals. Those change between releases. For example, Happy
Hare's development branch (Oct 2026) removes `_MMU_ERROR_DIALOG` and the
`error_dialog_macro` setting, so anything that overrode them breaks.

Everything we use is listed in `macros/system/dependencies.cfg`.

The dialogs use the `action:prompt` messages that Fluidd, KlipperScreen and
Mainsail all render. KlipperScreen only has two plain menu entries
(`KlipperScreen.conf`), so its updates can't break them.

## After updating Happy Hare

1. **Before restarting Klipper**, on the Pi:

   ```sh
   cd ~/printer_data/config
   python3 tools/check_deps.py --happy-hare ~/Happy-Hare
   ```

   This checks every command, status field and variable we use against the
   new Happy Hare source. `PROBLEM:` lines name what has gone.

2. Restart Klipper. `CHECK_CONFIG` runs 5 s later and checks the same list
   against the running printer. It also checks that the hooks still call our
   macros, because the installer rewrites `mmu_macro_vars.cfg`.

3. If both are clean, set `happy_hare_tested` in
   `macros/system/dependencies.cfg` to the new major.minor version. That
   silences the "last checked against" warning.

If something is reported:

- **A command or field was renamed:** check Happy Hare's release notes, then
  update the macro that uses it and the list.
- **A hook variable has gone:** the installer will also have dropped our
  value. Find the new hook name in `mmu/base/mmu_macro_vars.cfg` and set it
  again.
- **A hook no longer calls our macro:** the installer reset it. Put our macro
  name back. The value is in `macros/system/dependencies.cfg`.

## When writing a new macro

- Use only public commands and fields. `tools/check_deps.py` fails if a macro
  calls another project's `_internal` macro.
- Add anything new it uses to `_DEPENDENCIES`. `tools/check_deps.py` (no
  arguments) fails until you do.
- Build dialogs with the `_DIALOG*` helpers in `macros/ui/dialog.cfg`. Their
  header lists what can't go in dialog text.
- Add a simulator scenario (`tools/macro_sim/scenarios.py`).
