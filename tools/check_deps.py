#!/usr/bin/env python3
"""Check what our macros use from other projects against the list in
macros/system/dependencies.cfg, and optionally against a Happy Hare source tree.

    python3 tools/check_deps.py                         # list is complete?
    python3 tools/check_deps.py --happy-hare ~/Happy-Hare  # and still exists?

Run the second form on the Pi after updating Happy Hare (before restarting
Klipper). It exits non-zero if anything is wrong; docs/updating.md says what
to do next.
"""
import argparse, ast, glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUR_DIRS = ('macros', 'config')
# Commands from other projects start with one of these. Anything with a
# leading underscore is a project's internal macro, which we must not call.
PLUGIN_PREFIXES = ('MMU_', 'BLOBIFIER', 'BEACON_')
INTERNAL_PREFIXES = ('_MMU', '_BLOBIFIER', '_BEACON')
SHAKETUNE = {'AXES_MAP_CALIBRATION', 'AXES_SHAPER_CALIBRATION', 'COMPARE_BELTS_RESPONSES',
             'CREATE_VIBRATIONS_PROFILE', 'EXCITATE_AXIS_AT_FREQ'}


def sections(path):
    """Yield (section, {option: value}) from one Klipper config file."""
    cur, key, opts = None, None, {}
    for raw in open(path, errors='replace').read().split('\n'):
        if raw.startswith('#*#'):
            break
        m = re.match(r'^\[([^\]]+)\]', raw)
        if m:
            if cur:
                yield cur, opts
            cur, key, opts = m.group(1).strip(), None, {}
            continue
        if cur is None:
            continue
        if raw[:1] in (' ', '\t') and key:
            opts[key] += '\n' + re.sub(r'(^|\s)[#;].*$', '', raw)
            continue
        m = re.match(r'^([A-Za-z_0-9]+)\s*[:=]\s*(.*)$', re.sub(r'(^|\s)[#;].*$', '', raw))
        if m:
            key = m.group(1).lower()
            opts[key] = m.group(2)
    if cur:
        yield cur, opts


def our_macros():
    macros = {}
    for d in OUR_DIRS:
        for p in glob.glob(os.path.join(ROOT, d, '**', '*.cfg'), recursive=True):
            for name, opts in sections(p):
                if name.startswith('gcode_macro '):
                    macros[name[12:].strip().upper()] = (opts, os.path.relpath(p, ROOT))
    return macros


def used(macros):
    """What our macros use: commands, printer.mmu fields, Happy Hare variables."""
    cmds, fields, settings, internal, params = {}, {}, {}, {}, {}
    for name, (opts, path) in macros.items():
        body = opts.get('gcode', '')
        where = '%s (%s)' % (name, path)
        # Commands: the first word of each line, plus ACTION=... in dialog buttons.
        words = [l.strip().split()[0] for l in body.split('\n')
                 if l.strip() and not l.strip().startswith('{')]
        words += [w.strip('"\'') for w in re.findall(r'ACTION=("[^"]+"|\S+)', body)]
        words = [w.split()[0].upper() for w in words if w.strip('"\'')]
        for w in words:
            if w in macros:
                continue
            if w.startswith(INTERNAL_PREFIXES):
                internal.setdefault(w, where)
            elif w.startswith(PLUGIN_PREFIXES) or w in SHAKETUNE:
                cmds.setdefault(w, where)
        # printer.mmu fields (directly, or through a variable named mmu).
        for f in re.findall(r'printer\.mmu\.(\w+)|(?<![\w.])mmu\.(\w+)', body):
            f = f[0] or f[1]
            if f not in ('get',):
                fields.setdefault(f, where)
        # Happy Hare [mmu] parameters read from printer.configfile.settings.mmu.
        for f in re.findall(r'settings\.mmu(?:\|default\(\{\}\)\))?\.(\w+)', body):
            params.setdefault(f, where)
        # Happy Hare / Blobifier variables read through an alias.
        for alias, macro in re.findall(r"set (\w+) = printer\[['\"]gcode_macro (_(?:MMU|BLOBIFIER)\w+)['\"]\]", body):
            for v in re.findall(r'(?<![\w.])%s\.(\w+)' % alias, body):
                settings.setdefault((macro, v), where)
    return cmds, fields, settings, internal, params


def listed():
    for p in glob.glob(os.path.join(ROOT, 'macros', 'system', 'dependencies.cfg')):
        for name, opts in sections(p):
            if name == 'gcode_macro _DEPENDENCIES':
                get = lambda k: ast.literal_eval(opts['variable_' + k].strip())
                return dict(commands=get('commands'), mmu_fields=get('mmu_fields'),
                            hooks=get('hooks'), settings=get('settings'), params=get('mmu_params'),
                            tested=get('happy_hare_tested'))
    sys.exit('macros/system/dependencies.cfg: no _DEPENDENCIES macro')


def happy_hare_surface(hh):
    """Commands, status fields, macro variables and version from a Happy Hare tree."""
    py = ''.join(open(p, errors='replace').read()
                 for p in glob.glob(os.path.join(hh, 'extras', '**', '*.py'), recursive=True))
    cmds = set(re.findall(r'CMD\s*=\s*"([A-Z_0-9]+)"', py))
    cmds |= set(re.findall(r"register_command\(\s*['\"]([A-Z_0-9]+)['\"]", py))
    fields = set(re.findall(r"^\s*'(\w+)'\s*:", py, re.M))
    params = set(re.findall(r"ParamSpec\(\s*'(\w+)'", py))
    variables = {}
    for p in glob.glob(os.path.join(hh, 'config', '**', '*.cfg'), recursive=True):
        for name, opts in sections(p):
            if name.startswith('gcode_macro '):
                m = name[12:].strip().upper()
                cmds.add(m)
                variables.setdefault(m, set()).update(k[9:] for k in opts if k.startswith('variable_'))
    m = re.search(r'VERSION\s*=\s*"([\d.]+)"', py)
    return cmds, fields, params, variables, (m.group(1) if m else '?')


DIALOG_ARG = re.compile(r'^\s*_(?:DIALOG\w*|CAL_DONE)\b.*?\b(MSG|LABEL)="(.*)"')


def dialog_text_problems():
    """Dialog text reaches Klipper as a G-code line, where ; and # start a comment and
    action:prompt treats | as a separator, so any of them cuts the dialog short."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'macros', '**', '*.cfg'), recursive=True)):
        for n, line in enumerate(open(path), 1):
            m = DIALOG_ARG.match(line)
            if not m:
                continue
            text = re.sub(r'\{[^{}]*\}', '', m.group(2))  # Jinja is checked when it runs
            bad = sorted(set(text) & set(';#*|'))
            if bad:
                out.append('%s:%d dialog %s contains %s' % (os.path.relpath(path, ROOT), n, m.group(1), ' '.join(bad)))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--happy-hare', help='path to a Happy Hare checkout (e.g. ~/Happy-Hare)')
    a = ap.parse_args()
    problems = []
    cmds, fields, settings, internal, params = used(our_macros())
    deps = listed()

    for c, where in sorted(internal.items()):
        problems.append('%s calls %s, another project\'s internal macro. Use a public command or hook instead' % (where, c))
    for c, where in sorted(cmds.items()):
        if c not in deps['commands']:
            problems.append('%s uses %s, which is missing from _DEPENDENCIES commands' % (where, c))
    for f, where in sorted(fields.items()):
        if f not in deps['mmu_fields']:
            problems.append('%s uses printer.mmu.%s, which is missing from _DEPENDENCIES mmu_fields' % (where, f))
    for f, where in sorted(params.items()):
        if f not in deps['params']:
            problems.append('%s reads the Happy Hare parameter %s, which is missing from _DEPENDENCIES mmu_params' % (where, f))
    known = {tuple(s) for s in deps['settings']} | {(h[0], h[1]) for h in deps['hooks']}
    for s, where in sorted(settings.items()):
        if s not in known:
            problems.append('%s reads %s.%s, which is missing from _DEPENDENCIES settings' % (where, s[0], s[1]))

    problems += dialog_text_problems()

    if a.happy_hare:
        hh = os.path.expanduser(a.happy_hare)
        hcmds, hfields, hparams, hvars, version = happy_hare_surface(hh)
        print('Happy Hare %s at %s' % (version, hh))
        for c in deps['commands']:
            if c.startswith(('MMU_', 'BLOBIFIER')) and c not in hcmds:
                problems.append('Happy Hare no longer has the command %s' % c)
        for f in deps['mmu_fields']:
            if f not in hfields:
                problems.append('Happy Hare no longer reports printer.mmu.%s' % f)
        for f in deps['params']:
            if f not in hparams:
                problems.append('Happy Hare no longer has the parameter %s' % f)
        for macro, var in [tuple(s) for s in deps['settings']] + [(h[0], h[1]) for h in deps['hooks']]:
            if var not in hvars.get(macro.upper(), set()):
                problems.append('Happy Hare no longer has the variable %s.%s' % (macro, var))
        if '.'.join(version.split('.')[:2]) != deps['tested']:
            print('Note: these macros were last checked against Happy Hare %s. If everything '
                  'above passes, update happy_hare_tested in macros/system/dependencies.cfg.' % deps['tested'])

    for p in problems:
        print('PROBLEM:', p)
    print('%d problem(s)' % len(problems) if problems else
          'OK: %d commands, %d mmu fields, %d mmu parameters, %d settings/hooks' %
          (len(deps['commands']), len(deps['mmu_fields']), len(deps['params']), len(deps['settings']) + len(deps['hooks'])))
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
