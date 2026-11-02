"""PrusaSlicer profiles for this printer: the one place to change slicer settings.

tools/build_slicer_profiles.py turns this into ordinary PrusaSlicer presets
(printer, print and filament .ini files), so nothing is duplicated by hand:

    printer  = slicer/base/printer.ini + PRINTER + the nozzle's NOZZLES entry
    print    = slicer/base/print.ini + PRINT + nozzle-derived widths/layers
               + the intent (INTENTS)
    filament = slicer/base/filament.ini + MATERIALS[type] + the filament's
               values in Spoolman (temperatures, EM, flow, PA per nozzle...)

Machine limits (max_accel, max_velocity) are read from config/machine.cfg, so
re-tuning the printer and rebuilding keeps the slicer in step.

Every value that is *measured* rather than chosen says how to measure it:
"tune:" comments point at docs/slicer.md -> "What gets tuned, and how".
Don't edit the generated presets in PrusaSlicer; change this file (or the
filament in Spoolman) and rebuild. To try something out, "Save as" a new
name in PrusaSlicer; the generator never touches presets it didn't write.
"""

# ---------------------------------------------------------------------------
# Nozzles. One printer preset per nozzle (plus a "(bypass)" twin), and one set
# of print presets per nozzle size. 'key' is how the printer and Spoolman name
# the nozzle (NOZZLE_SET DIAMETER=0.6 TYPE=hf  ->  0.60_hf).
#
# max_flow: what the hotend can melt with this nozzle, mm³/s. Prints are capped
#   to it; each filament can cap lower (its 'max_flow' in Spoolman).
#   tune: CAL_FILAMENT TEST=flow with your fastest filament.
# retract: firmware-independent slicer retraction, mm. tune: retraction test.
# ---------------------------------------------------------------------------
NOZZLES = [
    # key         name                        dia   type       max_flow retract lift
    dict(key='0.25',     name='Revo 0.25',         d=0.25, type='brass',    max_flow=6,  retract=0.8, lift=0.1),
    dict(key='0.40',     name='Revo 0.40',         d=0.40, type='brass',    max_flow=12, retract=0.8, lift=0.2),
    dict(key='0.40_obx', name='Revo ObXidian 0.40', d=0.40, type='obxidian', max_flow=12, retract=0.5, lift=0.2),
    dict(key='0.60',     name='Revo 0.60',         d=0.60, type='brass',    max_flow=13, retract=0.8, lift=0.2),
    dict(key='0.60_hf',  name='Revo HF 0.60',      d=0.60, type='hf',       max_flow=24, retract=0.8, lift=0.2),
    dict(key='0.80',     name='Revo 0.80',         d=0.80, type='brass',    max_flow=14, retract=0.8, lift=0.3),
]
PRINTER_NAME = 'Voron 2.4 - {name}'          # + ' (bypass)' for the single-extruder twin
GATES = 8                                    # ERCF gates = PrusaSlicer extruders

# Line widths as multiples of the nozzle (PrusaSlicer's flow model). Wider
# first layer for adhesion; top surface at 1.0x for a smooth finish; sparse
# infill wider (fewer, fatter lines: same flow, fewer moves).
WIDTHS = dict(extrusion_width=1.125, external_perimeter_extrusion_width=1.125,
              perimeter_extrusion_width=1.125, first_layer_extrusion_width=1.25,
              infill_extrusion_width=1.25, solid_infill_extrusion_width=1.125,
              top_infill_extrusion_width=1.0, support_material_extrusion_width=1.0)
FIRST_LAYER_HEIGHT = {0.25: 0.15, 0.40: 0.25, 0.60: 0.30, 0.80: 0.40}

# ---------------------------------------------------------------------------
# Printer presets (all nozzles). Custom G-code matches docs/slicer.md.
# ---------------------------------------------------------------------------
START_GCODE_MMU = '\n'.join([
    'M140 S{first_layer_bed_temperature[initial_tool]}',
    'MMU_START_SETUP INITIAL_TOOL={initial_tool} REFERENCED_TOOLS=!referenced_tools! TOOL_COLORS=!colors! '
    'TOOL_TEMPS=!temperatures! TOOL_MATERIALS=!materials! FILAMENT_NAMES=!filament_names! PURGE_VOLUMES=!purge_volumes!',
    'MMU_START_CHECK',
    'PREFLIGHT_CHECK',
    'START_PRINT BED={first_layer_bed_temperature[initial_tool]} EXTRUDER={first_layer_temperature[initial_tool]} '
    'NOZZLE={nozzle_diameter[0]} NOZZLE_TYPE=@NOZZLE_TYPE@ CHAMBER=@CHAMBER@',
    'MMU_START_LOAD_INITIAL_TOOL',
    'POST_START_PRINT',
    'SET_PRINT_STATS_INFO TOTAL_LAYER=[total_layer_count]',
])

PRINTER = dict(
    gcode_flavor='klipper',
    autoemit_temperature_commands=0,      # START_PRINT heats; no M190/M109/M141 from the slicer
    use_relative_e_distances=1,
    use_firmware_retraction=0,            # retraction per filament/nozzle, from the slicer
    binary_gcode=0,                       # Klipper and Happy Hare's preprocessor need plain G-code
    machine_limits_usage='time_estimate_only',
    thumbnails='32x32/PNG, 300x300/PNG',  # Fluidd/KlipperScreen list and detail views
    end_gcode='MMU_END\nEND_PRINT',
    toolchange_gcode='T[next_extruder]',
    layer_gcode='SET_PRINT_STATS_INFO CURRENT_LAYER={layer_num + 1}\nMMU_UPDATE_HEIGHT',
    before_layer_gcode='',
    pause_print_gcode='PAUSE_FOR_USER',
    color_change_gcode='PAUSE_FOR_USER',  # there is no M600 on this printer
    template_custom_gcode='',
    bed_shape='0x0,350x0,350x350,0x350',
    max_print_height=325,
    z_offset=0,
    # Happy Hare's cutter does tip shaping: PrusaSlicer's single-extruder
    # MM tip forming must be exactly zero (Happy Hare slicer setup guide).
    cooling_tube_length=0, cooling_tube_retraction=0, parking_pos_retraction=0,
    extra_loading_move=0, high_current_on_filament_swap=0,
    # Per-tool (one value per gate; the generator expands them). The same
    # on every tool: T0 used to differ from T1-T7.
    retract_layer_change=1, wipe=1, retract_before_travel=1, retract_before_wipe='0%',
    retract_speed=35, deretract_speed=35, retract_restart_extra=0,
    retract_length_toolchange=0, retract_restart_extra_toolchange=0,
    retract_lift_above=0.25,              # no Z-hop on the first layer
    retract_lift_below=0,
    travel_ramping_lift=1, travel_slope=20, travel_lift_before_obstacle=1,
)

# ---------------------------------------------------------------------------
# Print presets: values for every intent, before the intent's own changes.
# Speeds are deliberately generous: on this printer the hotend's flow
# (max_flow above, and each filament's) is what actually limits most moves,
# and PrusaSlicer slows any move that would exceed it. The outer wall is the
# exception: it is held back for surface quality.
# Accelerations are fractions of max_accel from config/machine.cfg (7000 now;
# set from the input shaper's recommendation, see RETUNE).
# ---------------------------------------------------------------------------
ACCEL = dict(                              # fraction of max_accel
    default_acceleration=0.7,
    external_perimeter_acceleration=0.45,   # ringing on the visible surface
    perimeter_acceleration=0.7,
    top_solid_infill_acceleration=0.45,
    solid_infill_acceleration=1.0,
    infill_acceleration=1.0,
    bridge_acceleration=0.45,
    travel_acceleration=1.0,
)
PRINT = dict(
    first_layer_acceleration=500,
    travel_short_distance_acceleration=250,  # only the tiny hops (< retract_before_travel)
    external_perimeter_speed=150, perimeter_speed=200, small_perimeter_speed='50%',
    infill_speed=300, solid_infill_speed=250, top_solid_infill_speed=150, gap_fill_speed=150,
    bridge_speed=50, over_bridge_speed='60%',
    support_material_speed=200, support_material_interface_speed='60%',
    first_layer_speed=40, first_layer_infill_speed=80,
    travel_speed=350, travel_speed_z=15, max_print_speed=350,
    # Overhang speeds: index 0 is 0% overlap (bridging) and must be the
    # slowest; 3 is 75% overlap (barely overhanging). Percent of the outer wall.
    enable_dynamic_overhang_speeds=1,
    overhang_speed_0=15, overhang_speed_1=25, overhang_speed_2='40%', overhang_speed_3='80%',
    perimeter_generator='arachne', perimeters=3, extra_perimeters=0, extra_perimeters_on_overhangs=0,
    ensure_vertical_shell_thickness='enabled', thin_walls=0, gap_fill_enabled=1,
    top_solid_layers=5, top_solid_min_thickness=0.7, bottom_solid_layers=4, bottom_solid_min_thickness=0.5,
    top_one_perimeter_type='top', top_fill_pattern='monotonic', bottom_fill_pattern='monotonic',
    fill_pattern='cubic', fill_density='15%', infill_anchor='600%', infill_anchor_max=20, infill_overlap='25%',
    solid_infill_below_area=0,
    bridge_flow_ratio=1, thick_bridges=0, dont_support_bridges=0,
    # Seams: aligned at the sharpest corner, scarfed where the wall is smooth
    # (cylinders) so the seam all but disappears. tune: seam test.
    seam_position='aligned', staggered_inner_seams=1, seam_gap_distance='15%',
    scarf_seam_placement='everywhere', scarf_seam_only_on_smooth=1, scarf_seam_length=20,
    scarf_seam_on_inner_perimeters=0, scarf_seam_start_height='0%', scarf_seam_entire_loop=0,
    support_material=0, support_material_auto=1, support_material_buildplate_only=1,
    support_material_style='organic', support_material_contact_distance=0.2,
    support_material_interface_pattern='rectilinear', support_material_interface_contact_loops=0,
    avoid_crossing_perimeters=0, only_retract_when_crossing_perimeters=1,
    elefant_foot_compensation=0,          # tune: measure the base of a test part (docs/slicer.md)
    arc_fitting='disabled',               # Klipper has no [gcode_arcs] here
    gcode_label_objects='firmware',       # EXCLUDE_OBJECT + adaptive mesh
    gcode_resolution=0.0125,
    complete_objects=0, wipe_tower=0, single_extruder_multi_material_priming=0,
    wipe_tower_extruder=0, ooze_prevention=0,
    output_filename_format='{input_filename_base}_{nozzle_diameter[0]}n_{layer_height}mm.gcode',
    # Small Area Flow Compensation, as before. Path on the computer running
    # PrusaSlicer; set it to '' to turn it off.
    post_process='/home/joe/Voron/SAFC/SmallAreaFlowComp',
)

# ---------------------------------------------------------------------------
# Intents. Each is: which nozzle sizes it applies to, its layer height per
# size, and its changes from PRINT. Print preset names: "0.20mm Standard @0.40".
# ---------------------------------------------------------------------------
INTENTS = [
    dict(name='Quality', layers={0.25: 0.08, 0.40: 0.12, 0.60: 0.20},
         set=dict(external_perimeter_speed=100, top_solid_infill_speed=100,
                  external_perimeter_acceleration=0.35, top_solid_infill_acceleration=0.35)),
    dict(name='Standard', layers={0.25: 0.12, 0.40: 0.20, 0.60: 0.30, 0.80: 0.40}, set=dict()),
    dict(name='Draft', layers={0.40: 0.28, 0.60: 0.40, 0.80: 0.55},
         set=dict(perimeters=2, fill_density='10%', external_perimeter_speed=200,
                  top_solid_min_thickness=0.6, bottom_solid_min_thickness=0.5,
                  seam_position='nearest', scarf_seam_placement='nowhere')),
    # Voron Print It Forward part requirements: 4 walls, 5 top/bottom, 40% infill.
    dict(name='PIF', layers={0.40: 0.20}, set=dict(
        perimeters=4, top_solid_layers=5, bottom_solid_layers=5, top_solid_min_thickness=1,
        bottom_solid_min_thickness=1, fill_density='40%', fill_pattern='cubic')),
    dict(name='Gridfinity', layers={0.60: 0.35}, set=dict(
        perimeters=2, fill_pattern='lightning', fill_density='30%', top_solid_layers=4, bottom_solid_layers=2,
        top_fill_pattern='monotoniclines', bottom_fill_pattern='monotoniclines', elefant_foot_compensation=0.2,
        staggered_inner_seams=0, seam_position='nearest', scarf_seam_placement='nowhere')),
    # TPU: slow and steady; the filament's own max_flow (~3.5) does most of the limiting.
    dict(name='Flexi', layers={0.40: 0.15}, set=dict(
        perimeters=2, fill_pattern='archimedeanchords', fill_density='15%', avoid_crossing_perimeters=1,
        external_perimeter_speed=40, perimeter_speed=40, infill_speed=40, solid_infill_speed=40,
        top_solid_infill_speed=30, gap_fill_speed=40, bridge_speed=30, max_print_speed=40,
        bridge_flow_ratio=0.75, support_material_style='grid', support_material_contact_distance=0.3)),
    # Clear PETG: solid, aligned lines, no top/bottom skins, slow infill (fewer bubbles).
    dict(name='PETG Clear', layers={0.40: 0.10}, set=dict(
        perimeters=2, fill_pattern='alignedrectilinear', fill_density='100%', infill_overlap='35%',
        top_solid_layers=0, bottom_solid_layers=0, top_solid_min_thickness=0, bottom_solid_min_thickness=0,
        infill_speed=30, solid_infill_speed=30, top_solid_infill_speed=30, external_perimeter_speed=55)),
    # Thin flat stencils: one object at a time, gently.
    dict(name='Stencil', layers={0.25: 0.10}, set=dict(
        complete_objects=1, default_acceleration=2000, external_perimeter_acceleration=2000,
        perimeter_acceleration=2000, infill_acceleration=2000, solid_infill_acceleration=2000,
        top_solid_infill_acceleration=2000, travel_acceleration=2000, bridge_acceleration=2000,
        external_perimeter_speed=30, perimeter_speed=30, infill_speed=30, solid_infill_speed=30,
        top_solid_infill_speed=30, gap_fill_speed=30, bridge_speed=30, enable_dynamic_overhang_speeds=0)),
]

# ---------------------------------------------------------------------------
# Material defaults, by Spoolman 'material'. A filament's own values in
# Spoolman win (temperatures, and the extra fields: extrusion_multiplier,
# max_flow, pa_<nozzle>, fan_min, fan_max, chamber_temp, retract_length).
# chamber: from preheat_materials in config/variables.cfg when not set here.
# pa: per nozzle key, used until a filament has its own (CAL_FILAMENT TEST=pa).
# ---------------------------------------------------------------------------
MATERIALS = {
    'PLA': dict(filament_type='PLA', temperature=215, bed_temperature=60, max_flow=21, em=0.98,
                fan=(100, 100), bridge_fan=100, disable_fan_first_layers=1, slowdown_below_layer_time=8,
                min_print_speed=15, pa={'0.25': 0.06, '0.40': 0.035, '0.40_obx': 0.035, '0.60': 0.03,
                                        '0.60_hf': 0.027, '0.80': 0.025}),
    'PETG': dict(filament_type='PETG', temperature=240, bed_temperature=80, max_flow=17, em=0.935,
                 fan=(0, 0), bridge_fan=70, disable_fan_first_layers=2, slowdown_below_layer_time=10,
                 min_print_speed=15, retract_length=None,
                 pa={'0.25': 0.07, '0.40': 0.04, '0.40_obx': 0.04, '0.60': 0.035, '0.60_hf': 0.032, '0.80': 0.03}),
    'ABS': dict(filament_type='ABS', temperature=245, bed_temperature=110, max_flow=22, em=0.965,
                fan=(70, 70), bridge_fan=80, disable_fan_first_layers=2, slowdown_below_layer_time=5,
                min_print_speed=15,
                pa={'0.25': 0.06, '0.40': 0.033, '0.40_obx': 0.033, '0.60': 0.03, '0.60_hf': 0.028, '0.80': 0.025}),
    'ASA': dict(filament_type='ASA', temperature=250, bed_temperature=110, max_flow=20, em=0.94,
                fan=(80, 80), bridge_fan=80, disable_fan_first_layers=2, slowdown_below_layer_time=5,
                min_print_speed=15,
                pa={'0.25': 0.06, '0.40': 0.03, '0.40_obx': 0.03, '0.60': 0.028, '0.60_hf': 0.028, '0.80': 0.025}),
    'PC': dict(filament_type='PC', temperature=270, bed_temperature=110, max_flow=12, em=0.95,
               fan=(0, 30), bridge_fan=50, disable_fan_first_layers=3, slowdown_below_layer_time=5,
               min_print_speed=15, pa={}),
    'TPU': dict(filament_type='FLEX', temperature=230, bed_temperature=50, max_flow=3.5, em=1.0,
                fan=(60, 100), bridge_fan=100, disable_fan_first_layers=1, slowdown_below_layer_time=8,
                min_print_speed=10, retract_length=0.4, pa={'0.40': 0.11, '0.40_obx': 0.11}),
}
# Used for any nozzle a material has no 'pa' value for, so a tool change never
# keeps the previous filament's pressure advance.
GENERIC_PA = {'0.25': 0.06, '0.40': 0.035, '0.40_obx': 0.035, '0.60': 0.03, '0.60_hf': 0.028, '0.80': 0.025}
MATERIAL_ALIASES = {'PET': 'PETG', 'PETG+': 'PETG', 'ABS+': 'ABS', 'FLEX': 'TPU', 'TPU95A': 'TPU', 'PLA+': 'PLA'}

FILAMENT = dict(
    filament_diameter=1.75,
    cooling=1, fan_always_on=1, cooling_slowdown_logic='consistent_surface',
    enable_dynamic_fan_speeds=0, full_fan_speed_layer=0, fan_below_layer_time=60,
    start_filament_gcode='',              # written by the generator: pressure advance per nozzle
    end_filament_gcode='""',
    # Happy Hare cuts and parks the filament: no PrusaSlicer ramming or tip forming.
    filament_cooling_moves=0, filament_cooling_initial_speed=0, filament_cooling_final_speed=0,
    filament_loading_speed=0, filament_loading_speed_start=0, filament_unloading_speed=0,
    filament_unloading_speed_start=0, filament_toolchange_delay=0, filament_multitool_ramming=0,
    filament_stamping_distance=0, filament_stamping_loading_speed=0, filament_minimal_purge_on_wipe_tower=0,
    compatible_printers='', compatible_printers_condition='', compatible_prints='', compatible_prints_condition='',
)
