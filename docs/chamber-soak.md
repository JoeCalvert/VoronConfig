# Chamber warm-up and soak

For a print with `CHAMBER` above zero, START_PRINT waits for the bed, parks the
moving chamber sensor at `chamber_soak_position_xyz`, and warms towards the
requested chamber temperature. The filter circulates air during this wait.

There are three ways to finish warm-up:

- The chamber reaches the target: start the timed soak normally.
- Warming has persistently flattened below target: warn, then soak at the
  achieved temperature.
- The maximum warm-up time expires: warn, then soak at the achieved temperature.

After the soak, preparation continues through probing, meshing and final nozzle
heating. Only after that finishes does the print file proceed to the first
Happy Hare tool load. Files with `CHAMBER=0` keep the direct preparation path.
No slicer changes are needed.

## Settings

All times are in minutes, in `config/variables.cfg`:

| Setting | Default | Meaning |
|---|---:|---|
| `print_default_chamber_max_heating_time` | 15 | Maximum warm-up time, excluding the soak |
| `print_default_chamber_soak` | 5 | Timed soak after target, plateau, or timeout |

The target comes from the slicer's `CHAMBER` parameter. The existing bed soak
(`print_default_soak`) is separate and still happens first.

For manual use, with axes homed and the bed heater already on:

```gcode
HEATSOAK_CHAMBER TEMP=50 SOAKTIME=5 MAXTIME=15
```

`SOAKTIME=0` skips the timed soak. `MAXTIME=0` immediately takes the warm-up
fallback. SOAKTIME and MAXTIME accept 0..120 minutes. Cancel with `CANCEL_PRINT`.

## Flattening detection

The timer samples every 30 seconds. It ignores the first minute to let the
moving sensor settle, then retains thirteen readings (six minutes). Three
averaged groups give two successive heating rates. Both must be near zero or
below one tenth of the fastest observed rate, with a 0.05 C/min noise floor.
Sustained cooling does not count as a plateau. This gives a minimum of about
seven minutes before a plateau can be declared; target detection and timeout
can finish sooner.

A brief flat patch or one noisy reading is insufficient. A steady positive
ramp above the noise floor keeps waiting until the target or timeout. These
are fixed, conservative checks, not a fitted model or a calibration procedure.
A plateau is an observation under current conditions, not proof of an absolute
maximum temperature.

## Cancellation and errors

The wait uses short delayed callbacks, not a long dwell holding Klipper's
command lock. The SD reader is held during preparation; this is not a user/MMU
pause and does not invoke Happy Hare's parking or retraction. Cancel invalidates
the callbacks, shuts down heaters and lets Happy Hare's normal base cancellation
close the file. Optional cancellation parking happens afterwards.

An explicit user pause freezes the wait clocks and clears the temperature trend
because the sensor may move. Resume returns control to the wait; it does not
skip warm-up or soaking. Heater-off or a changed/ended file aborts the wait.
A failed timer-driven preparation shuts heaters off and keeps the file held;
check the console error and cancel before retrying.

## Printer checks before use

- Warm-up/soak: cancel in each stage; verify the file stays stopped and heaters
  turn off, including after the original timer deadline passes.
- Reachable target: verify the full timed soak completes before probing starts.
- Unreachable target: verify a plateau/timeout warning, then soak and continuation.
- Warm restart: contact probing waits until the nozzle is within 148..152 C.
- A tall-print park with a positive Z offset stays below the Z limit; X moves
  before Y when leaving the tray. If clearance is insufficient, parking is
  skipped with a message while essential cleanup still completes.
