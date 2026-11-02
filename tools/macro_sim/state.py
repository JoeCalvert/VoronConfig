from macrosim import D

# Commands other projects register (what printer.gcode.commands would list).
COMMANDS = ['BEACON_HOME_Z_CONTACT', 'BEACON_MODEL_SELECT', 'BLOBIFIER_CLEAN', 'BLOBIFIER_PARK',
            'MMU_RECOVER', 'MMU_UNLOCK', 'MMU_HOME', 'MMU_LOAD', 'MMU_UNLOAD', 'MMU_EJECT',
            'MMU_PRELOAD', 'MMU_CHECK_GATE', 'MMU_SELECT', 'MMU_CHANGE_TOOL', 'MMU_TTG_MAP',
            'SET_PAUSE_NEXT_LAYER', 'MMU_ENDLESS_SPOOL', 'MMU_CALIBRATE_SELECTOR', 'MMU_CALIBRATE_GEAR',
            'MMU_CALIBRATE_ENCODER', 'MMU_CALIBRATE_BOWDEN', 'MMU_CALIBRATE_GATE', 'MMU_CALIBRATE_TOOLHEAD', 'MMU_TEST_MOVE', 'MMU_MOTORS_OFF', 'MMU_SERVO', 'MMU_SOAKTEST_LOAD_SEQUENCE', 'RUN_SHELL_COMMAND', 'MMU_SELECT_BYPASS', 'AXES_MAP_CALIBRATION', 'AXES_SHAPER_CALIBRATION', 'COMPARE_BELTS_RESPONSES']

# A plausible printer state for rendering macros. Override per scenario.
def make_state(**o):
    st = {
      'toolhead': D(position=D(x=175, y=175, z=10, e=0), axis_maximum=D(x=353, y=359, z=330), axis_minimum=D(x=0,y=0,z=-15), homed_axes='xyz'),
      'heater_bed': D(temperature=25, target=0),
      'idle_timeout': D(state='Idle'),
      'print_stats': D(state='standby', filename='', print_duration=3600.0, message=''),
      'display_status': D(message='', progress=0),
      'extruder': D(temperature=25, target=0, pressure_advance=0.03),
      'temperature_sensor Chamber': D(temperature=45),
      'save_variables': D(variables=D(nozzle_diameter=0.6, maintenance_hours=D(filter=99.5, lube=12.0))),
      'configfile': D(settings=D({'beacon': D(home_method='proximity'), 'beacon model default': D(), 'virtual_sdcard': D(path='/home/pi/printer_data/gcodes'), 'printer': D(max_accel=7000, max_velocity=400)}),
                      save_config_pending_items=D(extruder=D(pid_kp='28.112', pid_ki='3.241', pid_kd='60.950'),
                                                input_shaper=D(shaper_type_x='mzv', shaper_freq_x='58.2', shaper_type_y='mzv', shaper_freq_y='44.0')),
                      config=D(stepper_x=D(position_max='353'), stepper_y=D(position_max='359'), stepper_z=D(position_max='330'),
                               )),
      'gcode': D(commands=D({c: D() for c in COMMANDS})),
      'quad_gantry_level': D(applied=True),
      'pause_resume': D(is_paused=False),
      'mmu': D(enabled=True, gate=0, tool=0, next_tool=-1, filament='Loaded', filament_pos=10, num_gates=4,
               gate_color_rgb=[(1,0,0)]*4, ttg_map=[0, 1, 2, 3], gate_status=[1, 1, 0, -1],
               gate_material=['PLA', 'PETG', 'ABS', ''], gate_temperature=[215, 240, 0, 0], gate_spool_id=[11, 12, -1, -1], gate_filament_name=['Galaxy Black', 'Orange', '', ''],
               print_state='printing', reason_for_pause='', operation='', action='Idle', endless_spool_groups=[0, 1, 2, 3],
               slicer_tool_map=D(referenced_tools=[0, 1], initial_tool=0,
                                 tools=D({'0': D(material='PLA', name='Galaxy Black'), '1': D(material='PETG', name='Orange')}))),
      'gcode_macro _MMU_CUT_TIP_VARS': D(pin_loc_xy=(10,346), restore_position=False, pin_park_dist=20.0, safe_margin_xy=(60,50)),
    }
    st.update(o); return st
