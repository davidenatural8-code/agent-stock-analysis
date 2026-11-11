#!/usr/bin/env python3
"""
Token-aware helpers for building slides with python-pptx.

These are plain functions over native python-pptx objects -- there is no wrapper
class and no hidden state. You create the Presentation, you call add_slide, you
call save; each helper takes a real `slide` plus resolved `tokens` and returns
the real python-pptx object it created, so you can keep styling it by hand
afterwards or ignore these helpers entirely for a case they don't cover.

    from pptx import Presentation
    import grid, build, tokens

    tk  = tokens.load("design/brand.tokens.json")
    prs = Presentation("templates/blank.pptx")

    # chrome (logo, title position, footer) comes from the slide type;
    # `body` is the box left over to compose in
    slide, body = build.new_slide(prs, tk, "content",
                                  heading="Q3 Regional Performance",
                                  subtitle="Revenue by region")

    # the arrangement is composed here, not chosen from a preset
    chart_box, note = grid.cols(tk, body, weights=[0.62, 0.38])

    build.card(slide, tk, chart_box, title="Quarterly revenue ($M)")
    build.chart(slide, tk, "bar", build.chart_box(tk, chart_box),
                ["Q1", "Q2", "Q3", "Q4"],
                {"Europe": [42, 48, 51, 60], "Americas": [30, 35, 33, 40]})
    build.card(slide, tk, note, title="Key insight", body="...")
    prs.save("output/deck.pptx")

The only thing these add over raw python-pptx is reading every font, colour and
size from the design layer instead of taking them as arguments. Nothing here
contains a literal font name or hex value.
"""
import os
import sys

from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import (XL_CHART_TYPE, XL_DATA_LABEL_POSITION,
                             XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_MARK)
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grid  # noqa: E402
import tokens as tokens_mod  # noqa: E402

# A chart kind names both a recipe in `charts.*` and the OOXML chart type to
# create, keeping the two in lockstep.
CHART_TYPES = {
    "bar": XL_CHART_TYPE.COLUMN_CLUSTERED,
    "bar_stacked": XL_CHART_TYPE.COLUMN_STACKED,
    "bar_horizontal": XL_CHART_TYPE.BAR_CLUSTERED,
    "line": XL_CHART_TYPE.LINE,
    "area": XL_CHART_TYPE.AREA,
    "pie": XL_CHART_TYPE.PIE,
}

# Pie charts have no axes; touching chart.value_axis on one raises.
KINDS_WITHOUT_AXES = {"pie"}
# Kinds where colour varies per point rather than per series.
KINDS_COLOURED_BY_POINT = {"pie"}

_LEGEND_POS = {"bottom": XL_LEGEND_POSITION.BOTTOM, "top": XL_LEGEND_POSITION.TOP,
               "left": XL_LEGEND_POSITION.LEFT, "right": XL_LEGEND_POSITION.RIGHT}
_LABEL_POS = {"outside_end": XL_DATA_LABEL_POSITION.OUTSIDE_END,
              "inside_end": XL_DATA_LABEL_POSITION.INSIDE_END,
              "center": XL_DATA_LABEL_POSITION.CENTER,
              "above": XL_DATA_LABEL_POSITION.ABOVE,
              "best_fit": XL_DATA_LABEL_POSITION.BEST_FIT}
_TICKS = {"none": XL_TICK_MARK.NONE, "inside": XL_TICK_MARK.INSIDE,
          "outside": XL_TICK_MARK.OUTSIDE, "cross": XL_TICK_MARK.CROSS}
_ALIGN = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}
_ANCHOR = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}

_PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
_DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


# --------------------------------------------------------------------------
# small shared bits
# --------------------------------------------------------------------------

def rgb(value):
    """RGBColor from a resolved '#RRGGBB' token value."""
    return RGBColor.from_string(value.lstrip("#").upper())


def _emu_box(box):
    """A {x,y,w,h} box in inches -> the four Emu values add_* wants."""
    return (Inches(box["x"]), Inches(box["y"]), Inches(box["w"]), Inches(box["h"]))


def _set_shadow(shape, on):
    """Turn an autoshape's drop shadow off properly.

    `shape.shadow.inherit = False` writes an empty <a:effectLst/> into spPr, which
    per the spec overrides the theme effect. PowerPoint honours that; LibreOffice
    does not, and keeps drawing the shadow named by <p:style><a:effectRef idx="2">
    -- so QA renders show a shadow the tokens said to suppress. Clearing effectRef
    as well makes the two renderers agree.
    """
    shape.shadow.inherit = on
    if on:
        return
    style = shape._element.find(f"{{{_PML_NS}}}style")
    if style is not None:
        effect_ref = style.find(f"{{{_DML_NS}}}effectRef")
        if effect_ref is not None:
            effect_ref.set("idx", "0")


def _style_run(run, spec):
    """Apply a `type.<role>` recipe to one run. Setting the font explicitly is
    required: patching the theme does not reach a run that carries its own
    typeface, which is what python-pptx writes."""
    run.font.name = spec["font"]
    run.font.size = Pt(spec["size"])
    run.font.bold = spec.get("bold", False)
    run.font.color.rgb = rgb(spec["color"])


line_height_in = tokens_mod.line_height_in  # re-export; defined once, in tokens.py


def blank_slide(prs, layout_index=6):
    """Add a slide on the blank layout, with no chrome at all. Plain python-pptx;
    here so callers don't have to remember which stock layout index is empty."""
    return prs.slides.add_slide(prs.slide_layouts[layout_index])


def content_area(tk):
    return tokens_mod.content_area(tk)


def chart_box(tk, box):
    """Where a chart goes inside a block that carries a title above it: inset at
    the sides, and pushed down by exactly the space that title occupies."""
    return grid.pad(box, top=tokens_mod.card_label_pad_in(tk),
                    left=tk["layout"]["inset_in"], right=tk["layout"]["inset_in"],
                    bottom=tk["layout"]["inset_in"])


# --------------------------------------------------------------------------
# text
# --------------------------------------------------------------------------

def text(slide, tk, role, content, box, align=None, anchor="top"):
    """A textbox whose every run is styled from `type.<role>`.

    `content` is a string, or a list of strings for multiple paragraphs.
    Returns the textbox shape.
    """
    spec = tokens_mod.text_spec(tk, role)
    paragraphs = [content] if isinstance(content, str) else list(content)

    shape = slide.shapes.add_textbox(*_emu_box(box))
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = 0
    tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = _ANCHOR[anchor]

    for i, line in enumerate(paragraphs):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        if align:
            p.alignment = _ALIGN[align]
        if i:
            p.space_before = Pt(spec["size"] * tk["layout"]["paragraph_space_em"])
        run = p.add_run()
        run.text = line
        _style_run(run, spec)
    return shape


def title(slide, tk, heading, subtitle=None, at="top_left"):
    """A title (and optional subtitle) placed in the title band, or centred on
    the slide for `at="center"`. Returns (title_shape, subtitle_shape|None).

    Normally you get this via new_slide(), which reads the position from the
    slide type rather than taking it as an argument.
    """
    layout = tk["layout"]
    m, canvas = layout["margin"], layout["canvas"]
    width = canvas["w_in"] - 2 * m["x_in"]
    align = {"top_left": "left", "top_right": "right", "center": "center"}[at]

    sub_h = line_height_in(tk, "subtitle") if subtitle else 0
    role = "section" if at == "center" else "title"
    head_h = line_height_in(tk, role)

    if at == "center":
        top = (canvas["h_in"] - head_h - sub_h) / 2
    else:
        top = m["top_in"]

    t = text(slide, tk, role, heading,
             {"x": m["x_in"], "y": top, "w": width, "h": head_h},
             align=align, anchor="top")
    s = None
    if subtitle:
        s = text(slide, tk, "subtitle", subtitle,
                 {"x": m["x_in"], "y": top + head_h, "w": width, "h": sub_h},
                 align=align)
    return t, s


def logo(slide, tk, at="top_left"):
    """The brand mark, from the `logo` tokens. Uses the image at logo.path when
    one is set and present, otherwise falls back to a text wordmark, so a deck
    still carries branding before anyone supplies an asset."""
    spec = tk.get("logo") or {}
    h = spec.get("height_in", 0.35)
    m, canvas = tk["layout"]["margin"], tk["layout"]["canvas"]

    path = spec.get("path")
    if path and os.path.exists(path):
        pic = slide.shapes.add_picture(path, Inches(0), Inches(0), height=Inches(h))
        w = pic.width / 914400
        pic.left = Inches(m["x_in"] if "left" in at else canvas["w_in"] - m["x_in"] - w)
        pic.top = Inches(m["top_in"])
        return pic

    if not spec.get("text"):
        return None
    box = {"x": m["x_in"], "y": m["top_in"], "w": canvas["w_in"] - 2 * m["x_in"], "h": h}
    return text(slide, tk, spec.get("role", "card_title"), spec["text"], box,
                align="left" if "left" in at else "right", anchor="top")


def new_slide(prs, tk, slide_type="content", heading=None, subtitle=None,
              footer_text=None):
    """Add a slide carrying the chrome its slide type calls for: background,
    logo, title position, footer.

    Returns (slide, body) where `body` is the box to compose content in, or None
    for a slide type that has no body (a home slide). Compose that box with
    grid.rows / grid.cols -- the arrangement is yours to decide, the chrome is
    the design layer's.
    """
    types = tk["layout"]["slide_type"]
    if slide_type not in types:
        raise ValueError(f"unknown slide type '{slide_type}' "
                         f"(have: {', '.join(sorted(types))})")
    spec = types[slide_type]
    slide = blank_slide(prs)

    canvas = tk["layout"]["canvas"]
    bg = spec.get("background")
    if bg:
        back = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, 0, 0, Inches(canvas["w_in"]), Inches(canvas["h_in"]))
        back.fill.solid()
        back.fill.fore_color.rgb = rgb(bg)
        back.line.fill.background()
        _set_shadow(back, False)

    if spec.get("logo"):
        logo(slide, tk, spec["logo"].get("at", "top_left"))
    if heading:
        title(slide, tk, heading, subtitle, at=spec["title"].get("at", "top_left"))
    if spec.get("footer"):
        footer_bar(slide, tk, footer_text)

    return slide, (content_area(tk) if spec.get("body") else None)


def bullets(slide, tk, items, box, role="body"):
    """A bulleted list. python-pptx has no real bullet API for plain textboxes,
    so the marker is a character in the run -- which is also what keeps it in the
    body font rather than a theme-supplied one.

    That marker-as-character approach means a wrapped line has no hanging
    indent by default: python-pptx exposes no paragraph_format.left_indent, so
    without help the second line of a long bullet falls back to the box's left
    edge instead of aligning under the bullet's text. Set marL/indent directly
    in the paragraph XML to fix it -- component.bullet.indent_in is the token.
    """
    prefix = tk["component"]["bullet"]["prefix"]
    shape = text(slide, tk, role, [f"{prefix}{i}" for i in items], box)
    indent = Inches(tk["component"]["bullet"]["indent_in"])
    for p in shape.text_frame.paragraphs:
        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(indent))
        pPr.set("indent", str(-indent))
    return shape


# --------------------------------------------------------------------------
# shapes
# --------------------------------------------------------------------------

def card(slide, tk, box, title=None, body=None, component="card"):
    """A background block from `component.<name>`, optionally with a card title
    and body text laid inside its padding. Returns the card shape."""
    spec = tk["component"][component]
    b = box["card_box"] if "card_box" in box else box

    shape = slide.shapes.add_shape(getattr(MSO_SHAPE, spec["shape"]), *_emu_box(b))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(spec["fill"])
    if spec.get("border", "none") == "none":
        shape.line.fill.background()
    else:
        shape.line.color.rgb = rgb(spec["border"])
    _set_shadow(shape, spec.get("shadow", False))
    shape.text_frame.text = ""  # a shape's own frame stays empty; text goes in its own boxes

    pad = spec["pad_in"]
    y = b["y"] + pad
    if title:
        th = line_height_in(tk, "card_title")
        text(slide, tk, "card_title", title,
             {"x": b["x"] + pad, "y": y, "w": b["w"] - 2 * pad, "h": th}, align="left")
        y += th + spec["title_gap_in"]
    if body:
        text(slide, tk, "body", body,
             {"x": b["x"] + pad, "y": y, "w": b["w"] - 2 * pad,
              "h": b["y"] + b["h"] - pad - y}, align="left")
    return shape


def kpi(slide, tk, box, value, label):
    """A single big number over a caption, on a card. Use this instead of a
    one-bar bar chart -- the number is the chart."""
    b = box["card_box"] if "card_box" in box else box
    shape = card(slide, tk, b, component="kpi")
    spec = tk["component"]["kpi"]
    pad = spec["pad_in"]

    vh = line_height_in(tk, "kpi_value")
    lh = line_height_in(tk, "kpi_label")
    text(slide, tk, "kpi_value", value,
         {"x": b["x"] + pad, "y": b["y"] + pad, "w": b["w"] - 2 * pad, "h": vh}, align="left")
    text(slide, tk, "kpi_label", label,
         {"x": b["x"] + pad, "y": b["y"] + pad + vh, "w": b["w"] - 2 * pad, "h": lh},
         align="left")
    return shape


def footer_bar(slide, tk, label=None):
    """The full-width band along the bottom, sized from layout + component tokens."""
    spec = tk["component"]["footer_bar"]
    canvas = tk["layout"]["canvas"]
    h = spec["height_in"]
    box = {"x": 0, "y": canvas["h_in"] - h, "w": canvas["w_in"], "h": h}

    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, *_emu_box(box))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(spec["fill"])
    shape.line.fill.background()
    _set_shadow(shape, False)
    if label:
        m = tk["layout"]["margin"]["x_in"]
        text(slide, tk, "footer", label,
             {"x": m, "y": box["y"], "w": canvas["w_in"] - 2 * m, "h": h}, anchor="middle")
    return shape


# --------------------------------------------------------------------------
# charts
# --------------------------------------------------------------------------

def _style_axis(axis, axis_spec, spec, tk):
    """Axis visibility, gridlines, ticks and the axis line itself."""
    palette = tk["semantic"]["chart"]
    axis.visible = axis_spec.get("visible", True)
    axis.has_major_gridlines = axis_spec.get("gridlines", False)
    if axis.has_major_gridlines:
        gl = axis.major_gridlines.format.line
        gl.color.rgb = rgb(palette["grid"])
        gl.width = Pt(spec["grid_width_pt"])
    axis.major_tick_mark = _TICKS[axis_spec.get("tick_marks", "none")]
    if axis_spec.get("line", False):
        axis.format.line.color.rgb = rgb(palette["axis"])
        axis.format.line.width = Pt(spec["axis_width_pt"])
    else:
        axis.format.line.fill.background()


def _apply_spec(chart, kind, spec, tk, n_series, n_points, number_format=None):
    """Apply a resolved chart recipe to a freshly created chart."""
    palette = tk["semantic"]["chart"]

    # All chart text at once (axis ticks, legend, labels), then labels can override.
    chart.font.name = spec["font"]
    chart.font.size = Pt(spec["font_size"])
    chart.font.color.rgb = rgb(spec["font_color"])

    # A single-series chart otherwise auto-titles itself with the series name,
    # which duplicates the card title sitting right above it.
    chart.has_title = spec.get("chart_title", False)

    legend = spec.get("legend", {})
    chart.has_legend = n_series >= legend.get("when_series_gte", 2)
    if chart.has_legend:
        chart.legend.position = _LEGEND_POS[legend.get("position", "bottom")]
        chart.legend.include_in_layout = legend.get("in_layout", False)

    labels = dict(spec.get("data_labels", {}))
    if number_format:
        labels["number_format"] = number_format
    show_labels = labels.get("show", False)

    # Direct labels are what let a bar chart drop its value axis. Past
    # max_points_for_labels there are too many to label legibly, so the labels
    # come off -- and the axis has to come back, or the values become unreadable.
    axis_override = {}
    cap = spec.get("max_points_for_labels")
    if show_labels and cap is not None and n_points * n_series > cap:
        show_labels = False
        if not spec.get("value_axis", {}).get("visible", True):
            axis_override = {"visible": True, "gridlines": True}

    if kind not in KINDS_WITHOUT_AXES:
        value_spec = {**spec.get("value_axis", {}), **axis_override}
        _style_axis(chart.value_axis, value_spec, spec, tk)
        _style_axis(chart.category_axis, spec.get("category_axis", {}), spec, tk)

    plot = chart.plots[0]
    if "gap_width" in spec and hasattr(plot, "gap_width"):
        plot.gap_width = spec["gap_width"]
    if "overlap" in spec and hasattr(plot, "overlap"):
        plot.overlap = spec["overlap"]

    plot.has_data_labels = show_labels
    if show_labels:
        dl = plot.data_labels
        if labels.get("number_format"):
            dl.number_format = labels["number_format"]
            dl.number_format_is_linked = False
        dl.show_value = labels.get("show_value", not labels.get("show_percentage", False))
        if labels.get("show_percentage"):
            dl.show_percentage = True
        # OUTSIDE_END is invalid on a stacked plot (the segments have no outside),
        # so skip positioning there rather than raise. It is valid on pie.
        pos = labels.get("position")
        if pos and "stacked" not in kind:
            dl.position = _LABEL_POS[pos]
        dl.font.name = spec["font"]
        dl.font.size = Pt(spec["font_size"])
        dl.font.color.rgb = rgb(spec["font_color"])

    # Line weight / markers, where the plot type has them.
    for series in plot.series:
        if hasattr(series, "smooth"):
            series.smooth = spec.get("smooth", False)
        if "width_pt" in spec:
            series.format.line.width = Pt(spec["width_pt"])
        if hasattr(series, "marker") and spec.get("marker") is not None:
            series.marker.style = XL_MARKER_STYLE.NONE if spec["marker"] == "none" \
                else getattr(XL_MARKER_STYLE, spec["marker"].upper())
    return palette


def _colour(chart, kind, tk, n_points, emphasize):
    """Assign categorical colours in fixed order by index -- never cycled, so a
    series keeps its hue no matter how many others are present."""
    palette = tk["semantic"]["chart"]
    categorical, muted = palette["categorical"], palette["muted"]
    plot = chart.plots[0]

    if kind in KINDS_COLOURED_BY_POINT:
        series = plot.series[0]
        for i in range(n_points):
            point = series.points[i]
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = rgb(categorical[i])
        return

    for i, series in enumerate(plot.series):
        colour = categorical[i]
        if kind in ("line", "area"):
            series.format.line.color.rgb = rgb(colour)
            if kind == "area":
                series.format.fill.solid()
                series.format.fill.fore_color.rgb = rgb(colour)
        else:
            series.format.fill.solid()
            series.format.fill.fore_color.rgb = rgb(colour)

    # Emphasis: one category keeps slot 1, the rest go muted. Only meaningful on
    # a single-series bar chart, where hue is otherwise carrying no information.
    if emphasize is not None and kind not in ("line", "area"):
        series = plot.series[0]
        for i in range(n_points):
            point = series.points[i]
            point.format.fill.solid()
            point.format.fill.fore_color.rgb = rgb(
                categorical[0] if i == emphasize else muted)


def chart(slide, tk, kind, box, categories, series, emphasize=None,
          number_format=None):
    """Add a chart styled entirely by the `charts.<kind>` recipe.

    kind        one of CHART_TYPES / the recipes in the tokens' `charts`
    box         {x,y,w,h} in inches (pass a grid box's "chart_box")
    categories  list of category labels
    series      {name: [values]} -- insertion order fixes the colour order
    emphasize   index of the one category to highlight (others go muted)
    number_format  overrides the recipe default. How many decimals a figure
                needs is a property of the data, not of the brand, so the tokens
                only supply a sensible default and decimal data passes e.g.
                "0.0" or "0.0%" here.

    Returns the python-pptx Chart, so you can keep adjusting it directly.
    """
    if kind not in CHART_TYPES:
        raise ValueError(f"unknown chart kind '{kind}' (have: {', '.join(sorted(CHART_TYPES))})")

    rules = tk.get("rules", {})
    palette = tk["semantic"]["chart"]
    n_series, n_points = len(series), len(categories)

    max_series = min(rules.get("max_series", 8), len(palette["categorical"]))
    if n_series > max_series:
        raise ValueError(
            f"{n_series} series exceeds max_series={max_series}; fold the tail into "
            "'Other' or use small multiples rather than cycling colours")
    if kind == "pie":
        cap = tokens_mod.chart_spec(tk, "pie").get("max_slices", 6)
        if n_points > cap:
            raise ValueError(f"{n_points} slices exceeds pie max_slices={cap}; "
                             "group the tail into 'Other' or use a bar chart")
        if n_series != 1:
            raise ValueError("a pie chart takes exactly one series")
    if n_series == 1 and n_points == 1 and rules.get("single_value_use_kpi"):
        raise ValueError("a single value is not a chart; use build.kpi() instead")

    data = CategoryChartData()
    data.categories = categories
    for name, values in series.items():
        data.add_series(name, values)

    frame = slide.shapes.add_chart(CHART_TYPES[kind], *_emu_box(box), data)
    ch = frame.chart

    spec = tokens_mod.chart_spec(tk, kind)
    _apply_spec(ch, kind, spec, tk, n_series, n_points, number_format)
    _colour(ch, kind, tk, n_points, emphasize)
    return ch
