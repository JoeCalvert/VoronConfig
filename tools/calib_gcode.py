#!/usr/bin/env python3
"""Write a pressure advance or extrusion multiplier test print for this printer.

Run on the printer by the RETUNE dialogs (RUN_SHELL_COMMAND CMD=calib_gcode),
which then start the file. It can also be run by hand:

    python3 tools/calib_gcode.py pa --out ~/printer_data/gcodes/calibration \\
        --name pa_test --tool 0 --nozzle 0.6 --hotend 250 --bed 105 \\
        --start 0 --step 0.004 --count 21

The file uses this printer's own start and end sequence, the same as a
PrusaSlicer file (docs/slicer.md): START_PRINT (home, heat, level, Beacon
contact Z, adaptive mesh), loading the chosen tool through Happy Hare,
POST_START_PRINT, and MMU_END + END_PRINT. EXCLUDE_OBJECT_DEFINE tells the
adaptive mesh where the test is. Retraction is the printer's firmware
retraction (G10/G11).

Patterns
  pa  Andrew Ellis's pattern method: nested chevrons, one pressure advance
      value each, printed at your perimeter speed and acceleration. Pick the
      one whose corner is sharpest with no gap or bulge at the line ends.
  em  Ellis's extrusion multiplier method, as solid squares: each square at
      a different multiplier (M221). Pick the one whose top surface is smooth
      with no gaps and no ridges.

Each pattern is numbered on the first layer (1 = leftmost); the file's
header and the result dialog list the values.

Extrusion widths and amounts use PrusaSlicer's flow formula, so the
multiplier you pick transfers directly to the PrusaSlicer filament profile.
"""

import argparse
import glob
import math
import os
import sys

FILAMENT_DIAMETER = 1.75
BED_CENTRE = (175.0, 175.0)
BED_MIN, BED_MAX = 10.0, 340.0      # keep everything well inside the plate

# 7-segment digits: segments a b c d e f g
SEGMENTS = {
    '0': 'abcdef', '1': 'bc', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
    '5': 'afgcd', '6': 'afgedc', '7': 'abc', '8': 'abcdefg', '9': 'abcdfg',
}


class Writer:
    """Collects G-code lines and tracks position, extrusion and bounds."""

    def __init__(self, width, height, flow_mult=1.0):
        self.lines = []
        self.width = width
        self.height = height
        self.flow_mult = flow_mult
        self.x = self.y = None
        self.z = 0.0
        self.retracted = False
        self.hopped = False
        self.min = [1e9, 1e9]
        self.max = [-1e9, -1e9]

    def add(self, line):
        self.lines.append(line)

    def e_per_mm(self, width=None, height=None):
        w = width or self.width
        h = height or self.height
        area = h * (w - h * (1 - math.pi / 4))             # PrusaSlicer's flow model
        return area / (math.pi * (FILAMENT_DIAMETER / 2) ** 2)

    def _track(self, x, y):
        self.min = [min(self.min[0], x), min(self.min[1], y)]
        self.max = [max(self.max[0], x), max(self.max[1], y)]

    def layer(self, z):
        self.z = z
        if self.x is not None:              # the first layer lowers after the first travel
            self.add('G1 Z%.3f F600' % z)

    def travel(self, x, y, speed):
        dist = math.hypot(x - self.x, y - self.y) if self.x is not None else 0
        if dist > 2 and not self.retracted:
            self.add('G10')
            self.retracted = True
        if dist > 5:                        # hop over what's already printed
            self.add('G1 Z%.3f F1200' % (self.z + 0.4))
            self.hopped = True
        first = self.x is None
        if first:
            self.add('G1 Z%.3f F600' % (self.z + 2))
        self.add('G0 X%.3f Y%.3f F%d' % (x, y, speed * 60))
        if first:
            self.add('G1 Z%.3f F600' % self.z)
        if self.hopped:
            self.add('G1 Z%.3f F1200' % self.z)
            self.hopped = False
        self.x, self.y = x, y

    def extrude(self, x, y, speed, width=None):
        if self.retracted:
            self.add('G11')
            self.retracted = False
        length = math.hypot(x - self.x, y - self.y)
        e = length * self.e_per_mm(width) * self.flow_mult
        self.add('G1 X%.3f Y%.3f E%.5f F%d' % (x, y, e, speed * 60))
        self._track(self.x, self.y)
        self._track(x, y)
        self.x, self.y = x, y

    def path(self, points, speed, travel_speed, width=None):
        self.travel(points[0][0], points[0][1], travel_speed)
        for x, y in points[1:]:
            self.extrude(x, y, speed, width)


def digit_strokes(text, x, y, height):
    """Line segments for text in 7-segment style, lower-left corner at x, y."""
    w = height * 0.5
    gap = w * 0.6
    strokes = []
    for ch in text:
        if ch == '.':
            strokes.append([(x, y), (x, y + height * 0.08)])
            x += gap
            continue
        segs = SEGMENTS[ch]
        top, mid, bot = y + height, y + height / 2, y
        pts = {
            'a': [(x, top), (x + w, top)], 'b': [(x + w, top), (x + w, mid)],
            'c': [(x + w, mid), (x + w, bot)], 'd': [(x + w, bot), (x, bot)],
            'e': [(x, bot), (x, mid)], 'f': [(x, mid), (x, top)],
            'g': [(x, mid), (x + w, mid)],
        }
        for s in 'afbgecd':
            if s in segs:
                strokes.append(pts[s])
        x += w + gap
    return strokes


def text_width(text, height):
    w = height * 0.5
    return sum((w * 0.6) if c == '.' else (w * 1.6) for c in text) - w * 0.6


def draw_label(g, text, cx, y, height, speed, travel):
    x = cx - text_width(text, height) / 2
    for stroke in digit_strokes(text, x, y, height):
        g.path(stroke, speed, travel)


def pa_pattern(a):
    nozzle = a.nozzle
    h = a.layer_height
    w = round(nozzle * 1.125, 3)
    g = Writer(w, h)
    count = a.count
    values = [round(a.start + i * a.step, 5) for i in range(count)]

    walls = 3
    side = 25.0                                   # leg length
    d = side * math.cos(math.radians(45))         # x depth and y half-height of a chevron
    wall_dx = w * math.sqrt(2)                    # nested lines w apart, measured perpendicular
    pitch = walls * wall_dx + 2.0
    width = d + (count - 1) * pitch + walls * wall_dx
    x0 = BED_CENTRE[0] - width / 2
    yc = BED_CENTRE[1]
    label_h = max(4.0, nozzle * 8)

    speed = min(a.speed, a.max_flow / (w * h))    # stay inside the hotend's flow
    first_speed = min(30.0, speed)
    travel = 250

    body = []
    for layer in range(a.layers):
        z = h * (layer + 1)
        body.append(';LAYER_CHANGE')
        body.append(';Z:%.3f' % z)
        g.lines = []
        g.layer(z)
        if layer == 1:
            g.add('M106 S%d' % a.fan)
        lspeed = first_speed if layer == 0 else speed
        if layer == 0:
            # anchor line under the patterns' ends, then numbers below
            g.path([(x0 - 3, yc - d - 3), (x0 + width + 3, yc - d - 3)], first_speed, travel)
            for i in range(count):
                if i % a.label_every == 0 or i == count - 1:
                    vx = x0 + i * pitch
                    draw_label(g, str(i + 1), vx + d, yc - d - 6 - label_h, label_h, 15, travel)
        for i, pa in enumerate(values):
            g.add('SET_PRESSURE_ADVANCE ADVANCE=%.4f' % pa)
            vx = x0 + i * pitch
            for j in range(walls):
                s = vx + j * wall_dx
                top, vertex, bottom = (s + d, yc + d), (s, yc), (s + d, yc - d)
                pts = [top, vertex, bottom] if j % 2 == 0 else [bottom, vertex, top]
                g.path(pts, lspeed, travel)
        body.extend(g.lines)

    header = ['; Pressure advance test (Ellis pattern method)',
              '; nozzle %.2f, line width %.3f, layer %.3f, speed %.0f mm/s, accel %d'
              % (nozzle, w, h, speed, a.accel)]
    header += ['; pattern %d: PA %.4f' % (i + 1, v) for i, v in enumerate(values)]
    return g, header, body


def em_pattern(a):
    nozzle = a.nozzle
    h = a.layer_height
    w = round(nozzle * 1.125, 3)
    count = a.count
    values = [round(a.start + i * a.step, 4) for i in range(count)]
    size = 30.0
    gap = 6.0
    total = count * size + (count - 1) * gap
    cols = count if total <= 300 else math.ceil(count / 2)
    rows = math.ceil(count / cols)
    width = cols * size + (cols - 1) * gap
    height = rows * size + (rows - 1) * (gap + 8)
    x0 = BED_CENTRE[0] - width / 2
    y0 = BED_CENTRE[1] - height / 2
    label_h = max(4.0, nozzle * 8)
    speed = min(a.speed, a.max_flow / (w * h))
    first_speed = min(30.0, speed)
    travel = 250

    g = Writer(w, h)
    body = []
    for layer in range(a.layers):
        z = h * (layer + 1)
        body.append(';LAYER_CHANGE')
        body.append(';Z:%.3f' % z)
        g.lines = []
        g.layer(z)
        if layer == 1:
            g.add('M106 S%d' % a.fan)
        lspeed = first_speed if layer == 0 else speed
        for i, em in enumerate(values):
            cx0 = x0 + (i % cols) * (size + gap)
            cy0 = y0 + (rows - 1 - i // cols) * (size + gap + 8)
            if layer == 0:
                draw_label(g, str(i + 1), cx0 + size / 2, cy0 - 2 - label_h, label_h, 15, travel)
            g.add('M221 S%.1f' % (em * 100))
            # two perimeters
            for p in range(2):
                o = w / 2 + p * w
                corners = [(cx0 + o, cy0 + o), (cx0 + size - o, cy0 + o),
                           (cx0 + size - o, cy0 + size - o), (cx0 + o, cy0 + size - o),
                           (cx0 + o, cy0 + o)]
                g.path(corners, lspeed, travel)
            # solid infill, alternating direction each layer
            inner = 2 * w
            lo, hi = inner + w / 2, size - inner - w / 2
            n = int((hi - lo) / w) + 1
            step = (hi - lo) / (n - 1)
            for k in range(n):
                t = lo + k * step
                if layer % 2 == 0:
                    a1, a2 = (cx0 + lo, cy0 + t), (cx0 + hi, cy0 + t)
                else:
                    a1, a2 = (cx0 + t, cy0 + lo), (cx0 + t, cy0 + hi)
                if k % 2:
                    a1, a2 = a2, a1
                if k == 0:
                    g.travel(a1[0], a1[1], travel)
                else:
                    g.extrude(a1[0], a1[1], lspeed)        # short connector keeps it continuous
                g.extrude(a2[0], a2[1], lspeed)
            g.add('M221 S100')
        body.extend(g.lines)

    header = ['; Extrusion multiplier test (Ellis method, solid squares)',
              '; nozzle %.2f, line width %.3f, layer %.3f, speed %.0f mm/s'
              % (nozzle, w, h, speed)]
    header += ['; square %d: EM %.3f' % (i + 1, v) for i, v in enumerate(values)]
    return g, header, body


def build(a):
    g, header, body = (pa_pattern if a.test == 'pa' else em_pattern)(a)
    lo, hi = g.min, g.max
    if lo[0] < BED_MIN or lo[1] < BED_MIN or hi[0] > BED_MAX or hi[1] > BED_MAX:
        sys.exit('calib_gcode: the test does not fit on the bed (%.0f,%.0f to %.0f,%.0f). '
                 'Use fewer patterns.' % (lo[0], lo[1], hi[0], hi[1]))
    m = 3
    poly = '[[%.1f,%.1f],[%.1f,%.1f],[%.1f,%.1f],[%.1f,%.1f]]' % (
        lo[0] - m, lo[1] - m, hi[0] + m, lo[1] - m, hi[0] + m, hi[1] + m, lo[0] - m, hi[1] + m)
    centre = '%.1f,%.1f' % ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)

    out = ['; generated by tools/calib_gcode.py for RETUNE'] + header + [
        '; tool T%d, hotend %d, bed %d, chamber %d' % (a.tool, a.hotend, a.bed, a.chamber),
        'EXCLUDE_OBJECT_DEFINE NAME=%s_test CENTER=%s POLYGON=%s' % (a.test, centre, poly),
        'M140 S%d' % a.bed,
        'START_PRINT BED=%d EXTRUDER=%d NOZZLE=%.2f CHAMBER=%d' % (a.bed, a.hotend, a.nozzle, a.chamber),
        'MMU_CHANGE_TOOL STANDALONE=1 RESTORE=0 TOOL=%d' % a.tool,
        'POST_START_PRINT',
        'SET_VELOCITY_LIMIT ACCEL=%d' % a.accel,
    ] + (['SET_PRESSURE_ADVANCE ADVANCE=%.4f' % a.pa] if a.pa is not None else []) + [
        'M107',
        'G90',
        'M83',
        'G92 E0',
        'EXCLUDE_OBJECT_START NAME=%s_test' % a.test,
    ] + body + [
        'EXCLUDE_OBJECT_END NAME=%s_test' % a.test,
        'M107',
        'SET_VELOCITY_LIMIT ACCEL=%d' % a.restore_accel,
        'M221 S100',
        'G10',
        'MMU_END',
        'END_PRINT',
        '_CAL_FILAMENT_RESULT',
    ]
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('test', choices=['pa', 'em'])
    ap.add_argument('--out', required=True, help='directory for the file (e.g. ~/printer_data/gcodes/calibration)')
    ap.add_argument('--name', required=True, help='file name, without .gcode')
    ap.add_argument('--tool', type=int, required=True)
    ap.add_argument('--nozzle', type=float, required=True)
    ap.add_argument('--hotend', type=int, required=True)
    ap.add_argument('--bed', type=int, required=True)
    ap.add_argument('--chamber', type=int, default=0)
    ap.add_argument('--start', type=float, required=True)
    ap.add_argument('--step', type=float, required=True)
    ap.add_argument('--count', type=int, required=True)
    ap.add_argument('--speed', type=float, default=100, help='mm/s, your perimeter speed')
    ap.add_argument('--accel', type=int, default=4000, help='mm/s², your perimeter acceleration')
    ap.add_argument('--restore-accel', type=int, required=True, help="the printer's max_accel, restored at the end")
    ap.add_argument('--max-flow', type=float, default=15, help='mm³/s; the speed is capped to stay under it')
    ap.add_argument('--pa', type=float, help='pressure advance for the EM test (the filament\'s PA result)')
    ap.add_argument('--fan', type=int, default=255, help='part fan 0-255 from layer 2')
    ap.add_argument('--layer-height', type=float)
    ap.add_argument('--layers', type=int)
    ap.add_argument('--label-every', type=int, default=5)
    ap.add_argument('--keep', type=int, default=4, help='old test files of this kind to keep')
    a = ap.parse_args()

    if not 0.2 <= a.nozzle <= 1.2:
        sys.exit('calib_gcode: nozzle %.2f mm is not plausible' % a.nozzle)
    if not 2 <= a.count <= 30:
        sys.exit('calib_gcode: count must be 2 to 30')
    if a.layer_height is None:
        a.layer_height = round(min(0.3, max(0.1, a.nozzle * 0.5)), 2)
    if a.layers is None:
        a.layers = 4 if a.test == 'pa' else max(6, int(round(2.4 / a.layer_height)))

    text = build(a)
    out = os.path.expanduser(a.out)
    os.makedirs(out, exist_ok=True)
    old = sorted(glob.glob(os.path.join(out, '%s_*.gcode' % a.test)), key=os.path.getmtime)
    for f in old[:max(0, len(old) - a.keep)]:
        os.remove(f)
    path = os.path.join(out, a.name + '.gcode')
    with open(path + '.tmp', 'w') as f:
        f.write(text)
    os.replace(path + '.tmp', path)
    print('calib_gcode: wrote %s' % path)


if __name__ == '__main__':
    main()
