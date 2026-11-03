"""Small event model for lifecycle checks, not a thermodynamics simulator.

Models timers, SD reader state, heater targets and the cancel hook. Motion and
heater waits remain primitives; native Klipper coordinate checks live in tests.
"""
import ast
import shlex
from macrosim import Sim, ENV


def arguments(rest):
    lexer = shlex.shlex(rest, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = '#;'
    return dict(part.split('=', 1) for part in lexer if '=' in part)


class Runtime(Sim):
    def __init__(self, root, state):
        super().__init__(root, state)
        self.now = 0.0
        self.timers = {}
        self.errors = []
        self.fail_on = set()
        self.state['toolhead']['estimated_print_time'] = self.now

    def run(self, line, depth=0):
        parts = line.strip().split(None, 1)
        if not parts:
            return
        cmd = parts[0].upper()
        rest = parts[1] if len(parts) > 1 else ''
        if cmd in self.fail_on:
            raise RuntimeError('Injected failure in ' + cmd)
        super().run(line, depth)
        if cmd in self.macros:
            return
        p = arguments(rest)
        if cmd == 'UPDATE_DELAYED_GCODE':
            duration = float(p['DURATION'])
            if duration:
                self.timers[p['ID']] = self.now + duration
            else:
                self.timers.pop(p['ID'], None)
        elif cmd == 'M25':
            self.state['virtual_sdcard']['is_active'] = False
            self.state['print_stats']['state'] = 'paused'
        elif cmd == 'M24':
            if not self.state['virtual_sdcard']['file_path']:
                raise RuntimeError('No SD file to resume')
            self.state['virtual_sdcard']['is_active'] = True
            self.state['print_stats']['state'] = 'printing'
        elif cmd == 'BASE_CANCEL_PRINT':
            # The native pause_resume command must see the re-armed SD reader.
            if self.state['virtual_sdcard']['is_active']:
                self.state['virtual_sdcard'].update(is_active=False, file_path=None)
                self.state['print_stats']['state'] = 'cancelled'
            self.state['pause_resume']['is_paused'] = False
        elif cmd == 'TURN_OFF_HEATERS':
            self.state['extruder']['target'] = 0
            self.state['heater_bed']['target'] = 0
        elif cmd == 'SET_HEATER_TEMPERATURE':
            self.state[p['HEATER']]['target'] = float(p['TARGET'])
        elif cmd in ('M140', 'M190'):
            target = float(rest.strip().lstrip('S'))
            self.state['heater_bed']['target'] = target
            if cmd == 'M190':
                self.state['heater_bed']['temperature'] = target
        elif cmd == 'BED_MESH_CLEAR':
            self.state['bed_mesh']['mesh_matrix'] = []
        elif cmd == 'SAVE_VARIABLE':
            self.state['save_variables']['variables'][p['VARIABLE']] = ast.literal_eval(p['VALUE'])

    def advance(self, seconds, temperature=None):
        end = self.now + seconds
        for _ in range(10000):
            due = [(when, name) for name, when in self.timers.items() if when <= end]
            if not due:
                break
            self.now, name = min(due)
            self.timers.pop(name)
            self.state['toolhead']['estimated_print_time'] = self.now
            if temperature is not None:
                self.state['temperature_sensor Chamber']['temperature'] = temperature(self.now)
            body = self.secs['delayed_gcode ' + name]['gcode']
            script = ENV.from_string(body).render(printer=self.printer(), params={})
            try:
                for line in script.splitlines():
                    if line.strip():
                        self.run(line)
            except RuntimeError as error:
                self.errors.append(str(error))
        else:
            raise RuntimeError('Timer loop did not terminate')
        self.now = end
        self.state['toolhead']['estimated_print_time'] = end

    def drain_chamber(self):
        for _ in range(600):
            if self.macros['_CHAMBER_WAIT']['vars']['phase'] == 'idle':
                return
            self.advance(30)
        raise RuntimeError('Chamber wait did not finish')
