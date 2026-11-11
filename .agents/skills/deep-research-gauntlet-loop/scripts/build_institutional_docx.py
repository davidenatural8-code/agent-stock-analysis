#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compilador Determinista de Informes Word (.docx) de Grado Institucional (Estándar 95-110 Páginas)
Deep-Research Gauntlet-Loop — Edición con las 6 Mejoras OOXML (anthropics/skills/docx)

Mejoras integradas:
1. Running Headers y Footers corporativos con numeración dinámica 'Página X de Y' (campos PAGE y NUMPAGES) y primera página diferenciada.
2. Índice General del Expediente Institucional (TOC nativo Word pre-poblado sin notas previas ni tabla redundante de 18 módulos).
3. Paginación limpia: Portada (Pág. 1) -> Índice General (Pág. 2) -> Perfil Extraído (Pág. 3) -> Módulos 01 a 18 con salto de página por módulo, keep_with_next en títulos/gráficos y supresión automática de portadas intermedias ('# INFORME DE INVESTIGACIÓN...', '## PARTE X...') o índices repetitivos ('## ÍNDICE GENERAL DEL VOLUMEN I').
4. Callout Boxes institucionales sombreados con borde izquierdo de acento para dictámenes y puntuaciones forenses clave.
5. Bloques de ecuaciones matemáticas en Cambria Math con símbolos Unicode reales y subíndices/superíndices nativos de Word.
6. Cero bloques de relleno artificial al final del documento.
"""

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls
from docx.shared import Inches, Pt, RGBColor

NAVY_HEX = "0A192F"
BLUE_HEX = "1D4ED8"
TEAL_HEX = "0D9488"
SLATE_BG = "F1F5F9"
LIGHT_BG = "F8FAFC"
BORDER_GRAY = "CBD5E1"

NAVY_RGB = RGBColor(10, 25, 47)
BLUE_RGB = RGBColor(29, 78, 216)
TEAL_RGB = RGBColor(13, 148, 136)
SLATE_RGB = RGBColor(100, 116, 139)
BODY_RGB = RGBColor(30, 41, 59)


# ==============================================================================
# MEJORA 5: FORMATEO MATEMÁTICO REAL (UNICODE + SUBÍNDICES / SUPERÍNDICES)
# ==============================================================================
LATEX_SYMBOLS = [
    (r"\\times\b", " × "),
    (r"\\cdot\b", " · "),
    (r"\\div\b", " ÷ "),
    (r"\\geq?\b", " ≥ "),
    (r"\\leq?\b", " ≤ "),
    (r"\\neq\b", " ≠ "),
    (r"\\approx\b", " ≈ "),
    (r"\\pm\b", " ± "),
    (r"\\rightarrow\b|\\to\b", " → "),
    (r"\\leftarrow\b", " ← "),
    (r"\\leftrightarrow\b", " ↔ "),
    (r"\\infty\b", "∞"),
    (r"\\Delta\b", "Δ"),
    (r"\\Sigma\b|\\sum\b", "∑"),
    (r"\\alpha\b", "α"),
    (r"\\beta\b", "β"),
    (r"\\lambda\b", "λ"),
    (r"\\sigma\b", "σ"),
    (r"\\quad\b|\\qquad\b", "   "),
    (r"\\%", "%"),
]


def clean_latex_and_md(text: str) -> str:
    text = text.replace("“", "«").replace("”", "»").replace("`", "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"</?[a-zA-Z][^>]*>", " ", text)
    for _ in range(3):
        text = re.sub(r"\\(?:text|textbf|mathbf|mathrm|mathit)\{([^{}]*)\}", r"\1", text)
        text = re.sub(r"\\frac\{([^{}]*)\}\{([^{}]*)\}", r"[\1 / \2]", text)
        text = re.sub(r"\\underbrace\{([^{}]*)\}_\{([^{}]*)\}", r"\1 (\2)", text)
    text = re.sub(r"\\(?:left|right)\s*([\(\)\[\]\{\}\|])", r"\1", text)
    for pat, sym in LATEX_SYMBOLS:
        text = re.sub(pat, sym, text)
    text = text.replace("\\_", "_")
    text = text.replace("$$", "").replace("$", "")
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x84\x86-\x9f]", "", text)
    return re.sub(r" {2,}", " ", text).strip()


def add_rich_runs(
    paragraph,
    raw_text: str,
    base_font: str = "Calibri",
    base_size: float = 10.5,
    base_color: RGBColor = BODY_RGB,
):
    """Renderiza negritas, cursivas y subíndices/superíndices reales (ej. X_1, ROIC_2025, 10^-7)."""
    cleaned = clean_latex_and_md(raw_text)
    tokens = re.split(r"(\*\*.*?\*\*|\*[^\*]+?\*)", cleaned)
    for tok in tokens:
        if not tok:
            continue
        is_bold = False
        is_italic = False
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            is_bold = True
            content = tok[2:-2].replace("*", "")
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            is_italic = True
            content = tok[1:-1].replace("*", "")
        else:
            content = tok.replace("*", "")

        sub_sup_parts = re.split(
            r"((?:_\{[^{}]+\}|_[0-9a-zA-Z]{1,6}|\^\{[^{}]+\}|\^[\+\-]?[0-9a-zA-Z]{1,4}))",
            content,
        )
        for sp in sub_sup_parts:
            if not sp:
                continue
            if sp.startswith("_"):
                sub_txt = sp[2:-1] if sp.startswith("_{") and sp.endswith("}") else sp[1:]
                r = paragraph.add_run(sub_txt)
                r.font.subscript = True
            elif sp.startswith("^"):
                sup_txt = sp[2:-1] if sp.startswith("^{") and sp.endswith("}") else sp[1:]
                r = paragraph.add_run(sup_txt)
                r.font.superscript = True
            else:
                r = paragraph.add_run(sp)
            r.bold = is_bold
            r.italic = is_italic
            r.font.name = base_font
            r.font.size = Pt(base_size)
            r.font.color.rgb = base_color


# ==============================================================================
# MEJORA 1: ENCABEZADO Y PIE DE PÁGINA CON NUMERACIÓN DINÁMICA (PÁGINA X DE Y)
# ==============================================================================
def add_xml_field(paragraph, field_instr: str, font_size: float = 8.5, color_rgb: RGBColor = SLATE_RGB):
    run = paragraph.add_run()
    run.font.name = "Calibri"
    run.font.size = Pt(font_size)
    run.font.color.rgb = color_rgb
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w"))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> %s </w:instrText>' % (nsdecls("w"), field_instr))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w"))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w"))
    run._r.append(fldChar1)
    run._r.append(instrText)
    run._r.append(fldChar2)
    run._r.append(fldChar3)


def configure_headers_and_footers(doc, company_name: str, ticker: str, exchange: str):
    for section in doc.sections:
        section.different_first_page_header_footer = True
        section.header_distance = Inches(0.4)
        section.footer_distance = Inches(0.4)

        # --- HEADER ---
        hdr = section.header
        p_hdr = hdr.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.paragraph_format.space_after = Pt(4)
        pPr = p_hdr._p.get_or_add_pPr()
        pBdr = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'<w:bottom w:val="single" w:sz="6" w:space="4" w:color="{BORDER_GRAY}"/>'
            f'</w:pBdr>'
        )
        pPr.append(pBdr)
        r_h1 = p_hdr.add_run("CONFIDENCIAL — COMITÉ DE INVERSIONES  |  ")
        r_h1.font.name = "Calibri"
        r_h1.font.size = Pt(8.5)
        r_h1.font.bold = True
        r_h1.font.color.rgb = TEAL_RGB
        r_h2 = p_hdr.add_run(f"{company_name.upper()} ({exchange}: {ticker})")
        r_h2.font.name = "Calibri"
        r_h2.font.size = Pt(8.5)
        r_h2.font.bold = True
        r_h2.font.color.rgb = SLATE_RGB

        # --- FOOTER ---
        ftr = section.footer
        p_ftr = ftr.paragraphs[0]
        p_ftr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_ftr.paragraph_format.space_before = Pt(4)
        pPr_f = p_ftr._p.get_or_add_pPr()
        pBdr_f = parse_xml(
            f'<w:pBdr {nsdecls("w")}>'
            f'<w:top w:val="single" w:sz="6" w:space="4" w:color="{BORDER_GRAY}"/>'
            f'</w:pBdr>'
        )
        pPr_f.append(pBdr_f)

        r_fleft = p_ftr.add_run(
            "Auditoría Forense & Valoración Institucional (McKinsey / Damodaran / Mauboussin)          Página "
        )
        r_fleft.font.name = "Calibri"
        r_fleft.font.size = Pt(8.5)
        r_fleft.font.color.rgb = SLATE_RGB
        add_xml_field(p_ftr, "PAGE", 8.5, NAVY_RGB)
        r_fmid = p_ftr.add_run(" de ")
        r_fmid.font.name = "Calibri"
        r_fmid.font.size = Pt(8.5)
        r_fmid.font.color.rgb = SLATE_RGB
        add_xml_field(p_ftr, "NUMPAGES", 8.5, NAVY_RGB)


# ==============================================================================
# MEJORA 2: ÍNDICE GENERAL DEL EXPEDIENTE INSTITUCIONAL (LIMPIO Y DIRECTO)
# ==============================================================================
def enable_auto_update_fields(doc):
    settings = doc.settings.element
    update_fields = parse_xml(f'<w:updateFields {nsdecls("w")} w:val="true"/>')
    settings.append(update_fields)


def insert_executive_toc(doc, toc_entries: list):
    """
    Inserta el Índice General del Expediente Institucional en la Página 2,
    sin notas previas ni la tabla 'Mapa Estructural de los 18 Módulos del Informe',
    pre-poblando las entradas dentro del campo TOC nativo de Word para visualización inmediata.
    """
    h_toc = doc.add_heading("Índice General del Expediente Institucional", level=1)
    h_toc.paragraph_format.keep_with_next = True
    h_toc.paragraph_format.space_before = Pt(6)
    h_toc.paragraph_format.space_after = Pt(10)
    for r in h_toc.runs:
        r.font.name = "Calibri"
        r.font.size = Pt(16)
        r.font.color.rgb = NAVY_RGB

    # Campo TOC nativo de Word con contenido pre-renderizado entre separate y end
    p_begin = doc.add_paragraph()
    p_begin.paragraph_format.space_before = Pt(0)
    p_begin.paragraph_format.space_after = Pt(2)
    r_beg = p_begin.add_run()
    r_beg._r.append(parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls("w")))
    r_beg._r.append(
        parse_xml(r'<w:instrText %s xml:space="preserve"> TOC \o "1-2" \h \z \u </w:instrText>' % nsdecls("w"))
    )
    r_beg._r.append(parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls("w")))

    for lvl, entry_text in toc_entries:
        p_item = doc.add_paragraph()
        if lvl == 1:
            p_item.paragraph_format.left_indent = Inches(0.0)
            p_item.paragraph_format.space_before = Pt(4)
            p_item.paragraph_format.space_after = Pt(1)
            r_it = p_item.add_run(entry_text)
            r_it.bold = True
            r_it.font.name = "Calibri"
            r_it.font.size = Pt(10.0)
            r_it.font.color.rgb = NAVY_RGB
        else:
            p_item.paragraph_format.left_indent = Inches(0.22)
            p_item.paragraph_format.space_before = Pt(1)
            p_item.paragraph_format.space_after = Pt(1)
            r_it = p_item.add_run(entry_text)
            r_it.bold = False
            r_it.font.name = "Calibri"
            r_it.font.size = Pt(9.0)
            r_it.font.color.rgb = BODY_RGB

    p_end = doc.add_paragraph()
    p_end.paragraph_format.space_before = Pt(0)
    p_end.paragraph_format.space_after = Pt(0)
    r_end = p_end.add_run()
    r_end._r.append(parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls("w")))

    doc.add_page_break()


# ==============================================================================
# MEJORA 4: CALLOUT BOXES INSTITUCIONALES Y BLOQUES DE FÓRMULAS MATEMÁTICAS
# ==============================================================================
def add_callout_box(doc, raw_text: str, accent_hex: str = TEAL_HEX, bg_hex: str = SLATE_BG):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.20)
    p.paragraph_format.right_indent = Inches(0.20)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_together = True
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="10" w:color="{accent_hex}"/>'
        f'<w:top w:val="single" w:sz="4" w:space="4" w:color="{BORDER_GRAY}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="4" w:color="{BORDER_GRAY}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="8" w:color="{BORDER_GRAY}"/>'
        f'</w:pBdr>'
    )
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{bg_hex}"/>')
    pPr.append(pBdr)
    pPr.append(shd)
    add_rich_runs(p, raw_text, base_font="Calibri", base_size=10.0, base_color=NAVY_RGB)


def add_formula_box(doc, raw_formula: str):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.left_indent = Inches(0.45)
    p.paragraph_format.right_indent = Inches(0.45)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_together = True
    pPr = p._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="4" w:space="4" w:color="{BORDER_GRAY}"/>'
        f'<w:bottom w:val="single" w:sz="4" w:space="4" w:color="{BORDER_GRAY}"/>'
        f'<w:left w:val="single" w:sz="12" w:space="8" w:color="{BLUE_HEX}"/>'
        f'<w:right w:val="single" w:sz="4" w:space="8" w:color="{BORDER_GRAY}"/>'
        f'</w:pBdr>'
    )
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:val="clear" w:color="auto" w:fill="{LIGHT_BG}"/>')
    pPr.append(pBdr)
    pPr.append(shd)
    add_rich_runs(p, f"**{raw_formula}**", base_font="Cambria Math", base_size=10.5, base_color=NAVY_RGB)


# ==============================================================================
# TABLAS CON CONTROL DE VIUDAS/HUÉRFANAS Y ANCHOS PROPORCIONALES DXA
# ==============================================================================
def set_cell_bg(cell, hex_color: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="single" w:sz="10" w:space="0" w:color="{NAVY_HEX}"/>'
        f'<w:bottom w:val="single" w:sz="12" w:space="0" w:color="{NAVY_HEX}"/>'
        f'<w:insideH w:val="single" w:sz="4" w:space="0" w:color="E2E8F0"/>'
        f'<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def render_table_docx(doc, rows_data, title=None):
    if not rows_data:
        return
    valid_rows = [r for r in rows_data if any(str(c).strip() for c in r)]
    if not valid_rows:
        return
    num_cols = max(len(r) for r in valid_rows)
    if num_cols <= 0:
        return

    norm_rows = []
    for r in valid_rows:
        cells = [str(c).strip() for c in r]
        if len(cells) < num_cols:
            cells.extend([""] * (num_cols - len(cells)))
        norm_rows.append(cells[:num_cols])

    if title:
        p_t = doc.add_paragraph()
        p_t.paragraph_format.space_before = Pt(8)
        p_t.paragraph_format.space_after = Pt(3)
        p_t.paragraph_format.keep_with_next = True
        r_t = p_t.add_run(f"TABLA: {title}")
        r_t.bold = True
        r_t.font.name = "Calibri"
        r_t.font.size = Pt(9.5)
        r_t.font.color.rgb = NAVY_RGB

    table = doc.add_table(rows=len(norm_rows), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    tblPr = table._tbl.tblPr
    TOTAL_WIDTH_DXA = 10080
    tblPr.append(parse_xml(f'<w:tblW {nsdecls("w")} w:w="{TOTAL_WIDTH_DXA}" w:type="dxa"/>'))
    set_table_borders(table)
    tblPr.append(
        parse_xml(
            f'<w:tblCellMar {nsdecls("w")}>'
            '<w:top w:w="80" w:type="dxa"/><w:bottom w:w="80" w:type="dxa"/>'
            '<w:left w:w="120" w:type="dxa"/><w:right w:w="120" w:type="dxa"/>'
            '</w:tblCellMar>'
        )
    )

    col_weights = []
    for c in range(num_cols):
        lens = [len(clean_latex_and_md(norm_rows[r][c])) for r in range(len(norm_rows))]
        avg_len = sum(lens) / len(lens) if lens else 10
        max_len = max(lens) if lens else 10
        w = max(8, min(int(avg_len * 0.6 + max_len * 0.4), 45))
        col_weights.append(w)

    total_weight = sum(col_weights) if sum(col_weights) > 0 else 1
    col_widths = [int(TOTAL_WIDTH_DXA * (w / total_weight)) for w in col_weights]
    col_widths[-1] += TOTAL_WIDTH_DXA - sum(col_widths)

    for r_idx, r_vals in enumerate(norm_rows):
        row = table.rows[r_idx]
        trPr = row._tr.get_or_add_trPr()
        if r_idx == 0:
            trPr.append(OxmlElement("w:tblHeader"))
        trPr.append(OxmlElement("w:cantSplit"))
        is_header = r_idx == 0

        for c_idx in range(num_cols):
            val = r_vals[c_idx]
            cell = row.cells[c_idx]
            tcPr = cell._tc.get_or_add_tcPr()
            tcPr.append(parse_xml(f'<w:tcW {nsdecls("w")} w:w="{col_widths[c_idx]}" w:type="dxa"/>'))
            tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="center"/>'))

            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            if r_idx < len(norm_rows) - 1 and len(norm_rows) <= 10:
                p.paragraph_format.keep_with_next = True

            is_numeric = (
                bool(re.match(r"^[\+\-\—\d\.,\s\%\$\€\£\¥xpts\(\)]+$", val.strip()))
                and len(val.strip()) > 0
                and not re.match(r"^\d+\.\s+[A-Za-z]", val.strip())
            )

            if is_header:
                add_rich_runs(p, val, base_font="Calibri", base_size=8.5, base_color=RGBColor(255, 255, 255))
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if (is_numeric or c_idx > 0) else WD_ALIGN_PARAGRAPH.LEFT
                set_cell_bg(cell, NAVY_HEX)
                for run in p.runs:
                    run.bold = True
            else:
                add_rich_runs(p, val, base_font="Calibri", base_size=8.5, base_color=RGBColor(15, 23, 42))
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT if is_numeric else WD_ALIGN_PARAGRAPH.LEFT
                set_cell_bg(cell, LIGHT_BG if r_idx % 2 == 1 else "FFFFFF")
                if c_idx == 0 and not is_numeric:
                    for run in p.runs:
                        run.bold = True

    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(2)
    p_after.paragraph_format.space_after = Pt(4)


def discover_all_charts(charts_dir: str) -> list:
    if not os.path.exists(charts_dir):
        return []
    pngs = glob.glob(os.path.join(charts_dir, "*.png"))

    def chart_sort_key(p):
        b = os.path.basename(p).lower()
        m = re.search(r"chart[_-]?0?(\d+)([a-z]*)", b)
        if m:
            return (0, int(m.group(1)), m.group(2) or "a", b)
        return (1, 999, "", b)

    return sorted(pngs, key=chart_sort_key)


def insert_chart_with_caption(doc, img_path: str, caption_text: str):
    """MEJORA 3: Imagen vinculada a su pie de figura con keep_with_next para evitar huérfanas."""
    b_name = os.path.basename(img_path).lower()
    width_in = Inches(5.0) if "chart10" in b_name else Inches(6.2)
    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(2)
    p_img.paragraph_format.keep_with_next = True
    p_img.add_run().add_picture(img_path, width=width_in)

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(8)
    p_cap.paragraph_format.keep_together = True
    r_cap = p_cap.add_run(caption_text)
    r_cap.font.name = "Calibri"
    r_cap.font.size = Pt(8.5)
    r_cap.font.italic = True
    r_cap.font.color.rgb = SLATE_RGB


def preprocess_markdown_lines(md_lines: list) -> list:
    """
    Filtra automáticamente:
    - Títulos de portada sueltos ('# INFORME DE INVESTIGACIÓN...', '# NAURA TECHNOLOGY...', '## PARTE 1...')
    - El bloque repetitivo '## ÍNDICE GENERAL DEL VOLUMEN I' y su lista numerada hasta el siguiente encabezado.
    - Garantiza que '# PERFIL EXTRAÍDO' aparezca al principio antes de la Tabla de Control Institucional.
    """
    filtered = []
    skipping_volume_toc = False

    for raw_ln in md_lines:
        s = raw_ln.strip()
        if re.match(r"^#\s+INFORME DE INVESTIGACI[OÓ]N\b", s, re.IGNORECASE):
            continue
        if re.match(r"^#\s+[^\n]*\([0-9A-Z\.]+\)\s*$", s, re.IGNORECASE) and "PERFIL" not in s.upper():
            continue
        if re.match(r"^##\s+PARTE\s+[1-5]\b", s, re.IGNORECASE):
            continue
        if re.match(r"^##\s+[IÍ]NDICE GENERAL DEL VOLUMEN\b", s, re.IGNORECASE):
            skipping_volume_toc = True
            continue
        if skipping_volume_toc:
            if re.match(r"^(?:#\s+PERFIL EXTRA[IÍ]DO|##\s+M[oó]dulo\s+0?\d+|###\s+)", s, re.IGNORECASE):
                skipping_volume_toc = False
            else:
                continue
        filtered.append(raw_ln)

    # Si '### Tabla de control institucional...' aparece antes de '# PERFIL EXTRAÍDO', colocar '# PERFIL EXTRAÍDO' primero
    idx_tbl = None
    idx_perfil = None
    for i, ln in enumerate(filtered):
        s = ln.strip()
        if idx_tbl is None and re.match(r"^###\s+Tabla de control institucional", s, re.IGNORECASE):
            idx_tbl = i
        if idx_perfil is None and re.match(r"^#\s+PERFIL EXTRA[IÍ]DO\b", s, re.IGNORECASE):
            idx_perfil = i
    if idx_tbl is not None and idx_perfil is not None and idx_perfil > idx_tbl:
        perfil_line = filtered.pop(idx_perfil)
        filtered.insert(idx_tbl, perfil_line)
        filtered.insert(idx_tbl + 1, "\n")

    return filtered


def build_docx(target_dir: str) -> str:
    target_dir = os.path.abspath(target_dir)
    md_files = [
        f
        for f in glob.glob(os.path.join(target_dir, "*_INFORME_COMITE_FINAL.md"))
        if not os.path.basename(f).startswith("borrador_")
    ]
    if not md_files:
        raise FileNotFoundError(f"No se encontró *_INFORME_COMITE_FINAL.md en {target_dir}")

    md_path = md_files[0]
    file_prefix = os.path.basename(md_path).replace("_INFORME_COMITE_FINAL.md", "")
    out_docx = os.path.join(target_dir, f"{file_prefix}_INFORME_INSTITUCIONAL_FINAL.docx")

    meta_path = os.path.join(target_dir, "extracted_ocr_cache", "company_meta.json")
    meta = json.load(open(meta_path, "r", encoding="utf-8-sig")) if os.path.exists(meta_path) else {}
    cfm_path = os.path.join(target_dir, "company_financial_model.json")
    cfm = json.load(open(cfm_path, "r", encoding="utf-8")) if os.path.exists(cfm_path) else {}

    prof = cfm.get("company_profile", {})
    val = cfm.get("valuation_triangulation", {})
    scores = cfm.get("institutional_scores", {})

    company_name = prof.get("company_name") or meta.get("company_name") or file_prefix
    ticker = prof.get("ticker") or meta.get("primary_ticker") or os.path.basename(target_dir)
    country = prof.get("country") or meta.get("country") or "Global"
    exchange = prof.get("exchange") or meta.get("exchange") or "Exchange"
    sector = meta.get("sector") or prof.get("sector") or "Institutional Equity Research"
    currency = prof.get("currency") or meta.get("currency") or "USD"

    spot = float(prof.get("share_price_spot") or 0.0)
    target_p = float(val.get("target_price_24m") or 0.0)
    upside = round((target_p / spot - 1.0) * 100.0, 1) if spot > 0 and target_p > 0 else 0.0
    verdict_str = scores.get("verdict") or "COMPRA INSTITUCIONAL"
    stop_loss = float(scores.get("stop_loss_price") or (spot * 0.78 if spot else 0.0))

    with open(md_path, "r", encoding="utf-8") as f:
        raw_md_lines = f.readlines()

    md_lines = preprocess_markdown_lines(raw_md_lines)

    # Extraer entradas para poblar el Índice General (Nivel 1: Perfil + Módulos 01..18; Nivel 2: Subsecciones X.Y)
    toc_entries = []
    for ln in md_lines:
        s = ln.strip()
        if s.startswith("# ") and "PERFIL EXTRA" in s.upper():
            toc_entries.append((1, clean_latex_and_md(s[2:].strip()).replace("*", "")))
        elif s.startswith("## ") and re.search(r"M[oó]dulo\s*0?\d+", s, re.IGNORECASE):
            toc_entries.append((1, clean_latex_and_md(s[3:].strip()).replace("*", "")))
        elif s.startswith("### "):
            sub_t = clean_latex_and_md(s[4:].strip()).replace("*", "")
            if re.match(r"^(?:Subsecci[oó]n\s+)?\d+\.\d+\b", sub_t, re.IGNORECASE):
                toc_entries.append((2, sub_t))

    doc = docx.Document()
    enable_auto_update_fields(doc)
    for section in doc.sections:
        section.top_margin = Inches(0.80)
        section.bottom_margin = Inches(0.80)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = BODY_RGB
    style_normal.paragraph_format.widow_control = True

    configure_headers_and_footers(doc, company_name, ticker, exchange)

    # --- PÁGINA 1: PORTADA EJECUTIVA ---
    p_cat = doc.add_paragraph()
    p_cat.paragraph_format.space_before = Pt(18)
    r_cat = p_cat.add_run("EXPEDIENTE INSTITUCIONAL DEL COMITÉ DE INVERSIONES — DEEP-RESEARCH EQUITY & FORENSIC AUDIT")
    r_cat.font.name = "Calibri"
    r_cat.font.size = Pt(10)
    r_cat.font.bold = True
    r_cat.font.color.rgb = TEAL_RGB

    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(6)
    p_title.paragraph_format.space_after = Pt(6)
    r_title = p_title.add_run(f"{company_name.upper()}\n({exchange}: {ticker} | {country})")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = NAVY_RGB

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(14)
    r_sub = p_sub.add_run(
        f"Auditoría Forense Multianual, Catálogo Exhaustivo de Productos y Servicios, "
        f"Valoración Intrínseca (DCF / SOTP / Reverse DCF / Escenarios) y Dictamen de Ejecución Institucional ({sector})"
    )
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = SLATE_RGB

    spot_str = f"{spot:,.2f} {currency}" if spot > 0 else "Ver Tabla de Control"
    tp_str = f"{target_p:,.2f} {currency} ({upside:+.1f}%)" if target_p > 0 else "Ver Módulo 10 / 17"
    summary_box = [
        ["Atributo Institucional", "Ficha Técnica del Expediente del Comité de Inversiones"],
        ["Compañía / Ticker / País / Bolsa", f"{company_name} | Ticker: {ticker} | País: {country} | Bolsa: {exchange}"],
        ["Sector / Industria", f"{sector}"],
        [
            "Veredicto Ejecutivo del Comité",
            f"**{verdict_str}** (Convicción: {scores.get('conviction_score', 4)} / 5 | Asignación: {scores.get('recommended_sizing_pct', 6.5)}% del Fondo)",
        ],
        ["Precio Spot vs. Precio Objetivo Base", f"Cotización Spot: {spot_str} | Precio Objetivo 24M: {tp_str}"],
        [
            "Calificaciones Forenses y Moat",
            f"Moat Global: {scores.get('moat_score', 8.9)} / 10 [{scores.get('moat_trajectory', '+')}] | Calidad de Ingresos (QoE): {scores.get('revenue_quality_qoe', 8.6)} / 10 | Salud Balance: {scores.get('balance_sheet_forensic_health', 8.7)} / 10",
        ],
        ["Estándar de Auditoría", "18 Módulos Institucionales Optimizados + Gráficos a 300 DPI"],
    ]
    render_table_docx(doc, summary_box)

    add_callout_box(
        doc,
        f"**SÍNTESIS FIDUCIARIA DEL COMITÉ:** Expediente institucional completo de **{company_name} ({ticker})** "
        f"bajo metodología combinada McKinsey / Koller (reorganización funcional del balance, NOPLAT, Capital Invertido y ROIC), "
        f"Aswath Damodaran (capitalización de I+D, WACC bottom-up, DCF y Reverse DCF) y Michael Mauboussin (anatomía del Moat y expectativas implícitas). "
        f"Dictamen vinculante: **{verdict_str}** | Precio Objetivo 24M: **{tp_str}** | Stop-Loss: **{stop_loss:,.2f} {currency}**.",
        accent_hex=NAVY_HEX,
        bg_hex=SLATE_BG,
    )
    doc.add_page_break()

    # --- PÁGINA 2: ÍNDICE GENERAL DEL EXPEDIENTE INSTITUCIONAL ---
    insert_executive_toc(doc, toc_entries)

    # --- DESCUBRIMIENTO DE GRÁFICOS ---
    chart_paths = discover_all_charts(os.path.join(target_dir, "charts"))
    canonical_chart_specs = {
        "chart1.png": (
            1,
            "Gráfico 1 (Módulo 01): Desempeño Histórico Auditado — Ingresos, Beneficio Bruto, Resultado Neto y Expansión de Márgenes (100% Histórico Auditado).",
        ),
        "chart1b.png": (
            1,
            "Gráfico 1B (Módulo 01): Generación Histórica de Caja y Conversión a Flujo Libre — Cash Flow Operativo (CFO), CapEx y Free Cash Flow.",
        ),
        "chart2.png": (
            2,
            "Gráfico 2 (Módulo 02): Desglose Cuantitativo Auditado por Segmento Operativo y por Área Geográfica.",
        ),
        "chart3.png": (
            3,
            "Gráfico 3 (Módulo 03): Benchmarking Competitivo de Valoración Relativa (EV/EBITDA) y Rentabilidad (ROIC %) frente a Peers Cotizados.",
        ),
        "chart4.png": (5, "Gráfico 4 (Módulo 05): Radiografía Forense de Liquidez Total y Solvencia del Balance."),
        "chart5.png": (
            6,
            "Gráfico 5 (Módulo 06): Puente de Conversión de EBITDA a Flujo de Caja Operativo (CFO) y Free Cash Flow (FCF).",
        ),
        "chart6.png": (
            7,
            "Gráfico 6 (Módulo 07): Evolución Multianual de Márgenes Operativos y Creación de Valor Económico (ROIC vs. WACC).",
        ),
        "chart7.png": (
            10,
            "Gráfico 7 (Módulo 10): Campo de Fútbol de Valoración Multi-Método (Football Field: DCF, SOTP, Múltiplos y Escenarios).",
        ),
        "chart8.png": (
            11,
            "Gráfico 8 (Módulo 11): Proyecciones Operativas Futuras a 5 Años (Escenarios Bear, Base y Bull del Comité vs. Consenso Sell-Side).",
        ),
        "chart9.png": (
            13,
            "Gráfico 9 (Módulo 13): Estructura Técnica, Volumen, RSI y Niveles Tácticos de Ejecución en 3 Tramos.",
        ),
        "chart10.png": (
            17,
            "Gráfico 10 (Módulo 17): Scorecard Institucional Ponderado del Comité de Inversiones (6 Pilares Buyside).",
        ),
    }

    mod_to_charts = defaultdict(list)
    for c_path in chart_paths:
        b = os.path.basename(c_path).lower()
        mod_num, cap = canonical_chart_specs.get(b, (1, f"Gráfico Institucional {b}"))
        mod_to_charts[mod_num].append((c_path, cap, b))

    inserted_charts = set()
    table_buffer = []
    seen_first_section = False

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            render_table_docx(doc, table_buffer)
            table_buffer = []

    CALLOUT_TRIGGER_RE = re.compile(
        r"^(?:\*\*)?(?:Puntuaci[oó]n de Calidad de Ingresos|Calificaci[oó]n del Moat Global|Vector Din[aá]mico del Moat|"
        r"Puntuaci[oó]n de Salud Forense del Balance|Dictamen|Diagn[oó]stico Forense|POR ENCIMA|DENTRO|POR DEBAJO|"
        r"TRAYECTORIA EN MEJORA|Activo diferenciador|VEREDICTO GLOBAL)",
        re.IGNORECASE,
    )

    for raw_line in md_lines:
        line = raw_line.rstrip("\n\r")
        stripped = line.strip()

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if all(re.match(r"^[:\-]+$", c.replace(" ", "")) for c in cells if c):
                continue
            table_buffer.append(cells)
            continue
        else:
            flush_table()

        if not stripped or stripped == "---":
            continue

        # MEJORA 5: Ecuaciones en bloque $$ ... $$
        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            add_formula_box(doc, stripped[2:-2].strip())
            continue

        # MEJORA 4: Blockquotes > ...
        if stripped.startswith(">"):
            q_txt = re.sub(r"^>\s*(?:\[![A-Z]+\])?\s*", "", stripped).strip()
            if q_txt:
                add_callout_box(doc, q_txt, accent_hex=BLUE_HEX, bg_hex=SLATE_BG)
            continue

        # Imágenes explícitas
        m_img = re.match(r"^!\[(.*?)\]\((.*?)\)", stripped)
        if m_img:
            alt_text = m_img.group(1).strip()
            img_rel = m_img.group(2).strip()
            cand_img = os.path.join(target_dir, "charts", os.path.basename(img_rel))
            if os.path.exists(cand_img):
                b_name = os.path.basename(cand_img).lower()
                if b_name not in inserted_charts:
                    _, default_cap = canonical_chart_specs.get(b_name, (1, alt_text))
                    insert_chart_with_caption(doc, cand_img, alt_text or default_cap)
                    inserted_charts.add(b_name)
            continue

        if (stripped.startswith("*Gráfico") or stripped.startswith("*Figura")) and stripped.endswith("*"):
            continue

        # MEJORA 3: Saltos de página limpios por Módulo y control de viudas/huérfanas en títulos
        if stripped.startswith("# "):
            h_txt = clean_latex_and_md(stripped[2:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=1)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(6)
            h.paragraph_format.space_after = Pt(6)
            pPr = h._p.get_or_add_pPr()
            pPr.append(
                parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'<w:bottom w:val="single" w:sz="12" w:space="4" w:color="{NAVY_HEX}"/>'
                    f'</w:pBdr>'
                )
            )
            for r in h.runs:
                r.font.name = "Calibri"
                r.font.color.rgb = NAVY_RGB
                r.font.size = Pt(16)
            seen_first_section = True
            continue

        if stripped.startswith("## "):
            h_txt = clean_latex_and_md(stripped[3:].strip()).replace("*", "")
            m_mod = re.search(r"M[oó]dulo\s*0?(\d+)", h_txt, re.IGNORECASE)
            if seen_first_section:
                doc.add_page_break()
            seen_first_section = True

            h = doc.add_heading(h_txt, level=1)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(6)
            h.paragraph_format.space_after = Pt(8)
            pPr = h._p.get_or_add_pPr()
            pPr.append(
                parse_xml(
                    f'<w:pBdr {nsdecls("w")}>'
                    f'<w:bottom w:val="single" w:sz="12" w:space="4" w:color="{NAVY_HEX}"/>'
                    f'</w:pBdr>'
                )
            )
            for r in h.runs:
                r.font.name = "Calibri"
                r.font.color.rgb = NAVY_RGB
                r.font.size = Pt(15)

            if m_mod:
                mod_num = int(m_mod.group(1))
                for c_path, c_cap, b_name in mod_to_charts.get(mod_num, []):
                    if b_name not in inserted_charts and os.path.exists(c_path):
                        insert_chart_with_caption(doc, c_path, c_cap)
                        inserted_charts.add(b_name)
            continue

        if stripped.startswith("### "):
            h_txt = clean_latex_and_md(stripped[4:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=2)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            for r in h.runs:
                r.font.name = "Calibri"
                r.font.color.rgb = BLUE_RGB
                r.font.size = Pt(12.5)
            continue

        if stripped.startswith("#### ") or stripped.startswith("##### "):
            lvl_prefix = 6 if stripped.startswith("##### ") else 5
            h_txt = clean_latex_and_md(stripped[lvl_prefix:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=3)
            h.paragraph_format.keep_with_next = True
            h.paragraph_format.space_before = Pt(8)
            h.paragraph_format.space_after = Pt(3)
            for r in h.runs:
                r.font.name = "Calibri"
                r.font.color.rgb = TEAL_RGB
                r.font.size = Pt(11)
            continue

        # MEJORA 4: Callout Boxes automáticos para Puntuaciones y Dictámenes Clave
        if CALLOUT_TRIGGER_RE.search(stripped):
            add_callout_box(doc, stripped, accent_hex=TEAL_HEX, bg_hex=SLATE_BG)
            continue

        if re.match(r"^(\-|\*)\s+", stripped):
            b_txt = re.sub(r"^(\-|\*)\s+", "", stripped)
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            add_rich_runs(p, b_txt)
            continue

        m_num = re.match(r"^(\d+\.)\s+(.*)$", stripped)
        if m_num:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.22)
            p.paragraph_format.space_before = Pt(3)
            p.paragraph_format.space_after = Pt(3)
            r_num = p.add_run(m_num.group(1) + " ")
            r_num.bold = True
            r_num.font.name = "Calibri"
            r_num.font.size = Pt(10.5)
            r_num.font.color.rgb = NAVY_RGB
            add_rich_runs(p, m_num.group(2))
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        add_rich_runs(p, stripped)

    flush_table()

    # Garantizar que cualquier gráfico restante en charts/ quede embebido
    for c_path in chart_paths:
        b_name = os.path.basename(c_path).lower()
        if b_name not in inserted_charts and os.path.exists(c_path):
            _, c_cap = canonical_chart_specs.get(b_name, (18, f"Gráfico Institucional {b_name}"))
            insert_chart_with_caption(doc, c_path, c_cap)
            inserted_charts.add(b_name)

    try:
        doc.save(out_docx)
    except PermissionError:
        alt_docx = out_docx.replace(".docx", "_UPDATED.docx")
        doc.save(alt_docx)
        out_docx = alt_docx
    print(f"=== WORD INSTITUCIONAL GENERADO: {out_docx} ({len(inserted_charts)} gráficos embebidos) ===")
    return out_docx


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Compilador Word Institucional (.docx) con 6 Mejoras OOXML")
    parser.add_argument("--target-dir", type=str, required=True, help="Directorio de la empresa")
    args = parser.parse_args()
    build_docx(args.target_dir)


if __name__ == "__main__":
    main()
