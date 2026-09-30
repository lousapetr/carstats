# App icon

The icon is a red car in profile with a border collie's head in the windshield.
Two SVGs ship: `../public/favicon.svg` (transparent, also used for the header
logo and the apple-touch-icon) and `favicon-maskable.svg` (full-bleed on grey,
for Android's adaptive icons). The four PNGs in `../public/` are rendered from
those two. All of them are generated -- edit the sources here, not the output.
The manifest lists only the `pwa-*.png` pair: Firefox + Nova Launcher show a
maskable entry as a blank square (see the comment in `../vite.config.ts`).

Everything needs only Python 3 and ImageMagick (`magick`).

## Regenerating what the app serves

    python3 gen.py --install

Writes both SVGs and re-renders `pwa-*.png` and `maskable-icon-*.png` at 192
and 512. Run this after any change here, then commit the output alongside it.
Also bump `icon=` in `start_url` in `../vite.config.ts`, or Android home
screens keep showing the previous icon after a reinstall.

## The car

`gen.py` holds three bodies: `a` (hatchback), `b` (low fastback, the one we
ship) and `c` (boxy SUV). `CHOSEN` picks the one that gets installed.

    python3 gen.py        # renders all three to build/ for comparison

A body is a red silhouette path plus a windshield quad, a rear-glass quad, a
headlight and wheel positions. The windshield quad does double duty: it is both
the blue pane and the clip path for the dog, which is why the dog's chest can
run off the bottom of it and come out looking like it is sitting in the seat.

## The dog

`dog.py` is the drawing, in its own coordinate system: nose pointing left (-x),
head around the origin, chest running off the bottom past the window sill.

Edit it as code if the change is small. For real drawing, round-trip it through
a vector editor:

    python3 make_edit_svg.py              # writes dog-edit.svg
    # open dog-edit.svg, edit inside the group id="dog", save as Plain SVG
    python3 import_dog.py dog-edit.svg    # rewrites dog.py
    python3 gen.py --install

In `dog-edit.svg` the dashed `id="window"` path is the windshield drawn in the
dog's coordinates, and `id="context"` is the car around it. Anything outside
the dashed outline is clipped in the real icon; below its bottom edge that is
deliberate. Leave the guide path alone -- it is what lines the drawing back up
on import, so any shifting or rescaling the editor does gets undone. Inkscape
dissolves the `dog` group on save; the importer copes.

An imported dog is pinned by `PLACE` in `dog.py` at exactly the size and spot
it was drawn, rather than being re-fitted. If a redraw ends up poking through
the A-pillar, the B-pillar or the roof:

    python3 fit_placement.py

It reads the dog's real outline off a render, shrinks it about the window sill
(so its relation to the beltline survives) and nudges it sideways as little as
it can, then rewrites `PLACE`.

## Palette

Body `#dc2626`, glass `#60a5fa`, headlight `#fef3c7`, tyres `#111827`, hubs
`#6b7280`, maskable background `#d1d5db`. The dog carries its own colours
inline, including the pink inner ear and amber eye. The glass is deliberately
two steps darker than the blue-200 the icon used before 2026-09-29: at favicon
size the dog's white markings dissolved into the paler blue.

Keep it flat -- no gradients, filters or text. At 40px only the big shapes
survive, which is the size that matters most.
