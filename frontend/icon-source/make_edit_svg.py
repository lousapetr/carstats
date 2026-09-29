#!/usr/bin/env python3
"""Write dog-edit.svg: the dog alone in its own coordinate system, with the
windshield it has to live in drawn as a guide. Edit the dog there, keep the
guide where it is, and import-dog.py folds the result back into dog.py."""
import json
import os

from dog import collie
from gen import CHOSEN, OPTIONS, fit_dog

try:  # a dog imported from SVG is pinned where it was drawn
    from dog import PLACE
except ImportError:
    PLACE = {}

OUT = os.path.dirname(os.path.abspath(__file__))
OPT = CHOSEN
pane = OPTIONS[OPT]["ws"]
cx, cy, s = PLACE[OPT] if OPT in PLACE else fit_dog(pane)

dog_group = collie(0, 0, 1).replace(
    '      <g transform="translate(0.0,0.0) scale(1.000)">', '  <g id="dog">')

# the windshield, expressed in the dog's own coordinates
guide = " ".join(f"{'ML'[i > 0]} {(x - cx) / s:.1f},{(y - cy) / s:.1f}"
                 for i, (x, y) in enumerate(pane)) + " Z"

open(f"{OUT}/dog-edit.svg", "w").write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!--
  CarStats icon: the border collie head, on its own.

  * The dog lives in the group id="dog". Edit, add or delete anything inside it.
  * id="window" is the windshield of option B, drawn in the dog's own
    coordinates. Anything outside it gets clipped away in the real icon; the
    chest running off the bottom edge is meant to be clipped. Leave that path
    where it is: it is what lines the drawing up again on the way back in.
  * Flat fills only, no gradients, filters or text. Palette: black #111827,
    white #f8fafc, eye #eef2f7, glass behind the dog #bfdbfe.
  * Save as plain SVG (Inkscape: File > Save As > Plain SVG) and hand it back.
-->
<svg xmlns="http://www.w3.org/2000/svg" viewBox="-150 -140 290 260" width="870" height="780">
  <g id="context">
    <rect x="-150" y="-140" width="290" height="260" fill="#dc2626"/>
    <path d="{guide}" fill="#bfdbfe"/>
  </g>
{dog_group}
  <path id="window" d="{guide}" fill="none" stroke="#111827"
        stroke-width="1.5" stroke-dasharray="6 5" opacity="0.55"/>
</svg>
''')
json.dump({"option": OPT, "place": [round(cx, 1), round(cy, 1), round(s, 3)],
           "guide": guide},
          open(f"{OUT}/dog-edit.json", "w"), indent=2)
print(f"option {OPT}: dog placed at ({cx:.1f},{cy:.1f}) scale {s:.3f}")
