#!/usr/bin/env python3
"""Load the config the way Klipper does and compile every template.

    python3 tools/klipper_load_check.py --klipper ~/klipper

Uses Klipper's own config reader (klippy/configfile.py), so comment stripping,
includes and option merging are exactly Klipper's; then, like
klippy/extras/gcode_macro.py, it compiles each [gcode_macro]/[delayed_gcode]
template in Klipper's Jinja environment and parses each variable_* with
ast.literal_eval. Klipper stops at the first such error and won't start; this
lists all of them. It does not run the macros (tools/macro_sim does that).
"""

import argparse
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTOSAVE = '#*# <---------------------- SAVE_CONFIG ---------------------->'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--klipper', required=True, help='a Klipper checkout (its klippy/ is used)')
    ap.add_argument('--root', default=ROOT)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(os.path.expanduser(a.klipper), 'klippy'))
    import configfile
    import jinja2

    path = os.path.join(a.root, 'printer.cfg')
    data = open(path).read()
    data = data.split(AUTOSAVE)[0]
    reader = configfile.ConfigFileReader()
    missing = []
    real_read = reader.read_config_file

    def read(filename):                 # Happy Hare's links into its install dir exist only on the Pi
        if not os.path.exists(filename):
            missing.append(os.path.relpath(filename, a.root))
            return ''
        return real_read(filename)
    reader.read_config_file = read
    fc = reader.build_fileconfig_with_includes(data, path)
    env = jinja2.Environment('{%', '%}', '{', '}')      # as gcode_macro.PrinterGCodeMacro
    problems, count = [], 0
    for section in fc.sections():
        kind = section.split()[0]
        if kind not in ('gcode_macro', 'delayed_gcode'):
            continue
        for opt in fc.options(section):
            value = fc.get(section, opt)
            if opt == 'gcode':
                count += 1
                try:
                    env.from_string(value)
                except jinja2.TemplateSyntaxError as e:
                    lines = value.split('\n')
                    near = lines[e.lineno - 1].strip()[:100] if e.lineno and e.lineno <= len(lines) else ''
                    problems.append('[%s] gcode line %s: %s  (%s)' % (section, e.lineno, e.message, near))
            elif opt.startswith('variable_'):
                try:
                    ast.literal_eval(value)
                except Exception as e:
                    problems.append('[%s] %s is not a literal Klipper can read: %s' % (section, opt, e))
    for m in missing:
        print('skipped (not here, e.g. a link into the Happy Hare install):', m)
    for p in problems:
        print('PROBLEM:', p)
    print('%d problem(s)' % len(problems) if problems else 'OK: %d templates compile as Klipper loads them' % count)
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
