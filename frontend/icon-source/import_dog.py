#!/usr/bin/env python3
"""Fold a hand-edited dog-edit.svg back into dog.py.

    python3 import_dog.py <edited.svg>

Keeps whatever is inside the group id="dog" and drops the context/guide. The
guide path (id="window") is used to undo any shift or rescale the editor
applied, so the dog lands in the windshield exactly as it was drawn.
"""
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
HERE = os.path.dirname(os.path.abspath(__file__))
ET.register_namespace("", SVG)


def numbers(text):
    return [float(n) for n in re.findall(r"-?\d+(?:\.\d+)?(?:e-?\d+)?", text)]


def bbox(points):
    xs, ys = points[0::2], points[1::2]
    return min(xs), min(ys), max(xs), max(ys)


def find(root, el_id):
    return next((e for e in root.iter() if e.get("id") == el_id), None)


def strip(el):
    """Drop editor bookkeeping so the result stays readable."""
    for e in el.iter():
        e.tag = e.tag.split("}")[-1]
        for attr in list(e.attrib):
            if "}" in attr or attr.startswith(("inkscape:", "sodipodi:")):
                del e.attrib[attr]
    return el


def main(path):
    meta = json.load(open(f"{HERE}/dog-edit.json"))
    root = ET.parse(path).getroot()

    skip = {"context", "window", "defs", "namedview", "metadata"}
    dog = find(root, "dog")
    if dog is None:
        # Inkscape dissolves single-use groups on save: fall back to every
        # top-level drawable that is not the context or the guide.
        dog = [e for e in root
               if e.get("id") not in skip and e.tag.split("}")[-1] not in skip]
        print(f"no id='dog' group; taking {len(dog)} top-level elements instead")

    window = find(root, "window")
    fix = ""
    if window is not None:
        want = bbox(numbers(meta["guide"]))
        got = bbox(numbers(window.get("d", "")))
        sx = (want[2] - want[0]) / (got[2] - got[0])
        sy = (want[3] - want[1]) / (got[3] - got[1])
        if abs(sx - 1) > 1e-3 or abs(sy - 1) > 1e-3 or \
           abs(want[0] - got[0]) > 1e-3 or abs(want[1] - got[1]) > 1e-3:
            fix = (f'transform="translate({want[0] - got[0] * sx:.3f},'
                   f'{want[1] - got[1] * sy:.3f}) scale({sx:.4f},{sy:.4f})"')
            print(f"guide moved; compensating with {fix}")
    else:
        print("warning: no id='window' guide found, assuming coordinates are unchanged")

    # an earlier import's own wrapper comes back as a lone bare <g>: unwrap it
    # rather than nesting a new one on every trip through the editor
    children = list(dog)
    while len(children) == 1 and children[0].tag.split("}")[-1] == "g" \
            and not {k for k in children[0].attrib if k != "id"}:
        children = list(children[0])

    body = "".join(ET.tostring(strip(child), encoding="unicode").strip()
                   for child in children)
    body = re.sub(r"\s+", " ", body).replace("> <", ">\n        <")
    cx, cy, s = meta["place"]
    open_fix = f"<g {fix}>" if fix else ""
    close_fix = "</g>" if fix else ""

    open(f"{HERE}/dog.py", "w").write(f'''"""The border collie head, imported from a hand-edited SVG by import_dog.py.
gen.py draws this into the windshield; PLACE pins it where it was drawn."""

PLACE = {{"{meta['option']}": ({cx}, {cy}, {s})}}


def collie(cx, cy, s):
    return (f\'      <g transform="translate({{cx:.1f}},{{cy:.1f}}) scale({{s:.3f}})">\'
            \'{open_fix}\'
            \'\'\'
        {body}\'\'\'
            \'{close_fix}</g>\')
''')
    print(f"dog.py rewritten from {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else f"{HERE}/dog-edit.svg")
