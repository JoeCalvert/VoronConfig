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
    ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'preparing\'"', '_SET_STATE STATE=leveling', '_JOB_FAILED', 'MENU', '_JOB_REPRINT', '_JOB_HEATERS_OFF']),
 ('failed_while_printing', dict(print_stats=D(state='error', filename='part.gcode', message='Move out of range: 360.0 10.0 2.0 [5.0]')),
    ['SET_GCODE_VARIABLE MACRO=_JOB VARIABLE=phase VALUE="\'printing\'"', '_JOB_FAILED', '_UNLOAD_NOW']),
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
 ('retune_list', dict(save_variables=D(variables=D(nozzle_diameter=0.6, retune_done=['mech']))), ['RETUNE', '_RETUNE_MARK STEP=belts DONE=1', '_RETUNE_RESET']),
 ('retune_steps', dict(), ['_RETUNE_MECH', '_RETUNE_BELTS', '_RETUNE_BELT_POSITION', '_RETUNE_EDGES', '_RETUNE_SHAPER', '_RETUNE_PID', '_RETUNE_EXTRUDER', '_RETUNE_FIRSTLAYER', '_RETUNE_FILAMENT', '_RETUNE_SELECTOR', '_RETUNE_GEAR', '_RETUNE_REWINDER', '_RETUNE_TOOLHEAD', '_RETUNE_SOAK']),
 ('retune_ercf', dict(save_variables=D(variables=D(nozzle_diameter=0.6, mmu_unit0_selector_offsets=[3.2, 26.6], mmu_unit0_gear_rotation_distances=[23.6, 23.1, 24.4, -1], mmu_unit0_bowden_lengths=[-1]))), ['_RETUNE_GATES', '_RETUNE_MMU_DO STEP=selector', '_RETUNE_MMU_DO STEP=servo_move', '_RETUNE_MMU_DO STEP=gear_advance', '_RETUNE_MMU_DO STEP=gear_move', '_RETUNE_MMU_DO STEP=gates', '_RETUNE_MMU_DO STEP=soak_quick']),
 ('retune_rewind', dict(mmu=MMU(filament_pos=0)), ['_RETUNE_MMU_DO STEP=rewind GATE=1']),
 ('cal_filament', dict(), ['CAL_FILAMENT TEST=pa', 'CAL_FILAMENT TEST=pa GATE=1', 'CAL_FILAMENT TEST=pa GATE=1 RANGE=wide', 'CAL_FILAMENT TEST=em GATE=0']),
 ('cal_filament_cancel', dict(print_stats=D(state='printing', filename='calibration/pa_g1_4.gcode', print_duration=60.0, message=''), save_variables=D(variables=D(nozzle_diameter=0.6, cal_last=D(test='pa', gate=1, key='PETG Orange 0.60', start=0.0, step=0.004, count=21, restore_pa=0.03)))), ['_CANCEL_PRINT_EXTENSION']),
 ('cal_filament_result', dict(save_variables=D(variables=D(nozzle_diameter=0.6, cal_seq=3, cal_last=D(test='pa', gate=1, key='PETG Orange 0.60', start=0.0, step=0.004, count=21), filament_tuning=D({'PETG Orange 0.60': D(em=0.94, pa=0.036)})))), ['_CAL_FILAMENT_RESULT', '_CAL_FILAMENT_RESULT PICK=9', '_RETUNE_FILAMENT', 'CAL_FILAMENT TEST=pa GATE=1 RANGE=around']),
 ('cal_shaper_klipper', dict(quad_gantry_level=D(applied=True)), ['_CAL_SHAPER_KLIPPER BACK=_RETUNE_SHAPER', '_CAL_SAVE']),
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
