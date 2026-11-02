#!/usr/bin/env python3
"""Deploy this repository onto the printer, then restart and check it.

Run on the Pi, from a clone of this repository (not from the live config):

    git clone https://github.com/JoeCalvert/VoronConfig ~/VoronConfig   # once
    python3 ~/VoronConfig/tools/deploy.py            # show the plan, ask, deploy
    python3 ~/VoronConfig/tools/deploy.py --dry-run  # only show the plan
    python3 ~/VoronConfig/tools/deploy.py --rollback ~/printer_data/config_deploys/<file>.tar.gz

What it does:
 1. git pull --ff-only (unless --no-pull), and refuses a clone with local changes.
 2. Refuses while a print is running.
 3. Runs tools/check_deps.py against ~/Happy-Hare (if present).
 4. Shows what will change in ~/printer_data/config:
    - files added or changed;
    - files removed: ones in our own folders (macros, config, tools, docs, ukam)
      that the repository no longer has. Klipper includes those folders by
      wildcard, so a stale copy of a moved file would be loaded twice.
 5. Backs the whole config folder up to ~/printer_data/config_deploys/ first.
 6. Copies the files. The printer keeps what it owns:
    - the SAVE_CONFIG block at the end of printer.cfg (Beacon model, etc.);
    - KlipperScreen.conf's auto-generated section;
    - mmu/mmu_vars.cfg (Happy Hare and save_variables state);
    - ShakeTune_results.
 7. Restarts Klipper (and Moonraker / KlipperScreen if their config changed),
    then runs CHECK_CONFIG and prints its result.
 8. Runs klipper-backup (if installed) so the backup matches what was
    deployed, but only if it backs up to a different repository. Pointed at
    this one it would damage it: it skips symbolic links (so Happy Hare's
    mmu/macros links would be deleted), replaces .gitignore with its own, and
    with the usual backupPaths it writes everything under printer_data/config/.
"""
import argparse, datetime, filecmp, json, os, shutil, subprocess, sys, tarfile, time, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OURS = ('macros/', 'config/', 'tools/', 'docs/', 'ukam/')     # folders this repo owns completely
PRINTER_OWNS = ('mmu/mmu_vars.cfg', 'ShakeTune_results/')       # never overwritten
GENERATED_MARKERS = {'printer.cfg': '#*# <---------------------- SAVE_CONFIG',
                     'KlipperScreen.conf': '#~# --- Do not edit below this line'}
RESTARTS = {'moonraker.conf': 'moonraker', 'KlipperScreen.conf': 'KlipperScreen',
            'mmu_klipperscreen.conf': 'KlipperScreen', 'crowsnest.conf': 'crowsnest'}


def git(*args):
    return subprocess.run(['git', '-C', ROOT] + list(args), check=True, capture_output=True, text=True).stdout


def api(base, path, method='GET', timeout=10):
    req = urllib.request.Request(base + path, method=method, data=b'' if method == 'POST' else None)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def merged(path, src, dst):
    """Repository content, but keep the printer's auto-generated block."""
    data = open(src, encoding='utf-8', errors='surrogateescape').read()
    marker = GENERATED_MARKERS.get(path)
    if marker and os.path.isfile(dst):
        live = open(dst, encoding='utf-8', errors='surrogateescape').read()
        if marker in live:
            data = data.split(marker)[0] + live[live.index(marker):]
    return data


def plan(target):
    tracked = [p for p in git('ls-files', '-z').split('\0') if p]
    tracked = [p for p in tracked if not p.startswith(PRINTER_OWNS)]
    add, change = [], []
    for p in tracked:
        src, dst = os.path.join(ROOT, p), os.path.join(target, p)
        if os.path.islink(src):
            same = os.path.islink(dst) and os.readlink(dst) == os.readlink(src)
        elif p in GENERATED_MARKERS:
            same = os.path.isfile(dst) and open(dst, encoding='utf-8', errors='surrogateescape').read() == merged(p, src, dst)
        else:
            same = os.path.isfile(dst) and not os.path.islink(dst) and filecmp.cmp(src, dst, shallow=False)
        if not os.path.lexists(dst):
            add.append(p)
        elif not same:
            change.append(p)
    keep = set(tracked)
    remove = []
    for d in OURS:
        for dirpath, _, files in os.walk(os.path.join(target, d)):
            for f in files:
                rel = os.path.relpath(os.path.join(dirpath, f), target)
                if rel not in keep and '__pycache__' not in rel:
                    remove.append(rel)
    return tracked, add, change, sorted(remove)


def backup(target):
    folder = os.path.join(os.path.dirname(target.rstrip('/')), 'config_deploys')
    os.makedirs(folder, exist_ok=True)
    name = os.path.join(folder, datetime.datetime.now().strftime('config-%Y%m%d-%H%M%S.tar.gz'))
    with tarfile.open(name, 'w:gz') as t:
        t.add(target, arcname='config')
    return name


def install(target, files, remove):
    for p in files:
        src, dst = os.path.join(ROOT, p), os.path.join(target, p)
        os.makedirs(os.path.dirname(dst) or '.', exist_ok=True)
        if os.path.lexists(dst) and (os.path.islink(dst) or os.path.islink(src)):
            os.remove(dst)
        if os.path.islink(src):
            os.symlink(os.readlink(src), dst)
        elif p in GENERATED_MARKERS:
            data = merged(p, src, dst)   # read the printer's block before opening for writing
            with open(dst, 'w', encoding='utf-8', errors='surrogateescape', newline='') as f:
                f.write(data)
        else:
            shutil.copy2(src, dst)
    for p in remove:
        os.remove(os.path.join(target, p))


def restart_and_check(base, changed):
    services = sorted({RESTARTS[p] for p in changed if p in RESTARTS})
    print('Restarting Klipper...')
    api(base, '/printer/restart', 'POST')
    for _ in range(60):
        time.sleep(2)
        try:
            if api(base, '/printer/info')['result']['state'] == 'ready':
                break
        except Exception:
            pass
    else:
        print('Klipper did not come back ready. Check the console / klippy.log.')
        return False
    time.sleep(7)  # the startup check runs 5 s after Klipper starts
    since = time.time()
    api(base, '/printer/gcode/script?script=CHECK_CONFIG', 'POST', timeout=60)
    lines = api(base, '/server/gcode_store?count=100')['result']['gcode_store']
    report = [l['message'] for l in lines if l['time'] >= since - 1 and 'CHECK_CONFIG' in l['message']]
    print('\n'.join(report) or 'CHECK_CONFIG printed nothing; check the console.')
    for s in services:
        print('Restarting %s (its config changed)...' % s)
        try:
            api(base, '/machine/services/restart?service=%s' % s, 'POST')
        except Exception as e:
            print('  could not restart %s: %s' % (s, e))
    return not any('error' in r.lower() for r in report)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--target', default=os.path.expanduser('~/printer_data/config'))
    ap.add_argument('--moonraker', default='http://localhost:7125')
    ap.add_argument('--happy-hare', default=os.path.expanduser('~/Happy-Hare'))
    ap.add_argument('--dry-run', action='store_true', help='only show what would change')
    ap.add_argument('--yes', action='store_true', help="don't ask before deploying")
    ap.add_argument('--no-pull', action='store_true')
    ap.add_argument('--no-restart', action='store_true')
    ap.add_argument('--force', action='store_true', help='deploy even if check_deps finds problems')
    ap.add_argument('--rollback', metavar='TAR', help='restore a backup made by an earlier deploy')
    a = ap.parse_args()
    target = os.path.abspath(a.target)

    if a.rollback:
        if not os.path.isfile(a.rollback):
            sys.exit('No such backup: %s' % a.rollback)
        shutil.rmtree(target)
        with tarfile.open(a.rollback) as t:
            try:
                t.extractall(os.path.dirname(target), filter='tar')
            except TypeError:   # Python without extraction filters
                t.extractall(os.path.dirname(target))
        print('Restored', a.rollback, 'to', target, '- restart Klipper to load it.')
        return

    if os.path.realpath(target).startswith(os.path.realpath(ROOT)) or os.path.realpath(ROOT).startswith(os.path.realpath(target)):
        sys.exit('Run this from a separate clone of the repository, not from the live config folder.')
    if git('status', '--porcelain', '--untracked-files=no').strip():
        sys.exit('The clone at %s has local changes. Commit or discard them first.' % ROOT)
    if not a.no_pull:
        print(git('pull', '--ff-only').strip())
    print('Deploying %s' % git('log', '-1', '--format=%h %s').strip())

    if not a.dry_run and not a.no_restart:
        try:
            state = api(a.moonraker, '/printer/objects/query?print_stats')['result']['status']['print_stats']['state']
        except Exception as e:
            sys.exit('Could not reach Moonraker at %s (%s). Use --no-restart to deploy without it.' % (a.moonraker, e))
        if state in ('printing', 'paused'):
            sys.exit('A print is %s. Deploy when it has finished.' % state)

    deps = [sys.executable, os.path.join(ROOT, 'tools', 'check_deps.py')]
    if os.path.isdir(a.happy_hare):
        deps += ['--happy-hare', a.happy_hare]
    r = subprocess.run(deps)
    if r.returncode and not a.force:
        sys.exit('check_deps found problems (above). Fix them, or use --force.')

    tracked, add, change, remove = plan(target)
    for title, items in (('Add', add), ('Change', change), ('Remove (no longer in the repository)', remove)):
        if items:
            print('\n%s:\n  %s' % (title, '\n  '.join(items)))
    if not (add or change or remove):
        print('\nThe printer already has this version.')
        return
    if a.dry_run:
        return
    if not a.yes and input('\nDeploy? [y/N] ').strip().lower() != 'y':
        return

    print('\nBackup:', backup(target))
    install(target, add + change, remove)
    print('Copied %d file(s), removed %d.' % (len(add) + len(change), len(remove)))

    if a.no_restart:
        print('Not restarting. Restart Klipper, then run CHECK_CONFIG.')
        return
    ok = restart_and_check(a.moonraker, add + change)
    if not ok:
        print('CHECK_CONFIG reported errors. Roll back with --rollback <backup above> if needed.')
    else:
        klipper_backup()


def klipper_backup():
    kb = os.path.expanduser('~/klipper-backup')
    env = os.path.join(kb, '.env')
    if not os.path.isfile(env):
        return
    conf = dict(l.split('=', 1) for l in open(env).read().splitlines() if '=' in l and not l.lstrip().startswith('#'))
    repo = conf.get('github_repository', '').strip().strip('"')
    remote = git('remote', 'get-url', 'origin').strip()
    if repo and remote.rstrip('/').removesuffix('.git').lower().endswith('/' + repo.lower()):
        print('\nklipper-backup backs up to this repository (%s), so it was not run. It would delete the '
              'mmu/macros symbolic links, replace .gitignore and nest files under printer_data/config/. '
              'Point it at a separate repository (github_repository in ~/klipper-backup/.env).' % repo)
        return
    print('\nRunning klipper-backup (to %s) so the backup matches what was deployed...' % (repo or '?'))
    subprocess.run(['bash', os.path.join(kb, 'script.sh'), '-c', 'Deploy %s' % git('log', '-1', '--format=%h').strip()])


if __name__ == '__main__':
    main()
