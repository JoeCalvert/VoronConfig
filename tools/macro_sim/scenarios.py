import sys, json, os, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from macrosim import Sim, D
from state import make_state
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
