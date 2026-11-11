#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_deliverables_reference.py — Generador Institucional de Gráficos (10 PNGs 300 DPI),
Documento Word OOXML (~110-125+ páginas, >=30,000 palabras) y Pitch Deck de 40 Diapositivas (.pptx)
exclusivo de referencia para el estándar Deep-Research Gauntlet-Loop.
"""

import os
import re
import sys
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

BASE_DIR = r"C:\PROJECT\Informes\Reports\9988.HK"
CHARTS_DIR = os.path.join(BASE_DIR, "charts")
MD_PATH = os.path.join(BASE_DIR, "ALIBABA_GROUP_HOLDING_9988.HK_INFORME_COMITE_FINAL.md")
DOCX_PATH = os.path.join(BASE_DIR, "ALIBABA_GROUP_HOLDING_9988.HK_INFORME_INSTITUCIONAL_FINAL.docx")
PPTX_PATH = os.path.join(BASE_DIR, "ALIBABA_GROUP_HOLDING_9988.HK_PRESENTACION_COMITE_40_SLIDES.pptx")

os.makedirs(CHARTS_DIR, exist_ok=True)


# ==============================================================================
# 1. GENERACIÓN DE LOS 6 GRÁFICOS INSTITUCIONALES (300 DPI)
# ==============================================================================
def build_charts():
    plt.rcParams["font.sans-serif"] = "DejaVu Sans"
    plt.rcParams["axes.edgecolor"] = "#CBD5E1"
    plt.rcParams["axes.linewidth"] = 0.8

    navy = "#0A192F"
    blue = "#1D4ED8"
    teal = "#0D9488"
    gold = "#D97706"
    red = "#DC2626"
    slate = "#475569"
    light_bg = "#F8FAFC"

    # Chart 1 (Módulo 01): Serie 100% Histórica Auditada de Ingresos, EBITDA/EBITA y Beneficio Neto (Sin proyecciones)
    fig, ax1 = plt.subplots(figsize=(10.5, 5.0), dpi=300)
    fig.patch.set_facecolor("white")
    ax1.set_facecolor(light_bg)
    hist_years = ["FY22A", "FY23A", "FY24A", "FY25A", "FY26A"]
    hist_rev = [853.1, 868.7, 941.2, 996.3, 1023.7]
    hist_ebita = [130.4, 147.9, 165.0, 173.1, 76.4]
    hist_ebita_m = [15.29, 17.03, 17.53, 17.37, 7.46]

    xh = np.arange(len(hist_years))
    w = 0.36
    b1 = ax1.bar(xh - w/2, hist_rev, width=w, color=navy, label="Ingresos Consolidados Auditados (RMB miles M)")
    b2 = ax1.bar(xh + w/2, hist_ebita, width=w, color=teal, label="Adjusted EBITA Auditado (RMB miles M)")
    ax1.set_ylabel("RMB Miles de Millones (Billions)", fontsize=10, fontweight="bold", color=navy)
    ax1.set_xticks(xh)
    ax1.set_xticklabels(hist_years, fontsize=9.5, fontweight="bold")
    ax1.set_ylim(0, 1250)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)

    for bar in b1:
        h = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2, h + 15, f"{h:.1f}B", ha="center", va="bottom", fontsize=8.5, color=navy, fontweight="bold")

    ax2 = ax1.twinx()
    ax2.plot(xh, hist_ebita_m, color=gold, marker="o", linewidth=2.5, markersize=6, label="Margen Adjusted EBITA Histórico (%)")
    ax2.set_ylabel("Margen Adjusted EBITA (%)", fontsize=10, fontweight="bold", color=gold)
    ax2.set_ylim(0, 24)
    for i, m in enumerate(hist_ebita_m):
        ax2.text(xh[i], m + 0.8, f"{m:.1f}%", ha="center", va="bottom", fontsize=8.5, color=gold, fontweight="bold")

    plt.title("Alibaba Group (9988.HK): Desempeño Histórico Auditado de Ingresos y Rentabilidad Operativa (FY22A–FY26A)", fontsize=11.5, fontweight="bold", color=navy, pad=14)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c1_path = os.path.join(CHARTS_DIR, "chart1_historical_performance_5y.png")
    plt.savefig(c1_path, dpi=300)
    plt.close(fig)

    # Variables de 10 años para el gráfico de proyecciones futuras (Módulo 11)
    years = ["FY22A", "FY23A", "FY24A", "FY25A", "FY26A", "FY27E", "FY28E", "FY29E", "FY30E", "FY31E"]
    rev = [853.1, 868.7, 941.2, 996.3, 1023.7, 1145.0, 1273.0, 1404.0, 1535.0, 1665.0]
    ebita = [130.4, 147.9, 165.0, 173.1, 76.4, 148.5, 209.0, 262.0, 305.0, 340.0]
    ebita_m = [15.29, 17.03, 17.53, 17.37, 7.46, 12.97, 16.42, 18.66, 19.87, 20.42]
    x = np.arange(len(years))

    # Chart 2: Desglose por Segmentos FY26 y Rampa Exponencial de Alibaba Cloud + IA
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    segs = ["China E-Commerce\n(Taobao/Tmall/Quick)", "Cloud Intelligence\n(Alibaba Cloud + Qwen)", "Intl Digital Commerce\n(AIDC: AliExpress/Trendyol)", "All Others\n(Amap/Freshippo/Health)"]
    seg_vals = [697.8, 152.8, 150.2, 104.2]
    colors_pie = [navy, blue, teal, gold]
    wedges, texts, autotexts = axL.pie(seg_vals, labels=segs, autopct="%1.1f%%", startangle=140, colors=colors_pie, pctdistance=0.75, textprops={"fontsize": 8, "fontweight": "bold"})
    for at in autotexts:
        at.set_color("white")
    axL.set_title("Mix de Ingresos Brutos por Segmento FY2026\n(Total Ex-Eliminaciones: RMB 1.105,0B | Neto: 1.023,7B)", fontsize=9.5, fontweight="bold", color=navy)

    c_years = ["FY24A", "FY25A", "FY26A", "FY27E", "FY28E", "FY29E", "FY30E", "FY31E"]
    c_rev = [106.4, 118.5, 152.8, 197.2, 250.4, 310.5, 375.7, 441.4]
    c_ebita = [2.3, 10.6, 13.6, 21.5, 31.3, 41.9, 52.6, 64.0]
    xc = np.arange(len(c_years))
    axR.set_facecolor(light_bg)
    axR.bar(xc, c_rev, width=0.52, color=blue, label="Ingresos Alibaba Cloud (RMB B)")
    axR.set_xticks(xc)
    axR.set_xticklabels(c_years, fontsize=8, fontweight="bold")
    axR.set_ylabel("Ingresos Cloud (RMB Miles M)", fontsize=9, fontweight="bold", color=blue)
    axR.set_ylim(0, 510)
    axR.grid(axis="y", linestyle="--", alpha=0.5)
    for i, v in enumerate(c_rev):
        axR.text(xc[i], v + 8, f"{v:.1f}B", ha="center", va="bottom", fontsize=7.5, color=blue, fontweight="bold")
    axR2 = axR.twinx()
    axR2.plot(xc, c_ebita, color=gold, marker="s", linewidth=2.2, label="Adjusted EBITA Cloud (RMB B)")
    axR2.set_ylabel("EBITA Cloud (RMB Miles M)", fontsize=9, fontweight="bold", color=gold)
    axR2.set_ylim(0, 75)
    axR.set_title("Alibaba Cloud + Qwen IA: Superciclo de Ingresos\ny Expansión de EBITA (CAGR FY26–31E: +23,6%)", fontsize=9.5, fontweight="bold", color=navy)
    l1, lb1 = axR.get_legend_handles_labels()
    l2, lb2 = axR2.get_legend_handles_labels()
    axR.legend(l1 + l2, lb1 + lb2, loc="upper left", fontsize=7.5)
    plt.tight_layout()
    c2_path = os.path.join(CHARTS_DIR, "chart2_segment_mix_cloud_ai.png")
    plt.savefig(c2_path, dpi=300)
    plt.close(fig)

    # Chart 8 (Módulo 11): Proyecciones Operativas Futuras a 5 Años (Ingresos, CapEx IA y FCF Consolidado)
    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    ocf = [142.8, 199.8, 182.6, 163.5, 76.2, 185.0, 246.0, 299.0, 340.0, 374.0]
    capex = [42.0, 30.4, 28.4, 86.0, 122.9, 130.0, 125.0, 115.0, 110.0, 105.0]
    fcf = [98.9, 171.7, 156.2, 73.9, -46.6, 55.0, 121.0, 184.0, 230.0, 269.0]

    w3 = 0.27
    ax.bar(x - w3, rev, width=w3, color=navy, label="Ingresos Proyectados Escenario Base Comité (RMB B)")
    ax.bar(x, ebita, width=w3, color=gold, label="Adjusted EBITA Proyectado (RMB B)")
    bars_fcf = ax.bar(x + w3, fcf, width=w3, color=teal, label="Flujo de Caja Libre Proyectado (FCF RMB B)")
    for b in bars_fcf:
        if b.get_height() < 0:
            b.set_color(red)
    for i, val in enumerate(fcf):
        offset = 8 if val >= 0 else -25
        ax.text(x[i] + w3, val + offset, f"{val:.1f}B", ha="center", va="bottom", fontsize=7.2, fontweight="bold", color=red if val < 0 else teal)

    ax.axhline(0, color=slate, linewidth=1.0)
    ax.axvline(4.5, color=red, linestyle=":", linewidth=1.3, label="Inicio Horizonte de Proyección Futura (FY27E–FY31E)")
    ax.set_xticks(x)
    ax.set_xticklabels(years, fontsize=9, fontweight="bold")
    ax.set_ylabel("RMB Miles de Millones (Billions)", fontsize=10, fontweight="bold", color=navy)
    ax.set_ylim(-100, 1850)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_title("Módulo 11 — Proyecciones Operativas Futuras a 5 Años (FY27E–FY31E): Ingresos, EBITA y Cosecha de FCF", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="upper left", frameon=True, fontsize=8.2)
    plt.tight_layout()
    c8_path = os.path.join(CHARTS_DIR, "chart8_future_projections_5y.png")
    plt.savefig(c8_path, dpi=300)
    plt.close(fig)

    # Chart 4 (Módulo 05): Fortaleza Patrimonial — Liquidez Total No Restringida vs Deuda y Caja Neta (FY26)
    fig, ax = plt.subplots(figsize=(10.2, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    categories = [
        "Efectivo y\nEquivalentes\n(Corriente)",
        "Inversiones\nCorto Plazo\n(Corriente)",
        "Depósitos LP\nTesorería Libre\n(1-3 Años)",
        "LIQUIDEZ TOTAL\nNO RESTRINGIDA\n(US$ 75,5B)",
        "Deuda Financiera\nBruta Total\n(Corto + Largo)",
        "CAJA NETA\nCONSOLIDADA\n(US$ 37,8B)",
        "Cartera Ant (33%)\ne Inversiones\n(Valor Libros)"
    ]
    vals4 = [127.1, 159.8, 234.1, 520.8, -260.0, 260.8, 439.1]
    cols4 = [blue, blue, teal, navy, red, "#16A34A", gold]
    x4 = np.arange(len(categories))
    bars4 = ax.bar(x4, vals4, width=0.55, color=cols4)
    ax.axhline(0, color=slate, linewidth=1.0)
    ax.set_xticks(x4)
    ax.set_xticklabels(categories, fontsize=8, fontweight="bold")
    ax.set_ylabel("RMB Miles de Millones (Billions)", fontsize=10, fontweight="bold", color=navy)
    ax.set_ylim(-320, 600)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, v in zip(bars4, vals4):
        pos_y = v + 12 if v >= 0 else v - 28
        ax.text(b.get_x() + b.get_width()/2, pos_y, f"RMB {v:+.1f}B" if v < 0 else f"RMB {v:.1f}B", ha="center", va="bottom", fontsize=8.5, fontweight="bold", color=navy)
    ax.set_title("Fortaleza Patrimonial FY2026: Liquidez No Restringida (RMB 520,8B), Caja Neta (+RMB 260,8B) y Cartera Ant Group", fontsize=10.8, fontweight="bold", color=navy, pad=12)
    plt.tight_layout()
    c4_path = os.path.join(CHARTS_DIR, "chart4_balance_sheet_liquidity.png")
    plt.savefig(c4_path, dpi=300)
    plt.close(fig)

    # Chart 7 (Módulo 10): Triangulación de Valoración, SOTP y Escenarios (HK$ por Acción)
    fig, ax = plt.subplots(figsize=(10.5, 5.0), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    methods = [
        "Escenario Bajista\n(Bear Case - 25%)",
        "Suelo Core SOTP\n(Taobao + Caja Neta + Ant)",
        "PRECIO ACTUAL\n(23-Oct-2026)",
        "Múltiplos Peers\n(13,5x PER Norm. - 15%)",
        "Valor Esperado\nProbabilístico E[V]",
        "PRECIO OBJETIVO BASE\n(Ponderado Comité)",
        "Suma de las Partes\n(SOTP Completo - 35%)",
        "Modelo DCF Base\n(WACC 9,6% - 50%)",
        "Escenario Alcista\n(Bull Case IA - 25%)"
    ]
    prices = [86.00, 97.02, 97.80, 136.50, 141.95, 146.90, 147.20, 149.80, 188.00]
    m_colors = [red, slate, "#334155", blue, teal, "#16A34A", blue, navy, gold]
    y5 = np.arange(len(methods))
    bars5 = ax.barh(y5, prices, height=0.6, color=m_colors)
    ax.axvline(97.80, color=red, linestyle="--", linewidth=1.6, label="Cotización Actual: HK$ 97,80")
    ax.axvline(146.90, color="#16A34A", linestyle="-.", linewidth=1.8, label="Precio Objetivo Base: HK$ 146,90 (+50,2%)")
    ax.set_yticks(y5)
    ax.set_yticklabels(methods, fontsize=8.5, fontweight="bold")
    ax.set_xlabel("Valor por Acción Ordinaria en HKEX (HK$)", fontsize=10, fontweight="bold", color=navy)
    ax.set_xlim(0, 215)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    for b, p in zip(bars5, prices):
        diff = ((p / 97.80) - 1.0) * 100
        ax.text(p + 2.5, b.get_y() + b.get_height()/2, f"HK$ {p:.2f} ({diff:+.1f}%)", va="center", ha="left", fontsize=8.5, fontweight="bold", color=navy)
    ax.set_title("Triangulación de Valoración Institucional (9988.HK): Ratio Rentabilidad/Riesgo Base vs. Bear de 4,16x", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="lower right", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c7_path = os.path.join(CHARTS_DIR, "chart7_valuation_sotp_football_field.png")
    plt.savefig(c7_path, dpi=300)
    plt.close(fig)

    # Chart 9 (Módulo 13): Estructura Técnica 12 Meses (9988.HK), Medias Móviles y Tramos de Entrada
    fig, ax = plt.subplots(figsize=(10.5, 4.9), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    months = ["Oct 25", "Nov 25", "Dec 25", "Jan 26", "Feb 26", "Mar 26", "Apr 26", "May 26", "Jun 26", "Jul 26", "Aug 26", "Sep 26", "Oct 26"]
    closes = [164.91, 151.33, 142.64, 169.01, 142.74, 118.87, 125.86, 120.76, 92.85, 117.00, 114.20, 106.60, 97.80]
    xm = np.arange(len(months))
    ax.plot(xm, closes, color=navy, marker="o", linewidth=2.6, markersize=6, label="Cierre Mensual 9988.HK (HK$)")
    ax.axhline(125.61, color=gold, linestyle="--", linewidth=1.6, label="MM200 Sesiones: HK$ 125,61 (Resistencia Mayor)")
    ax.axhline(110.43, color=blue, linestyle="-.", linewidth=1.6, label="MM50 Sesiones: HK$ 110,43 (Gatillo Tramo 3 Breakout)")
    ax.axhline(88.65, color=teal, linestyle=":", linewidth=1.8, label="Mínimo 52 Semanas: HK$ 88,65 (Soporte Estructural / Tramo 2)")
    ax.axhline(78.50, color=red, linestyle="-", linewidth=1.4, label="Stop-Loss Institucional Duro: Cierre Semanal < HK$ 78,50")
    ax.fill_between(xm, 88.65, 98.50, color=teal, alpha=0.13, label="Zona de Acumulación Táctica (Tramos 1 y 2: HK$ 88,65–98,50)")
    for i, c in enumerate(closes):
        ax.text(xm[i], c + 3.2, f"{c:.1f}", ha="center", va="bottom", fontsize=7.8, fontweight="bold", color=navy)
    ax.set_xticks(xm)
    ax.set_xticklabels(months, fontsize=8.5, fontweight="bold")
    ax.set_ylabel("Precio de Cierre en HKEX (HK$)", fontsize=10, fontweight="bold", color=navy)
    ax.set_ylim(68, 190)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title("Análisis Técnico y Timing (9988.HK): Doble Suelo Institucional sobre HK$ 88,65–97,80 (RSI 14 = 40,38)", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="upper right", frameon=True, fontsize=7.8)
    plt.tight_layout()
    c9_path = os.path.join(CHARTS_DIR, "chart9_price_technicals_tranches.png")
    plt.savefig(c9_path, dpi=300)
    plt.close(fig)

    # Chart 5 (Módulo 06): Evolución de Márgenes (Bruto, EBITDA, EBIT, Neto) y ROIC vs WACC
    fig, ax = plt.subplots(figsize=(10.5, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    gm = [36.8, 36.7, 37.7, 40.0, 39.8]
    roic = [11.2, 12.8, 14.1, 14.6, 8.9]
    ax.plot(xh, gm, color=navy, marker="o", linewidth=2.4, label="Margen Bruto Consolidado Histórico (%)")
    ax.plot(xh, hist_ebita_m, color=teal, marker="s", linewidth=2.4, label="Margen Adjusted EBITA Histórico (%)")
    ax.plot(xh, roic, color=gold, marker="^", linewidth=2.4, label="ROIC Operativo Post-Impuestos (%)")
    ax.axhline(9.6, color=red, linestyle="--", linewidth=1.5, label="Coste Medio Ponderado de Capital (WACC = 9,6%)")
    ax.set_xticks(xh)
    ax.set_xticklabels(hist_years, fontsize=9, fontweight="bold")
    ax.set_ylabel("Porcentaje (%)", fontsize=10, fontweight="bold", color=navy)
    ax.set_ylim(0, 48)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.set_title("Módulo 06 — Evolución Histórica de Márgenes Operativos y Creación de Valor (ROIC vs. WACC)", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="lower right", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c5_path = os.path.join(CHARTS_DIR, "chart5_margins_roic_vs_wacc.png")
    plt.savefig(c5_path, dpi=300)
    plt.close(fig)

    # Chart 6 (Módulo 07): Ciclo de Conversión de Caja (DSO, DIO, DPO, CCC) y Eficiencia Operativa
    fig, ax = plt.subplots(figsize=(10.2, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    wc_years = ["FY22A", "FY23A", "FY24A", "FY25A", "FY26A"]
    dso = [14.2, 13.8, 14.5, 15.1, 15.6]
    dio = [9.5, 8.8, 7.9, 6.4, 5.2]
    dpo = [-91.0, -92.4, -93.1, -93.8, -92.1]
    ccc = [-67.3, -69.8, -70.7, -72.3, -71.3]
    xw = np.arange(len(wc_years))
    ax.bar(xw - 0.25, dso, width=0.24, color=blue, label="DSO (Días de Cobro)")
    ax.bar(xw, dio, width=0.24, color=gold, label="DIO (Días de Inventario)")
    ax.bar(xw + 0.25, dpo, width=0.24, color=teal, label="DPO (Días de Pago - Financiación Proveedores)")
    ax.plot(xw, ccc, color=navy, marker="o", linewidth=2.5, label="Ciclo de Conversión de Caja Neto (CCC en días)")
    ax.axhline(0, color=slate, linewidth=1.0)
    ax.set_xticks(xw)
    ax.set_xticklabels(wc_years, fontsize=9, fontweight="bold")
    ax.set_ylabel("Días de Rotación de Circulante", fontsize=10, fontweight="bold", color=navy)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_title("Eficiencia del Capital Circulante: Ciclo de Conversión de Caja Estructuralmente Negativo (-71,3 Días)", fontsize=10.8, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="lower left", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c6_path = os.path.join(CHARTS_DIR, "chart6_working_capital_ccc.png")
    plt.savefig(c6_path, dpi=300)
    plt.close(fig)

    # Chart 3 (Módulo 03): Benchmarking Competitivo frente a Peers Cotizados (PER Forward vs. Margen / Crecimiento)
    fig, ax = plt.subplots(figsize=(10.2, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    peers = ["Alibaba\n(9988.HK)", "Tencent\n(0700.HK)", "PDD Holdings\n(PDD)", "JD.com\n(9618.HK)", "Meituan\n(3690.HK)", "Amazon\n(AMZN)"]
    pe_fwd = [10.86, 16.40, 10.20, 8.90, 17.50, 31.20]
    ev_eb = [7.40, 12.80, 7.90, 5.60, 13.10, 16.80]
    xp = np.arange(len(peers))
    ax.bar(xp - 0.18, pe_fwd, width=0.35, color=navy, label="P/E Forward 12M (x)")
    ax.bar(xp + 0.18, ev_eb, width=0.35, color=teal, label="EV / EBITDA Norm. (x)")
    ax.set_xticks(xp)
    ax.set_xticklabels(peers, fontsize=8.8, fontweight="bold")
    ax.set_ylabel("Múltiplo de Valoración (Veces - x)", fontsize=10, fontweight="bold", color=navy)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_title("Benchmarking de Múltiplos Bursátiles frente a Comparables Globales y Domésticos", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="upper left", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c3_path = os.path.join(CHARTS_DIR, "chart3_peer_benchmarking_multiples.png")
    plt.savefig(c3_path, dpi=300)
    plt.close(fig)

    # Chart 10: Desglose de Valoración SOTP por Unidad de Negocio (HK$ por Acción)
    fig, ax = plt.subplots(figsize=(10.2, 4.8), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor(light_bg)
    sotp_parts = [
        "Taobao & Tmall\nCore Commerce",
        "Alibaba Cloud\n& IA Qwen",
        "Caja Neta\nNo Restringida",
        "Ant Group (33%)\n& Cartera",
        "AIDC (AliExpress\n& Trendyol)",
        "Otros Activos\n(Amap/Cainiao)",
        "Descuento\nHolding (-10%)",
        "VALOR TOTAL\nSOTP (HK$/acc)"
    ]
    sotp_vals = [70.30, 40.75, 13.01, 13.71, 10.24, 15.55, -16.36, 147.20]
    sotp_cols = [navy, blue, "#16A34A", gold, teal, blue, red, "#16A34A"]
    xs = np.arange(len(sotp_parts))
    bars10 = ax.bar(xs, sotp_vals, width=0.55, color=sotp_cols)
    ax.axhline(0, color=slate, linewidth=1.0)
    ax.axhline(97.80, color=red, linestyle="--", linewidth=1.5, label="Precio Spot Actual: HK$ 97,80")
    ax.set_xticks(xs)
    ax.set_xticklabels(sotp_parts, fontsize=8, fontweight="bold")
    ax.set_ylabel("HK$ por Acción Ordinaria", fontsize=10, fontweight="bold", color=navy)
    ax.set_ylim(-30, 175)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    for b, v in zip(bars10, sotp_vals):
        py = v + 4 if v >= 0 else v - 12
        ax.text(b.get_x() + b.get_width()/2, py, f"{v:+.1f}" if v < 0 else f"{v:.1f}", ha="center", va="bottom", fontsize=8, fontweight="bold", color=navy)
    ax.set_title("Puente de Valoración por Suma de las Partes (SOTP): HK$ 147,20 por Acción (+50,5% Upside)", fontsize=11, fontweight="bold", color=navy, pad=12)
    ax.legend(loc="upper left", frameon=True, fontsize=8.5)
    plt.tight_layout()
    c10_path = os.path.join(CHARTS_DIR, "chart10_sotp_waterfall_breakdown.png")
    plt.savefig(c10_path, dpi=300)
    plt.close(fig)

    return [c1_path, c2_path, c3_path, c4_path, c5_path, c6_path, c7_path, c8_path, c9_path, c10_path]


# ==============================================================================
# 2. GENERACIÓN DEL DOCUMENTO WORD INSTITUCIONAL (.DOCX)
# ==============================================================================
def clean_md_inline(text: str) -> str:
    text = text.replace("`", "")
    text = re.sub(r"<br\s*/?>", " ", text, flags=re.IGNORECASE)
    text = text.replace("$$", "").replace("$", "")
    text = re.sub(r"\\text\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\frac\{([^}]*)\}\{([^}]*)\}", r"(\1 / \2)", text)
    text = re.sub(r"\\underbrace\{([^}]*)\}_\{([^}]*)\}", r"\1 (\2)", text)
    text = re.sub(r"\\left|\\right|\\times|\\rightarrow|\\sum_\{[^}]*\}\^\{[^}]*\}", " ", text)
    text = text.replace("\\", "")
    return text


def add_formatted_runs(paragraph, raw_text: str):
    cleaned = clean_md_inline(raw_text)
    tokens = re.split(r"(\*\*.*?\*\*|\*[^\*]+?\*)", cleaned)
    for tok in tokens:
        if not tok:
            continue
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            r = paragraph.add_run(tok[2:-2].replace("*", ""))
            r.bold = True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            r = paragraph.add_run(tok[1:-1].replace("*", ""))
            r.italic = True
        else:
            r = paragraph.add_run(tok.replace("*", ""))


def set_cell_bg(cell, hex_color: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def set_table_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        '<w:top w:val="single" w:sz="6" w:space="0" w:color="0A192F"/>'
        '<w:bottom w:val="single" w:sz="8" w:space="0" w:color="0A192F"/>'
        '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="CBD5E1"/>'
        '<w:left w:val="none"/><w:right w:val="none"/><w:insideV w:val="none"/>'
        '</w:tblBorders>'
    )
    tblPr.append(borders)


def render_table_docx(doc, rows_data):
    if not rows_data:
        return
    num_cols = max(len(r) for r in rows_data)
    table = doc.add_table(rows=len(rows_data), cols=num_cols)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    for r_idx, r_vals in enumerate(rows_data):
        row = table.rows[r_idx]
        if r_idx == 0:
            trPr = row._tr.get_or_add_trPr()
            trPr.append(OxmlElement("w:tblHeader"))
        trPr = row._tr.get_or_add_trPr()
        trPr.append(OxmlElement("w:cantSplit"))

        for c_idx in range(num_cols):
            val = r_vals[c_idx].strip() if c_idx < len(r_vals) else ""
            cell = row.cells[c_idx]
            p = cell.paragraphs[0]
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            add_formatted_runs(p, val)

            if r_idx == 0:
                set_cell_bg(cell, "0A192F")
                for run in p.runs:
                    run.font.bold = True
                    run.font.color.rgb = RGBColor(255, 255, 255)
                    run.font.size = Pt(8.5)
            else:
                if r_idx % 2 == 1:
                    set_cell_bg(cell, "F8FAFC")
                for run in p.runs:
                    run.font.size = Pt(8.5)
                    run.font.color.rgb = RGBColor(15, 23, 42)
    doc.add_paragraph()


def build_docx(chart_paths):
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_lines = f.readlines()

    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = RGBColor(30, 41, 59)

    # Portada Institucional Ejecutiva
    p_cat = doc.add_paragraph()
    r_cat = p_cat.add_run("EXPEDIENTE INSTITUCIONAL DEL COMITÉ DE INVERSIONES — DEEP-RESEARCH EQUITY AUDIT")
    r_cat.font.size = Pt(10)
    r_cat.font.bold = True
    r_cat.font.color.rgb = RGBColor(13, 148, 136)

    p_title = doc.add_paragraph()
    r_title = p_title.add_run("ALIBABA GROUP HOLDING LIMITED\n(HKEX: 9988.HK | NYSE: BABA)")
    r_title.font.size = Pt(24)
    r_title.font.bold = True
    r_title.font.color.rgb = RGBColor(10, 25, 47)

    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(
        "Auditoría Forense Quinquenal (FY2022–FY2026), Catálogo Exhaustivo de Ecosistemas (E-Commerce & Cloud/IA Qwen), "
        "Valoración Intrínseca (DCF / SOTP / Reverse DCF) y Estrategia de Ejecución Institucional"
    )
    r_sub.font.size = Pt(12.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = RGBColor(71, 85, 105)

    summary_box = [
        ["Atributo Institucional", "Dictamen Oficial del Comité de Inversiones (23 de Octubre de 2026)"],
        ["Veredicto Ejecutivo", "COMPRA (BUY) — Acumulación en Debilidad Táctica (Convicción: 7,8 / 10 | Score Global: 8,06 / 10)"],
        ["Cotización Actual vs. Objetivo", "Precio Actual: HK$ 97,80 (US$ 100,20 / ADS) | Precio Objetivo Base: HK$ 146,90 (+50,20% Upside)"],
        ["Valor Esperado Probabilístico", "HK$ 141,95 (+45,14% Potencial) | Escenarios: Bull HK$ 188,00 / Base HK$ 146,90 / Bear HK$ 86,00 (Ratio 4,16x)"],
        ["Métricas FY2026 Auditadas", "Ingresos: RMB 1.023.670M (+11,0% LfL) | Adj. EBITA: RMB 76.416M | Beneficio Neto GAAP: RMB 102.127M"],
        ["Fortaleza Patrimonial y Forense", "Liquidez No Restringida: RMB 520.824M (US$ 75,5B) | Caja Neta: +RMB 260.828M | Altman Z'': 6,55 | Beneish: -2,46"],
        ["Asignación en Cartera", "Peso Recomendado: 5,25% del NAV (Rango 4,5%–6,0%) en 3 Tramos | Stop-Loss Duro: Cierre Semanal < HK$ 78,50"]
    ]
    render_table_docx(doc, summary_box)
    doc.add_page_break()

    chart_map = {
        1: (chart_paths[0], "Gráfico 1 (Módulo 01): Desempeño Histórico Auditado de Ingresos y Rentabilidad Operativa (5 Ejercicios Cerrados — 100% Histórico, Sin Proyecciones)."),
        2: (chart_paths[1], "Gráfico 2 (Módulo 02): Mix de Ingresos por Segmento de Negocio y Geografía."),
        3: (chart_paths[2], "Gráfico 3 (Módulo 03): Mapa Competitivo Sectorial y Comparativa de Múltiplos frente a Peers Cotizados."),
        5: (chart_paths[3], "Gráfico 4 (Módulo 05): Radiografía Forense de Liquidez Total, Deuda Financiera Bruta y Caja Neta Real."),
        6: (chart_paths[4], "Gráfico 5 (Módulo 06): Evolución Histórica de Márgenes Operativos, Unit Economics y ROIC vs. WACC."),
        7: (chart_paths[5], "Gráfico 6 (Módulo 07): Eficiencia del Capital Circulante y Ciclo de Conversión de Caja (DSO, DIO, DPO, CCC)."),
        10: (chart_paths[6], "Gráfico 7 (Módulo 10): Campo de Fútbol de Valoración Institucional (DCF, SOTP, Múltiplos y Escenarios Bear/Base/Bull)."),
        11: (chart_paths[7], "Gráfico 8 (Módulo 11): Proyecciones Operativas Futuras a 5 Años (Ingresos, EBITA y FCF en Escenarios del Comité vs. Consenso)."),
        13: (chart_paths[8], "Gráfico 9 (Módulo 13): Estructura Técnica 12 Meses, Medias Móviles (MM50/MM200) y Zonas de Acumulación por Tramos."),
        17: (chart_paths[9], "Gráfico 10 (Módulo 17): Puente de Valoración SOTP y Anatomía del Retorno Total Esperado (Veredicto Final Ejecutable).")
    }
    inserted_charts = set()

    table_buffer = []
    in_code_block = False

    def flush_table():
        nonlocal table_buffer
        if table_buffer:
            render_table_docx(doc, table_buffer)
            table_buffer = []

    for raw_line in md_lines:
        line = raw_line.rstrip("\n\r")
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_table()
            in_code_block = not in_code_block
            continue

        if in_code_block:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            r = p.add_run(clean_md_inline(stripped))
            r.font.name = "Consolas"
            r.font.size = Pt(8.5)
            continue

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

        if stripped.startswith("# "):
            h_txt = clean_md_inline(stripped[2:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=1)
            for r in h.runs:
                r.font.color.rgb = RGBColor(10, 25, 47)
                r.font.size = Pt(16)
            continue

        if stripped.startswith("## "):
            h_txt = clean_md_inline(stripped[3:].strip()).replace("*", "")
            m_mod = re.search(r"M[oó]dulo\s*0?(\d+)", h_txt, re.IGNORECASE)
            h = doc.add_heading(h_txt, level=1)
            for r in h.runs:
                r.font.color.rgb = RGBColor(10, 25, 47)
                r.font.size = Pt(15)
            if m_mod:
                mod_num = int(m_mod.group(1))
                if mod_num in chart_map and mod_num not in inserted_charts:
                    c_path, c_cap = chart_map[mod_num]
                    if os.path.exists(c_path):
                        p_img = doc.add_paragraph()
                        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        p_img.add_run().add_picture(c_path, width=Inches(6.3))
                        p_cap = doc.add_paragraph()
                        p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                        r_cap = p_cap.add_run(c_cap)
                        r_cap.font.size = Pt(8.5)
                        r_cap.font.italic = True
                        r_cap.font.color.rgb = RGBColor(71, 85, 105)
                        inserted_charts.add(mod_num)
            continue

        if stripped.startswith("### "):
            h_txt = clean_md_inline(stripped[4:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=2)
            for r in h.runs:
                r.font.color.rgb = RGBColor(29, 78, 216)
                r.font.size = Pt(12.5)
            continue

        if stripped.startswith("#### "):
            h_txt = clean_md_inline(stripped[5:].strip()).replace("*", "")
            h = doc.add_heading(h_txt, level=3)
            for r in h.runs:
                r.font.color.rgb = RGBColor(13, 148, 136)
                r.font.size = Pt(11)
            continue

        if re.match(r"^(\-|\*)\s+", stripped):
            b_txt = re.sub(r"^(\-|\*)\s+", "", stripped)
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            add_formatted_runs(p, b_txt)
            continue

        m_num = re.match(r"^(\d+\.)\s+(.*)$", stripped)
        if m_num:
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.22)
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            r_num = p.add_run(m_num.group(1) + " ")
            r_num.bold = True
            add_formatted_runs(p, m_num.group(2))
            continue

        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(2)
        p.paragraph_format.space_after = Pt(4)
        add_formatted_runs(p, stripped)

    flush_table()
    doc.save(DOCX_PATH)
    print(f"[DOCX] Generado exitosamente: {DOCX_PATH}")


# ==============================================================================
# 3. GENERACIÓN DE LA PRESENTACIÓN DE 40 DIAPOSITIVAS (.PPTX + .PDF)
# ==============================================================================
SLIDES_DATA = [
    # --------------------------------------------------------------------------
    # ACTO I — Quién es la empresa y qué hace (Diapositivas 1 a 5 | Módulo 01)
    # --------------------------------------------------------------------------
    {
        "num": 1,
        "section": "ACTO I: QUIÉN ES LA EMPRESA  |  PORTADA & TESIS CENTRAL",
        "title": "Alibaba Group Holding Limited (9988.HK / BABA)",
        "subtitle": "Expediente del Comité de Inversiones | Auditoría Forense FY22–FY26, Ecosistema de IA y Valoración SOTP/DCF",
        "kpis": [("VEREDICTO COMITÉ", "COMPRA (BUY)"), ("PRECIO SPOT", "HK$ 97,80"), ("PRECIO OBJETIVO", "HK$ 146,90 (+50,2%)"), ("CAJA NETA FORENSE", "RMB 260.828M")],
        "bullets": [
            "Tesis Central: Al precio actual de HK$ 97,80 (10,86x PER Forward | 1,48x P/B), el mercado castiga como deterioro permanente lo que en realidad fue un valle transitorio de FCF por inversión en IA (-RMB 46.609M en FY26).",
            "Protección Patrimonial SOTP: Solo el negocio maduro de Taobao y Tmall (HK$ 70,30) más la Caja Neta (HK$ 13,01) y la participación en Ant Group (HK$ 13,71) suman HK$ 97,02 por acción, cubriendo el 99,2% del precio actual.",
            "Opcionalidad Tecnológica Gratuita: El inversor adquiere Alibaba Cloud y el ecosistema de IA Qwen (valorados en HK$ 40,75/acción) junto al negocio internacional AIDC (HK$ 10,24/acción) a coste implícito cero.",
            "Asignación Recomendada: Posición del 5,25% del NAV ejecutada en 3 tramos tácticos con un ratio rentabilidad/riesgo asimétrico de 4,16x frente al escenario bajista."
        ]
    },
    {
        "num": 2,
        "section": "ACTO I: QUIÉN ES LA EMPRESA  |  MÓDULO 01 — PERFIL Y ESCALA",
        "title": "Alibaba Group: escala global, tracción de ingresos y evolución histórica",
        "subtitle": "De plataforma de comercio B2B en Hangzhou a líder indiscutible del consumo digital y la nube en Asia",
        "kpis": [("MARKET CAP", "HK$ 1.946.412M"), ("INGRESOS FY26", "RMB 1.023.670M"), ("USUARIOS ACTIVOS", ">1.000 Millones"), ("CRECIMIENTO LFL", "+11,0% Interanual")],
        "table": [
            ["Dimensión Corporativa", "Métrica Auditada FY26 / Cierre 2026", "Lectura Estratégica del Comité"],
            ["Cotización Dual Primaria", "HKEX (9988.HK) y NYSE (BABA: 1 ADS = 8 Ord.)", "Inclusión en Southbound Stock Connect con más del 10% del capital en manos domésticas chinas."],
            ["Volumen Transaccional (GMV)", ">RMB 8,0 Billones en Taobao y Tmall", "Canaliza más del 28% de todo el comercio minorista online de China."],
            ["Ingresos Consolidados", "RMB 1.023.670M (+11,0% LfL ex-desinversiones)", "Crecimiento orgánico acelerando tras eliminar el arrastre de filiales físicas deficitarias."],
            ["Plantilla y Productividad", "125.800 empleados especializados", "Ingresos por empleado de RMB 8,14M (+18% YoY tras automatización con modelos de IA)."]
        ],
        "bullets": [
            "Hitos de Evolución: Desde su fundación en 1999 por Jack Ma, Alibaba construyó la infraestructura troncal del comercio chino (Taobao en 2003, Alipay en 2004, Alibaba Cloud en 2009 y la red Cainiao en 2013).",
            "Tracción Institucional: Su base transaccional superior a 1.000 millones de consumidores activos anuales otorga un efecto de red insustituible para marcas globales y pymes industriales."
        ]
    },
    {
        "num": 3,
        "section": "ACTO I: QUIÉN ES LA EMPRESA  |  MÓDULO 01 — CADENA DE VALOR",
        "title": "Qué problema resuelve y qué lugar ocupa en la cadena de valor",
        "subtitle": "Peaje digital sobre el consumo chino y facilitador troncal de computación para empresas",
        "table": [
            ["Eslabón de la Cadena", "Fricción Crítica Resuelta", "Mecanismo de Captura de Valor"],
            ["Descubrimiento y Demanda", "Resuelve la fragmentación de cientos de millones de compradores mediante algoritmos de recomendación en tiempo real.", "Monetización publicitaria (CMR) vía pujas por clic (P4P) y herramientas algorítmicas Quanzhantui."],
            ["Transacción y Confianza", "Elimina el riesgo de fraude en pagos y disputas comerciales entre compradores y comerciantes pymes.", "Tarifa de software básica del 0,6% sobre GMV liquidado más comisiones variables del 2% al 5% en Tmall."],
            ["Logística y Cumplimiento", "Resuelve el cuello de botella de distribución física integrando paquetería express y entregas en 30 minutos.", "Tarifas logísticas de Cainiao y take rates en comercio instantáneo (Taobao Instant Commerce)."],
            ["Computación en la Nube", "Democratiza la potencia de cálculo y modelos fundacionales de IA para corporaciones y desarrolladores.", "Suscripciones IaaS/PaaS/MaaS con contratos plurianuales y consumo escalable de inferencia IA."]
        ],
        "bullets": [
            "Posicionamiento Estratégico: Alibaba opera como la plataforma intermedia indispensable entre más de 10 millones de vendedores comerciales y la mayor clase media consumidora del planeta.",
            "Poder de Fijación de Precios: Su condición de estándar transaccional de facto le permite aplicar tarifas de software sin pérdida de cuota de mercado ni fuga de comerciantes."
        ]
    },
    {
        "num": 4,
        "section": "ACTO I: QUIÉN ES LA EMPRESA  |  MÓDULO 01 — TRANSFORMACIÓN ESTRATÉGICA",
        "title": "Transformación estratégica reciente: salida de negocios de bajo margen",
        "subtitle": "Racionalización de cartera bajo Eddie Wu: desinversión en retail físico y foco en E-Commerce e IA",
        "table": [
            ["Operación de Cartera", "Fecha de Ejecución", "Impacto Operativo y Financiero"],
            ["Cierre de Supervisión SAMR", "Agosto 2024", "Finalización formal del periodo de rectificación antimonopolio de 3 años, disipando la incertidumbre regulatoria."],
            ["Venta de Intime Retail", "Diciembre 2024", "Desinversión en grandes almacenes físicos por ~RMB 7.400M, eliminando costes fijos de arrendamiento."],
            ["Venta de Sun Art Retail", "Febrero 2025", "Venta de hipermercados físicos a DCP Capital por ~HK$ 13.138M, eliminando RMB 83.000M de ventas de margen estrecho."],
            ["Reintegración de Cainiao", "Marzo 2024", "Recompra del 36% de minoritarios por US$ 3.750M para integrar la red logística al servicio prioritario de Taobao y AliExpress."],
            ["Southbound Stock Connect", "Septiembre 2024", "Conversión a cotización primaria dual que atrajo más de US$ 22.000M de capital inversor doméstico chino."]
        ],
        "bullets": [
            "Foco Estratégico Absoluto: La directiva ha redirigido el 100% de la reinversión hacia dos motores prioritarios: el comercio digital orientado a la experiencia del usuario y la infraestructura de inteligencia artificial.",
            "Mejora Inmediata de Calidad: Aunque los ingresos reportados crecieron un modesto +2,7% por la desconsolidación de Sun Art, las ventas de las operaciones continuadas avanzaron un vigoroso +11,0% LfL."
        ]
    },
    {
        "num": 5,
        "section": "ACTO I: QUIÉN ES LA EMPRESA  |  MÓDULO 01 — HISTORIA AUDITADA (5 AÑOS)",
        "title": "Desempeño histórico auditado (FY22A–FY26A): ingresos y rentabilidad",
        "subtitle": "Resultados 100% históricos auditados sin proyecciones: escala consolidada superior a RMB 1,02 Billones",
        "chart": "chart1_historical_performance_5y.png",
        "bullets": [
            "Escala Auditada de Ingresos: La facturación consolidada creció desde RMB 853.088M en FY22 hasta RMB 1.023.670M en FY26; esto prueba la tracción comercial sólida frente a la debilidad del consumo discrecional chino.",
            "Evolución del Adjusted EBITA: El beneficio operativo ajustado promedió RMB 154.000M anuales entre FY22 y FY25, antes del valle puntual de FY26 originado por la inversión promocional en comercio rápido.",
            "Estabilidad de Margen Bruto: El margen bruto se mantuvo firme en el rango de 36,7% a 40,0% durante todo el lustro. Este comportamiento confirma el carácter asset-light del marketplace frente a distribuidores 1P.",
            "Cero Estimaciones Futuras: Este gráfico refleja de forma estricta los estados contables auditados por PwC; el Módulo 11 aborda el modelado de escenarios futuros."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO II — Cómo lo hace: modelo de negocio, catálogo, sector y ventaja competitiva (Diapositivas 6 a 13)
    # --------------------------------------------------------------------------
    {
        "num": 6,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 02 — DIVISIONES DE NEGOCIO",
        "title": "Estructura de las divisiones de negocio y peso en ingresos FY2026",
        "subtitle": "Desglose divisional: hegemonía del E-Commerce doméstico y expansión acelerada de Cloud e IA",
        "chart": "chart2_segment_mix_cloud_ai.png",
        "bullets": [
            "China E-Commerce Group (68,2% ingresos | RMB 697.810M): Motor de generación de caja que agrupa Taobao, Tmall, Alimama, Taobao Instant Commerce y la división mayorista 1688.com.",
            "Cloud Intelligence Group (14,9% ingresos | RMB 152.836M): Crecimiento interanual del +29,0% impulsado por los ingresos relacionados con IA (>100% interanual por diez trimestres consecutivos).",
            "International Digital Commerce - AIDC (14,7% ingresos | RMB 150.151M): Avance del +14,0% con fuerte tracción del modelo semi-gestionado AliExpress Choice y el liderazgo de Trendyol en Turquía.",
            "All Others (RMB 104.200M): Activos de alta frecuencia como la app de mapas Amap (>170M DAU), los supermercados Freshippo y la plataforma sanitaria Alibaba Health."
        ]
    },
    {
        "num": 7,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 02 — MODELO DE NEGOCIO Y UNIT ECONOMICS",
        "title": "Anatomía del modelo de negocio y unidad económica de monetización",
        "subtitle": "Cómo capta tráfico masivo, cómo cobra a comerciantes y empresas y cómo genera margen de contribución",
        "kpis": [("INGRESOS CMR FY26", "RMB 361.800M (+10%)"), ("TARIFA BÁSICA SOFTWARE", "0,6% sobre GMV"), ("MARGEN BRUTO GRUPO", "39,81% en FY26"), ("RETENCIÓN CLOUD", "NDR > 110% en IA")],
        "table": [
            ["Fase del Embudo", "Mecanismo Operativo", "Unidad Económica y Rendimiento"],
            ["1. Captación de Tráfico", "Tráfico orgánico masivo por búsqueda, retransmisiones en vivo y servicios locales de alta frecuencia.", "Coste marginal de captación cercano a cero; usuarios diarios (DAU) en máximos históricos."],
            ["2. Monetización Publicitaria", "Comerciantes pymes y marcas de Tmall pujan por visibilidad mediante la herramienta algorítmica Quanzhantui.", "Take rate de CMR en torno al 4,5% sobre GMV con margen de contribución superior al 85%."],
            ["3. Comisión por Transacción", "Cobro de comisión variable (2%–5%) en Tmall y nueva tarifa de software básica del 0,6% en todo Taobao.", "Generación directa de más de RMB 15.000M de ingresos operativos netos de alto margen incremental."],
            ["4. Monetización Cloud e IA", "Empresas despliegan aplicaciones empresariales sobre la plataforma Bailian consumiendo API tokens y almacenamiento.", "Margen de Adjusted EBITA en Cloud expandiéndose del 2,2% en FY24 al 8,9% en FY26 (RMB 13.646M)."]
        ],
        "bullets": [
            "Asset-Light en el Núcleo: A diferencia de minoristas tradicionales, Alibaba no compra ni almacena el inventario de Taobao y Tmall, cobrando cánones por servicios que fluyen directamente al margen.",
            "Sinergia de Ecosistema: El tráfico captado por las compras cotidianas alimenta la base de datos de comportamiento que luego entrena los modelos de IA y rentabiliza la nube."
        ]
    },
    {
        "num": 8,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 02 — CATÁLOGO COMERCIAL",
        "title": "Catálogo exhaustivo de productos y servicios comerciales (Parte I)",
        "subtitle": "Tabla maestra de plataformas de venta, tipología de clientes y mecanismos de cobro",
        "table": [
            ["Plataforma / Línea Comercial", "Segmento Cliente", "Propuesta de Valor Principal", "Mecanismo de Monetización", "Cuota / Volumen"],
            ["Taobao Marketplace", "Consumidor masivo C2C", "Búsqueda infinita de productos y pymes", "Pujas publicitarias CPC/CPM + tarifa 0,6%", ">1.000M usuarios activos"],
            ["Tmall Flagship Stores", "Marcas premium B2C", "Canal oficial directo de marcas líderes", "Comisión sobre venta (2%–5%) + cuotas fijas", ">250.000 marcas registradas"],
            ["Taobao Instant Commerce", "Consumo urbano hiperlocal", "Entrega ultrarrápida en 30 a 60 minutos", "Comisión por entrega y take rate de comercio", "RMB 82.300M (+36% YoY)"],
            ["Membresía 88VIP", "Clientes de alto valor", "Descuentos cruzados y suscripciones VIP", "Cuota anual de RMB 88/año por usuario", ">42 millones de miembros"],
            ["1688.com B2B Doméstico", "Comercio mayorista", "Aprovisionamiento directo de fábricas chinas", "Cuotas de membresía y comisiones comerciales", "RMB 53.100M (+19% YoY)"],
            ["AliExpress & Choice", "Consumidores globales", "Envíos internacionales en 5–7 días", "Comisiones cross-border y margen logístico", "Presencia en >100 países"],
            ["Trendyol", "Oriente Medio y Turquía", "Plataforma líder de moda y consumo digital", "Take rate de marketplace y servicios de entrega", "#1 en Turquía y Golfo"],
            ["Lazada", "Sudeste Asiático (ASEAN)", "Marketplace generalista adaptado a ASEAN", "Comisiones transaccionales y publicidad", "Top 2 en mercados ASEAN"],
            ["Alibaba.com Global B2B", "Importadores mundiales", "Mayor directorio de exportadores de China", "Suscripciones Gold Supplier y comisiones", ">40 millones de compradores"]
        ],
        "bullets": [
            "Diversidad Comercial: El catálogo cubre desde el comercio C2C de bajo ticket hasta transacciones B2B transfronterizas multimillonarias, blindando los ingresos ante fluctuaciones sectoriales."
        ]
    },
    {
        "num": 9,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 02 — CATÁLOGO TECNOLÓGICO",
        "title": "Catálogo tecnológico: nube, inteligencia artificial, semiconductores y logística",
        "subtitle": "Infraestructura propietaria: hiperescalador Cloud, ecosistema Qwen, chips T-Head y red Cainiao",
        "table": [
            ["Línea Tecnológica", "Activo Propietario / SKU", "Capacidad Funcional y Alcance Técnico", "Monetización y Despliegue"],
            ["Cloud Hiperescala", "Alibaba Cloud IaaS/PaaS", "30 regiones y 89 zonas de disponibilidad globales con refrigeración líquida.", "Facturación por uso de cómputo y almacenamiento (RMB 152,8B)."],
            ["Modelos Fundacionales IA", "Familia Qwen 2.5 y Qwen MoE", "Modelos de pesos abiertos líderes mundiales en benchmarks de matemáticas y código.", "Plataforma Model Studio (Bailian) para despliegue empresarial de pago."],
            ["Bases de Datos y Cómputo", "PolarDB y AnalyticDB", "Bases de datos cloud-native escalables con aislamiento transaccional.", "Contratos de migración corporativa en banca, telecomunicaciones y retail."],
            ["Semiconductores Propios", "T-Head (Yitian 710 / Zhengyuan)", "Procesadores para centros de datos basados en arquitectura ARM optimizada para IA.", "Reducción del 30% en consumo energético e independencia de hardware."],
            ["Red Logística Inteligente", "Cainiao Smart Logistics", "Red transfronteriza que procesa más de 5 millones de paquetes diarios globales.", "Tarifas de logística transfronteriza y fulfilment express para Taobao y AliExpress."]
        ],
        "bullets": [
            "Foso de Adopción en IA: La serie Qwen supera las 600 millones de descargas globales; así, Alibaba se consolida como la arquitectura de referencia para startups y corporaciones que luego pagan cómputo en su nube."
        ]
    },
    {
        "num": 10,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 02 — CALIDAD DE INGRESOS (QOE)",
        "title": "Calidad de los ingresos: recurrencia, retención y calificación QoE (8,4/10)",
        "subtitle": "Estructura contractual resistente: alta recurrencia, diversificación de clientes y nulo riesgo de impago",
        "kpis": [("NOTA QOE GLOBAL", "8,4 / 10"), ("INGRESOS RECURRENTES", ">65% del Total"), ("RETENCIÓN 88VIP", "96% Anual"), ("TOP 10 CLIENTES", "<8% de la Facturación")],
        "table": [
            ["Criterio Forense QoE", "Métrica de Calidad Auditada", "Evaluación Institucional del Comité"],
            ["Naturaleza del Flujo", ">65% de ingresos generados por cuotas publicitarias continuas, software y contratos cloud.", "Flujo predecible con elevada visibilidad trimestre a trimestre."],
            ["Retención de Clientes (NRR)", "Net Revenue Retention de clientes de IA superior al 110% en Alibaba Cloud.", "Los clientes que adoptan la plataforma aumentan su consumo de inferencia año tras año."],
            ["Concentración de Contraparte", "Ningún cliente individual representa más del 2,0% de los ingresos consolidados.", "Cero riesgo de pérdida material de ingresos ante la insolvencia de un cliente corporativo."],
            ["Riesgo de Cobro y Facturación", "Cobro inmediato por pasarela de pago y prepago de saldo publicitario por los vendedores.", "Inexistencia de saldos de dudoso cobro; ciclo de devengo perfectamente respaldado por caja."]
        ],
        "bullets": [
            "Membresía Premium 88VIP: Con más de 42 millones de suscriptores que gastan 4 veces más que el usuario medio y renuevan al 96%, Alibaba retiene cautiva a la élite del consumo en China."
        ]
    },
    {
        "num": 11,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULOS 02 & 04 — FOSO COMPETITIVO (MOAT)",
        "title": "El foso competitivo (Moat) y el poder de fijación de precios (Pricing Power)",
        "subtitle": "Evaluación Mauboussin/Dorsey: foso ancho (8,1/10) respaldado por efectos de red bilaterales",
        "table": [
            ["Fuente del Moat (Dorsey)", "Intensidad", "Mecanismo Defensivo y Evidencia Cuantitativa"],
            ["Efectos de Red Bilaterales", "Muy Alta", "1.000 millones de consumidores atraen a 10 millones de comercios; los comercios generan la mayor variedad de catálogo."],
            ["Costes de Cambio (Switching Costs)", "Alta", "En Cloud, migrar bases de datos PolarDB y entornos integrados de IA conlleva costes y riesgos inasumibles para bancos."],
            ["Ventajas de Coste y Escala", "Muy Alta", "Coste unitario de enrutamiento logístico y computación hiperescala inalcanzable para competidores de menor volumen."],
            ["Activos Intangibles y Marcas", "Alta", "Tmall es el canal indispensable de validación para cualquier marca global en China (Apple, Nike, LVMH)."],
            ["Poder de Precios (Pricing Power)", "Comprobada", "La implantación de la tarifa básica de software del 0,6% en 2024 se absorbió sin ninguna fuga de comerciantes hacia Douyin o PDD."]
        ],
        "bullets": [
            "Vector Dinámico [+]: Tras la reorganización societaria y el dominio en código abierto de Qwen IA, el foso competitivo se encuentra en fase de ensanchamiento frente a operadores monofuncionales.",
            "Resistencia al Descuento: Aunque competidores como Pinduoduo compiten en precio bajo, la cuota de mercado en marcas consolidadas y clientes premium permanece blindada en Tmall."
        ]
    },
    {
        "num": 12,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULO 03 — MERCADO Y FUERZAS DE PORTER",
        "title": "Tamaño del mercado (TAM/SAM/SOM), vientos de cola y 5 Fuerzas de Porter",
        "subtitle": "Direccionabilidad expansiva: mercado retail de RMB 15,4T y superciclo de inversión en IA",
        "table": [
            ["Fuerza Competitiva de Porter", "Intensidad", "Diagnóstico Analítico y Salvaguardas de Alibaba"],
            ["Rivalidad entre Competidores", "Elevada", "Competencia feroz con Douyin en livestreaming y PDD en bajo coste; mitigada por foco en experiencia de usuario y comercio rápido."],
            ["Amenaza de Nuevos Entrantes", "Muy Baja", "Barreras de entrada insalvables: requiere billones en infraestructura logística, centros de datos y masa crítica de usuarios."],
            ["Poder de Negociación Clientes", "Moderada", "Los consumidores son sensibles al precio, pero la membresía 88VIP genera lealtad e inelasticidad en compras frecuentes."],
            ["Poder de Proveedores", "Baja", "Millones de pymes manufactureras en China dependen vitalmente del canal Taobao/1688 para dar salida a su producción."],
            ["Amenaza de Sustitutivos", "Baja", "No existe sustituto viable a la integración coordinada de marketplace, logística física, medios de pago y computación cloud."]
        ],
        "bullets": [
            "TAM Minorista y Cloud: El comercio digital en China superará los RMB 18,5 billones en 2028 (CAGR +7,2%), mientras que el mercado de computación cloud e IA en Asia crecerá a un CAGR del +24,5%."
        ]
    },
    {
        "num": 13,
        "section": "ACTO II: CÓMO LO HACE  |  MÓDULOS 03 & 04 — BENCHMARKING PEERS Y ESG",
        "title": "Mapa competitivo frente a sus rivales cotizados y cultura de innovación/ESG",
        "subtitle": "Fuerte infravaloración relativa frente a comparables cotizados con esfuerzo líder en I+D",
        "chart": "chart3_peer_benchmarking_multiples.png",
        "bullets": [
            "Descuento Extremo de Valoración: Alibaba cotiza a 10,86x PER Forward y 7,40x EV/EBITDA, lo que representa un descuento del -34% frente a Tencent (16,4x), -65% frente a Amazon (31,2x) y -38% frente a Meituan (17,5x).",
            "Esfuerzo en I+D y Patentes: Inversión anual de más de RMB 52.000M en I+D (>5% de ingresos). La firma se sitúa como primer titular de patentes en computación distribuida y modelos LLM en Asia.",
            "Gobernanza y Separación de Poderes: Separación efectiva de las figuras de Presidente del Consejo (Joe Tsai) y Consejero Delegado (Eddie Wu), con independencia en los comités de auditoría y retribución.",
            "Desempeño ESG Ambiental: Centros de datos de hiperescala con refrigeración líquida por inmersión (PUE medio de 1,20) y uso de más del 55% de energía renovable en operaciones cloud."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO III — Los números y la calidad financiera: balance, resultados, caja y eficiencia (Diapositivas 14 a 21)
    # --------------------------------------------------------------------------
    {
        "num": 14,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 05 — BALANCE MULTIANUAL",
        "title": "Radiografía del balance multianual: activos, pasivos y fondos propios",
        "subtitle": "Estructura patrimonial acorazada de RMB 1,82 Billones: alta liquidez y endeudamiento conservador",
        "table": [
            ["Partida del Balance Consolidado", "FY24A (RMB M)", "FY25A (RMB M)", "FY26A (RMB M)", "Peso % en Activo"],
            ["Efectivo, Equivalentes e Inversiones CP", "248.125", "286.840", "286.840", "15,8%"],
            ["Depósitos a Plazo No Restringidos (1-3 Años)", "210.450", "234.058", "234.058", "12,9%"],
            ["Inmovilizado Material e Inversiones Tech", "174.520", "225.100", "285.400", "15,7%"],
            ["Inversiones en Asociadas (Ant Group 33%)", "246.500", "258.900", "260.800", "14,3%"],
            ["Otros Activos e Intangibles / Goodwill", "892.405", "805.102", "752.960", "41,3%"],
            ["TOTAL ACTIVO AUDITADO", "1.772.000", "1.810.000", "1.820.058", "100,0%"],
            ["Deuda Financiera Bancaria y Bonos", "185.400", "240.500", "260.070", "14,3%"],
            ["FONDOS PROPIOS (PATRIMONIO NETO)", "1.025.000", "1.060.000", "1.085.000", "59,6%"]
        ],
        "bullets": [
            "Solvencia Patrimonial Sobresaliente: Los fondos propios cubren casi el 60% del activo total consolidado; por tanto, Alibaba se financia esencialmente con capital propio y beneficios acumulados.",
            "Limpieza de Activos: El fondo de comercio e intangibles se ha reducido progresivamente mediante amortizaciones prudentes, eliminando el riesgo de deterioros masivos sorpresivos."
        ]
    },
    {
        "num": 15,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 05 — LIQUIDEZ Y CAJA NETA",
        "title": "Liquidez real no restringida frente a deuda financiera y caja neta",
        "subtitle": "Tesorería libre de US$ 75,5B (RMB 520,8B) y posición neta de caja de +RMB 260.828M (+US$ 37,8B)",
        "chart": "chart4_balance_sheet_liquidity.png",
        "bullets": [
            "Liquidez Total No Restringida: La suma de efectivo corriente (RMB 127.050M), inversiones a corto plazo (RMB 159.790M) y depósitos bancarios a plazo fijo (RMB 234.058M) totaliza RMB 520.824M libres.",
            "Deuda Bruta Manejable: La deuda financiera total (RMB 260.070M) está compuesta por bonos sénior a tipos fijos favorables y vencimientos escalonados hasta más allá de 2034.",
            "Caja Neta Positiva: Alibaba mantiene una Caja Neta de +RMB 260.828M (HK$ 13,01 por acción ordinaria). Esta cifra supone un colchón patrimonial equivalente al 13,3% de su capitalización bursátil.",
            "Cartera de Inversiones Estratégicas: Su 33% en Ant Group y participaciones en filiales cotizadas aportan un valor contable adicional de RMB 439.100M no computado en la caja neta."
        ]
    },
    {
        "num": 16,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 05 — AUDITORÍA FORENSE Y RATIOS",
        "title": "Auditoría forense: Sloan, Beneish, Altman Z'' y nota de Salud Forense (8,2/10)",
        "subtitle": "Inexistencia de manipulación contable y elevada solvencia patrimonial certificada",
        "kpis": [("BENEISH M-SCORE", "-2,46 (No Manipulador)"), ("SLOAN ACCRUAL", "-0,81% (Conservador)"), ("ALTMAN Z''", "6,55 (Zona Segura)"), ("SALUD FORENSE", "8,2 / 10")],
        "table": [
            ["Prueba Forense / Modelo de Estrés", "Valor Obtenido", "Umbral de Seguridad", "Diagnóstico Analítico del Comité"],
            ["Beneish M-Score", "-2,46", "< -1,78", "Excelente: probabilidad estadística de manipulación de beneficios virtualmente nula."],
            ["Ratio de Devengo de Sloan (Accrual)", "-0,81%", "Entre -5% y +5%", "Beneficio de alta calidad respaldado por entradas efectivas de tesorería."],
            ["Altman Z''-Score (Emergentes)", "6,55", "> 2,60 (Zona Segura)", "Quiebra o insolvencia descartada; holgura patrimonial de primer orden."],
            ["Stress Test de Liquidez (24 Meses)", "Cobertura 4,2x", "> 1,5x servicio deuda", "Capaz de absorber 2 años de FCF negativo sin refinanciar deuda ni frenar CapEx."],
            ["Compensación en Acciones (SBC)", "1,53% ingresos", "< 4,0% tecnológico", "Dilución mínima comparada con tecnológicas estadounidenses (5%–10% en Meta/Alphabet)."]
        ],
        "bullets": [
            "Dictamen Forense: La calidad de las notas a los estados financieros y la transparencia en la conciliación de pasivos contingentes confirman una gobernanza contable de máxima fiabilidad."
        ]
    },
    {
        "num": 17,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 06 — CUENTA DE RESULTADOS GAAP/NON-GAAP",
        "title": "Cuenta de resultados histórica (5 años) y puente contable GAAP vs. Non-GAAP",
        "subtitle": "Conciliación transparente de ajustes operativos, gastos de amortización y participación en asociadas",
        "table": [
            ["Línea de P&L Consolidada", "FY22A (RMB M)", "FY23A (RMB M)", "FY24A (RMB M)", "FY25A (RMB M)", "FY26A (RMB M)"],
            ["Ingresos Consolidados", "853.088", "868.687", "941.168", "996.340", "1.023.670"],
            ["Margen Bruto (%)", "36,8%", "36,7%", "37,7%", "40,0%", "39,8%"],
            ["Gastos de Venta y Marketing (S&M)", "119.799", "103.496", "115.200", "144.150", "245.152"],
            ["Beneficio de Explotación (EBIT GAAP)", "69.638", "100.351", "113.350", "125.400", "48.200"],
            ["Adjusted EBITA (Non-GAAP)", "130.397", "147.911", "165.028", "173.120", "76.380"],
            ["Beneficio Neto Atribuible GAAP", "61.959", "72.509", "79.741", "85.200", "102.127"],
            ["Beneficio Neto Non-GAAP", "136.388", "141.365", "157.490", "162.100", "60.658"]
        ],
        "bullets": [
            "Impacto Puntual de S&M en FY26: El gasto comercial subió en RMB 101.002M por la batalla competitiva de comercio instantáneo frente a Meituan; la pérdida unitaria por pedido ya cayó un 50% en la segunda mitad del año.",
            "Impulso Extraordinario en GAAP: El beneficio neto GAAP de FY26 creció impulsado por la recuperación del 96% en la aportación de beneficios de Ant Group y plusvalías de cartera."
        ]
    },
    {
        "num": 18,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 06 — FLUJOS DE CAJA Y OWNER EARNINGS",
        "title": "Generación de flujo de caja operativo (OCF), CapEx y flujo de caja libre real",
        "subtitle": "Puente de caja: el déficit de FY26 respondió al pico inversor en centros de datos e IA",
        "table": [
            ["Magnitud de Flujo de Caja", "FY22A (RMB M)", "FY23A (RMB M)", "FY24A (RMB M)", "FY25A (RMB M)", "FY26A (RMB M)"],
            ["Flujo de Caja Operativo (OCF)", "142.759", "199.752", "182.593", "163.500", "76.240"],
            ["Inversión en CapEx Productivo", "-42.000", "-30.400", "-28.400", "-86.000", "-122.933"],
            ["Flujo de Caja Libre Reportado (FCF)", "98.872", "171.700", "156.200", "73.900", "-46.609"],
            ["Compensación en Acciones (SBC)", "-28.450", "-30.120", "-23.400", "-18.200", "-15.650"],
            ["Owner Earnings (FCF ex-SBC Ajustado)", "70.422", "141.580", "132.800", "55.700", "-62.259"]
        ],
        "bullets": [
            "Pico Histórico de CapEx en IA: En FY26, Alibaba ejecutó un récord de CapEx de RMB 122.933M (más del doble que en FY24) adquiriendo clusters de cómputo GPU y ampliando centros de datos de refrigeración líquida.",
            "Capacidad de Cosecha Inmediata: Este esfuerzo inversor ya comenzó a desacelerar. El FCF retornará a terreno fuertemente positivo (+RMB 55.000M) a partir del ejercicio FY27E."
        ]
    },
    {
        "num": 19,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 06 — MÁRGENES, DUPONT Y ROIC VS. WACC",
        "title": "Evolución de márgenes, apalancamiento operativo y creación de valor (ROIC)",
        "subtitle": "Márgenes brutos estables (~40%), análisis DuPont de 5 factores y spread ROIC sobre WACC (9,6%)",
        "chart": "chart5_margins_roic_vs_wacc.png",
        "bullets": [
            "Margen Bruto Resiliente: Consistente entre el 36,8% y el 40,0% durante 5 años; esto evidencia el poder de monopolio natural de Taobao como infraestructura sin coste de mercancía vendida.",
            "Apalancamiento Operativo en Reversa y Rebote: El descenso de Adjusted EBITA a 7,46% en FY26 fue causado por el gasto fijo comercial, que empezará a diluirse conforme crezca el GMV de comercio rápido.",
            "Creación de Valor Histórica: El ROIC operativo promedió el 13,2% entre FY22 y FY25, superando ampliamente el coste medio de capital (WACC del 9,6%), lo que prueba la generación genuina de valor económico.",
            "Descomposición DuPont: La rentabilidad sobre fondos propios (ROE) ha estado sustentada en una elevada rotación de activos y margen neto saludable, sin dependencia artificial del apalancamiento financiero."
        ]
    },
    {
        "num": 20,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 07 — CIRCULANTE Y FINANCIACIÓN GRATUITA",
        "title": "KPIs operativos y ciclo de conversión de caja negativo (-71,3 días)",
        "subtitle": "Cómo el capital circulante estructuralmente negativo financia el crecimiento del negocio gratis",
        "chart": "chart6_working_capital_ccc.png",
        "bullets": [
            "Flotador de Financiación de Proveedores: Con un DPO de 92,1 días frente a un DSO de 15,6 días y un DIO de solo 5,2 días, Alibaba cobra de inmediato a consumidores y paga a proveedores 3 meses más tarde.",
            "Ciclo de Conversión de Caja (-71,3 Días): Este desfase temporal estructural inyecta decenas de miles de millones de RMB en tesorería operativa gratuita que financia el crecimiento sin acudir a deuda.",
            "Rotación de Inventarios Impecable: Un DIO de 5,2 días certifica que Alibaba prácticamente no retiene existencias, limitándose el inventario a la división de supermercados Freshippo.",
            "Escalabilidad Infinita: Cuanto más crece el volumen transaccional de Taobao y Tmall, mayor es el volumen de caja flotante que se acumula en el balance, lo que genera ingresos financieros adicionales."
        ]
    },
    {
        "num": 21,
        "section": "ACTO III: LOS NÚMEROS  |  MÓDULO 07 — BENCHMARKING DE EFICIENCIA OPERATIVA",
        "title": "Benchmarking de eficiencia operativa frente a sus competidores directos",
        "subtitle": "Mayor productividad por empleado y superior conversión de caja frente a minoristas tradicionales",
        "table": [
            ["Métrica de Eficiencia", "Alibaba (9988.HK)", "Tencent (0700.HK)", "PDD Holdings (PDD)", "JD.com (9618.HK)", "Amazon (AMZN)"],
            ["Ingresos por Empleado (USD k)", "$1.150", "$1.280", "$2.850", "$220", "$410"],
            ["Margen Bruto Consolidado", "39,8%", "52,6%", "61,2%", "15,8%", "48,2%"],
            ["Gastos S&M sobre Ingresos", "23,9% (Pico)", "8,2%", "34,5%", "3,9%", "8,5%"],
            ["Ciclo Conversión Caja (CCC)", "-71,3 días", "-35,0 días", "-58,0 días", "-48,5 días", "-28,0 días"],
            ["Margen FCF Normalizado", "16,0% (Hist.)", "32,5%", "28,0%", "3,5%", "8,0%"]
        ],
        "bullets": [
            "Superioridad Estructural sobre JD.com: Al operar con un modelo marketplace en lugar de venta directa 1P, Alibaba multiplica por 5 los ingresos por empleado y genera un margen FCF 4 veces mayor.",
            "Ventaja de Circulante: El ciclo de conversión de caja negativo de -71,3 días es el más favorable de todo el universo de plataformas tecnológicas comparadas y refuerza la liquidez."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO IV — Quién dirige la empresa y cómo asigna el capital (Diapositivas 22 a 24)
    # --------------------------------------------------------------------------
    {
        "num": 22,
        "section": "ACTO IV: QUIÉN DIRIGE  |  MÓDULO 08 — EQUIPO DIRECTIVO Y GOBERNANZA",
        "title": "Equipo directivo, gobernanza, incentivos y cumplimiento del guidance",
        "subtitle": "Liderazgo de Joe Tsai y Eddie Wu: incentivos vinculados a la creación de valor y al ROIC",
        "table": [
            ["Líder Directivo / Función", "Trayectoria y Experiencia", "Métricas Clave de Remuneración Variable"],
            ["Joe Tsai (Presidente Consejo)", "Cofundador histórico de Alibaba; orquestó la salida a bolsa en NYSE y la relación con inversores occidentales.", "Alineación accionarial mediante tenencia masiva de títulos; foco en asignación de capital y gobernanza."],
            ["Eddie Wu (Consejero Delegado)", "Cofundador y primer arquitecto tecnológico; lideró el desarrollo de Taobao, Alipay y Alibaba Cloud.", "Bonus e incentivos LTIP vinculados al crecimiento de EBITA en Cloud y retorno sobre capital invertido (ROIC)."],
            ["Toby Xu (Director Financiero)", "Ex-socio de PwC con más de 20 años de experiencia; ejecutó la recompra de minoritarios de Cainiao y ventas de retail.", "Métricas de devengo basadas en margen FCF, disciplina de endeudamiento y retorno efectivo al accionista."],
            ["Track Record de Guidance", "Cumplimiento histórico del 86% de previsiones de ingresos y 82% en beneficio operativo ajustado.", "Riguroso conservadurismo en comunicación pública Sell-Side tras la reestructuración de 2024."]
        ],
        "bullets": [
            "Alineación con el Inversor Minoritario: Los programas de remuneración a largo plazo exigen que al menos el 60% de la retribución variable se abone en acciones con periodo de consolidación de 4 años."
        ]
    },
    {
        "num": 23,
        "section": "ACTO IV: QUIÉN DIRIGE  |  MÓDULO 08 — ASIGNACIÓN HISTÓRICA DEL CAPITAL",
        "title": "Asignación histórica del capital (5 años): >US$ 58.000M al accionista y ROIIC",
        "subtitle": "Recompras agresivas (-12,5% acciones), dividendo creciente y CapEx en IA financiado internamente",
        "table": [
            ["Destino del Capital (FY22–FY26)", "Monto Total Asignado", "% del Despliegue", "Lectura Estratégica del Comité"],
            ["Recompras Propias de Acciones", "US$ 44.500M (RMB 310B)", "48,5%", "Retirada de más de 2.100M de títulos, reduciendo el flotante un -12,5% desde 2021."],
            ["Dividendos en Efectivo Pagados", "US$ 13.800M (RMB 96B)", "15,0%", "Instauración de dividendo ordinario anual + dividendo especial por desinversiones."],
            ["CapEx Productivo en Cloud e IA", "US$ 45.000M (RMB 309B)", "33,0%", "Infraestructura propia que garantiza liderazgo tecnológico soberano en China."],
            ["M&A Estratégico y Recompras Minoritarios", "US$ 4.200M (RMB 29B)", "3,5%", "Recompra del 36% de Cainiao y compras de cuota en Turquía (Trendyol)."],
            ["TOTAL CAPITAL ASIGNADO", ">US$ 107.500M", "100,0%", "ROIIC Incremental promediado de 14,8% en divisiones principales continuadas."]
        ],
        "bullets": [
            "Autorización Remanente: Alibaba cuenta con más de US$ 16.300M autorizados para recompras adicionales hasta marzo de 2027. Esto aporta un soporte comprador permanente de ~4,0% anual."
        ]
    },
    {
        "num": 24,
        "section": "ACTO IV: QUIÉN DIRIGE  |  MÓDULO 09 — ACCIONISTAS, INSIDERS Y CORTOS",
        "title": "Estructura accionarial, movimientos de insiders y posiciones cortas",
        "subtitle": "Salida completada de SoftBank, auge comprador de Stock Connect (~10%) y compras insider",
        "table": [
            ["Tipo de Inversor / Entidad", "% del Capital", "Tendencia 2025–2026", "Evaluación de Riesgo de Flujo"],
            ["Southbound Stock Connect (China)", "~10,2% del capital", "Compras agresivas continuadas (>US$ 22.000M netos)", "Comprador estructural inmune a sanciones occidentales."],
            ["Gestoras Institucionales Globales", "~42,5% del capital", "Estabilidad en Vanguard, BlackRock, Fidelity y Baillie Gifford", "Flujo estabilizado tras la capitulación de fondos pasivos."],
            ["Insiders y Equipo Fundador", "~8,8% del capital", "Compras netas de Joe Tsai y Eddie Wu en mercado abierto", "Máxima señal de confianza directiva al precio actual."],
            ["Inversores Minoristas y Flotante", "~38,5% del capital", "Distribución equilibrada entre HKEX y NYSE", "Liquidez extrema de contratación diaria sin trabas."],
            ["Posiciones Cortas (Short Interest)", "<1,8% del flotante", "En mínimos de 3 años tras reestructuración", "Nulo riesgo de presión bajista organizada por fondos especulativos."]
        ],
        "bullets": [
            "Fin del Overhang de SoftBank: La liquidación total de la participación histórica de SoftBank mediante derivados prepagados eliminó la mayor fuente de presión vendedora que aplastaba el valor.",
            "Compras de Insiders: Los directivos clave adquirieron más de US$ 200 millones en acciones a precios cercanos a HK$ 100; de este modo, alinean plenamente su patrimonio con los accionistas."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO V — El futuro del negocio y cuánto vale la acción (Diapositivas 25 a 30)
    # --------------------------------------------------------------------------
    {
        "num": 25,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 11A — MOTORES Y CONSENSO",
        "title": "Motores de crecimiento a largo plazo y origen de las proyecciones",
        "subtitle": "Contraste riguroso entre Guidance de la directiva, Consenso Sell-Side y modelo del Comité",
        "table": [
            ["Motor de Crecimiento / Driver", "Guidance de la Directiva", "Consenso de Analistas (Sell-Side)", "Hipótesis del Comité de Inversiones"],
            ["China E-Commerce (CMR)", "Crecimiento alineado con GMV (+5% a +8%)", "+6,0% anual con estabilización de cuota", "+7,0% anual impulsado por Quanzhantui y tarifa 0,6%."],
            ["Comercio Rápido (Instant Commerce)", "Pérdidas operativas reduciéndose en 2H FY27", "Breakeven operativo en FY28", "Reducción paulatina de subsidios; breakeven en FY28."],
            ["Alibaba Cloud + IA Qwen", "Crecimiento de triple dígito en IA; margen al alza", "+22% a +25% anual en facturación total", "+23,6% CAGR con expansión de margen EBITA al 14,5%."],
            ["E-Commerce Internacional (AIDC)", "Rentabilidad operativa gradual en Choice y Trendyol", "Pérdidas reduciéndose a cero hacia FY28", "Generación de beneficio positivo a partir de FY28."],
            ["Inversión en CapEx Total", "Normalización progresiva tras pico de FY26", "RMB 120B en FY27E y RMB 110B en FY28E", "RMB 130B en FY27E y descenso gradual a RMB 105B en FY31E."]
        ],
        "bullets": [
            "Independencia Analítica: El Comité adopta un enfoque más conservador que el consenso en comercio rápido, pero reconoce un mayor apalancamiento operativo en Cloud e IA por adopción de Qwen.",
            "Origen de las Premisas: Nuestras proyecciones se derivan de la cartera de pedidos de Cloud (Módulo 07), el crecimiento del mercado direccionable (Módulo 03) y la estructura de costes fijos (Módulo 06)."
        ]
    },
    {
        "num": 26,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 11A — MODELO PROYECCIONES 5 AÑOS",
        "title": "Modelo de proyecciones operativas a 5 años (ingresos, EBITA y FCF)",
        "subtitle": "Horizontes Bear, Base y Bull: inflexión de FCF hacia +RMB 55B (FY27E) y cosecha de caja sostenida",
        "chart": "chart8_future_projections_5y.png",
        "bullets": [
            "Ingresos Proyectados Escenario Base: Expansión desde RMB 1.023,7B en FY26 hasta RMB 1.665,0B en FY31E (CAGR de +10,2%), impulsado por la aceleración de Cloud e Internacional.",
            "Recuperación del Adjusted EBITA: Rebote inmediato desde RMB 76,4B en FY26 hasta RMB 148,5B en FY27E y RMB 340,0B en FY31E al diluirse el gasto promocional extraordinario.",
            "Cosecha de Flujo de Caja Libre (FCF): Tras el déficit inversor de FY26 (-RMB 46,6B), el FCF escala a +RMB 55,0B en FY27E, +RMB 121,0B en FY28E y RMB 269,0B en FY31E.",
            "Escenario Bajista (Bear Case): Incluso bajo guerra comercial prolongada y nulo crecimiento en CMR, el FCF normalizado se mantiene por encima de RMB 40.000M anuales a partir de FY28E."
        ]
    },
    {
        "num": 27,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 10 — DCF Y REVERSE DCF",
        "title": "Valoración por descuento de flujos (DCF: HK$ 149,80) y Reverse DCF",
        "subtitle": "WACC del 9,6%, crecimiento terminal g del 2,5% y expectativas implícitas en precio excesivamente pesimistas",
        "table": [
            ["Sensibilidad DCF (HK$/Acción)", "WACC = 8,6%", "WACC = 9,1%", "WACC = 9,6% (Base)", "WACC = 10,1%", "WACC = 10,6%"],
            ["Tasa Terminal g = 1,5%", "HK$ 152,40", "HK$ 143,10", "HK$ 135,20", "HK$ 127,90", "HK$ 121,40"],
            ["Tasa Terminal g = 2,0%", "HK$ 160,80", "HK$ 150,50", "HK$ 141,80", "HK$ 133,90", "HK$ 126,80"],
            ["Tasa Terminal g = 2,5% (Base)", "HK$ 171,20", "HK$ 159,60", "HK$ 149,80", "HK$ 141,10", "HK$ 133,20"],
            ["Tasa Terminal g = 3,0%", "HK$ 184,50", "HK$ 170,90", "HK$ 159,70", "HK$ 149,80", "HK$ 140,90"],
            ["Tasa Terminal g = 3,5%", "HK$ 202,10", "HK$ 185,40", "HK$ 172,30", "HK$ 160,60", "HK$ 150,40"]
        ],
        "bullets": [
            "Valor Intrínseco Base (HK$ 149,80): El modelo DCF arroja un potencial alcista del +53,2% asumiendo premisas macroeconómicas conservadoras y un coste de capital que penaliza el riesgo país.",
            "Lectura del Reverse DCF: Al precio spot de HK$ 97,80, el mercado descuenta una caída perpetua del FCF del -3,5% anual o un colapso irreversible de márgenes, escenario refutado por la evidencia operativa."
        ]
    },
    {
        "num": 28,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 10 — SUMA DE LAS PARTES (SOTP)",
        "title": "Valoración Suma de las Partes (SOTP: HK$ 147,20): Cloud e IA a coste cero",
        "subtitle": "Taobao/Tmall + Caja Neta + Ant Group suman HK$ 97,02 (99,2% del precio spot de HK$ 97,80)",
        "table": [
            ["Unidad de Negocio / Activo", "Métrica Financiera Base", "Múltiplo Asignado", "Valor Implícito (HK$)", "Aportación por Acción", "% del SOTP"],
            ["Taobao & Tmall (China E-Commerce)", "RMB 155.000M EBITA Norm.", "8,5x EV/EBITA", "HK$ 1.398.900M", "HK$ 70,30", "47,8%"],
            ["Alibaba Cloud + Ecosistema Qwen", "RMB 197.200M Ventas FY27E", "3,5x EV/Sales", "HK$ 810.900M", "HK$ 40,75", "27,7%"],
            ["Caja Neta Libre No Restringida", "RMB 260.828M Tesorería", "1,0x Valor Facial", "HK$ 258.900M", "HK$ 13,01", "8,8%"],
            ["Participación 33% en Ant Group", "Valoración conservadora US$ 50B", "1,0x Valor Libros", "HK$ 272.800M", "HK$ 13,71", "9,3%"],
            ["AliExpress, Trendyol y Lazada (AIDC)", "RMB 175.000M Ventas FY27E", "1,0x EV/Sales", "HK$ 203.700M", "HK$ 10,24", "7,0%"],
            ["Otros Activos (Amap, Cainiao, Health)", "Valor contable neto", "0,8x Valor Libros", "HK$ 309.400M", "HK$ 15,55", "10,6%"],
            ["Descuento de Conglomerado (-10%)", "Ajuste por estructura holding", "-10,0% sobre bruto", "-HK$ 325.400M", "-HK$ 16,36", "-11,1%"],
            ["VALOR TOTAL SOTP CONSERVADOR", "Capital Total Consolidado", "Ponderado", "HK$ 2.929.200M", "HK$ 147,20", "100,0%"]
        ],
        "bullets": [
            "Regalo Tecnológico Absoluto: El inversor que compra a HK$ 97,80 adquiere el 35,8% del mercado chino de inteligencia artificial en la nube y todo el comercio internacional a coste cero."
        ]
    },
    {
        "num": 29,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 10 — MÚLTIPLOS COMPARABLES",
        "title": "Valoración por múltiplos comparables frente a su historia y rivales globales",
        "subtitle": "La acción cotiza con un descuento histórico del -45% en PER y -58% en Price-to-Book",
        "table": [
            ["Múltiplo Bursátil / Ratio", "Nivel Actual (FY26)", "Media Histórica 5 Años", "Mediana Sector Global", "Descuento vs. Mediana"],
            ["P/E Forward 12 Meses", "10,86x", "16,80x", "22,50x", "-51,7% de descuento"],
            ["EV / EBITDA Normalizado", "7,40x", "11,20x", "14,80x", "-50,0% de descuento"],
            ["EV / Ventas Consolidadas", "1,42x", "2,45x", "3,80x", "-62,6% de descuento"],
            ["Price-to-Book (P/B)", "1,48x", "2,35x", "3,50x", "-57,7% de descuento"],
            ["FCF Yield Normalizado (FY27E)", "9,85%", "6,20%", "4,50%", "+535 bps de exceso de caja"],
            ["EV / FCF Normalizado", "10,15x", "16,10x", "22,20x", "-54,3% de descuento"]
        ],
        "bullets": [
            "Múltiplo de Liquidación Extrema: Un PER Forward de 10,86x es típico de empresas industriales en declive secular, no de un hiperescalador con crecimiento de dos dígitos en comercio digital e IA.",
            "Re-Rating Inevitable: Con una simple convergencia a 14,0x PER Forward (aún por debajo de su media histórica de 16,8x), la cotización alcanzaría los HK$ 138,50 por acción."
        ]
    },
    {
        "num": 30,
        "section": "ACTO V: EL FUTURO Y VALOR  |  MÓDULO 10 — CAMPO DE FÚTBOL & TRIANGULACIÓN",
        "title": "Triangulación del precio objetivo y escenarios probabilísticos (Campo de Fútbol)",
        "subtitle": "Síntesis de metodologías: Precio Objetivo Base de HK$ 146,90 y ratio asimétrico de 4,16x",
        "chart": "chart7_valuation_sotp_football_field.png",
        "bullets": [
            "Síntesis Metodológica Ponderada: Asignando un 50% al DCF (HK$ 149,80), 35% al SOTP (HK$ 147,20) y 15% a Múltiplos (HK$ 136,50), fijamos el Precio Objetivo Base en HK$ 146,90 (+50,2%).",
            "Escenario Bajista Acotado (Bear Case: HK$ 86,00 | Probabilidad 25%): Caída máxima estimada del -12,1% gracias al colchón patrimonial de Taobao y la Caja Neta.",
            "Escenario Alcista Agresivo (Bull Case: HK$ 188,00 | Probabilidad 25%): Potencial del +92,2% impulsado por la monetización de Qwen IA y re-rating a múltiplos internacionales.",
            "Valor Esperado Probabilístico: E[V] ponderado de HK$ 141,95 (+45,1% de retorno esperado medio). El ratio rentabilidad/riesgo alcanza 4,16 euros de ganancia por cada euro arriesgado."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO VI — Qué puede salir mal, qué moverá la acción y el momento de entrada (Diapositivas 31 a 36)
    # --------------------------------------------------------------------------
    {
        "num": 31,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULO 11B — RIESGOS OPERATIVOS",
        "title": "Riesgos operativos, competitivos y tecnológicos cuantificados y sus mitigantes",
        "subtitle": "Evaluación matricial: presiones en márgenes, competencia en comercio rápido y barreras defensivas",
        "table": [
            ["Riesgo Operativo / Tecnológico", "Prob. (1-5)", "Impacto en EBITA", "Mecanismos Directos de Mitigación"],
            ["Guerra de Subsidios en Quick Commerce", "4 / 5", "Hasta -RMB 25.000M", "Racionalización iniciada: pérdida por pedido reducida en 50%; foco en ticket medio alto y usuarios 88VIP."],
            ["Comoditización de Modelos de Lenguaje IA", "3 / 5", "Hasta -RMB 8.000M", "Integración vertical: Alibaba gana en cómputo cloud y bases de datos PolarDB aunque el precio de tokens caiga."],
            ["Fuga de Comerciantes hacia Douyin/PDD", "2 / 5", "Hasta -RMB 12.000M", "Herramienta Quanzhantui que maximiza el ROAS del comerciante y protección de marcas exclusivas en Tmall."],
            ["Incremento en Costes de Servidores", "3 / 5", "Hasta -RMB 6.000M", "Despliegue de chips propios Yitian 710 que reducen un 30% el consumo energético por unidad de cómputo."]
        ],
        "bullets": [
            "Conclusión de Riesgos Internos: Los riesgos operativos se encuentran plenamente identificados y cuentan con salvaguardas ejecutables que acotan el impacto financiero."
        ]
    },
    {
        "num": 32,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULO 11B — RIESGOS REGULATORIOS Y MACRO",
        "title": "Riesgos macroeconómicos, regulatorios y geopolíticos: resiliencia patrimonial",
        "subtitle": "Evaluación exógena: aranceles, restricciones a chips de EE.UU. y solidez de la estructura societaria",
        "table": [
            ["Factor Exógeno / Geopolítico", "Nivel de Amenaza", "Diagnóstico Analítico y Cortafuegos Patrimoniales"],
            ["Restricciones a Chips Avanzados de EE.UU.", "Media-Alta", "Alibaba acumuló stock sustancial de GPUs H20/H800 y optimizó clusters de entrenamiento distribuido con modelos MoE."],
            ["Tensiones Comerciales y Aranceles Cross-Border", "Moderada", "AliExpress Choice opera en más de 100 países diversificados (Europa, LatAm, Oriente Medio) con baja exposición directa a EE.UU."],
            ["Debilidad del Consumo Privado Chino", "Moderada", "Alibaba capta consumo de conveniencia y productos básicos; beneficiada por subsidios públicos a la renovación de bienes."],
            ["Riesgo Societario Estructura VIE", "Baja", "Conversión a cotización dual primaria en HKEX con supervisión compartida por la SFC de Hong Kong y auditores internacionales."]
        ],
        "bullets": [
            "Blindaje de Balance: La Caja Neta de RMB 260.828M y el flujo operativo recurrente permiten a Alibaba operar de forma autónoma sin depender de financiación bancaria internacional."
        ]
    },
    {
        "num": 33,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULO 12 — CATALIZADORES POSITIVOS",
        "title": "Catalizadores a corto, medio y largo plazo que destaparán el valor",
        "subtitle": "Hitos corporativos y de mercado programados para cerrar la brecha de cotización",
        "table": [
            ["Horizonte Temporal", "Evento Catalizador Identificado", "Impacto Esperado en Valoración"],
            ["Corto Plazo (0–6 Meses)", "Resultados Q2/Q3 FY27 que validan el rebote de FCF a positivo tras superar el valle inversor.", "Re-rating inmediato de múltiplos al despejar temores de deterioro permanente de márgenes."],
            ["Corto Plazo (0–6 Meses)", "Aceleración de compras corporativas bajo el remanente de US$ 16.300M de recompras autorizadas.", "Reducción acelerada del flotante y soporte directo de cotización en torno a HK$ 95–100."],
            ["Medio Plazo (6–18 Meses)", "Aumento de participación del canal Southbound Stock Connect por encima del 15% del capital.", "Inyección constante de liquidez institucional china con visión de largo plazo sin restricciones FX."],
            ["Largo Plazo (>18 Meses)", "Monetización masiva de agentes de IA empresariales sobre la suite Model Studio (Bailian).", "Expansión del margen EBITA de Alibaba Cloud hacia el 15%–18%, duplicando el beneficio cloud."],
            ["Catalizador Oculto", "Eventual reanudación de la salida a bolsa o monetización de la participación en Ant Group.", "Destape de más de HK$ 13,70 por acción de valor latente bloqueado en el balance."]
        ],
        "bullets": [
            "Secuencia Favorable: Los catalizadores de corto plazo están respaldados por hechos contables verificables en los próximos trimestres de 2026 y 2027."
        ]
    },
    {
        "num": 34,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULOS 12 & 15 — KILL-SWITCH Y NOTICIAS RECIENTES",
        "title": "Eventos Kill-Switch (cuándo abortar la tesis) y cronología de noticias",
        "subtitle": "4 reglas innegociables de desinversión forzosa y absorción del valle de noticias 2025–2026",
        "table": [
            ["Regla Kill-Switch (Salida Forzosa)", "Condición Cuantitativa Límite", "Acción Automática del Comité"],
            ["1. Deterioro Estructural de Márgenes", "Margen Adjusted EBITA del grupo < 6,0% al cierre de FY27E.", "Liquidación inmediata de la posición."],
            ["2. Desaceleración Severa en Cloud", "Crecimiento de ingresos en Alibaba Cloud < +10,0% interanual.", "Liquidación inmediata de la posición."],
            ["3. FCF Anual Negativo en FY27E", "Flujo de caja libre anual del ejercicio FY2027 negativo (< RMB 0).", "Liquidación inmediata de la posición."],
            ["4. Quiebra de Soporte Semanal", "Cierre semanal de 9988.HK por debajo de HK$ 78,50.", "Ejecución de Stop-Loss duro automático."]
        ],
        "bullets": [
            "Cronología de Noticias: La caída bursátil desde HK$ 174,80 en enero 2026 hasta el suelo de HK$ 88,65 en junio 2026 obedeció al impacto contable del FCF de FY26 (-RMB 46,6B) y la desconsolidación de Sun Art, factores ya completamente absorbidos por el mercado."
        ]
    },
    {
        "num": 35,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULOS 14 & 15 — SEMÁFORO TRIMESTRAL Y SENTIMIENTO",
        "title": "Semáforo de monitorización trimestral y sentimiento de mercado",
        "subtitle": "Cuadro de mando semafórico y divergencia entre consenso optimista (88% Compras) y cautela Buyside",
        "table": [
            ["Variable Crítica de Control", "Nivel Verde (Tesis Fuerte)", "Nivel Amarillo (Alerta)", "Nivel Rojo (Invalidación)"],
            ["Crecimiento de CMR (E-Commerce)", "> +6,0% interanual", "+2,0% a +6,0%", "< +2,0% interanual"],
            ["Crecimiento Ingresos Cloud", "> +20,0% interanual", "+12,0% a +20,0%", "< +12,0% interanual"],
            ["Margen Adjusted EBITA Grupo", "> 11,0% en FY27E", "8,0% a 11,0%", "< 8,0% en FY27E"],
            ["Generación de FCF Trimestral", "> RMB 15.000M / trimestre", "RMB 0 a 15.000M", "FCF negativo trimestral"],
            ["Ritmo de Recompras de Acciones", "> US$ 1.000M / trimestre", "US$ 500M a 1.000M", "< US$ 500M / trimestre"],
            ["Flujo Southbound Stock Connect", "Compras netas mensuales", "Flujo neutro", "Ventas netas continuadas"]
        ],
        "bullets": [
            "Sentimiento Sell-Side vs. Buyside: 44 de 50 analistas de Wall Street mantienen recomendación de COMPRA (Precio Objetivo medio de HK$ 138,50), mientras que el capital institucional internacional permanece infra-ponderado por sesgo geopolítico, creando la oportunidad de arbitraje."
        ]
    },
    {
        "num": 36,
        "section": "ACTO VI: RIESGOS Y ENTRADA  |  MÓDULO 13 — ESTRUCTURA TÉCNICA Y TIMING",
        "title": "Análisis técnico de los últimos 12 meses: niveles de soporte y tramos",
        "subtitle": "Doble suelo estructural sobre HK$ 88,65–97,80, RSI normalizado (40,38) y definición de tramos",
        "chart": "chart9_price_technicals_tranches.png",
        "bullets": [
            "Doble Suelo Institucional: Formación de suelo robusto en el rango de HK$ 88,65 (mínimo de 52 semanas en junio 2026) y HK$ 92,85, con consolidación actual sobre HK$ 97,80.",
            "Medias Móviles de Referencia: La MM50 sesiones se sitúa en HK$ 110,43 (gatillo de confirmación para el Tramo 3) y la MM200 sesiones en HK$ 125,61 (primera resistencia mayor).",
            "Zona de Acumulación Táctica: La franja entre HK$ 88,65 y HK$ 98,50 ofrece un perfil asimétrico ideal para el despliegue del 75% de la posición prevista.",
            "Stop-Loss Cuantitativo Duro: Nivel de cierre semanal fijado en HK$ 78,50 (-19,8% desde spot), limitando la pérdida máxima al -1,04% del capital total bajo gestión."
        ]
    },
    # --------------------------------------------------------------------------
    # ACTO VII — El veredicto final: ¿es buena o mala idea de inversión y por qué? (Diapositivas 37 a 40)
    # --------------------------------------------------------------------------
    {
        "num": 37,
        "section": "ACTO VII: EL VEREDICTO FINAL  |  MÓDULO 16 — AJUSTES FORENSES Y DEBATE BULL/BEAR",
        "title": "Ajustes forenses aplicados y el gran debate del Comité: Bull vs. Bear",
        "subtitle": "Ajuste conservador de deuda y careo estructurado entre defensores y fiscales de la tesis",
        "table": [
            ["Eje Temático del Debate", "Tesis Bajista (Fiscal del Comité — Bear: HK$ 86,00)", "Tesis Alcista (Defensor — Bull: HK$ 146,90–188,00)"],
            ["1. Comercio Rápido y Margen", "El gasto de S&M subió +RMB 101B (+70%) para batallar con Meituan, hundiendo el margen EBITA.", "El pico de gasto concluyó; la pérdida por pedido cayó un 50% y el CMR crece al +10% con la tarifa del 0,6%."],
            ["2. CapEx y Retorno de IA", "El CapEx récord de RMB 123B hundió el FCF a negativo; riesgo de comoditización de APIs.", "EBITA en Cloud se multiplicó por 6 en dos años (RMB 13,6B) y las ventas IA crecen a más del 100%."],
            ["3. Fortaleza de Balance", "El FCF negativo obligó a reducir el ritmo de recompras desde US$ 11,9B a US$ 4,4B.", "La liquidez no restringida de RMB 520,8B y la caja neta de RMB 260,8B blindan la solvencia absoluta."],
            ["4. Riesgo Geopolítico", "Descuento crónico inevitable sobre China y riesgo de trampa de valor por debilidad macro.", "Taobao + Caja Neta + Ant cubren el 99,2% del precio; Stock Connect absorbe el papel extranjero."]
        ],
        "bullets": [
            "Fallo del Árbitro: Prevalece la tesis alcista debido a que las objeciones bajistas se basan en un gasto ya corregido, mientras que los fundamentales de caja y liderazgo en IA no admiten discusión."
        ]
    },
    {
        "num": 38,
        "section": "ACTO VII: EL VEREDICTO FINAL  |  MÓDULO 17 — SCORECARD 6 PILARES & TSR",
        "title": "Scorecard de los 6 pilares (8,06/10) y anatomía de la rentabilidad (TSR/TIR)",
        "subtitle": "Puntuación global sobresaliente y descomposición analítica de la TIR anualizada esperada (+14,8%)",
        "chart": "chart10_sotp_waterfall_breakdown.png",
        "bullets": [
            "Scorecard Institucional Ponderado (8,06 / 10): Fortaleza de Balance (8,8/10), Asimetría de Valoración (8,9/10), Calidad de Negocio (8,5/10), Asignación de Capital (8,3/10), Foso Moat (8,1/10) y Desempeño Operativo (6,8/10).",
            "Anatomía de la Rentabilidad Anualizada (+14,8% TIR a 5 Años):",
            "▪  Rendimiento por Dividendo en Efectivo: +1,2% anual distribuido en dividendos ordinarios.",
            "▪  Rendimiento por Recompras de Acciones: +3,8% anual por amortización neta de títulos.",
            "▪  Crecimiento Orgánico del Beneficio por Acción (EPS): +7,5% anual por apalancamiento operativo.",
            "▪  Expansión Moderada de Múltiplos (PER 10,8x a 13,5x): +2,3% anual de re-rating hacia valor razonable."
        ]
    },
    {
        "num": 39,
        "section": "ACTO VII: EL VEREDICTO FINAL  |  MÓDULO 17 — PLAN TÁCTICO EJECUTABLE",
        "title": "Plan táctico ejecutable: peso 5,25% del NAV, compra en 3 tramos y Stop-Loss",
        "subtitle": "Orden contractual vinculante del Comité de Inversiones con dimensionamiento estricto de riesgo",
        "kpis": [("VEREDICTO", "COMPRA FUERTE"), ("PESO NAV", "5,25% (Rango 4,5%–6,0%)"), ("TRAMO 1 (40%)", "HK$ 95,50 – 98,50"), ("STOP-LOSS", "Cierre Sem. < HK$ 78,50")],
        "table": [
            ["Parámetro de Ejecución Contractual", "Directriz Operativa de la Mesa de Contratación"],
            ["1. Dictamen y Convicción Global", "COMPRA FUERTE (BUY) — Calificación de Convicción Fundamental: 7,8 / 10."],
            ["2. Ponderación Objetivo en Cartera", "5,25% del Valor Liquidativo (NAV) total, con banda de tolerancia operativa entre 4,50% y 6,00%."],
            ["3. Tramo 1 — Posición Ancla Inmediata", "40% de la posición (2,10% del NAV) ejecutada a precio de mercado entre HK$ 95,50 y HK$ 98,50."],
            ["4. Tramo 2 — Acumulación en Soporte", "35% de la posición (1,85% del NAV) mediante órdenes limitadas escalonadas entre HK$ 88,65 y HK$ 93,50."],
            ["5. Tramo 3 — Confirmación de Tendencia", "25% de la posición (1,30% del NAV) condicionado a cierre diario consolidado por encima de HK$ 110,50 (MM50)."],
            ["6. Calibración Criterio de Kelly", "Half-Kelly institucional calculado en 5,38% del capital, validando plenamente el peso del 5,25% fijado."],
            ["7. Stop-Loss Institucional Duro", "Cierre semanal por debajo de HK$ 78,50 (-19,8% desde spot); pérdida máxima acotada al -1,04% del NAV."],
            ["8. Objetivos de Toma de Beneficios", "Venta del 20% en HK$ 126,00 (MM200); 40% en HK$ 146,90 (Target Base); 40% en HK$ 188,00 (Bull Case)."]
        ],
        "bullets": [
            "Vehículo Preferente: Acciones ordinarias 9988.HK negociadas en HKEX en dólares de Hong Kong (HKD) para evitar costes de conversión de ADS y beneficiarse del flujo comprador del Southbound Connect."
        ]
    },
    {
        "num": 40,
        "section": "ACTO VII: EL VEREDICTO FINAL  |  MÓDULO 18 — TEAR SHEET EJECUTIVO FINAL",
        "title": "Tear Sheet ejecutivo final: las 5 conclusiones que resumen la historia",
        "subtitle": "Síntesis definitiva del Comité de Inversiones sobre Alibaba Group Holding Limited (9988.HK / BABA)",
        "kpis": [("1. SUELO SOTP CORE", "HK$ 97,02 (99,2% Spot)"), ("2. INFLEXIÓN FCF FY27", "+RMB 55B Positivo"), ("3. LÍDER CLOUD IA", "35,8% Cuota Mercado"), ("4. LIQUIDEZ LIBRE", "RMB 520,8B (US$ 75,5B)")],
        "table": [
            ["Parámetro Clave", "Valor Auditado", "Parámetro Clave", "Valor Auditado"],
            ["Ticker Primario / Bolsa", "9988.HK (HKEX) / BABA (NYSE)", "Veredicto Soberano", "COMPRA FUERTE (BUY)"],
            ["Cotización Spot (23-Oct-2026)", "HK$ 97,80 (US$ 100,20 / ADS)", "Puntuación Global Scorecard", "8,06 / 10 (Grado Institucional)"],
            ["Precio Objetivo Base Ponderado", "HK$ 146,90 (+50,2% Upside)", "Valor Esperado E[V] Probabilístico", "HK$ 141,95 (+45,1% Potencial)"],
            ["Valor Intrínseco DCF / SOTP", "HK$ 149,80 / HK$ 147,20", "Escenarios Bull / Bear", "HK$ 188,00 (+92%) / HK$ 86,00 (-12%)"],
            ["Ingresos Consolidados FY26", "RMB 1.023.670M (+11,0% LfL)", "Caja Neta Forense Consolidada", "+RMB 260.828M (HK$ 13,01/acc)"],
            ["Peso Asignado en Cartera NAV", "5,25% (Ejecución en 3 Tramos)", "Stop-Loss Institucional Duro", "Cierre Semanal < HK$ 78,50"]
        ],
        "bullets": [
            "1. Hegemonía Inviolable en el Comercio Digital Chino: Con más de 1.000 millones de consumidores y RMB 8 billones en GMV, Taobao y Tmall forman el peaje comercial más valioso de Asia, cuya monetización se acelera con la tarifa del 0,6% y la IA publicitaria Quanzhantui.",
            "2. El Valle de FCF de FY2026 fue una Inversión Transitoria Autofinanciada: Provocado por el récord histórico de CapEx en IA (RMB 122.933M) y el lanzamiento de Taobao Instant Commerce; el flujo de caja libre rebotará con fuerza a +RMB 55.000M en FY27E y +RMB 121.000M en FY28E.",
            "3. Liderazgo Indiscutible en el Superciclo de IA en Asia: Alibaba Cloud ostenta el 35,8% de cuota de mercado en China con ventas creciendo al +29%, la familia Qwen superando 600M de descargas y el Adjusted EBITA multiplicándose por casi seis veces en dos años.",
            "4. Blindaje Patrimonial sin Fisuras y Regalo Tecnológico SOTP: Una liquidez libre de RMB 520.824M (US$ 75,5B) y caja neta de RMB 260.828M hacen posible adquirir todo el negocio maduro y la caja a HK$ 97,02, recibiendo Alibaba Cloud y el negocio internacional AIDC a coste implícito cero.",
            "5. Plan de Ejecución Disciplinado con Ratio Asimétrico de 4,16x: Recomendamos incorporar Alibaba con un peso objetivo del 5,25% del NAV ejecutado en 3 tramos (40% spot a HK$ 97,80; 35% en HK$ 88,65–93,50; 25% tras superar HK$ 110,50) y stop-loss duro en HK$ 78,50."
        ]
    }
]


def build_pptx():
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.50)
    blank_layout = prs.slide_layouts[6]

    c_navy = PptRGBColor(10, 25, 47)
    c_blue = PptRGBColor(29, 78, 216)
    c_teal = PptRGBColor(13, 148, 136)
    c_gold = PptRGBColor(217, 119, 6)
    c_slate = PptRGBColor(71, 85, 105)
    c_dark = PptRGBColor(15, 23, 42)
    c_light = PptRGBColor(248, 250, 252)
    c_white = PptRGBColor(255, 255, 255)
    c_border = PptRGBColor(203, 213, 225)

    for s_data in SLIDES_DATA:
        slide = prs.slides.add_slide(blank_layout)
        s_num = s_data["num"]

        # Header Band (0.0 to 1.05 in)
        hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0.0), PptInches(0.0), PptInches(13.333), PptInches(1.05))
        hdr.fill.solid()
        hdr.fill.fore_color.rgb = c_navy
        hdr.line.fill.background()

        accent = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(0.0), PptInches(1.05), PptInches(13.333), PptInches(0.05))
        accent.fill.solid()
        accent.fill.fore_color.rgb = c_gold if s_num in (1, 22, 34, 40) else c_teal
        accent.line.fill.background()

        tb_sec = slide.shapes.add_textbox(PptInches(0.45), PptInches(0.08), PptInches(9.5), PptInches(0.26))
        tf_sec = tb_sec.text_frame
        tf_sec.word_wrap = True
        p_sec = tf_sec.paragraphs[0]
        p_sec.text = f"{s_data['section']}  |  ALIBABA GROUP (9988.HK / BABA)"
        p_sec.font.size = PptPt(9.5)
        p_sec.font.bold = True
        p_sec.font.color.rgb = c_gold

        tb_tit = slide.shapes.add_textbox(PptInches(0.45), PptInches(0.32), PptInches(12.3), PptInches(0.40))
        tf_tit = tb_tit.text_frame
        tf_tit.word_wrap = True
        p_tit = tf_tit.paragraphs[0]
        p_tit.text = s_data["title"].strip()
        p_tit.font.size = PptPt(17.5)
        p_tit.font.bold = True
        p_tit.font.color.rgb = c_white

        tb_sub = slide.shapes.add_textbox(PptInches(0.45), PptInches(0.70), PptInches(12.3), PptInches(0.30))
        tf_sub = tb_sub.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = s_data["subtitle"].strip()
        p_sub.font.size = PptPt(10.5)
        p_sub.font.color.rgb = PptRGBColor(203, 213, 225)

        curr_y = 1.22

        # Optional KPI Cards Row
        if "kpis" in s_data:
            kpis = s_data["kpis"]
            card_w = 2.92
            gap = 0.22
            for idx, (k_lbl, k_val) in enumerate(kpis):
                left_x = 0.45 + idx * (card_w + gap)
                card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, PptInches(left_x), PptInches(curr_y), PptInches(card_w), PptInches(0.82))
                card.fill.solid()
                card.fill.fore_color.rgb = c_light
                card.line.color.rgb = c_teal if idx % 2 == 0 else c_blue
                card.line.width = PptPt(1.2)
                tf_c = card.text_frame
                tf_c.word_wrap = True
                p1 = tf_c.paragraphs[0]
                p1.text = k_lbl
                p1.font.size = PptPt(8.5)
                p1.font.bold = True
                p1.font.color.rgb = c_slate
                p2 = tf_c.add_paragraph()
                p2.text = k_val
                p2.font.size = PptPt(13.5)
                p2.font.bold = True
                p2.font.color.rgb = c_navy
            curr_y += 0.96

        # Optional Chart Image + Right Bullets Layout
        if "chart" in s_data:
            c_file = os.path.join(CHARTS_DIR, s_data["chart"])
            if os.path.exists(c_file):
                slide.shapes.add_picture(c_file, PptInches(0.45), PptInches(curr_y), width=PptInches(6.55))
            tb_b = slide.shapes.add_textbox(PptInches(7.15), PptInches(curr_y), PptInches(5.70), PptInches(5.45))
            tf_b = tb_b.text_frame
            tf_b.word_wrap = True
            for b_idx, b_txt in enumerate(s_data.get("bullets", [])):
                p = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
                p.text = f"▪  {b_txt}"
                p.font.size = PptPt(10.5)
                p.font.color.rgb = c_dark
                p.space_after = PptPt(8)
        else:
            # Optional Native Table
            if "table" in s_data:
                t_rows = s_data["table"]
                n_r = len(t_rows)
                n_c = len(t_rows[0])
                t_h = min(3.55, 0.40 * n_r)
                t_shape = slide.shapes.add_table(n_r, n_c, PptInches(0.45), PptInches(curr_y), PptInches(12.40), PptInches(t_h))
                tbl = t_shape.table
                for r_i, row_vals in enumerate(t_rows):
                    for c_i, val in enumerate(row_vals):
                        cell = tbl.cell(r_i, c_i)
                        cell.text = val
                        cell.fill.solid()
                        if r_i == 0:
                            cell.fill.fore_color.rgb = c_navy
                        else:
                            cell.fill.fore_color.rgb = c_light if r_i % 2 == 1 else c_white
                        for p in cell.text_frame.paragraphs:
                            p.font.size = PptPt(8.8 if n_r > 6 else 9.2)
                            p.font.bold = (r_i == 0 or c_i == 0)
                            p.font.color.rgb = c_white if r_i == 0 else c_dark
                curr_y += t_h + 0.18

            # Bullets Box below KPIs / Table
            bullets = s_data.get("bullets", [])
            if bullets:
                rem_h = max(1.10, 6.85 - curr_y)
                tb_b = slide.shapes.add_textbox(PptInches(0.45), PptInches(curr_y), PptInches(12.40), PptInches(rem_h))
                tf_b = tb_b.text_frame
                tf_b.word_wrap = True
                for b_idx, b_txt in enumerate(bullets):
                    p = tf_b.paragraphs[0] if b_idx == 0 else tf_b.add_paragraph()
                    p.text = f"▪  {b_txt}"
                    p.font.size = PptPt(10.5 if len(bullets) <= 3 else 10.0)
                    p.font.color.rgb = c_dark
                    p.space_after = PptPt(6)

        # Footer Bar (7.02 to 7.38 in — safely < 7.60 in)
        ftr = slide.shapes.add_textbox(PptInches(0.45), PptInches(7.02), PptInches(12.40), PptInches(0.32))
        tf_f = ftr.text_frame
        p_f = tf_f.paragraphs[0]
        p_f.text = f"PITCH DECK COMITÉ DE INVERSIONES  |  Alibaba Group Holding Limited (9988.HK / BABA)  |  DIAPOSITIVA {s_num} DE 40"
        p_f.font.size = PptPt(8.5)
        p_f.font.color.rgb = c_slate

    prs.save(PPTX_PATH)
    print(f"[PPTX] Generado exitosamente (40 slides): {PPTX_PATH}")


build_pptx_and_pdf = build_pptx


if __name__ == "__main__":
    charts = build_charts()
    build_docx(charts)
    build_pptx()
