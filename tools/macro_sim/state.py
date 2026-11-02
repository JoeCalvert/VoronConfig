from macrosim import D

# Commands other projects register (what printer.gcode.commands would list).
COMMANDS = ['BEACON_HOME_Z_CONTACT', 'BEACON_MODEL_SELECT', 'BLOBIFIER_CLEAN', 'BLOBIFIER_PARK',
            'MMU_RECOVER', 'MMU_UNLOCK', 'MMU_HOME', 'MMU_LOAD', 'MMU_UNLOAD', 'MMU_EJECT',
            'MMU_PRELOAD', 'MMU_CHECK_GATE', 'MMU_SELECT', 'MMU_CHANGE_TOOL', 'MMU_TTG_MAP']

# A plausible printer state for rendering macros. Override per scenario.
def make_state(**o):
    st = {
      'toolhead': D(position=D(x=175, y=175, z=10, e=0), axis_maximum=D(x=353, y=359, z=330), axis_minimum=D(x=0,y=0,z=-15), homed_axes='xyz'),
      'heater_bed': D(temperature=25, target=0),
      'idle_timeout': D(state='Idle'),
      'display_status': D(message='', progress=0),
      'extruder': D(temperature=25, target=0),
      'temperature_sensor Chamber': D(temperature=45),
      'save_variables': D(variables=D(nozzle_diameter=0.6)),
      'configfile': D(settings=D({'beacon': D(home_method='proximity'), 'beacon model default': D(), 'mmu': D(disable_heater=600)}),
                      config=D(stepper_x=D(position_max='353'), stepper_y=D(position_max='359'), stepper_z=D(position_max='330'),
                               mmu=D(happy_hare_version='4.1.0'))),
      'gcode': D(commands=D({c: D() for c in COMMANDS})),
      'quad_gantry_level': D(applied=True),
      'pause_resume': D(is_paused=False),
      'mmu': D(enabled=True, gate=0, tool=0, next_tool=-1, filament='Loaded', filament_pos=10, num_gates=4,
               gate_color_rgb=[(1,0,0)]*4, ttg_map=[0, 1, 2, 3], gate_status=[1, 1, 0, -1],
               gate_material=['PLA', 'PETG', 'ABS', ''], gate_filament_name=['Galaxy Black', 'Orange', '', ''],
               print_state='printing', reason_for_pause='', operation='', action='Idle',
               slicer_tool_map=D(referenced_tools=[0, 1], initial_tool=0,
                                 tools=D({'0': D(material='PLA', name='Galaxy Black'), '1': D(material='PETG', name='Orange')}))),
      'print_stats': D(state='standby', filename=''),
      'gcode_macro _MMU_CUT_TIP_VARS': D(pin_loc_xy=(10,346), restore_position=False, pin_park_dist=20.0, safe_margin_xy=(60,50)),
    }
    st.update(o); return st
