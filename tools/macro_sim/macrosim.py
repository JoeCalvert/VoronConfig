"""Tiny Klipper macro simulator: renders our gcode_macro templates and expands
calls to other macros of ours, producing the primitive command sequence."""
import ast, glob, os, re, shlex, sys, copy
try:
    import jinja2       # only needed to render; parse_files() (used by check_deps) works without it
except ImportError:
    jinja2 = None

class D(dict):
    def __getattr__(s, k):
        try: return s[k]
        except KeyError: raise AttributeError(k)
def wrap(o):
    if isinstance(o, dict): return D({k: wrap(v) for k, v in o.items()})
    if isinstance(o, list): return [wrap(v) for v in o]
    return o

def parse_files(root):
    """Return {macro_name_upper: {'gcode': str, 'vars': {..}}} for every
    [gcode_macro] reached from printer.cfg (Klipper merge semantics)."""
    seen = []; secs = {}
    def walk(p):
        p = os.path.normpath(p)
        if p in seen or not os.path.isfile(p): return
        seen.append(p); base = os.path.dirname(p)
        cur = None; key = None
        for raw in open(p, errors='replace').read().split('\n'):
            if raw.startswith('#*#'): break
            # Klipper (configfile.py) cuts every line at its first '#', even
            # inside quotes; ';' starts a comment only after whitespace.
            raw = raw.split('#')[0]
            hdr = raw.split('#')[0].strip()
            # Indented lines continue the previous option, even if they start with '['
            m = re.match(r'^\[([^\]]+)\]', hdr) if raw[:1] not in (' ', '\t') else None
            if m:
                n = m.group(1).strip()
                if n.startswith('include '):
                    for f in sorted(glob.glob(os.path.join(base, n[8:].strip()))): walk(f)
                    cur = None
                else:
                    cur = secs.setdefault(n, {}); key = None
                continue
            if cur is None: continue
            if raw[:1] in (' ', '\t') and key is not None:
                cur[key] += '\n' + raw; continue
            s = re.sub(r'(^|\s)[#;].*$', '', raw)
            m = re.match(r'^([A-Za-z_0-9]+)\s*[:=]\s*(.*)$', s)
            if m:
                key = m.group(1).lower(); cur[key] = m.group(2)
            elif not raw.strip() or raw.lstrip().startswith(';'):
                pass
    walk(os.path.join(root, 'printer.cfg'))
    macros = {}
    for n, opts in secs.items():
        if n.startswith('gcode_macro '):
            vars_ = {}
            for k, v in opts.items():
                if k.startswith('variable_'):
                    try: vars_[k[9:]] = ast.literal_eval(v.strip())
                    except Exception: vars_[k[9:]] = v.strip()
            body = opts.get('gcode', '')
            # strip config comments like Klipper does
            lines = []
            for l in body.split('\n'):
                l2 = re.sub(r'(^|\s)[#;].*$', '', l)
                lines.append(l2)
            macros[n[12:].strip().upper()] = {'gcode': '\n'.join(lines), 'vars': vars_, 'opts': opts}
    return macros, secs

ENV = jinja2.Environment('{%', '%}', '{', '}', extensions=['jinja2.ext.do']) if jinja2 else None

class Sim:
    def __init__(self, root, state):
        self.macros, self.secs = parse_files(root)
        self.state = state  # extra printer objects
        self.out = []
    def printer(self):
        p = D(copy.deepcopy(self.state))
        # printer.configfile comes from the real config files, so a macro that
        # reads a section the printer doesn't have fails here as it would there.
        # The scenario state can override individual values.
        def typed(v):
            v = v.strip()
            if v.lower() in ('true', 'false'): return v.lower() == 'true'
            try: return int(v)
            except ValueError: pass
            try: return float(v)
            except ValueError: return v
        real_cfg = {s: {k: v.strip() for k, v in o.items()} for s, o in self.secs.items()
                    if not s.startswith(('gcode_macro ', 'include '))}
        real_set = {s: {k: typed(v) for k, v in o.items()} for s, o in real_cfg.items()}
        cf = p.get('configfile', D())
        for key, real in (('config', real_cfg), ('settings', real_set)):
            merged = copy.deepcopy(real)
            for s, o in (cf.get(key) or {}).items():
                merged.setdefault(s, {}).update(o)
            cf[key] = wrap(merged)
        p['configfile'] = cf
        for n, m in self.macros.items():
            p['gcode_macro ' + n] = wrap(m['vars'])
            p['gcode_macro ' + n.lower()] = p['gcode_macro ' + n]
        return p
    def run(self, line, depth=0):
        parts = line.strip().split(None, 1)
        if not parts: return
        cmd = parts[0].upper(); rest = parts[1] if len(parts) > 1 else ''
        if cmd == 'SET_GCODE_VARIABLE':
            kv = dict(re.findall(r'(\w+)=("[^"]*"|\'[^\']*\'|\S+)', rest))
            v = kv['VALUE']
            try: val = ast.literal_eval(v)
            except Exception: val = v
            if isinstance(val, str):
                try: val = ast.literal_eval(val)
                except Exception: pass
            self.macros[kv['MACRO'].upper()]['vars'][kv['VARIABLE'].lower()] = val
        if cmd in self.macros and depth < 20:
            params = {k.upper(): v.strip('"\'') for k, v in re.findall(r'(\w+)=("[^"]*"|\'[^\']*\'|\S+)', rest)}
            def raise_error(msg): raise RuntimeError(msg)
            t = ENV.from_string(self.macros[cmd]['gcode'])
            txt = t.render(params=params, rawparams=rest, printer=self.printer(),
                           action_raise_error=raise_error, action_respond_info=lambda m: '',
                           action_call_remote_method=lambda m, **kw: 'REMOTE %s %s' % (m, sorted(kw.items())))
            self.out.append(('  ' * depth) + '> ' + cmd + (' ' + rest if rest else ''))
            for l in txt.split('\n'):
                if l.strip(): self.run(l, depth + 1)
        else:
            self.out.append(('  ' * depth) + line.strip())
    def primitives(self):
        return [l.strip() for l in self.out if not l.strip().startswith('> ')]
