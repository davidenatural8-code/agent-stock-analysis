#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_institutional_pptx.py — Compilador Determinista Institucional de Pitch Deck (40 Diapositivas 16:9).

Integra de forma nativa los estándares de diseño y narrativa de:
- academic-pptx-skill: Títulos de acción declarativos (Action Titles 17.5–19.2 pt), prueba del Ghost Deck,
  composición visual izquierda→derecha (60% evidencia gráfica / 40% síntesis + KPIs), fondo blanco puro (#FFFFFF)
  y barra inferior de conclusión ejecutiva (Takeaway Bar).
- claude-pptx-skills: Tokens semánticos de diseño, eliminación total de sombras OOXML por defecto (effectRef idx="0"),
  micro-redondeo físico constante en pulgadas (adjustments[0] calibrado, cero deformación ovalada), sangría francesa
  real en viñetas (<a:pPr marL / indent>), tablas editoriales McKinsey con bordes horizontales limpios y alineación
  financiera inteligente, motor híbrido de gráficos (Vectorial Nativo OOXML editable + PNG 300 DPI escalado contain
  sin deformar aspect-ratio) y verificación estructural OOXML integrada.
- humanamente: Normalización tipográfica limpia y títulos directos sin ruido visual ni plantillas rígidas.

Uso:
    python build_institutional_pptx.py --target-dir "<COMPANY_DIR>" [--style mix|mckinsey|modern]
"""

import os
import sys
import re
import ast
import glob
import json
import math
import struct
import shutil
import zipfile
import argparse
import subprocess
import importlib.util
import xml.etree.ElementTree as ET

VENV_PY = r"C:\PROJECT\odoo-18.3\venv\Scripts\python.exe"
if os.path.exists(VENV_PY) and "venv" not in sys.prefix.lower():
    sys.exit(subprocess.call([VENV_PY] + sys.argv))

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.chart.data import CategoryChartData
from pptx.enum.chart import (
    XL_CHART_TYPE,
    XL_LEGEND_POSITION,
    XL_DATA_LABEL_POSITION,
    XL_TICK_MARK,
    XL_TICK_LABEL_POSITION,
)
from pptx.oxml.xmlchemy import OxmlElement

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ==============================================================================
# 1. TOKENS DE DISEÑO INSTITUCIONAL (MCKINSEY EDITORIAL + CLAUDE-PPTX-SKILLS)
# ==============================================================================
NAVY_DARK    = RGBColor(10, 25, 47)     # #0A192F - Primario institucional
NAVY_MED     = RGBColor(23, 37, 84)     # #172554 - Acento secundario
ROYAL_BLUE   = RGBColor(29, 78, 216)    # #1D4ED8 - Destacados cuantitativos / KPIs
GOLD_ACCENT  = RGBColor(180, 83, 9)     # #B45309 - Kicker / Eyebrow de alto contraste sobre blanco
GOLD_BRIGHT  = RGBColor(217, 119, 6)    # #D97706 - Línea de acento sobre fondos oscuros
EMERALD      = RGBColor(5, 150, 105)    # #059669 - Señal positiva / Compra / Alpha
EMERALD_BG   = RGBColor(236, 253, 245)  # #ECFDF5 - Superficie suave positiva
CRIMSON      = RGBColor(220, 38, 38)    # #DC2626 - Alerta / Riesgo / Venta
SLATE_INK    = RGBColor(15, 23, 42)     # #0F172A - Títulos secundarios y cifras
SLATE_BODY   = RGBColor(51, 65, 85)     # #334155 - Cuerpo de lectura descansada
SLATE_MUTED  = RGBColor(100, 116, 139)  # #64748B - Etiquetas, ejes y pie de página
SURFACE_SOFT = RGBColor(248, 250, 252)  # #F8FAFC - Fondo de tarjetas y zebra de tablas
SURFACE_TINT = RGBColor(241, 245, 249)  # #F1F5F9 - Píldoras neutras
HIGHLIGHT_BG = RGBColor(239, 246, 255)  # #EFF6FF - Fila total / KPI destacado
BORDER_LIGHT = RGBColor(226, 232, 240)  # #E2E8F0 - Reglas divisorias finas
BORDER_MED   = RGBColor(203, 213, 225)  # #CBD5E1 - Contorno sutil
WHITE        = RGBColor(255, 255, 255)  # #FFFFFF - Lienzo inmaculado

PML_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


# ==============================================================================
# 2. PRIMITIVAS OOXML LIMPIAS (CERO SOMBRAS, MICRO-RADIO CONSTANTE, SANGRÍA)
# ==============================================================================
def _load_humanamente_helpers():
    cand = os.path.join(os.path.dirname(os.path.abspath(__file__)), "humanamente_gate.py")
    if os.path.exists(cand):
        spec = importlib.util.spec_from_file_location("humanamente_gate", cand)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    return None


_HUMANAMENTE_MOD = _load_humanamente_helpers()


def clean_typography(s: str) -> str:
    """Normalización tipográfica castellana según vicentealvarezasencio/humanamente (P14, P18, P19)."""
    if not s:
        return ""
    out = str(s).strip()
    # P19: Comillas curvas inglesas -> comillas latinas « »
    out = out.replace("“", "«").replace("”", "»")
    # P18: Eliminar emojis accidentales
    if _HUMANAMENTE_MOD is not None:
        out = _HUMANAMENTE_MOD.EMOJI_RE.sub("", out)
    # P14: Sustituir raya inglesa con espacios (' — ' o ' -- ') por puntuación castellana limpia
    out = out.replace(" — ", ": " if len(out) < 75 and ":" not in out else ", ")
    out = out.replace(" -- ", ", ")
    out = out.replace(" -> ", " → ").replace("->", "→")
    out = re.sub(r"\s+", " ", out).strip()
    return out


def to_spanish_sentence_case_title(s: str) -> str:
    """
    Aplica la regla P17 de `humanamente` a titulares de diapositiva:
    En español solo llevan mayúscula la primera palabra (o primera tras ':') y los nombres propios o siglas.
    """
    txt = clean_typography(s)
    if not txt or _HUMANAMENTE_MOD is None:
        return txt

    def _fix_segment(seg: str) -> str:
        tokens = re.split(r"(\s+)", seg)
        seen_first_word = False
        out_toks = []
        for tok in tokens:
            if not tok or tok.isspace():
                out_toks.append(tok)
                continue
            # Separar puntuación inicial/final pegada a la palabra (ej. "(Módulo", "Superiores)")
            m = re.match(r"^([^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]*)([A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]+)([^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]*)$", tok)
            if not m:
                out_toks.append(tok)
                continue
            pre, core, post = m.groups()
            if not seen_first_word:
                if any(ch.isalpha() for ch in core):
                    seen_first_word = True
                out_toks.append(tok)
                continue
            if _HUMANAMENTE_MOD.is_mid_sentence_title_case_word(core):
                out_toks.append(f"{pre}{core.lower()}{post}")
            else:
                out_toks.append(tok)
        return "".join(out_toks)

    parts = re.split(r"(:\s+)", txt)
    fixed = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            fixed.append(part)
        else:
            fixed.append(_fix_segment(part))
    return "".join(fixed)


def clear_shadow(shape):
    """Desactiva por completo la sombra heredada y el effectRef por defecto de Office."""
    shape.shadow.inherit = False
    style = shape._element.find(f"{{{PML_NS}}}style")
    if style is not None:
        eff = style.find(f"{{{DML_NS}}}effectRef")
        if eff is not None:
            eff.set("idx", "0")


def add_clean_box(slide, x, y, w, h, fill_rgb=WHITE, border_rgb=None, border_pt=0.75, radius_in=0.0):
    """Crea un contenedor rectangular o micro-redondeado con radio físico constante en pulgadas."""
    if radius_in > 0.0:
        sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        min_dim = max(0.05, min(w, h))
        sh.adjustments[0] = min(0.45, radius_in / min_dim)
    else:
        sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid()
    sh.fill.fore_color.rgb = fill_rgb
    if border_rgb is None:
        sh.line.fill.background()
    else:
        sh.line.color.rgb = border_rgb
        sh.line.width = Pt(border_pt)
    clear_shadow(sh)
    sh.text_frame.text = ""
    return sh


def add_text(slide, x, y, w, h, text_str, size=11.5, bold=False, color=SLATE_INK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.14):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    p.line_spacing = line_spacing
    r = p.add_run()
    r.text = clean_typography(text_str)
    r.font.name = "Calibri"
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.color.rgb = color
    return tb


def split_lead_and_body(text_str: str):
    t = clean_typography(text_str)
    if ": " in t:
        lead, body = t.split(": ", 1)
        if 2 <= len(lead) <= 72:
            return lead.strip(), body.strip()
    return "", t


def estimate_bullets_height(bullets, box_w_in: float, font_pt: float, space_after_pt: float, line_spacing: float = 1.16) -> float:
    if not bullets:
        return 0.35
    usable_w = max(1.4, box_w_in - 0.24)
    char_w_in = 0.525 * (font_pt / 72.0)
    chars_per_line = max(20, int(usable_w / char_w_in))
    line_h_in = (font_pt * line_spacing) / 72.0
    total_h = 0.06
    for idx, b in enumerate(bullets):
        txt = clean_typography(b)
        n_lines = max(1, math.ceil((len(txt) + 3) / float(chars_per_line)))
        total_h += n_lines * line_h_in
        if idx < len(bullets) - 1:
            total_h += space_after_pt / 72.0
    return total_h


def fit_bullets_params(bullets, box_w_in: float, avail_h_in: float, max_pt: float = 14.2, min_pt: float = 11.2):
    font_pt = max_pt
    n_b = len(bullets) if bullets else 1
    while font_pt >= min_pt:
        base_h = estimate_bullets_height(bullets, box_w_in, font_pt, 0.0, 1.25)
        rem_h = avail_h_in - base_h
        if rem_h > 0 and n_b > 1:
            sp = min(26.0, max(9.0, (rem_h * 72.0) / float(n_b - 0.2)))
        elif rem_h > 0 and n_b == 1:
            sp = 0.0
        else:
            sp = 9.0 if font_pt >= 12.8 else (7.0 if font_pt >= 11.8 else 5.0)
        ls = 1.26 if font_pt >= 12.5 else 1.20
        if estimate_bullets_height(bullets, box_w_in, font_pt, sp, ls) <= avail_h_in:
            return font_pt, sp, ls
        font_pt = round(font_pt - 0.3, 2)
    return min_pt, 6.0, 1.18


def add_bullets(slide, x, y, w, h, items, max_font_pt=14.2, min_font_pt=11.2,
                bullet_char="▪", bullet_color=ROYAL_BLUE):
    """Renderiza viñetas con marcador garantizado en el 100% de los puntos y sangría francesa OOXML."""
    if not items:
        return None
    font_pt, space_after, line_spacing = fit_bullets_params(items, w, h, max_pt=max_font_pt, min_pt=min_font_pt)

    # Balanceo vertical sutil si sobra holgura considerable en tarjetas con pocas viñetas
    used_h = estimate_bullets_height(items, w, font_pt, space_after, line_spacing)
    if h > used_h + 0.35 and len(items) <= 3:
        y_offset = min(0.35, (h - used_h) * 0.25)
        y += y_offset
        h -= y_offset

    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    indent_emu = int(Inches(0.18))

    for idx, raw_item in enumerate(items):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(space_after if idx < len(items) - 1 else 0)
        p.line_spacing = line_spacing

        pPr = p._p.get_or_add_pPr()
        pPr.set("marL", str(indent_emu))
        pPr.set("indent", str(-indent_emu))

        r_bul = p.add_run()
        r_bul.text = f"{bullet_char}  "
        r_bul.font.name = "Calibri"
        r_bul.font.size = Pt(font_pt)
        r_bul.font.bold = True
        r_bul.font.color.rgb = bullet_color

        # P15 y P16 de humanamente: prosa fluida sin convertir cada viñeta en "**Término:** definición"
        item_clean = clean_typography(re.sub(r"\*\*(.+?)\*\*", r"\1", str(raw_item)))
        r_body = p.add_run()
        r_body.text = item_clean
        r_body.font.name = "Calibri"
        r_body.font.size = Pt(font_pt)
        r_body.font.bold = False
        r_body.font.color.rgb = SLATE_BODY
    return tb


# ==============================================================================
# 3. TABLAS EDITORIALES MCKINSEY & MOTOR HÍBRIDO DE GRÁFICOS (NATIVO + PNG 300DPI)
# ==============================================================================
def set_cell_border_xml(cell, top=None, bottom=None, left=None, right=None):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ("lnL", "lnR", "lnT", "lnB"):
        old = tcPr.find(f"{{{DML_NS}}}{tag}")
        if old is not None:
            tcPr.remove(old)

    def _make_ln(tag, spec):
        ln = OxmlElement(f"a:{tag}")
        if spec is None:
            ln.append(OxmlElement("a:noFill"))
        else:
            hex_c, pt_w = spec
            ln.set("w", str(int(Pt(pt_w))))
            sf = OxmlElement("a:solidFill")
            srgb = OxmlElement("a:srgbClr")
            srgb.set("val", hex_c.lstrip("#").upper())
            sf.append(srgb)
            ln.append(sf)
        return ln

    tcPr.append(_make_ln("lnL", left))
    tcPr.append(_make_ln("lnR", right))
    tcPr.append(_make_ln("lnT", top))
    tcPr.append(_make_ln("lnB", bottom))


NUMERIC_FIN_RE = re.compile(
    r"^[\~\+\-\—\(\)\$€£¥]*\s*(?:USD|CAD|EUR|HKD|CNY|RMB|GBP|JPY|CHF|AUD|BRL|CLP|MXN|C\$|US\$|HK\$|S\$)?\s*"
    r"[\+\-\—\(\)\$€£¥]?\d[\d\.,\s\/\-–]*\s*"
    r"(?:M|B|T|k|m|b|%|x|pts|bps|Moz|koz|t|g/t|d|días|años|a|/oz|/año|/acc\.?|/día|Yield|TER|NAV|cash|neto|com\.)*[\)]?$",
    re.IGNORECASE,
)


def is_financial_numeric(val: str) -> bool:
    v = clean_typography(val)
    if not v or len(v) > 36:
        return False
    if v in ("—", "-", "N/A", "n.a."):
        return True
    if re.match(r"^\d+(\.\d+)?\s*/\s*\d+(\.\d+)?$", v):
        return True
    return bool(NUMERIC_FIN_RE.match(v))


def add_mckinsey_table(slide, x, y, w, h, headers, rows, style="mix", col_ratios=None):
    r_cnt = len(rows) + 1
    c_cnt = len(headers)
    t_shape = slide.shapes.add_table(r_cnt, c_cnt, Inches(x), Inches(y), Inches(w), Inches(h))
    tbl = t_shape.table

    if col_ratios and len(col_ratios) == c_cnt:
        s_rat = float(sum(col_ratios))
        for ci, rat in enumerate(col_ratios):
            tbl.columns[ci].width = Inches((rat / s_rat) * w)
    elif c_cnt == 2:
        max_left = max([len(str(headers[0]))] + [len(str(r[0])) for r in rows])
        max_right = max([len(str(headers[1]))] + [len(str(r[1])) for r in rows])
        left_share = 0.36 if max_right > max_left * 1.25 else 0.44
        tbl.columns[0].width = Inches(w * left_share)
        tbl.columns[1].width = Inches(w * (1.0 - left_share))
    else:
        weights = []
        for ci in range(c_cnt):
            h_len = len(str(headers[ci]))
            mx = max([h_len] + [len(str(r[ci])) if ci < len(r) else 4 for r in rows])
            if ci == 0:
                mx = int(mx * 1.15)
            cap_w = 88 if c_cnt <= 4 else (65 if c_cnt == 5 else 48)
            weights.append(max(h_len + 3, min(cap_w, mx)))
        sw = float(sum(weights))
        for ci in range(c_cnt):
            tbl.columns[ci].width = Inches((weights[ci] / sw) * w)

    # Tamaño de fuente adaptativo según densidad de filas, columnas y longitud de celdas
    max_cell_chars = max([len(str(r[ci])) for r in rows for ci in range(min(len(r), c_cnt))] + [10])
    if r_cnt >= 10 or c_cnt >= 8:
        font_sz = 9.8
    elif r_cnt >= 8 or c_cnt >= 7 or max_cell_chars > 140:
        font_sz = 10.2
    elif r_cnt >= 7 or max_cell_chars > 105:
        font_sz = 10.8
    elif max_cell_chars > 78:
        font_sz = 11.2
    else:
        font_sz = 11.8

    row_h = h / float(r_cnt)
    for ri in range(r_cnt):
        tbl.rows[ri].height = Inches(row_h)

    hdr_bg = NAVY_DARK if style != "modern" else NAVY_MED
    col_is_num = []
    for ci in range(c_cnt):
        vals = [str(r[ci]) for r in rows if ci < len(r)]
        num_votes = sum(1 for v in vals if is_financial_numeric(v))
        col_is_num.append(ci > 0 and len(vals) > 0 and num_votes > (len(vals) / 2.0))

    for ci, h_txt in enumerate(headers):
        cell = tbl.cell(0, ci)
        cell.fill.solid()
        cell.fill.fore_color.rgb = hdr_bg
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = Inches(0.09 if c_cnt >= 7 else 0.11)
        cell.margin_right = Inches(0.09 if c_cnt >= 7 else 0.11)
        cell.margin_top = Inches(0.03)
        cell.margin_bottom = Inches(0.03)
        set_cell_border_xml(cell, top=("0A192F", 1.0), bottom=("D97706", 1.5))

        p = cell.text_frame.paragraphs[0]
        if ci == 0 or (c_cnt == 2 and not col_is_num[ci]):
            p.alignment = PP_ALIGN.LEFT
        elif col_is_num[ci]:
            p.alignment = PP_ALIGN.RIGHT
        else:
            p.alignment = PP_ALIGN.LEFT

        r = p.add_run()
        r.text = clean_typography(h_txt)
        r.font.name = "Calibri"
        r.font.size = Pt(font_sz)
        r.font.bold = True
        r.font.color.rgb = WHITE

    highlight_keys = (
        "total", "ponderado", "veredicto", "fcf", "free cash flow",
        "consenso medio", "valoración comité", "media peers", "beneish m-score consolidado",
    )

    for ri, r_vals in enumerate(rows):
        first_low = str(r_vals[0]).strip().lower() if r_vals else ""
        is_highlight = (ri == len(rows) - 1 and any(k in first_low for k in highlight_keys))
        for ci in range(c_cnt):
            val_str = clean_typography(r_vals[ci] if ci < len(r_vals) else "")
            cell = tbl.cell(ri + 1, ci)
            cell.fill.solid()
            if is_highlight:
                cell.fill.fore_color.rgb = HIGHLIGHT_BG
            elif ri % 2 == 1:
                cell.fill.fore_color.rgb = SURFACE_SOFT
            else:
                cell.fill.fore_color.rgb = WHITE

            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            cell.margin_left = Inches(0.09 if c_cnt >= 7 else 0.11)
            cell.margin_right = Inches(0.09 if c_cnt >= 7 else 0.11)
            cell.margin_top = Inches(0.03)
            cell.margin_bottom = Inches(0.03)

            b_bot = ("0A192F", 1.2) if ri == len(rows) - 1 else ("E2E8F0", 0.6)
            b_top = ("93C5FD", 0.9) if is_highlight else None
            set_cell_border_xml(cell, top=b_top, bottom=b_bot)

            p = cell.text_frame.paragraphs[0]
            if ci == 0:
                p.alignment = PP_ALIGN.LEFT
            elif c_cnt == 2 and not is_financial_numeric(val_str):
                p.alignment = PP_ALIGN.LEFT
            elif is_financial_numeric(val_str) or col_is_num[ci]:
                p.alignment = PP_ALIGN.RIGHT
            else:
                p.alignment = PP_ALIGN.LEFT

            r = p.add_run()
            r.text = val_str
            r.font.name = "Calibri"
            r.font.size = Pt(font_sz)
            r.font.bold = (ci == 0 or is_highlight)
            if is_highlight and ci > 0:
                r.font.color.rgb = ROYAL_BLUE
            elif ci == 0:
                r.font.color.rgb = NAVY_DARK
            else:
                r.font.color.rgb = SLATE_INK
    return t_shape


def _get_image_dimensions(img_path: str):
    try:
        from PIL import Image
        with Image.open(img_path) as im:
            return im.size
    except Exception:
        with open(img_path, "rb") as f:
            head = f.read(24)
        if len(head) >= 24 and head[:8] == b"\x89PNG\r\n\x1a\n":
            w_px, h_px = struct.unpack(">II", head[16:24])
            return int(w_px), int(h_px)
        return 1600, 900


def add_picture_contain(slide, img_path: str, x: float, y: float, w: float, h: float):
    """Incrusta un gráfico PNG de 300 DPI centrado dentro de (x,y,w,h) sin deformar jamás su proporción."""
    iw, ih = _get_image_dimensions(img_path)
    img_ratio = iw / float(max(1, ih))
    box_ratio = w / float(max(0.1, h))
    if img_ratio >= box_ratio:
        draw_w = w
        draw_h = w / img_ratio
        draw_x = x
        draw_y = y + (h - draw_h) / 2.0
    else:
        draw_h = h
        draw_w = h * img_ratio
        draw_y = y
        draw_x = x + (w - draw_w) / 2.0
    return slide.shapes.add_picture(
        img_path, Inches(draw_x), Inches(draw_y), width=Inches(draw_w), height=Inches(draw_h)
    )


def _nice_axis_bounds(all_vals):
    if not all_vals:
        return 0.0, 100.0, 20.0
    vmin = min(all_vals)
    vmax = max(all_vals)
    if vmin >= 0:
        raw_max = vmax * 1.18 if vmax > 0 else 10.0
        mag = 10 ** math.floor(math.log10(max(1e-6, raw_max)))
        for step_mult in (0.2, 0.25, 0.5, 1.0, 2.0, 2.5, 5.0, 10.0):
            unit = mag * step_mult
            if raw_max / unit <= 6.2:
                nice_max = math.ceil(raw_max / unit) * unit
                return 0.0, float(nice_max), float(unit)
        return 0.0, float(raw_max), float(raw_max / 5.0)
    else:
        span = max(abs(vmin), abs(vmax)) * 1.22
        mag = 10 ** math.floor(math.log10(max(1e-6, span)))
        unit = mag * 0.5 if (span / (mag * 0.5)) <= 4 else mag
        nice_min = -math.ceil((abs(vmin) * 1.22) / unit) * unit
        nice_max = math.ceil((abs(vmax) * 1.20) / unit) * unit
        return float(nice_min), float(nice_max), float(unit)


def add_native_chart(slide, x: float, y: float, w: float, h: float, spec: dict):
    """Construye un gráfico vectorial OOXML 100% nativo y editable en PowerPoint/Excel."""
    chart_data = CategoryChartData()
    categories = [str(c) for c in spec.get("categories", [])]
    chart_data.categories = categories
    series_list = spec.get("series", [])
    all_vals = []
    for s_name, s_vals in series_list:
        vals = [float(v) for v in s_vals]
        all_vals.extend(vals)
        chart_data.add_series(str(s_name), tuple(vals))

    ctype_str = str(spec.get("chart_type", "COLUMN_CLUSTERED")).upper()
    ctype_map = {
        "COLUMN_CLUSTERED": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "BAR_CLUSTERED": XL_CHART_TYPE.BAR_CLUSTERED,
        "LINE_MARKERS": XL_CHART_TYPE.LINE_MARKERS,
        "LINE": XL_CHART_TYPE.LINE,
    }
    xl_type = ctype_map.get(ctype_str, XL_CHART_TYPE.COLUMN_CLUSTERED)

    gf = slide.shapes.add_chart(xl_type, Inches(x), Inches(y), Inches(w), Inches(h), chart_data)
    chart = gf.chart
    chart.has_title = False
    chart.font.name = "Calibri"
    chart.font.size = Pt(9.0)

    chart.has_legend = True
    chart.legend.position = XL_LEGEND_POSITION.TOP
    chart.legend.include_in_layout = False
    chart.legend.font.name = "Calibri"
    chart.legend.font.size = Pt(9.0)

    plot = chart.plots[0]
    if xl_type in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.BAR_CLUSTERED):
        plot.gap_width = 85
        plot.overlap = -10

    palette = [NAVY_DARK, ROYAL_BLUE, EMERALD, GOLD_BRIGHT, SLATE_MUTED]
    num_fmt = spec.get("number_format", "$#,##0;-$#,##0;$0")
    if ";" not in num_fmt and min(all_vals or [0]) < 0 and "$" in num_fmt:
        num_fmt = f"{num_fmt};-{num_fmt};$0"
    lbl_idx = int(spec.get("label_series_idx", 0))
    used_colors = set()

    for idx, series in enumerate(plot.series):
        sname = series.name.lower()
        col = None
        if "efectivo" in sname or "fcf" in sname or "free cash" in sname or "caja libre" in sname:
            col = EMERALD
        elif "owner" in sname or "dividendo" in sname or "oro" in sname:
            col = GOLD_BRIGHT
        elif "margen" in sname or "ebitda" in sname or "roic" in sname:
            col = ROYAL_BLUE
        elif (
            ("deuda" in sname and "neta" not in sname)
            or "coste" in sname
            or ("aisc" in sname and "margen" not in sname)
            or "capex" in sname
        ):
            col = CRIMSON
        elif "neta" in sname or "ocf" in sname or "ingresos" in sname:
            col = NAVY_DARK

        if col is None or str(col) in used_colors:
            for p_col in palette + [CRIMSON]:
                if str(p_col) not in used_colors:
                    col = p_col
                    break
        if col is None:
            col = palette[idx % len(palette)]
        used_colors.add(str(col))

        if xl_type in (XL_CHART_TYPE.LINE_MARKERS, XL_CHART_TYPE.LINE):
            series.format.line.color.rgb = col
            series.format.line.width = Pt(2.2)
        else:
            series.invert_if_negative = False
            fill = series.format.fill
            fill.solid()
            fill.fore_color.rgb = col
            series.format.line.fill.background()

        if idx == lbl_idx:
            series.has_data_labels = True
            dl = series.data_labels
            dl.show_value = True
            dl.number_format = num_fmt
            if xl_type in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.BAR_CLUSTERED):
                dl.position = XL_DATA_LABEL_POSITION.OUTSIDE_END
            dl.font.name = "Calibri"
            dl.font.size = Pt(7.4 if len(series_list) >= 4 else 8.0)
            dl.font.bold = True
            dl.font.color.rgb = col

    vmin, vmax, vunit = _nice_axis_bounds(all_vals)
    val_axis = chart.value_axis
    val_axis.visible = True
    val_axis.minimum_scale = vmin
    val_axis.maximum_scale = vmax
    val_axis.major_unit = vunit
    val_axis.has_major_gridlines = True
    val_axis.major_gridlines.format.line.color.rgb = BORDER_LIGHT
    val_axis.major_gridlines.format.line.width = Pt(0.6)
    val_axis.format.line.fill.background()
    val_axis.major_tick_mark = XL_TICK_MARK.NONE
    val_axis.tick_labels.number_format = num_fmt
    val_axis.tick_labels.font.size = Pt(8.2)
    val_axis.tick_labels.font.color.rgb = SLATE_MUTED

    cat_axis = chart.category_axis
    cat_axis.major_tick_mark = XL_TICK_MARK.NONE
    if vmin < 0:
        cat_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    cat_axis.format.line.color.rgb = BORDER_MED
    cat_axis.format.line.width = Pt(0.75)
    cat_axis.tick_labels.font.size = Pt(9.0)
    cat_axis.tick_labels.font.bold = True
    cat_axis.tick_labels.font.color.rgb = NAVY_DARK
    return chart


# ==============================================================================
# 4. CHROME, TARJETAS EDITORIALES, KPI TILES Y TAKEAWAY BAR
# ==============================================================================
def add_chrome(slide, slide_num: int, total_slides: int, kicker: str, action_title: str,
               badge_text: str, company_label: str, style: str = "mix"):
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = WHITE

    kicker_clean = clean_typography(kicker)
    if len(kicker_clean) > 78:
        kicker_clean = kicker_clean[:75].rstrip(" ,;:-")

    title_clean = to_spanish_sentence_case_title(action_title)

    if style == "modern":
        add_clean_box(slide, 0.60, 0.16, 4.40, 0.25, fill_rgb=SURFACE_TINT, border_rgb=BORDER_LIGHT, border_pt=0.6, radius_in=0.10)
        add_text(slide, 0.72, 0.16, 4.16, 0.25, kicker_clean[:48].upper(), size=8.5, bold=True, color=NAVY_MED, anchor=MSO_ANCHOR.MIDDLE)
        add_clean_box(slide, 10.35, 0.16, 2.38, 0.25, fill_rgb=HIGHLIGHT_BG, border_rgb=ROYAL_BLUE, border_pt=0.6, radius_in=0.10)
        add_text(slide, 10.35, 0.16, 2.38, 0.25, badge_text.upper(), size=8.4, bold=True, color=ROYAL_BLUE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    else:
        add_clean_box(slide, 0, 0, 13.333, 0.05, fill_rgb=NAVY_DARK)
        add_clean_box(slide, 0, 0, 2.65, 0.05, fill_rgb=GOLD_BRIGHT)
        add_text(slide, 0.60, 0.16, 9.40, 0.23, kicker_clean.upper(), size=9.2, bold=True, color=GOLD_ACCENT)
        r_pill = 0.08 if style == "mix" else 0.0
        add_clean_box(slide, 10.35, 0.14, 2.38, 0.24, fill_rgb=HIGHLIGHT_BG, border_rgb=ROYAL_BLUE, border_pt=0.6, radius_in=r_pill)
        add_text(slide, 10.35, 0.14, 2.38, 0.24, badge_text.upper(), size=8.4, bold=True, color=ROYAL_BLUE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    if len(title_clean) > 105:
        t_sz = 16.2
    elif len(title_clean) > 85:
        t_sz = 17.4
    else:
        t_sz = 18.8

    add_text(slide, 0.60, 0.41, 12.133, 0.65, title_clean, size=t_sz, bold=True, color=NAVY_DARK, line_spacing=1.07)
    add_clean_box(slide, 0.60, 1.12, 12.133, 0.015 if style != "modern" else 0.01,
                  fill_rgb=NAVY_DARK if style != "modern" else BORDER_LIGHT)

    # Footer compatible al 100% con gauntlet_gatekeeper.py (incluye "PITCH DECK" y "DIAPOSITIVA")
    add_clean_box(slide, 0.60, 7.12, 12.133, 0.008, fill_rgb=BORDER_LIGHT)
    left_ftr = f"{company_label.upper()}  ·  PITCH DECK INSTITUCIONAL BUYSIDE"
    add_text(slide, 0.60, 7.16, 9.10, 0.22, left_ftr, size=8.4, bold=False, color=SLATE_MUTED)
    add_text(slide, 9.80, 7.16, 2.933, 0.22, f"DIAPOSITIVA {slide_num:02d} DE {total_slides:02d}",
             size=8.4, bold=True, color=NAVY_DARK, align=PP_ALIGN.RIGHT)


def add_editorial_card(slide, x, y, w, h, title_str="", accent_color=NAVY_DARK, fill_rgb=SURFACE_SOFT, style="mix") -> float:
    """Tarjeta sin barra superior oscura: devuelve el desplazamiento vertical (hdr_pad) donde empieza el cuerpo."""
    usable_w = max(1.8, w - 0.34)
    if style == "modern":
        add_clean_box(slide, x, y, w, h, fill_rgb=fill_rgb, border_rgb=BORDER_LIGHT, border_pt=0.85, radius_in=0.06)
        if not title_str:
            return 0.12
        t_disp = clean_typography(title_str)
        cap_10 = int(usable_w * 12.0)
        t_sz = 10.6 if len(t_disp) <= cap_10 else 9.4
        cap_eff = int(usable_w * (12.0 if t_sz >= 10.4 else 13.5))
        hdr_lines = max(1, min(2, math.ceil(len(t_disp) / max(14, cap_eff))))
        th = 0.24 if hdr_lines == 1 else 0.40
        div_y = 0.38 if hdr_lines == 1 else 0.54
        add_text(slide, x + 0.18, y + 0.10, w - 0.34, th, t_disp, size=t_sz, bold=True, color=NAVY_DARK, line_spacing=1.08)
        add_clean_box(slide, x + 0.18, y + div_y, w - 0.36, 0.008, fill_rgb=BORDER_LIGHT)
        return 0.45 if hdr_lines == 1 else 0.62
    else:
        add_clean_box(slide, x, y, w, h, fill_rgb=fill_rgb, border_rgb=BORDER_LIGHT, border_pt=0.75, radius_in=0.0)
        add_clean_box(slide, x, y, 0.055, h, fill_rgb=accent_color)
        if not title_str:
            return 0.12
        t_disp = clean_typography(title_str).upper()
        cap_10 = int(usable_w * 11.2)
        cap_9 = int(usable_w * 12.6)
        if len(t_disp) <= cap_10:
            t_sz = 10.0
            hdr_lines = 1
        elif len(t_disp) <= cap_9:
            t_sz = 9.0
            hdr_lines = 1
        else:
            t_sz = 8.8
            cap_88 = int(usable_w * 12.8)
            hdr_lines = max(1, min(2, math.ceil(len(t_disp) / max(14, cap_88))))
        th = 0.24 if hdr_lines == 1 else 0.40
        div_y = 0.37 if hdr_lines == 1 else 0.53
        add_text(slide, x + 0.18, y + 0.09, w - 0.30, th, t_disp, size=t_sz, bold=True, color=accent_color, line_spacing=1.06)
        add_clean_box(slide, x + 0.18, y + div_y, w - 0.32, 0.008, fill_rgb=BORDER_LIGHT)
        return 0.45 if hdr_lines == 1 else 0.61


def add_kpi_tile(slide, x, y, w, h, val: str, lbl: str, sub: str = "", style: str = "mix", highlight: bool = False):
    v_clean = clean_typography(val)
    l_clean = clean_typography(lbl)
    s_clean = clean_typography(sub)

    if style == "mckinsey":
        add_clean_box(slide, x, y, w, h, fill_rgb=WHITE, border_rgb=BORDER_MED, border_pt=0.75, radius_in=0.0)
        add_clean_box(slide, x, y, w, 0.045, fill_rgb=ROYAL_BLUE if highlight else NAVY_DARK)
    else:
        # En "mix" y "modern" usamos las tarjetas KPI micro-redondeadas r=0.055" sin sombras
        add_clean_box(
            slide, x, y, w, h,
            fill_rgb=HIGHLIGHT_BG if highlight else SURFACE_SOFT,
            border_rgb=ROYAL_BLUE if highlight else BORDER_LIGHT,
            border_pt=0.85, radius_in=0.055,
        )

    add_text(slide, x + 0.14, y + 0.10, w - 0.28, 0.20, l_clean.upper()[:36], size=8.6, bold=True, color=SLATE_MUTED)
    val_sz = 19.5 if len(v_clean) <= 12 else (16.5 if len(v_clean) <= 17 else 14.0)
    add_text(slide, x + 0.14, y + 0.31, w - 0.28, 0.40, v_clean, size=val_sz, bold=True,
             color=ROYAL_BLUE if highlight else NAVY_DARK)
    if s_clean:
        sub_col = EMERALD if any(k in s_clean for k in ("+", "Caja", "Yield", "TER", "Gratis", "Óptimo", "Segura")) else SLATE_BODY
        sub_sz = 8.5 if len(s_clean) <= 36 else 7.8
        sub_h = max(0.26, h - 0.72)
        add_text(slide, x + 0.14, y + 0.72, w - 0.28, sub_h, s_clean, size=sub_sz, bold=False, color=sub_col, line_spacing=1.06)


def add_takeaway_bar(slide, y: float, text_body: str, style: str = "mix"):
    if not text_body:
        return
    t_clean = clean_typography(text_body)
    lead, body = split_lead_and_body(t_clean)
    prefix = f"{lead.upper()}:  " if (lead and len(lead) <= 36) else "CONCLUSIÓN DEL COMITÉ:  "
    content = body if (lead and len(lead) <= 36) else t_clean

    if style == "modern":
        add_clean_box(slide, 0.60, y, 12.133, 0.48, fill_rgb=NAVY_DARK, radius_in=0.055)
        lead_col, body_col = GOLD_BRIGHT, WHITE
    else:
        add_clean_box(slide, 0.60, y, 12.133, 0.48, fill_rgb=HIGHLIGHT_BG, border_rgb=BORDER_LIGHT, border_pt=0.6)
        add_clean_box(slide, 0.60, y, 0.06, 0.48, fill_rgb=ROYAL_BLUE)
        lead_col, body_col = ROYAL_BLUE, NAVY_DARK

    tb = slide.shapes.add_textbox(Inches(0.78), Inches(y + 0.02), Inches(11.80), Inches(0.44))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]
    p.line_spacing = 1.08

    sz = 10.2 if len(prefix) + len(content) <= 155 else 9.5
    r1 = p.add_run()
    r1.text = prefix
    r1.font.name = "Calibri"
    r1.font.size = Pt(sz)
    r1.font.bold = True
    r1.font.color.rgb = lead_col

    r2 = p.add_run()
    r2.text = content
    r2.font.name = "Calibri"
    r2.font.size = Pt(sz)
    r2.font.bold = False
    r2.font.color.rgb = body_col


# ==============================================================================
# 5. PARSER SEGURO (AST SIN EFECTOS SECUNDARIOS) Y NORMALIZACIÓN DE ESPECIFICACIONES
# ==============================================================================
def _safe_extract_vars_from_py(py_path: str, var_names):
    """Extrae variables literales de un script .py con ast.literal_eval sin ejecutar código top-level."""
    found = {}
    if not os.path.exists(py_path):
        return found
    try:
        with open(py_path, "r", encoding="utf-8-sig") as f:
            src = f.read()
        tree = ast.parse(src, filename=py_path)
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in var_names:
                        try:
                            found[target.id] = ast.literal_eval(node.value)
                        except Exception:
                            pass
    except Exception:
        pass
    return found


def _fallback_import_module(py_path: str):
    mod_name = f"_deck_spec_{os.path.splitext(os.path.basename(py_path))[0]}"
    spec = importlib.util.spec_from_file_location(mod_name, py_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _is_mostly_upper(s: str) -> bool:
    letters = [ch for ch in s if ch.isalpha()]
    if not letters:
        return False
    return (sum(1 for ch in letters if ch.isupper()) / float(len(letters))) >= 0.72


def _extract_module_badge(slide_num: int, *texts) -> str:
    joined = " | ".join(str(t or "") for t in texts)
    m = re.search(r"M[ÓO]DULO[S]?\s*(\d{1,2}(?:[\.\–\-]\d{1,2})?)", joined, re.IGNORECASE)
    if m:
        return f"SLIDE {slide_num:02d} · MÓD. {m.group(1)}"
    return f"SLIDE {slide_num:02d}"


def load_company_context(target_dir: str) -> dict:
    ctx = {
        "company_name": os.path.basename(target_dir),
        "ticker": "",
        "secondary_ticker": "",
        "exchange": "",
        "country": "",
        "currency": "USD",
        "summary_kpis": {},
    }
    candidates = [
        os.path.join(target_dir, "extracted_ocr_cache", "company_meta.json"),
        os.path.join(target_dir, "company_meta.json"),
        os.path.join(target_dir, "extracted_ocr_cache", "forensic_metrics.json"),
        os.path.join(target_dir, "forensic_metrics.json"),
        os.path.join(target_dir, "company_summary.json"),
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                if data.get("company_name"):
                    ctx["company_name"] = data["company_name"]
                if data.get("primary_ticker") or data.get("ticker"):
                    ctx["ticker"] = data.get("primary_ticker") or data.get("ticker")
                if data.get("secondary_ticker"):
                    ctx["secondary_ticker"] = data["secondary_ticker"]
                if data.get("exchange"):
                    ctx["exchange"] = data["exchange"]
                if data.get("country"):
                    ctx["country"] = data["country"]
                if data.get("trading_currency") or data.get("currency"):
                    ctx["currency"] = data.get("trading_currency") or data.get("currency")
                if isinstance(data.get("summary_kpis"), dict):
                    ctx["summary_kpis"].update(data["summary_kpis"])
            except Exception:
                pass
    return ctx


def load_normalized_slides(target_dir: str) -> list:
    # 1. JSON declarativo previo si ya cuenta con 60 slides (rango 58-65)
    json_deck = os.path.join(target_dir, "slides_deck.json")
    if os.path.exists(json_deck):
        try:
            with open(json_deck, "r", encoding="utf-8-sig") as f:
                raw_list = json.load(f)
            if len(raw_list) >= 58:
                return _normalize_dict_slides(raw_list, target_dir)
        except Exception:
            pass

    # 2. Generador dinámico universal de 60 slides desde *_INFORME_COMITE_FINAL.md
    try:
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        shared_engine = os.path.join(os.path.dirname(target_dir), "_shared_engine")
        for cand in (cur_dir, shared_engine, target_dir):
            if cand and os.path.exists(cand) and cand not in sys.path:
                sys.path.insert(0, cand)
        from build_slides_deck_json import get_60_slides_spec
        spec_60 = get_60_slides_spec(target_dir)
        if len(spec_60) >= 58:
            with open(json_deck, "w", encoding="utf-8") as f:
                json.dump(spec_60, f, ensure_ascii=False, indent=2)
            print(f"[PPTX] Generadas automáticamente {len(spec_60)} diapositivas institucionales con build_slides_deck_json.")
            return _normalize_dict_slides(spec_60, target_dir)
    except Exception as e:
        print(f"[PPTX] Aviso en generador automático de 60 slides ({e}), evaluando scripts locales...")

    # 2. generate_pptx.py o build_deliverables*.py vía AST seguro (sin ejecutar código top-level)
    cand_py_files = [os.path.join(target_dir, "generate_pptx.py")]
    cand_py_files.extend(sorted(glob.glob(os.path.join(target_dir, "build_deliverables*.py"))))
    cand_py_files.extend(sorted(glob.glob(os.path.join(target_dir, "build_*slides*.py"))))
    for gen_py in cand_py_files:
        if os.path.exists(gen_py):
            vars_found = _safe_extract_vars_from_py(
                gen_py,
                {"slides_spec", "SLIDES_DATA", "slides_data", "NATIVE_CHARTS_BY_SLIDE", "KPIS_BY_SLIDE"},
            )
            if not vars_found.get("slides_spec") and not vars_found.get("SLIDES_DATA") and not vars_found.get("slides_data"):
                try:
                    mod = _fallback_import_module(gen_py)
                    for k in ("slides_spec", "SLIDES_DATA", "slides_data", "NATIVE_CHARTS_BY_SLIDE", "KPIS_BY_SLIDE"):
                        if hasattr(mod, k):
                            vars_found[k] = getattr(mod, k)
                except Exception:
                    pass

            native_map = vars_found.get("NATIVE_CHARTS_BY_SLIDE") or {}
            kpis_map = vars_found.get("KPIS_BY_SLIDE") or {}
            if vars_found.get("slides_spec"):
                return _normalize_tuple_slides(vars_found["slides_spec"], target_dir, native_map, kpis_map)
            if vars_found.get("SLIDES_DATA") or vars_found.get("slides_data"):
                return _normalize_dict_slides(vars_found.get("SLIDES_DATA") or vars_found.get("slides_data"), target_dir)

    # 3. slides_data*p1*.py / slides_data*p2*.py / slides_data*.py
    p1_files = sorted(glob.glob(os.path.join(target_dir, "slides_data_*p1*.py")))
    p2_files = sorted(glob.glob(os.path.join(target_dir, "slides_data_*p2*.py")))
    if p1_files and p2_files:
        v1 = _safe_extract_vars_from_py(p1_files[0], {"slides_p1", "slides_data", "SLIDES_DATA"})
        v2 = _safe_extract_vars_from_py(p2_files[0], {"slides_p2", "slides_data", "SLIDES_DATA"})
        s1 = v1.get("slides_p1") or v1.get("slides_data") or v1.get("SLIDES_DATA") or []
        s2 = v2.get("slides_p2") or v2.get("slides_data") or v2.get("SLIDES_DATA") or []
        if not s1 or not s2:
            mod1 = _fallback_import_module(p1_files[0])
            mod2 = _fallback_import_module(p2_files[0])
            s1 = getattr(mod1, "slides_p1", getattr(mod1, "slides_data", []))
            s2 = getattr(mod2, "slides_p2", getattr(mod2, "slides_data", []))
        if s1 or s2:
            return _normalize_dict_slides(list(s1) + list(s2), target_dir)

    for sdf in sorted(glob.glob(os.path.join(target_dir, "slides_data*.py"))):
        vs = _safe_extract_vars_from_py(sdf, {"slides_data", "slides", "SLIDES_DATA"})
        raw = vs.get("slides_data") or vs.get("slides") or vs.get("SLIDES_DATA")
        if not raw:
            try:
                mod = _fallback_import_module(sdf)
                for attr in ("slides_data", "slides", "SLIDES_DATA"):
                    if hasattr(mod, attr):
                        raw = getattr(mod, attr)
                        break
            except Exception:
                pass
        if raw:
            return _normalize_dict_slides(raw, target_dir)

    raise FileNotFoundError(f"No se encontraron especificaciones de diapositivas en {target_dir}")


def _resolve_chart_path(target_dir: str, chart_ref: str):
    if not chart_ref:
        return None
    base = os.path.basename(chart_ref)
    # 1. Prioridad: Buscar en la carpeta charts del target_dir actual por nombre base
    cand_local = os.path.join(target_dir, "charts", base)
    if os.path.exists(cand_local):
        return cand_local
    # 2. Buscar como ruta relativa a target_dir
    cand1 = os.path.join(target_dir, chart_ref)
    if os.path.exists(cand1):
        return cand1
    # 3. Búsqueda por prefijo numérico chartN*.png en target_dir/charts
    m = re.match(r"^(chart_?0?(\d+))", base, re.IGNORECASE)
    if m:
        c_num = m.group(2)
        matches = sorted(glob.glob(os.path.join(target_dir, "charts", f"chart{c_num}*.png")))
        if matches:
            return matches[0]
        matches = sorted(glob.glob(os.path.join(target_dir, "charts", f"chart_{c_num}*.png")))
        if matches:
            return matches[0]
    # 4. Fallback si existe la ruta absoluta indicada
    if os.path.exists(chart_ref):
        return chart_ref
    return None


def _normalize_tuple_slides(slides_spec: list, target_dir: str, native_map: dict, kpis_map: dict) -> list:
    norm = []
    for item in slides_spec:
        num = int(item[0])
        raw_title = clean_typography(item[1])
        raw_sub = clean_typography(item[2])
        raw_box = clean_typography(item[3])
        bullets = [clean_typography(b) for b in (item[4] or []) if str(b).strip()]
        tbl_hdr = list(item[5]) if item[5] else None
        tbl_rows = [list(r) for r in item[6]] if item[6] else None
        chart_ref = item[7] if len(item) > 7 else None
        native_spec = item[8] if len(item) > 8 and isinstance(item[8], dict) else native_map.get(num)
        kpis_spec = item[9] if len(item) > 9 and isinstance(item[9], list) else kpis_map.get(num)

        badge = _extract_module_badge(num, raw_box, raw_sub, raw_title)

        # Si el título era una etiqueta en MAYÚSCULAS y el subtítulo contiene la tesis declarativa,
        # promovemos el subtítulo a Action Title y dejamos la etiqueta como Kicker superior.
        if num > 1 and _is_mostly_upper(raw_title) and raw_sub and len(raw_sub) >= 24 and not _is_mostly_upper(raw_sub):
            kicker = raw_title
            action_title = raw_sub
        else:
            kicker = raw_sub or raw_box or f"DIAPOSITIVA {num:02d}"
            action_title = raw_title

        norm.append({
            "num": num,
            "badge": badge,
            "kicker": kicker,
            "title": action_title,
            "raw_title": raw_title,
            "raw_sub": raw_sub,
            "box_title": raw_box,
            "bullets": bullets,
            "tbl_hdr": tbl_hdr,
            "tbl_rows": tbl_rows,
            "chart_path": _resolve_chart_path(target_dir, chart_ref),
            "native_chart": native_spec,
            "kpis": kpis_spec,
            "takeaway": "",
        })
    return norm


def _normalize_dict_slides(raw_list: list, target_dir: str) -> list:
    norm = []
    for idx, s in enumerate(raw_list, start=1):
        num = int(s.get("num", idx))
        raw_kicker = clean_typography(s.get("kicker") or s.get("section") or s.get("subtitle") or f"MÓDULO {num:02d}")
        raw_title = clean_typography(s.get("title") or "")
        raw_sub = clean_typography(s.get("subtitle") or "")
        raw_box = clean_typography(s.get("box_title") or raw_sub or raw_kicker)

        bullets = [clean_typography(b) for b in s.get("bullets", []) if str(b).strip()]
        cards = s.get("cards", [])
        if not bullets and cards:
            for c_item in cards:
                if isinstance(c_item, (list, tuple)) and len(c_item) >= 2:
                    bullets.extend([clean_typography(b) for b in c_item[1] if str(b).strip()])

        tbl_hdr, tbl_rows = None, None
        tdata = s.get("table")
        if isinstance(tdata, dict):
            tbl_hdr = list(tdata.get("headers") or [])
            tbl_rows = [list(r) for r in (tdata.get("rows") or [])]
        elif isinstance(tdata, list) and len(tdata) >= 2:
            tbl_hdr = list(tdata[0])
            tbl_rows = [list(r) for r in tdata[1:]]

        # Normalizar KPIs a tuplas (valor, etiqueta, subtexto)
        norm_kpis = []
        for k in (s.get("kpis") or []):
            if isinstance(k, (list, tuple)) and len(k) >= 2:
                k0, k1 = str(k[0]), str(k[1])
                k2 = str(k[2]) if len(k) >= 3 else ""
                # Detectar si k0 es la etiqueta en mayúsculas y k1 es el número
                if is_financial_numeric(k1) and not is_financial_numeric(k0):
                    norm_kpis.append((k1, k0, k2))
                else:
                    norm_kpis.append((k0, k1, k2))
            elif isinstance(k, dict):
                norm_kpis.append((str(k.get("value", "")), str(k.get("label", "")), str(k.get("sub", ""))))

        chart_ref = (
            s.get("chart")
            or s.get("chart_file")
            or s.get("chart_path")
            or s.get("chart_ref")
            or s.get("chart_png")
        )
        takeaway = clean_typography(s.get("takeaway") or s.get("bottom_notes") or "")
        badge = _extract_module_badge(num, raw_kicker, raw_box, raw_title)

        norm.append({
            "num": num,
            "badge": badge,
            "kicker": raw_kicker,
            "title": raw_title,
            "raw_title": raw_title,
            "raw_sub": raw_sub,
            "box_title": raw_box,
            "bullets": bullets,
            "tbl_hdr": tbl_hdr,
            "tbl_rows": tbl_rows,
            "chart_path": _resolve_chart_path(target_dir, chart_ref),
            "native_chart": s.get("native_chart"),
            "kpis": norm_kpis or None,
            "takeaway": takeaway,
            "cards": cards,
        })
    return norm


# ==============================================================================
# 6. EXTRACCIÓN INTELIGENTE DE KPIs PARA PORTADA, GRÁFICOS Y CIERRE
# ==============================================================================
def build_cover_kpis(sdata: dict, ctx: dict) -> list:
    if sdata.get("kpis") and len(sdata["kpis"]) >= 4:
        return sdata["kpis"][:4]

    sk = ctx.get("summary_kpis") or {}
    ccy = sk.get("currency") or ctx.get("currency") or ""
    price = sk.get("current_price")
    fv = sk.get("fair_value_base")
    upside = sk.get("upside_pct")
    verdict = sk.get("verdict")
    conv = sk.get("conviction_score")
    pe = sk.get("pe_trailing") or sk.get("pe_forward")
    eveb = sk.get("ev_ebitda")
    fcfy = sk.get("fcf_yield_pct")
    roic = sk.get("roic_pct")
    wacc = sk.get("wacc_pct")
    altz = sk.get("altman_z")

    if price is not None and fv is not None and verdict:
        sub1_parts = []
        if pe:
            sub1_parts.append(f"P/E {pe:.2f}x")
        if eveb:
            sub1_parts.append(f"EV/EBITDA {eveb:.2f}x")
        sub1 = "  |  ".join(sub1_parts) if sub1_parts else f"Bolsa: {ctx.get('exchange', 'Primaria')}"

        sub2 = f"{upside:+.1f}% Potencial Base" if upside is not None else "Valoración Multi-Método"

        if fcfy is not None:
            val3 = f"{fcfy:.2f}%"
            lbl3 = "FCF Yield Auditado"
            sub3 = f"ROIC {roic:.1f}% vs WACC {wacc:.2f}%" if (roic is not None and wacc is not None) else "Flujo de Caja Libre"
        elif roic is not None:
            val3 = f"{roic:.1f}%"
            lbl3 = "ROIC Operativo"
            sub3 = f"Spread positivo vs WACC {wacc:.2f}%" if wacc is not None else "Creación de valor"
        else:
            val3, lbl3, sub3 = "VERIFICADO", "Auditoría Forense", f"Altman Z: {altz}" if altz else "Estados Auditados"

        sub4 = f"Score {conv:.2f}/10" if conv is not None else "Dictamen Comité"
        if sk.get("recommended_weight_pct"):
            sub4 += f"  |  {sk['recommended_weight_pct']}"

        return [
            (f"{ccy} {price:,.2f}".strip(), "Cotización de Referencia", sub1, False),
            (f"{ccy} {fv:,.2f}".strip(), "Valor Intrínseco Comité", sub2, True),
            (val3, lbl3, sub3, False),
            (str(verdict).upper(), "Veredicto & Sizing", sub4, True),
        ]

    # Fallback desde tabla de portada
    tiles = []
    for r in (sdata.get("tbl_rows") or [])[:4]:
        if len(r) >= 2:
            v_main = str(r[1]).split("/")[0].split("|")[0].strip()
            tiles.append((v_main[:18], str(r[0])[:30], "", len(tiles) % 2 == 1))
    return tiles


def derive_chart_side_kpis(sdata: dict) -> list:
    if sdata.get("kpis") and len(sdata["kpis"]) >= 2:
        res = []
        for idx, k in enumerate(sdata["kpis"][:2]):
            if len(k) >= 4:
                res.append(k)
            elif len(k) == 3:
                res.append((k[0], k[1], k[2], idx == 0))
            else:
                res.append((k[0], k[1], "", idx == 0))
        return res

    nc = sdata.get("native_chart")
    if isinstance(nc, dict) and len(nc.get("series", [])) >= 2 and nc.get("categories"):
        cats = nc["categories"]
        last_cat = cats[-1]
        s_list = nc["series"]
        fmt_curr = "$" if "$" in str(nc.get("number_format", "")) else ""
        picks = [s_list[0], s_list[-1] if len(s_list) > 2 else s_list[1]]
        out = []
        for idx, (sname, svals) in enumerate(picks):
            v = svals[-1]
            v_str = f"-{fmt_curr}{abs(v):,.0f}" if v < 0 else f"{fmt_curr}{v:,.0f}"
            lbl = re.sub(r"\s*\(.*?\)", "", str(sname)).strip()
            out.append((v_str, lbl, f"Cierre {last_cat}", idx == 0))
        return out

    # Extracción determinista de métricas etiquetadas en las viñetas de la diapositiva
    metric_patterns = [
        (r"ROIC[^0-9\n]{0,25}?(\d{1,2}[\.,]\d{1,2}%)", "ROIC Operativo", "Creación de valor vs WACC"),
        (r"WACC[^0-9\n]{0,18}?(\d{1,2}[\.,]\d{1,2}%)", "Coste Capital WACC", "Tasa descuento auditada"),
        (r"RSI[^0-9\n]{0,18}?(\d{2}[\.,]\d{1,2})", "RSI (14 Sesiones)", "Nivel técnico actual"),
        (r"SOTP[^0-9\n]{0,22}?((?:CAD|USD|EUR|HKD|HK\$|C\$|\$)\s?\d+[\.,]\d{2})", "Valor SOTP NAV", "Suma de las partes"),
        (r"DCF[^0-9\n]{0,22}?((?:CAD|USD|EUR|HKD|HK\$|C\$|\$)\s?\d+[\.,]\d{2})", "Valor Intrínseco DCF", "Flujos descontados"),
        (r"margen\s+(?:bruto|ebitda|ebit)[^0-9\n]{0,30}?(\d{2}[\.,]\d{1,2}%)", "Margen Operativo", "Rentabilidad auditada"),
        (r"((?:USD|CAD|EUR|HKD|RMB)\s?\d[\d\.,]*M)\s+de\s+(?:FCF|flujo|EBIT|ingresos)", "Magnitud Clave", "Dato verificado"),
    ]
    joined = "  ".join(sdata.get("bullets") or [])
    found = []
    seen_lbls = set()
    for pat, lbl, sub in metric_patterns:
        m = re.search(pat, joined, re.IGNORECASE)
        if m and lbl not in seen_lbls:
            seen_lbls.add(lbl)
            found.append((m.group(1).strip(), lbl, sub, len(found) == 0))
            if len(found) == 2:
                return found
    return []


# ==============================================================================
# 7. ARQUETIPOS DE COMPOSICIÓN EJECUTIVA (1 A 40 SIN MONOTONÍA NI DESBORDES)
# ==============================================================================
def render_cover_slide(slide, sdata: dict, total_slides: int, company_label: str, ctx: dict, style: str):
    slide.background.fill.solid()
    slide.background.fill.fore_color.rgb = WHITE

    eyebrow = clean_typography(sdata.get("raw_sub") or sdata.get("kicker") or "MEMORANDO DEL COMITÉ DE INVERSIONES")
    comp_title = clean_typography(sdata.get("raw_title") or company_label)
    bullets = list(sdata.get("bullets") or [])

    # Construir subtítulo ejecutivo a partir de tesis / primera conclusión
    sk = ctx.get("summary_kpis") or {}
    if len(bullets) >= 4:
        hero_thesis = bullets[2] if len(bullets[2]) > 55 else bullets[0]
        card_bullets = [b for b in bullets if b != hero_thesis]
    elif bullets:
        hero_thesis = bullets[0]
        card_bullets = bullets[1:] if len(bullets) > 1 else bullets
    else:
        hero_thesis = eyebrow
        card_bullets = []

    if style == "modern":
        add_clean_box(slide, 0.60, 0.28, 12.133, 2.28, fill_rgb=SURFACE_SOFT, border_rgb=BORDER_LIGHT, border_pt=1.0, radius_in=0.08)
        add_clean_box(slide, 0.84, 0.48, 5.40, 0.26, fill_rgb=HIGHLIGHT_BG, border_rgb=ROYAL_BLUE, border_pt=0.6, radius_in=0.10)
        add_text(slide, 0.84, 0.48, 5.40, 0.26, eyebrow[:64].upper(), size=8.6, bold=True, color=ROYAL_BLUE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        add_text(slide, 0.84, 0.86, 11.60, 0.56, comp_title, size=26.0, bold=True, color=SLATE_INK)
        add_text(slide, 0.84, 1.48, 11.60, 0.92, hero_thesis, size=12.6, color=SLATE_BODY, line_spacing=1.20)
        kpi_y = 2.74
    else:
        add_clean_box(slide, 0, 0, 13.333, 2.58, fill_rgb=NAVY_DARK)
        add_clean_box(slide, 0, 2.58, 13.333, 0.05, fill_rgb=GOLD_BRIGHT)
        add_text(slide, 0.60, 0.22, 9.60, 0.24, eyebrow.upper(), size=9.5, bold=True, color=GOLD_BRIGHT)
        verdict_tag = str(sk.get("verdict") or "AUDITORÍA BUYSIDE").upper()
        add_clean_box(slide, 10.45, 0.20, 2.28, 0.28, fill_rgb=EMERALD if "COMPRA" in verdict_tag or "BUY" in verdict_tag else ROYAL_BLUE, radius_in=0.05 if style == "mix" else 0.0)
        add_text(slide, 10.45, 0.20, 2.28, 0.28, f"DICTAMEN: {verdict_tag}", size=8.8, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        title_sz = 21.0 if len(comp_title) > 60 else 24.5
        add_text(slide, 0.60, 0.52, 12.133, 0.88, comp_title, size=title_sz, bold=True, color=WHITE, line_spacing=1.14)
        add_text(slide, 0.60, 1.48, 12.00, 0.95, hero_thesis, size=12.4, color=RGBColor(226, 232, 240), line_spacing=1.20)
        kpi_y = 2.80

    kpis = build_cover_kpis(sdata, ctx)
    if kpis:
        kw = (12.133 - 3 * 0.22) / 4.0
        for i, k_item in enumerate(kpis[:4]):
            kv, kl = k_item[0], k_item[1]
            ks = k_item[2] if len(k_item) > 2 else ""
            hi = bool(k_item[3]) if len(k_item) > 3 else (i % 2 == 1)
            add_kpi_tile(slide, 0.60 + i * (kw + 0.22), kpi_y, kw, 1.12, kv, kl, ks, style=style, highlight=hi)
        bot_y = kpi_y + 1.28
    else:
        bot_y = 2.76

    bot_h = 6.96 - bot_y
    if sdata.get("tbl_hdr") and sdata.get("tbl_rows"):
        add_editorial_card(slide, 0.60, bot_y, 6.25, bot_h, sdata.get("box_title") or "Síntesis Ejecutiva del Comité", accent_color=NAVY_DARK, style=style)
        add_bullets(slide, 0.80, bot_y + 0.46, 5.88, bot_h - 0.56, card_bullets, max_font_pt=12.5, min_font_pt=11.0)
        add_mckinsey_table(slide, 7.05, bot_y, 5.683, bot_h, sdata["tbl_hdr"], sdata["tbl_rows"], style=style)
    else:
        add_editorial_card(slide, 0.60, bot_y, 12.133, bot_h, sdata.get("box_title") or "Síntesis Ejecutiva del Comité", accent_color=NAVY_DARK, style=style)
        add_bullets(slide, 0.82, bot_y + 0.46, 11.70, bot_h - 0.56, card_bullets, max_font_pt=13.0, min_font_pt=11.4)

    add_clean_box(slide, 0.60, 7.12, 12.133, 0.008, fill_rgb=BORDER_LIGHT)
    add_text(slide, 0.60, 7.16, 9.10, 0.22, f"{company_label.upper()}  ·  PITCH DECK INSTITUCIONAL BUYSIDE", size=8.4, color=SLATE_MUTED)
    add_text(slide, 9.80, 7.16, 2.933, 0.22, f"DIAPOSITIVA 01 DE {total_slides:02d}", size=8.4, bold=True, color=NAVY_DARK, align=PP_ALIGN.RIGHT)


def render_chart_slide(slide, sdata: dict, style: str):
    bullets = list(sdata.get("bullets") or [])
    takeaway = sdata.get("takeaway") or ""
    if not takeaway and len(bullets) >= 4:
        takeaway = bullets[-1]
        bullets = bullets[:-1]

    bottom_limit = 6.38 if takeaway else 6.96
    card_top = 1.25
    card_h = bottom_limit - card_top

    # Izquierda (60%): Evidencia Gráfica (Nativo Vectorial OOXML o PNG 300 DPI contain)
    chart_title = sdata.get("box_title") or "Evidencia Cuantitativa Auditada"
    pad_c = add_editorial_card(slide, 0.60, card_top, 7.35, card_h, chart_title, accent_color=NAVY_DARK, fill_rgb=WHITE, style=style)

    if isinstance(sdata.get("native_chart"), dict):
        add_native_chart(slide, 0.76, card_top + pad_c, 7.04, card_h - pad_c - 0.10, sdata["native_chart"])
    elif sdata.get("chart_path") and os.path.exists(sdata["chart_path"]):
        add_picture_contain(slide, sdata["chart_path"], 0.74, card_top + pad_c - 0.01, 7.08, card_h - pad_c - 0.08)

    # Derecha (40%): Hallazgos Clave + 2 KPI Tiles
    side_kpis = derive_chart_side_kpis(sdata)
    if len(side_kpis) >= 2 and card_h >= 4.80:
        kpi_h = 1.12
        ins_h = card_h - kpi_h - 0.14
        pad_r = add_editorial_card(slide, 8.15, card_top, 4.583, ins_h, "Claves Analíticas del Módulo", accent_color=ROYAL_BLUE, style=style)
        add_bullets(slide, 8.34, card_top + pad_r, 4.22, ins_h - pad_r - 0.09, bullets, max_font_pt=12.5, min_font_pt=10.8)

        kw = (4.583 - 0.18) / 2.0
        ky = card_top + ins_h + 0.14
        for idx, (kv, kl, ks, hi) in enumerate(side_kpis[:2]):
            add_kpi_tile(slide, 8.15 + idx * (kw + 0.18), ky, kw, kpi_h, kv, kl, ks, style=style, highlight=hi)
    else:
        pad_r = add_editorial_card(slide, 8.15, card_top, 4.583, card_h, "Claves Analíticas del Módulo", accent_color=ROYAL_BLUE, style=style)
        add_bullets(slide, 8.34, card_top + pad_r, 4.22, card_h - pad_r - 0.10, bullets, max_font_pt=13.0, min_font_pt=11.0)

    if takeaway:
        add_takeaway_bar(slide, 6.50, takeaway, style=style)


def render_verdict_slide(slide, sdata: dict, ctx: dict, style: str):
    sk = ctx.get("summary_kpis") or {}
    ccy = sk.get("currency") or ctx.get("currency") or ""
    verdict = str(sk.get("verdict") or "COMPRA").upper()
    fv = sk.get("fair_value_base")
    upside = sk.get("upside_pct")
    conv = sk.get("conviction_score")
    weight = sk.get("recommended_weight_pct") or "Posición Institucional"

    # Columna izquierda: Tarjeta oscura de Orden Ejecutable + Pilares del Dictamen
    add_clean_box(slide, 0.60, 1.26, 4.45, 2.28, fill_rgb=NAVY_DARK, radius_in=0.055 if style != "mckinsey" else 0.0)
    if style == "mckinsey":
        add_clean_box(slide, 0.60, 1.26, 4.45, 0.05, fill_rgb=GOLD_BRIGHT)
    add_text(slide, 0.82, 1.42, 4.02, 0.22, "DICTAMEN VINCULANTE APROBADO", size=9.2, bold=True, color=GOLD_BRIGHT)
    add_text(slide, 0.82, 1.68, 4.02, 0.46, verdict, size=25.0, bold=True, color=WHITE)

    lines_v = []
    if fv is not None:
        lines_v.append(f"Valor Intrínseco Base: {ccy} {fv:,.2f}")
    if upside is not None:
        lines_v.append(f"Potencial Estimado: {upside:+.2f}%")
    if conv is not None:
        lines_v.append(f"Scorecard Comité: {conv:.2f} / 10.00")
    lines_v.append(f"Asignación Cartera: {weight}")
    add_text(slide, 0.82, 2.20, 4.02, 1.22, "\n".join(lines_v), size=10.8, color=RGBColor(226, 232, 240), line_spacing=1.24)

    add_editorial_card(slide, 0.60, 3.70, 4.45, 3.26, "Respaldo del Dictamen", accent_color=EMERALD, style=style)
    bullets_v = list(sdata.get("bullets") or [])
    if not bullets_v:
        bullets_v = [
            f"Asignación institucional recomendada: {weight} mediante criterio de Kelly.",
            "Estructura táctica en 3 tramos (40% spot, 30% en soporte, 30% en confirmación).",
            "Nivel de Stop-Loss incondicional fijado con control estricto de capital.",
            "Monitoreo trimestral de catalizadores y triggers de invalidación (Kill-Switch)."
        ]
    add_bullets(slide, 0.80, 4.14, 4.08, 2.70, bullets_v, max_font_pt=12.0, min_font_pt=10.5, bullet_color=EMERALD)

    # Columna derecha: Tabla contractual de 2 columnas alineada a la izquierda
    add_mckinsey_table(slide, 5.25, 1.26, 7.483, 5.70, sdata["tbl_hdr"], sdata["tbl_rows"], style=style, col_ratios=[0.39, 0.61])


def render_tearsheet_grid_slide(slide, sdata: dict, ctx: dict, style: str):
    bullets = list(sdata.get("bullets") or [])
    sk = ctx.get("summary_kpis") or {}
    ccy = sk.get("currency") or ctx.get("currency") or ""
    verdict = str(sk.get("verdict") or "COMPRA").upper()
    fv = sk.get("fair_value_base")
    upside = sk.get("upside_pct")
    conv = sk.get("conviction_score")
    weight = sk.get("recommended_weight_pct") or "3 Tramos Tácticos"

    cards_6 = []
    accents = [NAVY_DARK, ROYAL_BLUE, NAVY_DARK, ROYAL_BLUE, GOLD_BRIGHT]
    for idx, b in enumerate(bullets[:5]):
        b_stripped = re.sub(r"^\d+[\.\)]\s*", "", b).strip()
        lead, body = split_lead_and_body(b_stripped)
        c_title = f"0{idx + 1} · {lead}" if lead else f"PILAR EJECUTIVO 0{idx + 1}"
        c_body = body if lead else b_stripped
        cards_6.append((c_title, accents[idx % len(accents)], c_body, False))

    # Sexta tarjeta: Ficha sintética de Veredicto Ejecutable (o 6º bullet explícito de slides_deck.json)
    if len(bullets) >= 6:
        b6_stripped = re.sub(r"^\d+[\.\)]\s*", "", bullets[5]).strip()
        lead6, body6 = split_lead_and_body(b6_stripped)
        c6_title = f"06 · {lead6}" if lead6 else "DICTAMEN EJECUTABLE DEL COMITÉ"
        c6_body = body6 if lead6 else b6_stripped
        cards_6.append((c6_title, EMERALD, c6_body, True))
    else:
        v_parts = [f"Recomendación vinculante: {verdict}."]
        if fv is not None and upside is not None:
            v_parts.append(f"Precio objetivo del Comité: {ccy} {fv:,.2f} ({upside:+.2f}% de potencial respecto a cotización de referencia).")
        if conv is not None:
            v_parts.append(f"Calificación integral del Scorecard: {conv:.2f} / 10.00.")
        v_parts.append(f"Ejecución disciplinada aprobada ({weight}) sujeta a control estricto de invalidación y preservación de capital.")
        cards_6.append(("DICTAMEN EJECUTABLE DEL COMITÉ", EMERALD, " ".join(v_parts), True))

    cw = (12.133 - 2 * 0.22) / 3.0
    ch = 2.74
    for idx, (ctitle, ccol, cbody, is_verd) in enumerate(cards_6[:6]):
        col_i = idx % 3
        row_i = idx // 3
        cx = 0.60 + col_i * (cw + 0.22)
        cy = 1.28 + row_i * (ch + 0.22)
        bg_c = (EMERALD_BG if style != "modern" else HIGHLIGHT_BG) if is_verd else SURFACE_SOFT
        hdr_pad = add_editorial_card(slide, cx, cy, cw, ch, ctitle, accent_color=ccol, fill_rgb=bg_c, style=style)

        body_sz = 11.8 if len(cbody) <= 240 else (11.0 if len(cbody) <= 320 else (10.2 if len(cbody) <= 410 else 9.6))
        add_text(slide, cx + 0.18, cy + hdr_pad + 0.04, cw - 0.34, ch - hdr_pad - 0.10, cbody,
                 size=body_sz, bold=is_verd, color=NAVY_DARK if is_verd else SLATE_BODY, line_spacing=1.18)


def render_table_slide(slide, sdata: dict, style: str):
    bullets = list(sdata.get("bullets") or [])
    headers = sdata["tbl_hdr"]
    rows = sdata["tbl_rows"]
    kpis = sdata.get("kpis") or []
    takeaway = sdata.get("takeaway") or ""

    # Sub-Layout A: Tira de KPIs explícita arriba + Tabla + Takeaway
    if len(kpis) >= 3:
        n_k = min(4, len(kpis))
        kw = (12.133 - (n_k - 1) * 0.22) / float(n_k)
        for i, k_item in enumerate(kpis[:n_k]):
            kv, kl = k_item[0], k_item[1]
            ks = k_item[2] if len(k_item) > 2 else ""
            add_kpi_tile(slide, 0.60 + i * (kw + 0.22), 1.25, kw, 0.96, kv, kl, ks, style=style, highlight=(i % 2 == 1))

        if not takeaway and bullets:
            takeaway = bullets[0] if len(bullets) == 1 else bullets[-1]
        bot_lim = 6.38 if takeaway else 6.96
        tbl_top = 2.35
        add_mckinsey_table(slide, 0.60, tbl_top, 12.133, bot_lim - tbl_top, headers, rows, style=style)
        if takeaway:
            add_takeaway_bar(slide, 6.50, takeaway, style=style)
        return

    # Sub-Layout B: Tablas de 6 o menos filas de datos y >= 4 viñetas -> 2 Tarjetas Paralelas arriba + Tabla + Takeaway opcional
    if len(rows) <= 6 and len(bullets) >= 4:
        if len(bullets) >= 5 and not takeaway:
            takeaway = bullets[-1]
            upper_bullets = bullets[:-1]
        elif len(bullets) == 4 and len(rows) <= 5 and not takeaway:
            # Con <=5 filas cabe cómodamente 2+2 tarjetas Y barra de conclusión si hay takeaway explícito;
            # si son exactamente 4 puntos mantenemos 2 a la izquierda y 2 a la derecha con tabla amplia.
            upper_bullets = bullets
        else:
            upper_bullets = bullets

        mid = math.ceil(len(upper_bullets) / 2.0)
        b_left = upper_bullets[:mid]
        b_right = upper_bullets[mid:]

        cw = (12.133 - 0.233) / 2.0
        h_need_l = estimate_bullets_height(b_left, cw - 0.36, 10.8, 4.8, 1.15) + 0.52
        h_need_r = estimate_bullets_height(b_right, cw - 0.36, 10.8, 4.8, 1.15) + 0.52
        bot_lim = 6.38 if takeaway else 6.96
        min_tbl_h = max(2.25, (len(rows) + 1) * 0.39)
        max_card_h = max(1.48, bot_lim - 1.25 - min_tbl_h - 0.14)
        card_h = min(max_card_h, max(1.52, h_need_l, h_need_r))

        t_left = sdata.get("box_title") or "Análisis Operativo y Financiero"
        t_right = "Implicaciones Cuantitativas y Auditoría"
        pad_l = add_editorial_card(slide, 0.60, 1.25, cw, card_h, t_left, accent_color=NAVY_DARK, style=style)
        add_bullets(slide, 0.78, 1.25 + pad_l - 0.02, cw - 0.32, card_h - pad_l - 0.05, b_left, max_font_pt=12.6, min_font_pt=10.8)

        pad_r = add_editorial_card(slide, 0.60 + cw + 0.233, 1.25, cw, card_h, t_right, accent_color=ROYAL_BLUE, style=style)
        add_bullets(slide, 0.60 + cw + 0.233 + 0.18, 1.25 + pad_r - 0.02, cw - 0.32, card_h - pad_r - 0.05, b_right, max_font_pt=12.6, min_font_pt=10.8)

        tbl_top = 1.25 + card_h + 0.14
        add_mckinsey_table(slide, 0.60, tbl_top, 12.133, bot_lim - tbl_top, headers, rows, style=style)
        if takeaway:
            add_takeaway_bar(slide, 6.50, takeaway, style=style)
        return

    # Sub-Layout C: Tablas densas (>= 7 filas, ej. Catálogo o Scorecard) o <= 3 viñetas -> Tarjeta superior compacta adaptativa + Tabla amplia
    if len(rows) <= 6 and not takeaway and len(bullets) == 3:
        # Con 3 viñetas y tabla corta podemos usar barra de conclusión con la 3ª viñeta si es sintética, o dejar tabla respirable
        pass

    bot_lim = 6.38 if takeaway else 6.96
    has_hdr_line = len(rows) <= 7 and bool(sdata.get("box_title"))
    pad_top = 0.43 if has_hdr_line else 0.12
    needed_b_h = estimate_bullets_height(bullets, 11.75, 10.6, 3.8, 1.14) + pad_top + 0.08
    min_tbl_h = max(2.60, (len(rows) + 1) * 0.41)
    max_card_h = max(1.06, bot_lim - 1.24 - min_tbl_h - 0.12)
    card_h = min(max_card_h, max(1.08, needed_b_h))

    if bullets:
        add_editorial_card(
            slide, 0.60, 1.24, 12.133, card_h,
            sdata.get("box_title") if has_hdr_line else "",
            accent_color=GOLD_BRIGHT if len(rows) >= 7 else NAVY_DARK,
            style=style,
        )
        add_bullets(slide, 0.80, 1.24 + pad_top, 11.75, card_h - pad_top - 0.06, bullets, max_font_pt=12.5, min_font_pt=10.8)
        tbl_top = 1.24 + card_h + 0.12
    else:
        tbl_top = 1.26

    add_mckinsey_table(slide, 0.60, tbl_top, 12.133, bot_lim - tbl_top, headers, rows, style=style)
    if takeaway:
        add_takeaway_bar(slide, 6.50, takeaway, style=style)


def render_narrative_slide(slide, sdata: dict, style: str):
    bullets = list(sdata.get("bullets") or [])
    kpis = sdata.get("kpis") or []
    takeaway = sdata.get("takeaway") or ""
    if not takeaway and len(bullets) >= 4:
        takeaway = bullets[-1]
        bullets = bullets[:-1]

    curr_y = 1.25
    if kpis:
        n_k = min(4, len(kpis))
        kw = (12.133 - (n_k - 1) * 0.22) / float(n_k)
        for i, k_item in enumerate(kpis[:n_k]):
            kv, kl = k_item[0], k_item[1]
            ks = k_item[2] if len(k_item) > 2 else ""
            add_kpi_tile(slide, 0.60 + i * (kw + 0.22), curr_y, kw, 1.15, kv, kl, ks, style=style, highlight=(i % 2 == 1))
        curr_y += 1.30

    bot_lim = 6.38 if takeaway else 6.96
    avail_h = bot_lim - curr_y

    cards = sdata.get("cards") or []
    if len(cards) in (2, 3) and all(isinstance(c, (list, tuple)) and len(c) >= 2 for c in cards):
        n_c = len(cards)
        cw = (12.133 - (n_c - 1) * 0.22) / float(n_c)
        accents = [NAVY_DARK, ROYAL_BLUE, GOLD_BRIGHT]
        for idx, (ctit, cbuls) in enumerate(cards):
            cx = 0.60 + idx * (cw + 0.22)
            pad_c = add_editorial_card(slide, cx, curr_y, cw, avail_h, str(ctit), accent_color=accents[idx % len(accents)], style=style)
            add_bullets(slide, cx + 0.15, curr_y + pad_c, cw - 0.30, avail_h - pad_c - 0.10, list(cbuls), max_font_pt=12.5 if n_c == 3 else 13.5, min_font_pt=10.2 if n_c == 3 else 11.2)
    elif len(bullets) >= 4:
        mid = math.ceil(len(bullets) / 2.0)
        cw = (12.133 - 0.25) / 2.0
        pad_l = add_editorial_card(slide, 0.60, curr_y, cw, avail_h, sdata.get("box_title") or "Ejes Estructurales", accent_color=NAVY_DARK, style=style)
        add_bullets(slide, 0.78, curr_y + pad_l, cw - 0.34, avail_h - pad_l - 0.10, bullets[:mid], max_font_pt=13.5, min_font_pt=11.2)
        pad_r = add_editorial_card(slide, 0.60 + cw + 0.25, curr_y, cw, avail_h, "Evidencia Complementaria", accent_color=ROYAL_BLUE, style=style)
        add_bullets(slide, 0.60 + cw + 0.25 + 0.18, curr_y + pad_r, cw - 0.34, avail_h - pad_r - 0.10, bullets[mid:], max_font_pt=13.5, min_font_pt=11.2)
    else:
        pad_c = add_editorial_card(slide, 0.60, curr_y, 12.133, avail_h, sdata.get("box_title") or "Síntesis Analítica", accent_color=NAVY_DARK, style=style)
        add_bullets(slide, 0.82, curr_y + pad_c, 11.70, avail_h - pad_c - 0.10, bullets, max_font_pt=14.0, min_font_pt=11.5)

    if takeaway:
        add_takeaway_bar(slide, 6.50, takeaway, style=style)


# ==============================================================================
# 8. VERIFICACIÓN INTEGRADA DE INTEGRIDAD OOXML Y COMPILACIÓN PRINCIPAL
# ==============================================================================
def verify_ooxml_package(pptx_path: str):
    if not zipfile.is_zipfile(pptx_path):
        raise ValueError(f"El archivo generado no es un contenedor ZIP OOXML válido: {pptx_path}")
    with zipfile.ZipFile(pptx_path, "r") as zf:
        names = set(zf.namelist())
        for req in ("[Content_Types].xml", "_rels/.rels", "ppt/presentation.xml"):
            if req not in names:
                raise ValueError(f"Falta componente OOXML obligatorio ({req}) en {pptx_path}")
        for name in names:
            if name.endswith(".xml") or name.endswith(".rels"):
                ET.fromstring(zf.read(name))


def build_presentation(target_dir: str, style: str = "mix") -> str:
    target_dir = os.path.abspath(target_dir)
    ctx = load_company_context(target_dir)

    company_name = ctx["company_name"]
    ticker = ctx["ticker"]
    company_label = f"{company_name} ({ticker})" if ticker and ticker not in company_name else company_name

    md_files = sorted(glob.glob(os.path.join(target_dir, "*_INFORME_COMITE_FINAL.md")))
    if md_files:
        file_prefix = os.path.basename(md_files[0]).replace("_INFORME_COMITE_FINAL.md", "")
    else:
        file_prefix = os.path.basename(target_dir)

    slides_norm = load_normalized_slides(target_dir)
    total_slides = len(slides_norm)
    out_pptx = os.path.join(target_dir, f"{file_prefix}_PRESENTACION_COMITE_{total_slides}_SLIDES.pptx")

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.50)
    blank_layout = prs.slide_layouts[6]

    for sdata in slides_norm:
        num = sdata["num"]
        slide = prs.slides.add_slide(blank_layout)

        # Arquetipo 1: Portada Ejecutiva Hero
        if num == 1:
            render_cover_slide(slide, sdata, total_slides, company_label, ctx, style)
            continue

        add_chrome(
            slide,
            slide_num=num,
            total_slides=total_slides,
            kicker=sdata["kicker"],
            action_title=sdata["title"],
            badge_text=sdata["badge"],
            company_label=company_label,
            style=style,
        )

        has_chart = bool(sdata.get("native_chart") or (sdata.get("chart_path") and os.path.exists(sdata["chart_path"])))
        has_table = bool(sdata.get("tbl_hdr") and sdata.get("tbl_rows"))

        # Arquetipo 2: Evidencia Gráfica Izquierda→Derecha (60% Chart / 40% Insights + KPIs)
        if has_chart and not has_table:
            render_chart_slide(slide, sdata, style)
        # Arquetipo 3: Ficha Contractual de Veredicto en 2 Columnas (Módulo 17.5 / Slide 39)
        elif (
            has_table
            and len(sdata["tbl_hdr"]) == 2
            and ("veredicto" in sdata["raw_title"].lower() or "17.5" in sdata["box_title"].lower() or (num == total_slides - 1 and len(sdata["tbl_rows"]) >= 7))
        ):
            render_verdict_slide(slide, sdata, ctx, style)
        # Arquetipo 4: Tear Sheet Ejecutivo en Cuadrícula 3x2 (Módulo 18 / Slide Final)
        elif (
            not has_table
            and not has_chart
            and len(sdata.get("bullets") or []) in (5, 6)
            and (num == total_slides or "tear sheet" in sdata["raw_title"].lower() or "MÓD. 18" in sdata["badge"].upper() or "MÓDULO 18" in sdata.get("kicker", "").upper())
        ):
            render_tearsheet_grid_slide(slide, sdata, ctx, style)
        # Arquetipo 5: Diapositiva Financiera con Tabla McKinsey y Geometría Adaptativa
        elif has_table:
            render_table_slide(slide, sdata, style)
        # Arquetipo 6: Diapositiva Analítica en 2 Columnas Paralelas
        else:
            render_narrative_slide(slide, sdata, style)

    try:
        prs.save(out_pptx)
    except PermissionError:
        alt_pptx = out_pptx.replace('.pptx', '_UPDATED.pptx')
        prs.save(alt_pptx)
        print(f'=== AVISO: Archivo PPTX original abierto/bloqueado; guardado en {alt_pptx} ===', flush=True)
        out_pptx = alt_pptx
    verify_ooxml_package(out_pptx)
    print(f"=== PPTX compilado y verificado OOXML ({total_slides} diapositivas 16:9, style={style}): {out_pptx} ===", flush=True)

# Generación estricta de 60 slides sin duplicados legacy

    # Sincronización automática con carpetas consolidadas ppt/
    consolidated_ppt_dirs = [
        os.path.join(os.path.dirname(target_dir), "ppt"),
        os.path.join(os.path.dirname(os.path.dirname(target_dir)), "ppt"),
    ]
    for c_dir in consolidated_ppt_dirs:
        if os.path.exists(c_dir):
            shutil.copy2(out_pptx, os.path.join(c_dir, os.path.basename(out_pptx)))

    return out_pptx


def main():
    parser = argparse.ArgumentParser(description="Compilador Institucional de Presentación PPTX de 40 Diapositivas")
    parser.add_argument("--target-dir", type=str, required=True, help="Ruta de la carpeta de la empresa (<COMPANY_DIR>)")
    parser.add_argument(
        "--style",
        type=str,
        default="mix",
        choices=["mix", "mckinsey", "modern"],
        help="Estilo visual del deck: 'mix' (McKinsey + KPIs suaves, por defecto), 'mckinsey' o 'modern'",
    )
    args = parser.parse_args()
    build_presentation(args.target_dir, style=args.style)


if __name__ == "__main__":
    main()
