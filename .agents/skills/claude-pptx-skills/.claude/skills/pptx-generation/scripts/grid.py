#!/usr/bin/env python3
"""
Split a rectangle into non-overlapping rectangles.

This is deliberately *not* a catalogue of named slide layouts. A slide's content
arrangement varies with what's being asked for, so the agent composes it; this
module only does the arithmetic, so gaps, margins and alignment stay consistent
and boxes never overlap. Everything is inches, and every box is a plain
{x, y, w, h} dict that can be split again.

    body        = tokens.content_area(tk)
    left, right = grid.cols(tk, body, weights=[0.6, 0.4])
    head, mid, chart = grid.rows(tk, left, sizes=[1.05, 0.95, "auto"])
    a, b, c     = grid.cols(tk, mid, n=3)

Three ways to divide, mutually exclusive:
    n=3                          three equal parts
    weights=[3, 2]               proportional; any positive numbers, normalised
    sizes=[1.05, 0.95, "auto"]   absolute inches; "auto" shares what's left over

Gaps come from layout.gap_in unless overridden per call.

CLI (handy for checking geometry without writing a script):
    python grid.py --tokens design/brand.tokens.json --n 2
    python grid.py --tokens design/brand.tokens.json --rows --sizes 1.05,0.95,auto
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tokens as tokens_mod  # noqa: E402


def _spans(start, total, n, weights, sizes, gap):
    """Offsets and lengths along one axis. Returns [(offset, length), ...]."""
    given = [x is not None for x in (n, weights, sizes)]
    if sum(given) != 1:
        raise ValueError("pass exactly one of n=, weights=, sizes=")

    if n is not None:
        if n < 1:
            raise ValueError("n must be at least 1")
        weights = [1] * n

    if weights is not None:
        count = len(weights)
        if any(w <= 0 for w in weights):
            raise ValueError("weights must be positive")
        free = total - gap * (count - 1)
        if free <= 0:
            raise ValueError(f"{count} parts with {gap}in gaps don't fit in {total}in")
        scale = sum(weights)
        lengths = [free * w / scale for w in weights]
    else:
        count = len(sizes)
        free = total - gap * (count - 1)
        autos = [i for i, s in enumerate(sizes) if s == "auto"]
        fixed = sum(s for s in sizes if s != "auto")
        if fixed > free + 1e-9:
            raise ValueError(f"fixed sizes total {fixed}in but only {free:.3f}in "
                             f"is available after gaps")
        if not autos and abs(fixed - free) > 1e-9:
            raise ValueError(f"sizes total {fixed}in but the space is {free:.3f}in; "
                             f"add \"auto\" to absorb the difference")
        share = (free - fixed) / len(autos) if autos else 0
        lengths = [share if s == "auto" else s for s in sizes]

    out, pos = [], start
    for length in lengths:
        out.append((round(pos, 4), round(length, 4)))
        pos += length + gap
    return out


def _gap(tk, gap):
    return tk["layout"]["gap_in"] if gap is None else gap


def cols(tk, box, n=None, weights=None, sizes=None, gap=None):
    """Split a box into vertical columns, left to right."""
    g = _gap(tk, gap)
    return [{"x": off, "y": box["y"], "w": length, "h": box["h"]}
            for off, length in _spans(box["x"], box["w"], n, weights, sizes, g)]


def rows(tk, box, n=None, weights=None, sizes=None, gap=None):
    """Split a box into horizontal rows, top to bottom."""
    g = _gap(tk, gap)
    return [{"x": box["x"], "y": off, "w": box["w"], "h": length}
            for off, length in _spans(box["y"], box["h"], n, weights, sizes, g)]


def pad(box, by=None, top=0, right=0, bottom=0, left=0):
    """Shrink a box inward. `by` applies to all four sides; the named arguments
    add to it, so pad(b, 0.2, top=0.3) insets 0.2 everywhere and 0.5 at the top."""
    by = by or 0
    t, r, b, l = top + by, right + by, bottom + by, left + by
    return {"x": round(box["x"] + l, 4), "y": round(box["y"] + t, 4),
            "w": round(box["w"] - l - r, 4), "h": round(box["h"] - t - b, 4)}


def _parse(values):
    if not values:
        return None
    out = []
    for v in values.split(","):
        v = v.strip()
        out.append("auto" if v == "auto" else float(v))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tokens", required=True)
    p.add_argument("--rows", action="store_true", help="split into rows instead of columns")
    p.add_argument("--n", type=int)
    p.add_argument("--weights", help="comma-separated, e.g. 0.6,0.4")
    p.add_argument("--sizes", help="comma-separated inches or 'auto', e.g. 1.05,0.95,auto")
    p.add_argument("--box", help="x,y,w,h in inches; defaults to the content area")
    p.add_argument("--gap", type=float)
    args = p.parse_args()

    tk = tokens_mod.load(args.tokens)
    if args.box:
        x, y, w, h = (float(v) for v in args.box.split(","))
        box = {"x": x, "y": y, "w": w, "h": h}
    else:
        box = tokens_mod.content_area(tk)

    fn = rows if args.rows else cols
    print(json.dumps(fn(tk, box, n=args.n, weights=_parse(args.weights),
                        sizes=_parse(args.sizes), gap=args.gap), indent=2))


if __name__ == "__main__":
    main()
