#!/usr/bin/env python3
"""Keep filament tuning (PA per nozzle, EM, max flow...) in Spoolman.

Spoolman is the master copy of each filament: tools/build_slicer_profiles.py
reads these values into the PrusaSlicer filament presets.

    # once: create the extra fields in Spoolman (safe to re-run)
    python3 tools/spoolman_tuning.py setup

    # store a result against the filament of a spool (CAL_FILAMENT does this)
    python3 tools/spoolman_tuning.py set --spool 12 --field pa_0_60_hf --value 0.032

    # once: copy the values from an exported PrusaSlicer config bundle into
    # Spoolman (filaments matched by name). Shows the plan; --apply writes it.
    python3 tools/spoolman_tuning.py import-bundle PrusaSlicer_config_bundle.ini [--apply]

    # see what Spoolman holds
    python3 tools/spoolman_tuning.py show

--url defaults to http://localhost:7912 (Spoolman on the Pi, as in
moonraker.conf). From another computer: --url http://voron.local:7912.
Standard library only.
"""

import argparse
import importlib.util
import json
import os
import re
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Old printer_notes tags in the hand-made PrusaSlicer profiles -> nozzle keys
BUNDLE_TAGS = {'REVO_0.25_BRASS': '0.25', 'REVO_0.4_BRASS': '0.40', 'REVO_0.4_OBXIDIAN': '0.40_obx',
               'REVO_0.6_BRASS': '0.60', 'REVO_0.6_HIGH_FLOW': '0.60_hf', 'REVO_0.8_BRASS': '0.80'}


def nozzle_keys():
    spec = importlib.util.spec_from_file_location('profiles', os.path.join(ROOT, 'slicer', 'profiles.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return [n['key'] for n in mod.NOZZLES]


def pa_field(key):
    return 'pa_' + key.replace('.', '_')


def fields():
    out = [('extrusion_multiplier', 'Extrusion multiplier', 'float', None),
           ('max_flow', 'Max volumetric flow', 'float', 'mm³/s'),
           ('fan_min', 'Part fan min', 'integer', '%'),
           ('fan_max', 'Part fan max', 'integer', '%'),
           ('chamber_temp', 'Chamber temperature', 'integer', '°C'),
           ('retract_length', 'Retraction length', 'float', 'mm')]
    for k in nozzle_keys():
        out.append((pa_field(k), 'PA %s' % k.replace('_', ' '), 'float', None))
    return out


class Spoolman:
    def __init__(self, url):
        self.base = url.rstrip('/') + '/api/v1'

    def call(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method,
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                text = r.read()
                return json.loads(text) if text else None
        except urllib.error.HTTPError as e:
            sys.exit('spoolman_tuning: %s %s failed: %s %s' % (method, path, e.code, e.read()[:300].decode('utf-8', 'replace')))
        except urllib.error.URLError as e:
            sys.exit('spoolman_tuning: cannot reach Spoolman at %s (%s)' % (self.base, e.reason))


def cmd_setup(sm, a):
    have = {f['key'] for f in sm.call('GET', '/field/filament')}
    for i, (key, name, ftype, unit) in enumerate(fields()):
        if key in have:
            continue
        body = {'name': name, 'field_type': ftype, 'order': 100 + i}
        if unit:
            body['unit'] = unit
        sm.call('POST', '/field/filament/' + key, body)
        print('created filament field', key)
    print('spoolman_tuning: fields ready')


def parse_value(v):
    v = str(v).strip()
    try:
        return int(v) if re.fullmatch(r'-?\d+', v) else float(v)
    except ValueError:
        return v


def cmd_set(sm, a):
    known = {k for k, *_ in fields()}
    if a.field not in known:
        sys.exit('spoolman_tuning: unknown field %s (known: %s)' % (a.field, ', '.join(sorted(known))))
    spool = sm.call('GET', '/spool/%d' % a.spool)
    fil = spool['filament']
    value = parse_value(a.value)
    sm.call('PATCH', '/filament/%d' % fil['id'], {'extra': {a.field: json.dumps(value)}})
    print('spoolman_tuning: %s = %s saved for "%s" (filament %d)' % (a.field, value, fil.get('name'), fil['id']))


def bundle_filaments(path):
    out, cur = {}, None
    for line in open(path, encoding='utf-8'):
        line = line.rstrip('\n')
        m = re.match(r'^\[filament:(.*)\]$', line)
        if m:
            cur = out.setdefault(m.group(1), {})
            continue
        if line.startswith('['):
            cur = None
        elif cur is not None and ' = ' in line:
            k, v = line.split(' = ', 1)
            cur[k] = v
    return out


def values_from_bundle(cfg):
    vals = {}
    gcode = cfg.get('start_filament_gcode', '').strip('"').replace('\\n', '\n')
    # ';{elsif ...}' lines are still evaluated by PrusaSlicer, so they count
    for tag, pa in re.findall(r'printer_notes=~/\.?\*?(REVO_[A-Z0-9._]+?)\.?\*?/\}\s*SET_PRESSURE_ADVANCE ADVANCE=([0-9.]+)', gcode):
        if tag in BUNDLE_TAGS:
            vals[pa_field(BUNDLE_TAGS[tag])] = float(pa)
    if cfg.get('extrusion_multiplier'):
        vals['extrusion_multiplier'] = float(cfg['extrusion_multiplier'])
    if float(cfg.get('filament_max_volumetric_speed') or 0) > 0:
        vals['max_flow'] = float(cfg['filament_max_volumetric_speed'])
    if cfg.get('min_fan_speed') not in (None, ''):
        vals['fan_min'] = int(float(cfg['min_fan_speed']))
    if cfg.get('max_fan_speed') not in (None, ''):
        vals['fan_max'] = int(float(cfg['max_fan_speed']))
    rl = cfg.get('filament_retract_length', 'nil')
    if rl not in ('nil', ''):
        vals['retract_length'] = float(rl)
    if float(cfg.get('chamber_temperature') or 0) > 0:
        vals['chamber_temp'] = int(float(cfg['chamber_temperature']))
    return vals


def norm(s):
    return re.sub(r'\s+', ' ', (s or '').strip().lower())


def cmd_import(sm, a):
    known = {k for k, *_ in fields()}
    have = {f['key'] for f in sm.call('GET', '/field/filament')}
    if not a.apply or known - have:
        missing = known - have
        if missing and a.apply:
            sys.exit('spoolman_tuning: run "setup" first (missing fields: %s)' % ', '.join(sorted(missing)))
    spool_fils = sm.call('GET', '/filament')
    by_name = {}
    for f in spool_fils:
        by_name.setdefault(norm(f.get('name')), f)
        vendor = (f.get('vendor') or {}).get('name')
        if vendor:
            by_name.setdefault(norm('%s %s' % (vendor, f.get('name'))), f)
    unmatched = []
    for name, cfg in sorted(bundle_filaments(a.bundle).items()):
        if name.startswith('--'):
            continue
        f = by_name.get(norm(name))
        vals = values_from_bundle(cfg)
        if f is None:
            unmatched.append(name)
            continue
        print('%s -> Spoolman filament %d "%s": %s' % (name, f['id'], f.get('name'),
              ', '.join('%s=%s' % kv for kv in sorted(vals.items()))))
        if a.apply:
            sm.call('PATCH', '/filament/%d' % f['id'], {'extra': {k: json.dumps(v) for k, v in vals.items()}})
    for n in unmatched:
        print('NO MATCH in Spoolman for "%s": add it to Spoolman (or rename it) and run again' % n)
    print('spoolman_tuning: %s' % ('written' if a.apply else 'nothing written (add --apply)'))


def cmd_show(sm, a):
    for f in sm.call('GET', '/filament'):
        extra = {k: json.loads(v) for k, v in (f.get('extra') or {}).items() if v not in (None, '')}
        print('%3d %-40s %s' % (f['id'], f.get('name'), ' '.join('%s=%s' % kv for kv in sorted(extra.items()))))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', default='http://localhost:7912', help='Spoolman URL')
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('setup')
    s = sub.add_parser('set')
    s.add_argument('--spool', type=int, required=True)
    s.add_argument('--field', required=True)
    s.add_argument('--value', required=True)
    i = sub.add_parser('import-bundle')
    i.add_argument('bundle')
    i.add_argument('--apply', action='store_true')
    sub.add_parser('show')
    a = ap.parse_args()
    sm = Spoolman(a.url)
    {'setup': cmd_setup, 'set': cmd_set, 'import-bundle': cmd_import, 'show': cmd_show}[a.cmd](sm, a)


if __name__ == '__main__':
    main()
