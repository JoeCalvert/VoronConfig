import sys, json, os, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from macrosim import Sim, D
from state import make_state

def MMU(**o):
    m = D(make_state()['mmu']); m.update(o); return m
SCENARIOS = [
 ('start_abs',  dict(), ['SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True', 'START_PRINT BED=100 EXTRUDER=250 CHAMBER=40 NOZZLE=0.6', 'POST_START_PRINT', 'END_PRINT']),
 ('start_pla_hotbed', dict(heater_bed=D(temperature=58, target=60)), ['SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True', 'START_PRINT BED=60 EXTRUDER=215 CHAMBER=0 NOZZLE=0.6', 'POST_START_PRINT', 'END_PRINT']),
 ('cancel', dict(), ['SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True', 'START_PRINT BED=100 EXTRUDER=250 CHAMBER=40 NOZZLE=0.6', 'POST_START_PRINT', '_CANCEL_PRINT_EXTENSION']),
 ('park', dict(), ['PARK']),
 ('cg28_unhomed', dict(toolhead=D(position=D(x=0,y=0,z=0,e=0), axis_maximum=D(x=353,y=359,z=330), homed_axes='')), ['_CG28']),
 ('cg28_homed', dict(), ['_CG28']),
 ('soak_bed', dict(), ['HEATSOAK_BED TEMP=100 SOAKTIME=2']),
 ('soak_chamber_warm', dict(), ['HEATSOAK_CHAMBER TEMP=40 MAXTIME=3']),
 ('soak_chamber_cold', dict(**{'temperature_sensor Chamber': D(temperature=30)}), ['HEATSOAK_CHAMBER TEMP=40 MAXTIME=3']),
 ('status_all', dict(), ['STATUS_'+s for s in 'OFF READY PART_READY BUSY HEATING COOLING LEVELING HOMING CLEANING MESHING CALIBRATING_Z PRINTING'.split()]),
 ('mmu_state', dict(), ['_STATUS_FROM_MMU STATE=printing', '_STATUS_FROM_MMU STATE=pause_locked']),
 ('accessories', dict(), ['LIGHT_ON S=0.5', 'LIGHT_OFF', 'START_FILTER SPEED=0.7', 'STOP_FILTER']),
 ('check', dict(), ['CHECK_CONFIG']),
 ('nozzle', dict(), ['NOZZLE_SET DIAMETER=0.4', 'NOZZLE_SET']),
 ('menu', dict(), ['MENU']),
 ('menu_unhomed_park', dict(toolhead=D(position=D(x=0,y=0,z=0,e=0), axis_maximum=D(x=353,y=359,z=330), homed_axes='')), ['_MENU_PARK']),
 ('check_hh_renamed', dict(gcode=D(commands=D()), mmu=D(enabled=True, gate=0)), ['CHECK_CONFIG']),
 ('recovery_stuck_in_extruder', dict(mmu=MMU(print_state='pause_locked', filament_pos=8, next_tool=2, reason_for_pause='Failed to unload. Filament stuck #2; in extruder')), ['_MMU_RECOVERY']),
 ('recovery_in_bowden', dict(mmu=MMU(print_state='pause_locked', filament_pos=3, next_tool=2)), ['_MMU_RECOVERY']),
 ('recovery_parked_runout', dict(mmu=MMU(print_state='pause_locked', filament_pos=0, tool=1, gate=1, reason_for_pause='Runout')), ['_MMU_RECOVERY', '_MMU_RECOVERY_GATES TOOL=1']),
 ('recovery_ready', dict(mmu=MMU(print_state='paused', filament_pos=10, tool=2, next_tool=2), extruder=D(temperature=240, target=240)), ['_MMU_RECOVERY', '_MMU_RECOVERY_RESUME']),
 ('recovery_resume_refused', dict(mmu=MMU(print_state='paused', filament_pos=10, tool=1, next_tool=2)), ['_MMU_RECOVERY_RESUME']),
 ('recovery_step', dict(mmu=MMU(print_state='pause_locked', filament_pos=0, next_tool=2)), ['_MMU_RECOVERY_DO STEP=remap TOOL=2 GATE=1', '_CONFIRM_CANCEL BACK=_MMU_RECOVERY', '_CANCEL_NOW']),
 ('checkup', dict(), ['MMU_CHECKUP GATES=1']),
 ('checkup_printing', dict(print_stats=D(state='printing')), ['MMU_CHECKUP']),
 ('service', dict(toolhead=D(position=D(x=175, y=355, z=12, e=0), axis_maximum=D(x=353,y=359,z=330), homed_axes='xyz')), ['SERVICE_POSITION']),
 ('failed_while_starting', dict(print_stats=D(state='error', filename='benchy 0.6 ABS.gcode', message='Unable to obtain QGL: probed points out of range'), extruder=D(temperature=150, target=150), heater_bed=D(temperature=100, target=100)),
    ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'preparing\'"', '_SET_STATE STATE=leveling', '_STATUS_FROM_MMU STATE=error', 'MENU', '_JOB_REPRINT', '_JOB_HEATERS_OFF']),
 ('failed_while_printing', dict(print_stats=D(state='error', filename='part.gcode', message='Move out of range: 360.0 10.0 2.0 [5.0]')),
    ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'printing\'"', '_STATUS_FROM_MMU STATE=error', '_UNLOAD_NOW']),
 ('cancel_unloaded', dict(mmu=MMU(filament_pos=0)), ['SET_GCODE_VARIABLE MACRO=_STARTUP_CHECK_STATE VARIABLE=ok VALUE=True', 'START_PRINT BED=100 EXTRUDER=250 CHAMBER=40 NOZZLE=0.6', 'POST_START_PRINT', '_CANCEL_PRINT_EXTENSION']),
 ('preheat_loaded', dict(heater_bed=D(temperature=40, target=60)), ['_PREHEAT_MENU', 'PREHEAT', 'PREHEAT_OFF']),
 ('preheat_abs', dict(), ['PREHEAT MATERIAL=abs']),
 ('preflight_ok', dict(), ['PREFLIGHT_CHECK']),
 ('preflight_mismatch', dict(mmu=MMU(gate_material=['PLA', 'PLA', 'ABS', ''], gate_filament_name=['Galaxy Black', 'White', '', ''], slicer_tool_map=D(referenced_tools=[0, 1, 2], initial_tool=0, tools=D({'0': D(material='PLA', name='Galaxy Black'), '1': D(material='PETG', name='Orange'), '2': D(material='ABS', name='Red')})), gate_status=[1, 1, 0, -1])),
    ['PREFLIGHT_CHECK', 'PREFLIGHT_CHECK RECHECK=1', '_PREFLIGHT_CONTINUE']),
 ('nozzle_change', dict(), ['NOZZLE_CHANGE', '_NOZZLE_CHANGE_PREPARE', '_NOZZLE_CHANGE_DONE DIAMETER=0.4']),
 ('spool_swap', dict(mmu=MMU(print_state='ready')), ['SPOOL_SWAP', '_SPOOL_SWAP_EJECT GATE=1', '_SPOOL_SWAP_PRELOAD GATE=1']),
 ('spool_swap_empty_gate', dict(mmu=MMU(print_state='ready')), ['SPOOL_SWAP GATE=2', '_SPOOL_SWAP_RESULT GATE=2']),
 ('mmu_error_hook', dict(mmu=MMU(print_state='pause_locked', filament_pos=3, next_tool=1, reason_for_pause='Failed to load')), ['_MMU_RECOVERY NOTIFY=1']),
 ('pause_for_user', dict(display_status=D(message="Insert magnets now; it's layer 12")), ['PAUSE_FOR_USER', '_PAUSE_FOR_USER_SERVICE', '_CONFIRM_CANCEL BACK=_PAUSE_FOR_USER_SHOW', '_PAUSE_FOR_USER_RESUME']),
 ('pause_next_layer', dict(print_stats=D(state='printing', filename='x.gcode')), ['MENU', '_PAUSE_NEXT_LAYER', '_PAUSE_LAYER_REACHED']),
 ('part_ready', dict(heater_bed=D(temperature=35, target=0)), ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'complete\'"', '_PART_READY_CHECK']),
 ('part_still_hot', dict(heater_bed=D(temperature=80, target=0)), ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'complete\'"', '_PART_READY_CHECK']),
 ('notify_on', dict(), ['SET_GCODE_VARIABLE MACRO=_USER_VARIABLES VARIABLE=notifier_name VALUE="\'phone\'"', '_NOTIFY MSG="Test"']),
 ('maintenance', dict(), ['MAINTENANCE', '_MAINTENANCE_RESET ITEM=filter']),
 ('maintenance_add', dict(), ['_MAINTENANCE_ADD FILTER=1', '_MAINTENANCE_ADD FILTER=0']),
 ('calibrate', dict(quad_gantry_level=D(applied=False)), ['CALIBRATE', '_CAL_PID HEATER=extruder TARGET=240', '_CAL_SHAPER', '_CAL_MESH']),
 ('check_dialog_problem', dict(save_variables=D(variables=D())), ['CHECK_CONFIG STARTUP=1']),
 ('endless_spool_groups', dict(mmu=MMU(gate_material=['PLA', 'PLA', 'PETG', 'PLA'], gate_filament_name=['Galaxy Black', 'galaxy black ', 'Orange', ''])), ['_ENDLESS_SPOOL_AUTOGROUP']),
 ('endless_spool_unchanged', dict(), ['_ENDLESS_SPOOL_AUTOGROUP']),
 ('qgl', dict(), ['COARSE_QGL', 'FAST_QGL', 'BEACON_HOME_Z_CONTACT CALIBRATE=1', 'Z_QUICK_SETUP']),
]

def run(root):
    res = {}
    for name, st, cmds in SCENARIOS:
        sim = Sim(root, make_state(**st))
        try:
            for c in cmds: sim.run(c)
            res[name] = sim.primitives()
        except Exception as e:
            res[name] = ['ERROR: %s: %s' % (type(e).__name__, e)]
    return res

if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description='Expand macro scenarios to G-code; save or compare.')
    ap.add_argument('root', help='config folder containing printer.cfg')
    ap.add_argument('--save', help='write the expanded G-code to this JSON file')
    ap.add_argument('--compare', help='compare against a JSON file written with --save')
    a = ap.parse_args()
    res = run(a.root)
    errors = [k for k, v in res.items() if v and v[0].startswith('ERROR')]
    for k in errors: print('ERROR in', k, '->', res[k][0])
    if a.save:
        json.dump(res, open(a.save, 'w'), indent=1); print('saved', len(res), 'scenarios to', a.save)
    if a.compare:
        old = json.load(open(a.compare)); same = True
        for k in sorted(set(old) | set(res)):
            if old.get(k) != res.get(k):
                same = False
                print('=== %s' % k)
                print('\n'.join(l for l in difflib.unified_diff(old.get(k, []), res.get(k, []), lineterm='', n=1) if not l.startswith(('---', '+++'))))
        print('identical' if same else 'differences above')
    sys.exit(1 if errors else 0)
