#!/usr/bin/env python3
"""Work out how far a hand-drawn dog has to shrink to clear the windshield.

Rasterises the dog on its own, reads its real outline off the alpha channel,
then scales it about the window sill (so its relation to the beltline, and the
chest running off the bottom, stay as drawn) and slides it sideways as little
as possible until nothing pokes through the A-pillar, the B-pillar or the roof.
"""
import json
import os
import re
import subprocess
import sys

from dog import PLACE, collie

HERE = os.path.dirname(os.path.abspath(__file__))
R = 4                      # raster pixels per drawing unit
X0, Y0, W, H = -160, -150, 300, 280
MARGIN = 5.0

meta = json.load(open(f"{HERE}/dog-edit.json"))
(blx, bly), (tlx, tly), (trx, _), _ = [
    tuple(map(float, p.split(","))) for p in
    re.findall(r"(-?[\d.]+,-?[\d.]+)", meta["guide"])]
opt = meta["option"]
cx0, cy0, s0 = PLACE[opt]


def left_at(y):
    return tlx + (y - tly) / (bly - tly) * (blx - tlx)


# --- the dog's real outline, straight off a render -------------------------
open(f"{HERE}/_dogonly.svg", "w").write(
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{X0} {Y0} {W} {H}" '
    f'width="{W * R}" height="{H * R}">{collie(0, 0, 1)}</svg>')
subprocess.run(["magick", "-background", "none", f"{HERE}/_dogonly.svg",
                "-alpha", "extract", "-depth", "8", f"gray:{HERE}/_dogonly.raw"],
               check=True)
width, height = W * R, H * R
raw = open(f"{HERE}/_dogonly.raw", "rb").read()
assert len(raw) == width * height, (len(raw), width * height)

left_pts, right_pts = [], []
for row in range(height):
    y = Y0 + row / R
    if y > bly:                       # below the beltline: clipped on purpose
        continue
    line = raw[row * width:(row + 1) * width]
    first = next((c for c, v in enumerate(line) if v > 8), None)
    if first is not None:
        last = len(line) - 1 - next(c for c, v in enumerate(reversed(line)) if v > 8)
        left_pts.append((X0 + first / R, y))
        right_pts.append((X0 + last / R, y))
if not left_pts:
    sys.exit("nothing drawn above the beltline")
ytop = min(y for _, y in left_pts)

# --- largest scale about the sill that fits, with the smallest sideways nudge
k = 1.0
while k > 0.3:
    if bly + k * (ytop - bly) >= tly + MARGIN:
        lo = max(left_at(bly + k * (y - bly)) + MARGIN - k * x for x, y in left_pts)
        hi = min(trx - MARGIN - k * x for x, y in right_pts)
        if lo <= hi:
            dx = min(max(0.0, lo), hi)
            break
    k -= 0.005
else:
    sys.exit("could not fit the dog at any sane scale")

place = (round(cx0 + s0 * dx, 1),
         round(cy0 + s0 * bly * (1 - k), 1),
         round(s0 * k, 3))
print(f"as drawn: {(cx0, cy0, s0)}")
print(f"fitted:   {place}   (scaled to {k:.1%}, nudged {dx:+.1f} units)")

src = open(f"{HERE}/dog.py").read()
open(f"{HERE}/dog.py", "w").write(
    re.sub(r'PLACE = \{.*?\}', f'PLACE = {{"{opt}": {place}}}', src, count=1))
