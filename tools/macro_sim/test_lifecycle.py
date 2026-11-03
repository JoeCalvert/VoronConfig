"""Behaviour checks for chamber waits, timers, cancellation and safe parking.

python3 tools/macro_sim/test_lifecycle.py --klipper /tmp/klipper
No commands are sent to a printer. Native checks use a local Klipper checkout.
"""
import argparse
import math
import os
import re
import sys
import unittest
from macrosim import D
from runtime import Runtime
from state import make_state

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def printer():
    return Runtime(ROOT, make_state(
        heater_bed=D(temperature=100, target=100),
        extruder=D(temperature=240, target=240),
        print_stats=D(state='printing', filename='part.gcode', print_duration=0, message=''),
        virtual_sdcard=D(is_active=True, file_path='/gcodes/part.gcode')))


def start(rt, **params):
    options = dict(TEMP=50, SOAKTIME=1, MAXTIME=15)
    options.update(params)
    rt.run('HEATSOAK_CHAMBER ' + ' '.join('%s=%s' % x for x in options.items()))


def phase(rt):
    return rt.macros['_CHAMBER_WAIT']['vars']['phase']


def cancel(rt):
    # Happy Hare invokes our extension immediately before Klipper's base cancel.
    rt.run('_CANCEL_PRINT_EXTENSION')
    rt.run('BASE_CANCEL_PRINT')


class Lifecycle(unittest.TestCase):
    def test_target_then_full_soak_before_resuming(self):
        rt = printer(); start(rt)
        rt.advance(1, lambda t: 50)
        self.assertEqual(phase(rt), 'soaking')
        self.assertFalse(rt.state['virtual_sdcard']['is_active'])
        rt.advance(59)
        self.assertEqual(phase(rt), 'soaking')
        rt.advance(2)
        self.assertEqual(phase(rt), 'idle')
        self.assertTrue(rt.state['virtual_sdcard']['is_active'])
        self.assertNotIn('WARNING:', '\n'.join(rt.primitives()))

    def test_sustained_flat_temperature_warns_and_soaks(self):
        rt = printer(); start(rt)
        rt.advance(400, lambda t: 35)
        self.assertEqual(phase(rt), 'warming')
        rt.advance(30, lambda t: 35)
        self.assertEqual(phase(rt), 'soaking')
        self.assertIn('warming has flattened', '\n'.join(rt.primitives()))
        rt.advance(61)
        self.assertTrue(rt.state['virtual_sdcard']['is_active'])

    def test_relative_slowdown_is_detected(self):
        rt = printer(); start(rt)
        rt.advance(850, lambda t: 25 + 12 * (1 - math.exp(-t / 100)))
        self.assertEqual(phase(rt), 'idle')
        self.assertIn('warming has flattened', '\n'.join(rt.primitives()))

    def test_steady_slow_rise_waits_until_timeout(self):
        rt = printer(); start(rt)
        rt.advance(899, lambda t: 25 + .2 * t / 60)
        self.assertEqual(phase(rt), 'warming')
        rt.advance(2, lambda t: 25 + .2 * t / 60)
        self.assertEqual(phase(rt), 'soaking')
        self.assertIn('maximum warm-up time reached', '\n'.join(rt.primitives()))
        rt.advance(61)
        self.assertEqual(phase(rt), 'idle')

    def test_noise_does_not_prevent_flattening_detection(self):
        rt = printer(); start(rt)
        rt.advance(600, lambda t: 35 + .08 * math.sin(t / 17))
        self.assertEqual(phase(rt), 'idle')
        self.assertIn('warming has flattened', '\n'.join(rt.primitives()))

    def test_brief_stall_is_not_a_plateau(self):
        rt = printer(); start(rt, TEMP=80)
        def temperature(t):
            return 25 + min(t, 240) / 60 + max(0, t - 330) / 60
        rt.advance(700, temperature)
        self.assertEqual(phase(rt), 'warming')
        self.assertNotIn('warming has flattened', '\n'.join(rt.primitives()))

    def test_zero_warmup_and_soak_are_bounded(self):
        rt = printer(); start(rt, MAXTIME=0, SOAKTIME=0)
        rt.advance(1)
        self.assertEqual(phase(rt), 'idle')
        self.assertTrue(rt.state['virtual_sdcard']['is_active'])

    def test_cancel_during_warming_or_soaking_never_resumes_later(self):
        for soaking in (False, True):
            with self.subTest(soaking=soaking):
                rt = printer(); start(rt)
                rt.advance(1, lambda t: 50 if soaking else 25)
                cancel(rt)
                index = len(rt.primitives())
                rt.advance(2000)
                self.assertEqual(phase(rt), 'idle')
                self.assertEqual(rt.state['print_stats']['state'], 'cancelled')
                self.assertIsNone(rt.state['virtual_sdcard']['file_path'])
                self.assertNotIn('M24', rt.primitives()[index:])
                self.assertEqual(rt.state['heater_bed']['target'], 0)
                self.assertEqual(rt.state['extruder']['target'], 0)

    def test_user_pause_freezes_soak_and_does_not_auto_resume(self):
        rt = printer(); start(rt)
        rt.advance(1, lambda t: 50)
        rt.state['pause_resume']['is_paused'] = True
        rt.advance(300)
        self.assertEqual(phase(rt), 'soaking')
        self.assertFalse(rt.state['virtual_sdcard']['is_active'])
        rt.state['pause_resume']['is_paused'] = False
        rt.advance(61)
        self.assertEqual(phase(rt), 'idle')

    def test_new_filename_invalidates_old_wait(self):
        rt = printer(); start(rt)
        rt.state['print_stats']['filename'] = 'other.gcode'
        rt.advance(1)
        self.assertEqual(phase(rt), 'idle')
        self.assertNotIn('M24', rt.primitives())

    def test_filename_roundtrips_quotes_and_comment_characters(self):
        rt = printer()
        filename = 'test "quoted" \' #; Ω.gcode'
        rt.state['print_stats']['filename'] = filename
        start(rt)
        self.assertEqual(rt.macros['_CHAMBER_WAIT']['vars']['filename'], filename)

    def test_print_start_only_releases_file_after_preparation(self):
        rt = printer()
        rt.run('SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True')
        rt.run('START_PRINT BED=100 EXTRUDER=240 CHAMBER=50 NOZZLE=0.6')
        self.assertEqual(rt.macros['_JOB']['vars']['phase'], 'preparing')
        self.assertFalse(rt.state['virtual_sdcard']['is_active'])
        self.assertFalse(any(l.startswith('QUAD_GANTRY_LEVEL') for l in rt.primitives()))
        rt.advance(400, lambda t: 50)
        self.assertEqual(rt.macros['_JOB']['vars']['phase'], 'prepared')
        self.assertLess(rt.primitives().index('BED_MESH_CALIBRATE ADAPTIVE=1'), rt.primitives().index('M24'))
        self.assertIn('TEMPERATURE_WAIT SENSOR=extruder MINIMUM=148 MAXIMUM=152', rt.primitives())
        self.assertIn('TEMPERATURE_WAIT SENSOR=extruder MINIMUM=240.0 MAXIMUM=242.0', rt.primitives())
        self.assertEqual(rt.errors, [])

    def test_continuation_error_shuts_down_without_releasing_file(self):
        rt = printer()
        rt.run('SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True')
        rt.run('START_PRINT BED=100 EXTRUDER=240 CHAMBER=50 NOZZLE=0.6')
        rt.fail_on.add('QUAD_GANTRY_LEVEL')
        rt.advance(400, lambda t: 50)
        self.assertEqual(rt.macros['_JOB']['vars']['phase'], 'failed')
        self.assertEqual(rt.state['heater_bed']['target'], 0)
        self.assertEqual(rt.state['extruder']['target'], 0)
        self.assertFalse(rt.state['virtual_sdcard']['is_active'])
        self.assertNotIn('M24', rt.primitives())
        cancel(rt)
        self.assertEqual(rt.state['print_stats']['state'], 'cancelled')

    def test_filter_restart_and_stop_invalidate_pending_shutdown(self):
        for command in ('START_FILTER', 'STOP_FILTER'):
            rt = printer()
            rt.run('UPDATE_DELAYED_GCODE ID=_STOP_FILTER_DELAYED DURATION=600')
            rt.run(command)
            self.assertNotIn('_STOP_FILTER_DELAYED', rt.timers)

    def test_stale_callback_after_cancel_is_harmless(self):
        rt = printer(); start(rt)
        cancel(rt)
        index = len(rt.primitives())
        rt.run('_CHAMBER_TICK')
        rt.run('_CHAMBER_FINISH')
        self.assertEqual(rt.primitives()[index:], [])

    def test_second_start_cannot_replace_an_active_wait(self):
        rt = printer(); start(rt)
        with self.assertRaises(RuntimeError):
            rt.run('START_PRINT BED=100 EXTRUDER=240 CHAMBER=50')
        self.assertEqual(phase(rt), 'warming')

    def test_chamber_parking_failure_is_caught_by_watchdog(self):
        rt = printer(); rt.fail_on.add('G0')
        with self.assertRaises(RuntimeError):
            start(rt)
        rt.advance(2)
        self.assertEqual(phase(rt), 'idle')
        self.assertEqual(rt.state['extruder']['target'], 0)
        self.assertEqual(rt.state['heater_bed']['target'], 0)

    def test_end_cleanup_precedes_injected_parking_error(self):
        rt = printer(); rt.fail_on.add('G1')
        with self.assertRaises(RuntimeError):
            rt.run('END_PRINT')
        self.assertEqual(rt.state['heater_bed']['target'], 0)
        self.assertEqual(rt.state['extruder']['target'], 0)
        self.assertEqual(rt.state['bed_mesh']['mesh_matrix'], [])
        self.assertEqual(phase(rt), 'idle')

    def test_unhomed_or_insufficient_clearance_skips_park(self):
        for unhomed in (False, True):
            rt = printer()
            if unhomed:
                rt.state['toolhead']['homed_axes'] = ''
            else:
                rt.state['gcode_move']['gcode_position']['z'] = 330
                rt.state['gcode_move']['position']['z'] = 330
            rt.run('PARK')
            self.assertFalse(any(l.startswith('G1 ') for l in rt.primitives()))

    def test_invalid_parameters_do_not_hold_file(self):
        for options in (dict(SOAKTIME=-1), dict(MAXTIME=-1), dict(TEMP='nan'), dict(SOAKTIME='nan')):
            rt = printer()
            with self.assertRaises(RuntimeError):
                start(rt, **options)
            self.assertEqual(phase(rt), 'idle')
            self.assertTrue(rt.state['virtual_sdcard']['is_active'])


class NativeKlipper(unittest.TestCase):
    def test_actual_gcode_transform_stays_inside_limits(self):
        from extras.gcode_move import GCodeMove
        for offset in (.055, -.3, 3.2):
            with self.subTest(offset=offset):
                rt = printer()
                rt.state['toolhead']['axis_maximum']['z'] = 325
                rt.state['bed_mesh']['mesh_matrix'] = [[-.2, .8], [.1, .4]]
                rt.state['gcode_move'] = D(position=D(x=175,y=175,z=250+offset,e=0), gcode_position=D(x=173,y=176,z=250,e=0))
                rt.run('PARK')
                gm = GCodeMove.__new__(GCodeMove)
                gm.axis_map = {'X':0,'Y':1,'Z':2,'E':3}
                gm.base_position = [2,-1,offset,0]
                gm.last_position = [175,175,250+offset,0]
                gm.absolute_coord = True
                gm.allow_absolute_extrude = True
                gm.extrude_factor = 1
                gm.speed_factor = 1/60
                gm.speed = 10
                physical = []
                def move(p, speed):
                    physical.append([p[0],p[1],p[2]+.8])
                    self.assertLessEqual(p[2]+.8, 325)
                gm.move_with_transform = move
                for line in rt.primitives():
                    if not line.startswith('G1 '):
                        continue
                    params = dict(re.findall(r'([XYZEF])([-+\d.]+)', line))
                    class Command:
                        get_command_parameters = lambda s: params
                        get_commandline = lambda s: line
                        error = RuntimeError
                    gm.cmd_G1(Command())
                self.assertEqual(physical[-1][:2], [175,100])
                self.assertAlmostEqual(physical[-1][2], 324.5)

    def test_native_base_cancel_closes_m25_held_file(self):
        from extras.virtual_sdcard import VirtualSD
        from extras.pause_resume import PauseResume
        from io import StringIO
        sd = VirtualSD.__new__(VirtualSD)
        sd.work_timer = None
        sd.must_pause_work = True
        sd.cmd_from_sd = False
        file = sd.current_file = StringIO('G1 X0\n')
        sd.file_position = sd.file_size = 6
        events = []
        class Reactor:
            NOW = 0
            register_timer = lambda s, cb, when: events.append(cb) or object()
            # The paused reader exits on its next reactor turn before reading.
            pause = lambda s, when: setattr(sd, 'work_timer', None)
            monotonic = lambda s: 0
        class Stats:
            note_cancel = lambda s: events.append('cancelled')
        sd.reactor = Reactor(); sd.print_stats = Stats()
        # Scheduling M24 must not execute a file command before BASE_CANCEL_PRINT.
        sd.cmd_M24(None)
        pause = PauseResume.__new__(PauseResume)
        pause.v_sd = sd
        pause.sd_paused = pause.is_paused = pause.pause_command_sent = False
        pause.cmd_CANCEL_PRINT(None)
        self.assertTrue(file.closed)
        self.assertIsNone(sd.current_file)
        self.assertEqual(events[-1], 'cancelled')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--klipper', required=True)
    options, remaining = parser.parse_known_args()
    sys.path.insert(0, os.path.join(os.path.abspath(options.klipper), 'klippy'))
    unittest.main(argv=[sys.argv[0]] + remaining)
