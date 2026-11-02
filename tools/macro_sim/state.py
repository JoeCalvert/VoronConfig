from macrosim import D

# A plausible printer state for rendering macros. Override per scenario.
def make_state(**o):
    st = {
      'toolhead': D(position=D(x=175, y=175, z=10, e=0), axis_maximum=D(x=353, y=359, z=330), axis_minimum=D(x=0,y=0,z=-15), homed_axes='xyz'),
      'heater_bed': D(temperature=25, target=0),
      'extruder': D(temperature=25, target=0),
      'temperature_sensor Chamber': D(temperature=45),
      'save_variables': D(variables=D(nozzle_diameter=0.6)),
      'configfile': D(settings=D({'beacon': D(home_method='proximity'), 'beacon model default': D()}),
                      config=D(stepper_x=D(position_max='353'), stepper_y=D(position_max='359'), stepper_z=D(position_max='330'))),
      'quad_gantry_level': D(applied=True),
      'pause_resume': D(is_paused=False),
      'mmu': D(enabled=True, gate=0, gate_color_rgb=[(1,0,0)], print_state='printing'),
      'gcode_macro _MMU_CUT_TIP_VARS': D(pin_loc_xy=(10,346), restore_position=False, pin_park_dist=20.0, safe_margin_xy=(60,50)),
    }
    st.update(o); return st
