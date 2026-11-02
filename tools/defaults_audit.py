#!/usr/bin/env python3
"""List every Klipper option in this config that differs from Klipper's
documented default, plus options set explicitly to their default.

Defaults come from Klipper's docs/Config_Reference.md (the commented
"#option: default" lines in each section's example block), so the audit
always matches the installed Klipper version.

Usage:
  python3 tools/defaults_audit.py ~/klipper/docs/Config_Reference.md printer.cfg > docs/defaults-audit.md

Only Klipper sections are audited. Happy Hare marks its own defaults in
mmu/.mmu_config (#~DEFAULT~#); plugin sections (beacon, autotune_tmc,
shaketune, led_effect) are listed separately for manual review.
"""
import glob, os, re, sys

SKIP_TYPES = {'gcode_macro', 'delayed_gcode', 'gcode_shell_command', 'include',
              'menu', 'display_template', 'save_variables'}
PLUGIN_TYPES = {'beacon', 'autotune_tmc', 'shaketune', 'led_effect', 'mmu',
                'mmu_machine', 'mmu_unit', 'mmu_unit_parameters', 'mmu_parameters',
                'mmu_toolhead', 'mmu_servo', 'mmu_sensors', 'mmu_leds',
                'mmu_encoder', 'mmu_gear', 'mmu_selector', 'mmu_espooler',
                'mmu_stepper', 'mmu_heater', 'mmu_environment', 'mmu_buffer'}

def section_type(name):
    t = name.split()[0]
    if re.match(r'stepper_[a-z]\d*$', t):
        return 'stepper'
    return t

def parse_reference(path):
    defaults, required = {}, {}
    text = open(path, encoding='utf-8').read()
    for block in re.findall(r'```\n(\[.*?)```', text, re.S):
        lines = block.split('\n')
        head = re.match(r'\[(.+?)\]', lines[0])
        if not head:
            continue
        t = section_type(head.group(1))
        d = defaults.setdefault(t, {}); r = required.setdefault(t, set())
        for l in lines[1:]:
            m = re.match(r'^#([a-z_0-9]+):\s?(.*)$', l)
            if m and not l.startswith('#   '):
                d.setdefault(m.group(1), m.group(2).strip())
                continue
            m = re.match(r'^([a-z_0-9]+):', l)
            if m:
                r.add(m.group(1))
    return defaults, required

def read_config(path, seen=None, out=None):
    """Return {section: {option: (value, file)}} following [include] like Klipper."""
    seen = seen if seen is not None else set()
    out = out if out is not None else {}
    path = os.path.normpath(path)
    if path in seen:
        return out
    seen.add(path)
    if not os.path.isfile(path):
        print(f'warning: skipping missing file {path} (dangling symlink?)', file=sys.stderr)
        return out
    base = os.path.dirname(path)
    section = None
    key = None
    for raw in open(path, encoding='utf-8', errors='replace'):
        line = raw.rstrip('\r\n')
        if line.startswith('#*#'):
            break  # SAVE_CONFIG block: machine-written, reviewed separately
        stripped = re.sub(r'\s[#;].*$', '', line)
        if not stripped.strip() or stripped.lstrip().startswith(('#', ';')):
            continue
        m = re.match(r'^\[([^\]]+)\]', stripped)
        if m:
            name = m.group(1).strip()
            if name.startswith('include '):
                pat = os.path.join(base, name[len('include '):].strip())
                for f in sorted(glob.glob(pat)):
                    read_config(f, seen, out)
                section = None
            else:
                section = name
                out.setdefault(section, {})
            key = None
            continue
        if section is None:
            continue
        if line[:1] in (' ', '\t') and key:
            continue  # continuation line (gcode etc.)
        m = re.match(r'^([A-Za-z_0-9]+)\s*[:=]\s*(.*)$', stripped)
        if m:
            key = m.group(1).lower()
            out[section][key] = (m.group(2).strip(), os.path.relpath(path, START))
    return out

HARDWARE = re.compile(r'(_pin|^pin|^serial|canbus_uuid|canbus_interface|^aliases|^sensor_type|^sensor_pin|^sensor_mcu|^gantry_corners|^points|^probe_points|^chain_count|^color_order|^beta|^resistance1|^temperature1|^accel_chip|_gcode|^initial_(red|green|blue|white))')

def same(a, b):
    a, b = re.sub(r'\s+', '', a.lower()), re.sub(r'\s+', '', b.lower())
    try:
        return abs(float(a) - float(b)) < 1e-9
    except ValueError:
        return a == b

if __name__ == '__main__':
    ref, cfg = sys.argv[1], sys.argv[2]
    START = os.path.dirname(os.path.abspath(cfg))
    defaults, required = parse_reference(ref)
    conf = read_config(cfg)
    rows, redundant, plugin, unknown, happy_hare = [], [], [], [], set()
    for sec, opts in conf.items():
        t = section_type(sec)
        if t in SKIP_TYPES:
            continue
        if t in PLUGIN_TYPES or t not in defaults:
            (plugin if t in PLUGIN_TYPES else unknown).append(sec)
            continue
        for k, (v, f) in sorted(opts.items()):
            if k in required.get(t, set()) or HARDWARE.search(k):
                continue
            if f.startswith('mmu' + os.sep) or f.startswith('mmu/'):
                happy_hare.add(sec)
                continue
            d = defaults[t].get(k)
            if d is None:
                rows.append((sec, k, '(no documented default)', v, f))
            elif d == '' :
                rows.append((sec, k, '(computed)', v, f))
            elif same(d, v):
                redundant.append((sec, k, v, f))
            else:
                rows.append((sec, k, d, v, f))
    print('# Klipper defaults audit\n')
    print('Generated by `tools/defaults_audit.py` from Klipper\'s `Config_Reference.md`. '
          'Required options and hardware facts (pins, CAN UUIDs, sensor types, rotation distances) are not listed.\n')
    print('## Options that differ from the default\n')
    print('| Section | Option | Default | Ours | File | Class | Decision |')
    print('|---|---|---|---|---|---|---|')
    for sec, k, d, v, f in sorted(rows):
        print(f'| `{sec}` | `{k}` | {d} | {v} | `{f}` | | |')
    print('\n## Options set to their default (could be removed)\n')
    print('| Section | Option | Value | File |')
    print('|---|---|---|---|')
    for sec, k, v, f in sorted(redundant):
        print(f'| `{sec}` | `{k}` | {v} | `{f}` |')
    print('\n## Not audited here\n')
    print('Plugin sections (check against each project\'s docs): ' + ', '.join(f'`{s}`' for s in sorted(plugin)) + '\n')
    print('Sections written by the Happy Hare installer (audit those with the non-default lines in mmu/.mmu_config, the ones without `#~DEFAULT~#`): ' + ', '.join(f'`{s}`' for s in sorted(happy_hare)) + '\n')
    if unknown:
        print('Sections not found in Config_Reference.md: ' + ', '.join(f'`{s}`' for s in sorted(unknown)) + '\n')
