# Macro simulator

Renders our Klipper macros with Jinja and expands every call to another of our
macros, down to the G-code that would reach Klipper. Use it to check that a
macro change does what you expect before it goes on the printer.

It follows `printer.cfg`'s includes like Klipper does, applies
`SET_GCODE_VARIABLE` as it goes, and treats anything that isn't one of our
macros (Klipper commands, Happy Hare and Blobifier macros) as a primitive. The
printer state it renders against is in `state.py`.

```
pip install jinja2

# Before a change: save the expanded output of every scenario
python3 tools/macro_sim/scenarios.py . --save /tmp/before.json

# After the change: compare
python3 tools/macro_sim/scenarios.py . --compare /tmp/before.json
```

A refactor should print `identical`. For a behaviour change, check that the
listed differences are exactly the ones you intended. Errors raised by a macro
(`action_raise_error`) show up as `ERROR` lines and a non-zero exit code.

Add a scenario to `SCENARIOS` in `scenarios.py` when you add a macro:
`(name, state overrides, [commands to run])`.

Limits: it doesn't move a toolhead or change temperatures, so macros that loop
on live readings (like the chamber wait) see the values in `state.py`. Happy Hare
macros aren't expanded, because in this repo they're symlinks into the Happy
Hare install.
