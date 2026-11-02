# Notifications

The macros send a notification for the moments that need you at the machine:

| When | Sent by |
|---|---|
| MMU error during a print (the recovery dialog is waiting) | `_MMU_RECOVERY NOTIFY=1` |
| A print stopped with an error | `_JOB_FAILED` |
| A print is waiting at the preflight check | `PREFLIGHT_CHECK` |
| A planned pause (slicer pause or "Pause at the next layer") | `PAUSE_FOR_USER` |
| Print finished and the bed has cooled: safe to take the part off | `_PART_READY_CHECK` |

They go through Moonraker's notifier, which uses
[Apprise](https://github.com/caronc/apprise/wiki), so almost any service
works (ntfy, Pushover, Telegram, Discord, Home Assistant, email…).

## Set up

1. Put the Apprise URL for your service in `~/printer_data/moonraker.secrets`,
   which stays out of this repository:

   ```ini
   [notify]
   url: ntfys://ntfy.sh/your-private-topic
   ```

2. Add to `moonraker.conf`:

   ```ini
   # Our macros' messages (_NOTIFY)
   [notifier phone]
   url: {secrets.notify.url}
   events: gcode
   body: {event_message}

   # Moonraker's own "print complete" (the part-ready message follows once the bed cools)
   [notifier phone_complete]
   url: {secrets.notify.url}
   events: complete
   body: Print complete: {event_args[1].filename}
   ```

   Don't add Moonraker's `paused` or `error` events: the macros already send
   more useful messages for those.

3. In `config/variables.cfg`, set `variable_notifier_name: "phone"` (the name
   after `[notifier`), then restart Moonraker and Klipper.

4. Test from the console: `_NOTIFY MSG="Test"`.

While `notifier_name` is empty, `_NOTIFY` only writes to the console. The
macros never call Moonraker's notifier unless it's configured, because that
call fails, and stops the calling macro, if no notifier exists.
