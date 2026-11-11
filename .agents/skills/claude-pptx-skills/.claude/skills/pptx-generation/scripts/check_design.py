#!/usr/bin/env python3
"""
Check a generated deck against the design layer.

This is the gate that makes the tokens binding rather than advisory: it opens a
deck we just generated and fails if anything in it uses a font, colour, position
or chart setting the design layer didn't sanction. Run it with check_file.py as
part of QA.

Checks (FAIL blocks, WARN is reported but exits 0):
  FAIL  a run or chart uses a font family not in primitive.font
  FAIL  an explicit colour is not in primitive.color
  FAIL  a shape extends off the slide canvas
  FAIL  a chart contradicts its recipe (value axis / gridlines)
  WARN  a non-full-bleed shape crosses the safe-area margin
  WARN  two charts, or two cards, overlap each other

Scoped to decks generated from the design layer. It is not a general auditor of
arbitrary third-party decks, which will legitimately use other fonts and colours.

Usage: python check_design.py deck.pptx [design/brand.tokens.json]
"""
import os
import sys

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402
import tokens as tokens_mod  # noqa: E402

TOL = 0.02  # inches; absorbs Emu rounding so exact-fit shapes don't trip a check


class Report:
    def __init__(self):
        self.fails = []
        self.warns = []

    def fail(self, where, msg):
        self.fails.append((where, msg))

    def warn(self, where, msg):
        self.warns.append((where, msg))

    def render(self):
        for where, msg in self.fails:
            print(f"FAIL  {where}\n      {msg}")
        for where, msg in self.warns:
            print(f"WARN  {where}\n      {msg}")
        n_f, n_w = len(self.fails), len(self.warns)
        print(f"\n{n_f} failure{'s' * (n_f != 1)}, {n_w} warning{'s' * (n_w != 1)}")
        return 1 if n_f else 0


def allowed_fonts(tk):
    return set(tk.get("primitive", {}).get("font", {}).values())


def allowed_colors(tk):
    return {v.lstrip("#").upper()
            for v in tk.get("primitive", {}).get("color", {}).values()
            if isinstance(v, str) and v.startswith("#")}


def _emu_in(v):
    return v / 914400 if v is not None else None


def _box(shape):
    vals = [_emu_in(shape.left), _emu_in(shape.top),
            _emu_in(shape.width), _emu_in(shape.height)]
    if any(v is None for v in vals):
        return None
    return dict(zip(("x", "y", "w", "h"), vals))


def _is_full_bleed(box, tk):
    canvas = tk["layout"]["canvas"]
    return box["x"] <= TOL and box["w"] >= canvas["w_in"] - TOL


def _overlaps(a, b):
    return not (a["x"] + a["w"] <= b["x"] + TOL or b["x"] + b["w"] <= a["x"] + TOL
                or a["y"] + a["h"] <= b["y"] + TOL or b["y"] + b["h"] <= a["y"] + TOL)


def check_text(shape, where, fonts, colors, rep):
    if not shape.has_text_frame:
        return
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if not run.text.strip():
                continue
            name = run.font.name
            if name and name not in fonts:
                rep.fail(where, f"font {name!r} is not in the design layer "
                                f"(allowed: {', '.join(sorted(fonts))})")
            try:
                rgb = run.font.color.rgb
            except (AttributeError, TypeError):
                rgb = None
            if rgb is not None and str(rgb).upper() not in colors:
                rep.fail(where, f"text colour #{rgb} is not in the design layer palette")


def check_fill(shape, where, colors, rep):
    try:
        if shape.fill.type is not None and shape.fill.type == 1:  # MSO_FILL.SOLID
            rgb = shape.fill.fore_color.rgb
            if str(rgb).upper() not in colors:
                rep.fail(where, f"fill colour #{rgb} is not in the design layer palette")
    except (AttributeError, TypeError, ValueError):
        pass  # inherited / gradient / no fill -- nothing explicit to check


def check_geometry(shape, where, tk, rep):
    box = _box(shape)
    if box is None:
        return None
    canvas, margin = tk["layout"]["canvas"], tk["layout"]["margin"]

    # A negative or zero width/height is a degenerate shape, usually from a
    # box computed from bad arithmetic (e.g. placing content in a region that
    # was never actually free). It renders as invisible or inverted, so this
    # has to be its own check: neither of the box's edges individually looks
    # out of bounds when the width itself is what's broken.
    if box["w"] <= TOL or box["h"] <= TOL:
        rep.fail(where, f"degenerate size: w={box['w']:.2f} h={box['h']:.2f} "
                        f"(a positive width and height are required)")
        return box

    if (box["x"] < -TOL or box["y"] < -TOL
            or box["x"] + box["w"] > canvas["w_in"] + TOL
            or box["y"] + box["h"] > canvas["h_in"] + TOL):
        rep.fail(where, f"extends off the slide: x={box['x']:.2f} y={box['y']:.2f} "
                        f"w={box['w']:.2f} h={box['h']:.2f} on a "
                        f"{canvas['w_in']}x{canvas['h_in']}in canvas")
        return box

    # Full-bleed shapes (a footer band) are deliberate; only flag the others.
    full_bleed = box["x"] <= TOL and box["w"] >= canvas["w_in"] - TOL
    if not full_bleed:
        if box["x"] < margin["x_in"] - TOL or \
                box["x"] + box["w"] > canvas["w_in"] - margin["x_in"] + TOL:
            rep.warn(where, f"crosses the {margin['x_in']}in side margin")
    return box


def check_chart(shape, where, tk, fonts, rep):
    chart = shape.chart
    kinds = {v: k for k, v in build.CHART_TYPES.items()}
    kind = kinds.get(chart.chart_type)
    if kind is None:
        rep.warn(where, f"chart type {chart.chart_type} has no recipe in the design layer")
        return
    spec = tokens_mod.chart_spec(tk, kind)

    if chart.font.name and chart.font.name not in fonts:
        rep.fail(where, f"chart font {chart.font.name!r} is not in the design layer")

    if kind in build.KINDS_WITHOUT_AXES:
        return

    # The value axis is the load-bearing one: a bar recipe hides it precisely
    # because direct labels carry the numbers, so a visible axis normally means
    # the recipe was bypassed.
    #
    # The exception is the label cap. Past max_points_for_labels there are too
    # many bars to label, so build.py drops the labels and puts the axis back --
    # otherwise the values would be unreadable. When that has happened, the axis
    # is *supposed* to disagree with the recipe, so neither axis check applies.
    #
    # This has to test the point count, not merely "labels are missing": a
    # hand-rolled chart that simply never set labels would otherwise excuse
    # itself from the axis checks entirely, which is the bypass we're here to
    # catch. Same arithmetic as build.py, so the two agree by construction.
    want = spec.get("value_axis", {})
    plot = chart.plots[0]
    cap = spec.get("max_points_for_labels")
    n_points, n_series = len(list(plot.categories)), len(plot.series)
    if cap is not None and n_points * n_series > cap:
        return

    if "visible" in want and chart.value_axis.visible != want["visible"]:
        rep.fail(where, f"{kind}: value axis visible={chart.value_axis.visible}, "
                        f"recipe says {want['visible']}")
    if "gridlines" in want and chart.value_axis.has_major_gridlines != want["gridlines"]:
        rep.fail(where, f"{kind}: value-axis gridlines="
                        f"{chart.value_axis.has_major_gridlines}, "
                        f"recipe says {want['gridlines']}")


def check_deck(pptx_path, tokens_path):
    tk = tokens_mod.load(tokens_path)
    fonts, colors = allowed_fonts(tk), allowed_colors(tk)
    prs = Presentation(pptx_path)
    rep = Report()

    for idx, slide in enumerate(prs.slides, start=1):
        charts, cards = [], []
        for shape in slide.shapes:
            where = f"slide {idx}  {shape.shape_type}  {shape.name!r}"
            check_text(shape, where, fonts, colors, rep)
            box = check_geometry(shape, where, tk, rep)

            if shape.has_chart:
                check_chart(shape, where, tk, fonts, rep)
                if box:
                    charts.append((where, box))
                continue

            check_fill(shape, where, colors, rep)
            # Full-bleed shapes (slide background, footer band) are chrome and
            # are *meant* to sit under everything, so they're not peers of the
            # content blocks and don't participate in the overlap check.
            if box and shape.shape_type == MSO_SHAPE_TYPE.AUTO_SHAPE \
                    and not _is_full_bleed(box, tk):
                cards.append((where, box))

        # Peers of the same kind must not collide. Text deliberately sits on top
        # of cards, so text is excluded rather than producing constant noise.
        for group, label in ((charts, "charts"), (cards, "cards")):
            for i in range(len(group)):
                for j in range(i + 1, len(group)):
                    if _overlaps(group[i][1], group[j][1]):
                        rep.warn(group[i][0], f"overlaps another of the slide's {label}: "
                                              f"{group[j][0].split('  ', 1)[1]}")
    return rep


def main():
    if len(sys.argv) not in (2, 3):
        print("Usage: check_design.py deck.pptx [tokens.json]", file=sys.stderr)
        sys.exit(2)
    pptx_path = sys.argv[1]
    tokens_path = sys.argv[2] if len(sys.argv) == 3 else "design/brand.tokens.json"

    rep = check_deck(pptx_path, tokens_path)
    code = rep.render()
    if code == 0 and not rep.warns:
        print("design layer conformance PASSED")
    sys.exit(code)


if __name__ == "__main__":
    main()
