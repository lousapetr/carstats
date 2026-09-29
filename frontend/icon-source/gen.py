#!/usr/bin/env python3
"""Generate three CarStats icon options (red car + border collie in the
windshield) plus their maskable variants and a comparison sheet."""
import os
import subprocess
import sys

from dog import collie

try:  # set when the dog came from a hand-edited SVG: keep it where it was drawn
    from dog import PLACE
except ImportError:
    PLACE = {}

HERE = os.path.dirname(os.path.abspath(__file__))
CHOSEN = "b"  # the body the app ships; a and c are kept as alternatives
RED, GLASS, LAMP, TIRE, HUB = "#dc2626", "#60a5fa", "#fef3c7", "#111827", "#6b7280"

# Silhouette samples used for fitting the dog into a windshield: points on its
# left edge (the muzzle, which must clear the raked A-pillar), on its right edge,
# the ear tip and the jaw (the lowest part that must stay above the beltline).
HULL_LEFT = [(-62, -4), (-56, 8), (-54, 16), (-40, 24), (-27, -20), (-21, -30), (-16, 30)]
HULL_RIGHT = [(35, -84), (43, -40), (54, -22), (65, 20)]
D_TOP, D_BOT = -84.0, 31.0




def fit_dog(pane, margin=6.0, smax=1.0):
    """Largest scale + placement keeping the dog's head inside a windshield quad
    given as (bottom-left, top-left, top-right, bottom-right). Points below the
    beltline are ignored -- the window clips the chest on purpose."""
    (blx, bly), (tlx, tly), (trx, _), (_, bry) = pane
    top, bottom, right = tly, min(bly, bry), trx

    def left_at(y):  # x of the raked A-pillar edge at height y
        if bly == tly:
            return max(blx, tlx)
        t = (y - tly) / (bly - tly)
        return tlx + t * (blx - tlx)

    s = smax
    while s > 0.2:
        cy = top - D_TOP * s + margin
        if cy + D_BOT * s <= bottom - margin:
            lo = max(left_at(cy + dy * s) - dx * s + margin
                     for dx, dy in HULL_LEFT if cy + dy * s <= bottom)
            hi = min(right - dx * s - margin
                     for dx, dy in HULL_RIGHT if cy + dy * s <= bottom)
            if lo <= hi:
                return (lo + hi) / 2, cy, s
        s -= 0.01
    raise ValueError("windshield too small for the dog")


def path(pane):
    (a, b, c, d) = pane
    return f"M {a[0]},{a[1]} L {b[0]},{b[1]} L {c[0]},{c[1]} L {d[0]},{d[1]} Z"


def wheels(cxs, cy, r, hub):
    return "\n".join(
        f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{TIRE}"/>\n'
        f'    <circle cx="{cx}" cy="{cy}" r="{hub}" fill="{HUB}"/>' for cx in cxs)


OPTIONS = {
    # ---- A: modern crossover / hatchback -------------------------------
    "a": dict(
        body=f'''    <path fill="{RED}" d="M 44,296 C 44,276 51,265 66,261 L 176,246 L 214,140
      Q 218,132 230,132 L 356,130 Q 368,130 373,138 L 426,248 L 450,256
      Q 468,262 468,281 L 468,324 Q 468,340 452,340 L 434,340
      A 56,56 0 0 0 322,340 L 190,340 A 56,56 0 0 0 78,340 L 60,340
      Q 44,340 44,324 Z"/>''',
        ws=((190, 258), (226, 150), (332, 150), (332, 258)),
        rear=((350, 258), (350, 150), (364, 150), (412, 258)),
        lamp=f'    <ellipse cx="57" cy="281" rx="15" ry="12" fill="{LAMP}"/>',
        wheels=([134, 378], 340, 50, 20),
        shift=-4,
    ),
    # ---- B: low, sleek fastback ----------------------------------------
    "b": dict(
        body=f'''    <path fill="{RED}" d="M 38,300 C 38,278 47,266 66,262 L 172,250 L 234,158
      Q 242,150 254,150 L 348,150 Q 364,150 374,160 L 452,248
      Q 474,257 474,284 L 474,328 Q 474,344 458,344 L 442,344
      A 58,58 0 0 0 326,344 L 188,344 A 58,58 0 0 0 72,344 L 54,344
      Q 38,344 38,328 Z"/>''',
        ws=((190, 258), (250, 168), (334, 168), (334, 258)),
        rear=((352, 258), (352, 169), (362, 169), (420, 258)),
        lamp=f'    <ellipse cx="51" cy="282" rx="17" ry="11" fill="{LAMP}"/>',
        wheels=([130, 384], 344, 52, 21),
        shift=-17,
    ),
    # ---- C: boxy SUV / estate ------------------------------------------
    "c": dict(
        body=f'''    <path fill="{RED}" d="M 46,294 C 46,274 53,263 68,259 L 148,244 L 176,136
      Q 179,126 192,126 L 366,126 Q 378,126 382,136 L 420,244 L 450,252
      Q 466,258 466,278 L 466,322 Q 466,338 450,338 L 434,338
      A 58,58 0 0 0 318,338 L 192,338 A 58,58 0 0 0 76,338 L 60,338
      Q 46,338 46,322 Z"/>''',
        ws=((166, 252), (192, 144), (306, 144), (306, 252)),
        rear=((324, 252), (324, 144), (370, 144), (400, 252)),
        lamp=f'    <ellipse cx="59" cy="281" rx="15" ry="12" fill="{LAMP}"/>',
        wheels=([134, 376], 338, 52, 21),
        shift=-2,
    ),
}


def build(name):
    o = OPTIONS[name]
    ws, cid = path(o["ws"]), f"ws-{name}"
    cx, cy, s = PLACE[name] if name in PLACE else fit_dog(o["ws"])
    print(f"  {name}: dog cx={cx:.0f} cy={cy:.0f} scale={s:.2f}")
    return f'''  <defs>
    <clipPath id="{cid}"><path d="{ws}"/></clipPath>
  </defs>
{o['body']}
    <path fill="{GLASS}" d="{ws}"/>
    <path fill="{GLASS}" d="{path(o['rear'])}"/>
{o['lamp']}
    <g clip-path="url(#{cid})">
{collie(cx, cy, s)}
    </g>
{wheels(*o['wheels'])}'''


def svg(name, maskable=False):
    inner = build(name)
    if maskable:
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">\n'
                '  <rect width="512" height="512" fill="#d1d5db"/>\n'
                '  <g transform="translate(256,256) scale(0.82) '
                f'translate(-256,{-256 + OPTIONS[name]["shift"]})">\n'
                f'{inner}\n  </g>\n</svg>\n')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">\n'
            f'  <g transform="translate(0,{OPTIONS[name]["shift"]})">\n{inner}\n  </g>\n</svg>\n')


def install():
    """Write the files the app actually serves, PNGs included."""
    pub = os.path.normpath(f"{HERE}/../public")
    open(f"{pub}/favicon.svg", "w").write(svg(CHOSEN))
    open(f"{HERE}/favicon-maskable.svg", "w").write(svg(CHOSEN, True))
    for name, src in (("pwa", f"{pub}/favicon.svg"),
                      ("maskable-icon", f"{HERE}/favicon-maskable.svg")):
        for size in (192, 512):
            # -strip: without it ImageMagick stamps each PNG with the time it
            # ran, so re-running this would show a diff on every icon.
            subprocess.run(["magick", "-background", "none", src, "-resize",
                            f"{size}x{size}", "-strip",
                            f"{pub}/{name}-{size}x{size}.png"], check=True)
    print(f"installed favicon.svg, favicon-maskable.svg and four PNGs in {pub}")


def previews():
    out = f"{HERE}/build"
    os.makedirs(out, exist_ok=True)
    for n in OPTIONS:
        open(f"{out}/option-{n}.svg", "w").write(svg(n))
        open(f"{out}/option-{n}-maskable.svg", "w").write(svg(n, True))
    print(f"previews for every body in {out}")


if __name__ == "__main__":
    install() if "--install" in sys.argv else previews()
