#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_global_portfolio_summary.py — Consolidador Institucional de Cartera Global.
Extrae de todas las empresas procesadas en ROOT_DIR sus múltiplos, valoraciones y
las 7 métricas de calificación institucional (1 a 10):
  - Calidad de los Ingresos (1-10)
  - Puntuación del Moat (1-10)
  - Salud Forense del Balance (1-10)
  - Eficiencia Operativa (1-10)
  - Directiva, Gobernanza y Capital Allocation (1-10)
  - Asimetría de Valor (1-10)
  - Nota Global Ponderada (1-10)
Genera ROOT_DIR/RESUMEN_CARTERA_GLOBAL.md y ROOT_DIR/RESUMEN_CARTERA_GLOBAL.xlsx.
"""

import os
import re
import sys
import glob
import json
import shutil
import argparse
import unicodedata
from datetime import datetime
from typing import Dict, List, Any

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IGNORED_DIRS = {"_shared_engine", "logs", ".git", "__pycache__", ".venv", "venv", "node_modules", "kokoro_models", "doc", "mp3", "ppt"}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn").lower()


def _parse_score_1_to_10(s: Any) -> float:
    if not s:
        return 0.0
    m = re.search(r"(?<!\d)([1-9](?:[.,]\d+)?|10(?:[.,]0+)?)(?!\d)", str(s))
    return float(m.group(1).replace(",", ".")) if m else 0.0


def parse_fallback_from_md(md_path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return data

    if data.get("verdict") == "PENDIENTE":
        if re.search(r"VEREDICTO GLOBAL.*?(?:COMPRAR|COMPRA|ACUMULAR)", text, re.IGNORECASE | re.DOTALL):
            data["verdict"] = "COMPRAR"
        elif re.search(r"VEREDICTO GLOBAL.*?(?:VENDER|VENTA)", text, re.IGNORECASE | re.DOTALL):
            data["verdict"] = "VENDER"
        elif re.search(r"VEREDICTO GLOBAL.*?(?:ESPERAR|MANTENER)", text, re.IGNORECASE | re.DOTALL):
            data["verdict"] = "ESPERAR"

    if not data.get("moat_score") or data.get("moat_score") == 0.0:
        m_moat = re.search(r"Calificaci[oó]n del Moat Global[^\n]{0,120}?([1-9](?:[\.,]\d+)?|10(?:[\.,]0+)?)\s*/\s*10", text, re.IGNORECASE | re.DOTALL)
        if m_moat:
            data["moat_score"] = float(m_moat.group(1).replace(",", "."))

    if not data.get("revenue_quality_score") or data.get("revenue_quality_score") == 0.0:
        m_rev = re.search(r"Puntuaci[oó]n de Calidad de Ingresos[^\n]{0,120}?([1-9](?:[\.,]\d+)?|10(?:[\.,]0+)?)\s*/\s*10", text, re.IGNORECASE | re.DOTALL)
        if m_rev:
            data["revenue_quality_score"] = float(m_rev.group(1).replace(",", "."))

    if not data.get("forensic_health_score") or data.get("forensic_health_score") == 0.0:
        m_health = re.search(r"Puntuaci[oó]n de Salud Forense[^\n]{0,120}?([1-9](?:[\.,]\d+)?|10(?:[\.,]0+)?)\s*/\s*10", text, re.IGNORECASE | re.DOTALL)
        if m_health:
            data["forensic_health_score"] = float(m_health.group(1).replace(",", "."))

    # Extracción de los factores del Scorecard Institucional (Módulo 17.1)
    m17 = re.search(r"#{2,4}\s*(?:Subsecci[oó]n\s+)?\**17\.1\b.*?(?=#{2,4}\s*(?:Subsecci[oó]n\s+)?\**17\.2\b|##\s*M[oó]dulo\s*18|\Z)", text, re.IGNORECASE | re.DOTALL)
    if m17:
        for line in m17.group(0).splitlines():
            if not line.strip().startswith("|") or "---" in line:
                continue
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cols) < 4:
                continue
            is_num_col0 = bool(re.match(r"^[\*`\s]*\d+\.?[\*`\s]*$", cols[0].strip()))
            first_two_norm = _strip_accents(" ".join(cols[:2]))
            if not is_num_col0 and any(
                w in first_two_norm
                for w in (
                    "total",
                    "puntuacion global",
                    "puntuacion ponderada",
                    "puntuacion institucional",
                    "puntuacion compuesta",
                    "calificacion global",
                    "nota global",
                    "institutional score",
                )
            ):
                if not data.get("weighted_total_score") or data.get("weighted_total_score") == 0.0:
                    for c in cols[1:]:
                        if "%" in c:
                            continue
                        val = _parse_score_1_to_10(c)
                        if 1.0 <= val <= 10.0:
                            data["weighted_total_score"] = round(val, 2)
                            break
                continue

            factor_name = cols[1] if is_num_col0 else cols[0]
            fn_norm = _strip_accents(factor_name)
            start_idx = 2 if is_num_col0 else 1

            sc = 0.0
            # 1) Buscar patrón explícito "X.X / 10" en las celdas de datos
            for c_cell in cols[start_idx:]:
                m_slash = re.search(r"([1-9](?:[.,]\d+)?|10(?:[.,]0+)?)\s*/\s*10\b", c_cell)
                if m_slash:
                    sc = float(m_slash.group(1).replace(",", "."))
                    break
            # 2) Si no lleva "/ 10", buscar en la celda inmediatamente posterior a la columna de peso (%)
            if sc == 0.0:
                for idx_c in range(start_idx, min(len(cols) - 1, start_idx + 3)):
                    if "%" in cols[idx_c]:
                        cand_cell = cols[idx_c + 1]
                        if not re.search(r"(?:m[oó]dulo|secc|\b1[.,]0\s*[-–a]\s*10|x\b|%)", cand_cell, re.IGNORECASE):
                            v_cand = _parse_score_1_to_10(cand_cell)
                            if 3.0 <= v_cand <= 10.0:
                                sc = v_cand
                                break
            # 3) Fallback a la columna estándar de nota (excluyendo referencias a módulos o escalas "1.0 - 10.0")
            if sc == 0.0:
                std_col = cols[3] if is_num_col0 else cols[2]
                if not re.search(r"(?:m[oó]dulo|secc|\b1[.,]0\s*[-–a]\s*10|x\b|%)", std_col, re.IGNORECASE):
                    v_std = _parse_score_1_to_10(std_col)
                    if 3.0 <= v_std <= 10.0:
                        sc = v_std

            if not (1.0 <= sc <= 10.0):
                continue

            if (not data.get("moat_score") or data.get("moat_score") == 0.0) and any(
                k in fn_norm for k in ("moat", "foso competitivo")
            ):
                data["moat_score"] = sc
            if (not data.get("revenue_quality_score") or data.get("revenue_quality_score") == 0.0) and any(
                k in fn_norm for k in ("qoe", "calidad de ingresos", "calidad de beneficios", "calidad del beneficio")
            ):
                data["revenue_quality_score"] = sc
            if (not data.get("forensic_health_score") or data.get("forensic_health_score") == 0.0) and any(
                k in fn_norm for k in ("salud forense", "salud de balance", "solidez forense", "solidez de balance", "solvencia patrimonial")
            ):
                data["forensic_health_score"] = sc
            if (not data.get("operational_efficiency_score") or data.get("operational_efficiency_score") == 0.0) and any(
                k in fn_norm
                for k in (
                    "eficiencia operativa",
                    "roic",
                    "rentabilidad sobre el capital",
                    "rentabilidad del capital",
                    "rentabilidad operativa",
                    "unit economics",
                    "escalabilidad",
                )
            ):
                data["operational_efficiency_score"] = sc
            if (not data.get("governance_score") or data.get("governance_score") == 0.0) and any(
                k in fn_norm
                for k in (
                    "gobernanza",
                    "gobierno corporativo",
                    "directiva",
                    "equipo directivo",
                    "asignacion de capital",
                    "capital allocation",
                    "big boss",
                    "insiders",
                )
            ):
                data["governance_score"] = sc
            if (not data.get("valuation_asymmetry_score") or data.get("valuation_asymmetry_score") == 0.0) and any(
                k in fn_norm
                for k in (
                    "valoracion intrinseca",
                    "atractivo de valoracion",
                    "margen de seguridad",
                    "asimetria de valoracion",
                    "valoracion absoluta",
                    "valoracion multi",
                )
            ):
                data["valuation_asymmetry_score"] = sc

    if not data.get("weighted_total_score") or data.get("weighted_total_score") == 0.0:
        m_tot = re.search(
            r"(?:Puntuaci[oó]n\s+(?:Institucional\s+)?Ponderada(?:\s+Total|\s+Global)?|Nota\s+Global\s+Ponderada|TOTAL\s+PONDERADO)[^\n0-9]{0,80}?([1-9](?:[\.,]\d+)?|10(?:[\.,]0+)?)\s*/\s*10",
            text,
            re.IGNORECASE,
        )
        if m_tot:
            data["weighted_total_score"] = round(float(m_tot.group(1).replace(",", ".")), 2)

    cp = data.get("current_price", 0.0)
    curr_tok = r"(?:HK\$|HKD|CNY|RMB|KRW|USD|US\$|CAD|C\$|AUD|A\$|JPY|SEK|NOK|DKK|CHF|EUR|GBP|GBp|SAR|MYR|RM|SGD|S\$|BRL|R\$|MXN|CLP|TWD|NT\$|IDR|INR|THB|VND|PLN|ZAR|\$|¥|₩|€|£|₹|฿|₫|zł|peniques|pence|p\b)"
    amt_pat = rf"(?:{curr_tok}\s*([0-9]+(?:[.,][0-9]+)*)|([0-9]+(?:[.,][0-9]+)*)\s*{curr_tok})"
    is_buy = any(w in str(data.get("verdict", "")).upper() for w in ("COMPRA", "ACUMULAR", "SOBREPONDERAR", "INVERTIR", "BUY"))

    def parse_num_token(val_str: str) -> float:
        s = val_str.strip()
        # Si tiene comas de miles estilo 19,920 o 288,000
        if re.match(r"^\d{1,3}(?:,\d{3})+(?:\.\d+)?$", s):
            return float(s.replace(",", ""))
        if re.match(r"^\d{1,3}(?:\.\d{3})+(?:,\d+)?$", s):
            return float(s.replace(".", "").replace(",", "."))
        return float(s.replace(",", "."))

    # Búsqueda en tabla de veredicto (Módulo 17.5 / 11)
    if not data.get("target_price_base") or data.get("target_price_base") == 0.0:
        m_tbl_tp = re.search(
            r"\|\s*(?:Precio\s*Objetivo\s*(?:Ponderado|Base)?|Valor\s*Intr[ií]nseco\s*DCF|Fair\s*Value)[^|\n]*\|\s*(?:[A-Za-z$€£¥₩₹฿₫zł]+\s*)?([0-9]+(?:[.,][0-9]+)*)",
            text,
            re.IGNORECASE,
        )
        if m_tbl_tp:
            try:
                val = parse_num_token(m_tbl_tp.group(1))
                if cp <= 0 or (0.40 * cp <= val <= 5.0 * cp):
                    data["target_price_base"] = val
            except Exception:
                pass

    if not data.get("expected_value_price") or data.get("expected_value_price") == 0.0:
        m_tbl_ev = re.search(
            r"\|\s*(?:Valor\s*Esperado|E\[V\]|Precio\s*Objetivo\s*Ponderado)[^|\n]*\|\s*(?:[A-Za-z$€£¥₩₹฿₫zł]+\s*)?([0-9]+(?:[.,][0-9]+)*)",
            text,
            re.IGNORECASE,
        )
        if m_tbl_ev:
            try:
                val = parse_num_token(m_tbl_ev.group(1))
                if cp <= 0 or (0.40 * cp <= val <= 5.0 * cp):
                    data["expected_value_price"] = val
            except Exception:
                pass

    if not data.get("target_price_base") or data.get("target_price_base") == 0.0 or (cp > 0 and abs(data.get("target_price_base", 0.0) - cp) / cp < 0.03):
        candidates = []
        for m in re.finditer(r"(?:Precio Objetivo|Valor Intr[ií]nseco Base|Fair Value Base|Target Price)[^\n]{0,120}?" + amt_pat, text, re.IGNORECASE):
            val_str = m.group(1) or m.group(2)
            try:
                val = parse_num_token(val_str)
                if cp > 0 and abs(val - cp) / cp < 0.03:
                    continue
                if is_buy and cp > 0 and val < cp * 1.03:
                    continue
                if cp <= 0 or (0.50 * cp <= val <= 4.0 * cp):
                    candidates.append(val)
            except Exception:
                pass
        if candidates:
            data["target_price_base"] = candidates[0]

    if not data.get("expected_value_price") or data.get("expected_value_price") == 0.0 or (is_buy and cp > 0 and data.get("expected_value_price", 0.0) <= cp * 1.02):
        ev_candidates = []
        for m in re.finditer(r"(?:Valor Esperado|E\[V\]|Expected Value)[^\n]{0,120}?" + amt_pat, text, re.IGNORECASE):
            val_str = m.group(1) or m.group(2)
            try:
                val = parse_num_token(val_str)
                if cp > 0 and abs(val - cp) / cp < 0.03:
                    continue
                if is_buy and cp > 0 and val < cp * 1.03:
                    continue
                if cp <= 0 or (0.50 * cp <= val <= 4.0 * cp):
                    ev_candidates.append(val)
            except Exception:
                pass
        if ev_candidates:
            data["expected_value_price"] = ev_candidates[0]
        elif data.get("target_price_base", 0.0) > 0:
            data["expected_value_price"] = data["target_price_base"]

    if not data.get("ev_ebitda") or data.get("ev_ebitda") == 0.0:
        m_ev = re.search(r"EV\s*/\s*EBITDA[^\n]{0,80}?([0-9]+(?:[.,][0-9]+)?)\s*x", text, re.IGNORECASE)
        if m_ev:
            try:
                val = float(m_ev.group(1).replace(",", "."))
                if 0.5 <= val <= 80.0:
                    data["ev_ebitda"] = val
            except Exception:
                pass

    if not data.get("pe_forward") or data.get("pe_forward") == 0.0:
        m_pe = re.search(r"P\s*/\s*E[^\n]{0,60}?([0-9]+(?:[.,][0-9]+)?)\s*x", text, re.IGNORECASE)
        if m_pe:
            try:
                val = float(m_pe.group(1).replace(",", "."))
                if 1.0 <= val <= 100.0:
                    data["pe_forward"] = val
            except Exception:
                pass

    if not data.get("recommended_nav_pct") or data.get("recommended_nav_pct") == 0.0:
        m_nav = re.search(r"(?:Tamaño|Sizing|Asignaci[oó]n|Peso Recomendado)[^\n]{0,100}?([1-9](?:[.,][0-9]+)?)\s*%", text, re.IGNORECASE)
        if m_nav:
            try:
                val = float(m_nav.group(1).replace(",", "."))
                if 0.5 <= val <= 12.0:
                    data["recommended_nav_pct"] = val
            except Exception:
                pass
        elif "COMPRA" in str(data.get("verdict", "")).upper() or "ACUMULAR" in str(data.get("verdict", "")).upper():
            data["recommended_nav_pct"] = 4.0

    return data


def resolve_yfinance_identity(company_dir: str, meta: Dict[str, Any], market: Dict[str, Any], kpis: Dict[str, Any]) -> Dict[str, str]:
    folder_name = os.path.basename(company_dir)
    cache_dir = os.path.join(company_dir, "extracted_ocr_cache")
    market_path = os.path.join(cache_dir, "market_data_live.json")

    raw_ticker = (
        market.get("symbol")
        or market.get("yf_ticker")
        or market.get("ticker")
        or meta.get("primary_ticker")
        or kpis.get("ticker")
        or folder_name
    )
    padded_ticker = str(raw_ticker).strip()
    if padded_ticker.upper().endswith(".HK"):
        num_part = padded_ticker.split(".")[0]
        if num_part.isdigit() and len(num_part) < 4:
            padded_ticker = num_part.zfill(4) + ".HK"
    elif padded_ticker.isdigit():
        padded_ticker = padded_ticker.zfill(4) + ".HK"

    yf_symbol = market.get("symbol") or market.get("yf_ticker") or padded_ticker
    if yf_symbol.upper().endswith(".HK"):
        num_part = yf_symbol.split(".")[0]
        if num_part.isdigit() and len(num_part) < 4:
            yf_symbol = num_part.zfill(4) + ".HK"

    yf_country = market.get("country") or meta.get("country") or ""
    yf_exchange = market.get("fullExchangeName") or market.get("exchange") or meta.get("exchange") or ""
    if yf_exchange == "HKEX (Main Board)":
        yf_exchange = ""

    if not yf_country or not yf_exchange or yf_country == "N/D" or yf_exchange == "N/D" or not market.get("yf_verified"):
        try:
            import yfinance as yf
            candidates = [padded_ticker, str(raw_ticker).strip()]
            for tk_try in candidates:
                if not tk_try:
                    continue
                info = yf.Ticker(tk_try).info or {}
                if info.get("symbol") or info.get("country") or info.get("exchange") or info.get("fullExchangeName"):
                    yf_symbol = info.get("symbol") or yf_symbol
                    yf_country = info.get("country") or info.get("region") or yf_country or "N/D"
                    yf_exchange = info.get("fullExchangeName") or info.get("exchange") or yf_exchange or "N/D"
                    market.update({
                        "ticker": yf_symbol,
                        "yf_ticker": yf_symbol,
                        "symbol": yf_symbol,
                        "yf_verified": True,
                        "country": yf_country,
                        "exchange": yf_exchange,
                        "exchange_code": info.get("exchange") or yf_exchange,
                        "fullExchangeName": yf_exchange,
                    })
                    if os.path.exists(cache_dir):
                        try:
                            with open(market_path, "w", encoding="utf-8") as f:
                                json.dump(market, f, ensure_ascii=False, indent=2)
                        except Exception:
                            pass
                    break
        except Exception:
            pass

    return {
        "ticker": yf_symbol or "N/D",
        "country": yf_country or "N/D",
        "exchange": yf_exchange or "N/D",
    }


def collect_company_record(company_dir: str) -> Dict[str, Any]:
    folder_name = os.path.basename(company_dir)
    cache_dir = os.path.join(company_dir, "extracted_ocr_cache")
    meta_path = os.path.join(cache_dir, "company_meta.json")
    root_meta_path = os.path.join(company_dir, "company_meta.json")
    forensic_path = os.path.join(cache_dir, "forensic_metrics.json")
    root_forensic_path = os.path.join(company_dir, "forensic_metrics.json")
    summary_path = os.path.join(company_dir, "company_summary.json")
    market_path = os.path.join(cache_dir, "market_data_live.json")
    root_market_path = os.path.join(company_dir, "market_data_live.json")

    meta, forensic, market, summary_doc = {}, {}, {}, {}
    for p, d in [
        (meta_path, meta),
        (root_meta_path, meta),
        (forensic_path, forensic),
        (root_forensic_path, forensic),
        (market_path, market),
        (root_market_path, market),
        (summary_path, summary_doc),
    ]:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    d.update(json.load(f))
            except Exception:
                pass

    kpis = {}
    for src in (meta, forensic, summary_doc):
        for k, v in src.items():
            if not isinstance(v, (dict, list)) and k not in kpis:
                kpis[k] = v
        if isinstance(src.get("summary_kpis"), dict):
            kpis.update(src["summary_kpis"])
        if isinstance(src.get("valuation"), dict):
            kpis.update(src["valuation"])

    # Integración con el Modelo Financiero Canónico (company_financial_model.json)
    model_path = os.path.join(company_dir, "company_financial_model.json")
    if os.path.exists(model_path):
        try:
            with open(model_path, "r", encoding="utf-8") as f:
                c_model = json.load(f)
                prof = c_model.get("company_profile", {})
                triang = c_model.get("valuation_triangulation", {})
                scores = c_model.get("institutional_scores", {})
                mult = c_model.get("multiples", {})
                if prof.get("ticker"):
                    meta["primary_ticker"] = prof["ticker"]
                if prof.get("company_name"):
                    meta["official_name"] = prof["company_name"]
                if prof.get("country"):
                    meta["country"] = prof["country"]
                if prof.get("exchange"):
                    meta["exchange"] = prof["exchange"]
                if prof.get("currency"):
                    meta["currency"] = prof["currency"]
                if prof.get("share_price_spot"):
                    kpis["current_price"] = prof["share_price_spot"]
                for tp_k in ("target_price_24m", "expected_value_price", "target_fair_value", "dcf_intrinsic_base", "target_price", "base_target_price", "scenario_base_price", "dcf_per_share"):
                    if triang.get(tp_k):
                        kpis.setdefault("target_price_base", triang[tp_k])
                    if c_model.get(tp_k):
                        kpis.setdefault("target_price_base", c_model[tp_k])
                if triang.get("target_price_24m"):
                    kpis["target_price_base"] = triang["target_price_24m"]
                if triang.get("expected_value_price"):
                    kpis["expected_value_price"] = triang["expected_value_price"]
                elif kpis.get("target_price_base"):
                    kpis["expected_value_price"] = kpis["target_price_base"]
                if scores.get("revenue_quality_qoe"):
                    kpis["revenue_quality_score"] = scores["revenue_quality_qoe"]
                if scores.get("moat_score"):
                    kpis["moat_score"] = scores["moat_score"]
                if scores.get("balance_sheet_forensic_health"):
                    kpis["forensic_health_score"] = scores["balance_sheet_forensic_health"]
                for eff_k in ("operational_efficiency_score", "roic_wacc_score", "efficiency_score"):
                    if scores.get(eff_k):
                        kpis["operational_efficiency_score"] = scores[eff_k]
                        break
                for gov_k in ("governance_capital_allocation", "management_and_capital_allocation", "capital_allocation_score", "governance_score"):
                    if scores.get(gov_k):
                        kpis["governance_score"] = scores[gov_k]
                        break
                for asym_k in ("valuation_asymmetry_score", "asymmetry_score"):
                    if scores.get(asym_k):
                        kpis["valuation_asymmetry_score"] = scores[asym_k]
                        break
                for tot_k in ("weighted_total_score", "weighted_score_total_10", "total_weighted_score_1_to_10", "composite_score_10", "composite_conviction_score"):
                    if scores.get(tot_k):
                        kpis["weighted_total_score"] = scores[tot_k]
                        break
                if scores.get("conviction_score"):
                    kpis["conviction_score"] = scores["conviction_score"]
                if scores.get("recommended_sizing_pct"):
                    kpis["recommended_nav_pct"] = scores["recommended_sizing_pct"]
                if scores.get("verdict"):
                    kpis["verdict"] = scores["verdict"]
                if mult.get("pe_forward"):
                    kpis["pe_forward"] = mult["pe_forward"]
                if mult.get("ev_ebitda"):
                    kpis["ev_ebitda"] = mult["ev_ebitda"]
                if mult.get("pb_ratio"):
                    kpis["pb_ratio"] = mult["pb_ratio"]
        except Exception:
            pass

    def safe_float(val: Any, default: float = 0.0) -> float:
        if val is None or val == "":
            return default
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip()
        # Si empieza con texto tipo "9M26:" o "(FY25)", buscar primer número real
        # Eliminar comas de miles tipo 19,920
        s_clean = re.sub(r"(\d),(\d{3})\b", r"\1\2", s)
        m = re.search(r"[-+]?\d+(?:[.,]\d+)?", s_clean)
        return float(m.group(0).replace(",", ".")) if m else default

    def first_float(keys: List[str], prefix_match: str = "", default: float = 0.0) -> float:
        for k in keys:
            v = safe_float(kpis.get(k), 0.0)
            if v != 0.0:
                return v
            v_m = safe_float(market.get(k), 0.0)
            if v_m != 0.0:
                return v_m
        if prefix_match:
            for k, raw_v in kpis.items():
                if k.lower().startswith(prefix_match.lower()):
                    v = safe_float(raw_v, 0.0)
                    if v != 0.0:
                        return v
        return default

    def safe_int(val: Any, default: int = 4) -> int:
        v = int(round(safe_float(val, float(default))))
        if v > 5:
            v = max(1, min(5, int(round(v / 2.0))))
        return max(1, min(5, v))

    div_yield = first_float(["dividend_yield_pct", "dividend_yield"], default=0.0)
    if div_yield > 25.0:
        div_yield = round(div_yield / 100.0, 2)

    yf_id = resolve_yfinance_identity(company_dir, meta, market, kpis)
    tk_upper = yf_id["ticker"].upper()
    raw_curr = str(market.get("currency") or kpis.get("currency") or meta.get("currency") or kpis.get("trading_currency") or meta.get("trading_currency") or "").upper().strip()
    if not raw_curr or (raw_curr == "HKD" and not tk_upper.endswith(".HK")):
        if tk_upper.endswith((".SZ", ".SS")):
            raw_curr = "CNY"
        elif tk_upper.endswith((".KS", ".KQ")):
            raw_curr = "KRW"
        elif tk_upper.endswith(".T"):
            raw_curr = "JPY"
        elif tk_upper.endswith(".TO"):
            raw_curr = "CAD"
        elif tk_upper.endswith(".AX"):
            raw_curr = "AUD"
        elif tk_upper.endswith(".ST"):
            raw_curr = "SEK"
        elif tk_upper.endswith(".SR"):
            raw_curr = "SAR"
        elif tk_upper.endswith(".KL"):
            raw_curr = "MYR"
        elif tk_upper.endswith(".SI"):
            raw_curr = "SGD"
        elif tk_upper.endswith(".L"):
            raw_curr = "GBP"
        elif tk_upper.endswith(".SA"):
            raw_curr = "BRL"
        elif tk_upper.endswith((".MC", ".PA", ".AS", ".DE", ".MI")):
            raw_curr = "EUR"
        elif tk_upper.endswith(".SW"):
            raw_curr = "CHF"
        elif tk_upper.endswith(".OL"):
            raw_curr = "NOK"
        elif tk_upper.endswith(".CO"):
            raw_curr = "DKK"
        elif tk_upper.endswith((".TW", ".TWO")):
            raw_curr = "TWD"
        elif tk_upper.endswith(".HK"):
            raw_curr = "HKD"
        else:
            raw_curr = "USD"

    cp_val = first_float(["current_price", "spot_price", "latest_price", "price", "precio_actual", "spot_price_hkd", "spot_price_cny", "current_price_cny", "current_price_krw"], prefix_match="current_price_")
    tp_val = first_float(["target_price_base", "target_price", "fair_value_base", "valor_intrinseco_base", "base_target_price", "target_price_hkd", "base_target_price_hkd", "target_price_base_cny", "fair_value_base_cny", "fair_value_base_krw"], prefix_match="fair_value_base_")
    ev_p_val = first_float(["expected_value_price", "expected_value", "expected_value_pw", "valor_esperado_ponderado", "expected_value_hkd", "expected_value_cny", "expected_value_krw"], prefix_match="expected_value_")
    up_val = first_float(["upside_pct", "expected_upside_pct", "expected_upside_base_pct", "upside_base_pct", "upside_ponderado_pct", "base_upside_pct"])
    pe_tr_val = first_float(["pe_trailing", "pe_ttm", "pe_fy25_x"])
    pe_fw_val = first_float(["pe_forward", "pe_fwd", "pe_2026e"], default=pe_tr_val)
    ev_eb_val = first_float(["ev_ebitda", "ev_ebitda_1h26_x", "ev_ebitda_fy25_x", "ev_ebitda_2025"])
    pb_val = first_float(["pb_ratio", "pb", "pb_current", "pb_1h26_x", "pb_fy25_x"])
    rev_q_val = first_float(["revenue_quality_score", "overall_quality_score"])
    moat_val = first_float(["moat_score"])
    health_val = first_float(["forensic_health_score", "balance_sheet_score", "balance_health_score", "forensic_score", "forensic_balance_score"])
    eff_val = first_float(["operational_efficiency_score", "roic_wacc_score", "efficiency_score"])
    gov_val = first_float(["governance_score", "governance_capital_allocation", "management_and_capital_allocation", "capital_allocation_score"])
    asym_val = first_float(["valuation_asymmetry_score", "asymmetry_score"])
    tot_sc_val = first_float(["weighted_total_score", "weighted_score_total_10", "total_weighted_score_1_to_10", "composite_score_10", "composite_conviction_score"])
    verdict_val = str(kpis.get("verdict") or kpis.get("veredicto") or "PENDIENTE").upper()
    conv_val = safe_int(kpis.get("conviction_score") or kpis.get("conviction") or kpis.get("conviccion") or kpis.get("score_global"), 4)
    nav_val = first_float(["recommended_nav_pct", "sizing_sugerido", "recommended_weight_pct"])

    record = {
        "folder": folder_name,
        "company_name": kpis.get("company_name") or meta.get("company_name") or market.get("longName") or folder_name,
        "country": yf_id["country"],
        "exchange": yf_id["exchange"],
        "ticker": yf_id["ticker"],
        "sector": kpis.get("sector") or meta.get("sector") or kpis.get("perfil") or "Industrial / Tech",
        "trading_currency": raw_curr,
        "current_price": cp_val,
        "target_price_base": tp_val,
        "expected_value_price": ev_p_val,
        "upside_pct": up_val,
        "dividend_yield_pct": div_yield,
        "total_expected_return_pct": first_float(["total_expected_return_pct"]),
        "pe_trailing": pe_tr_val,
        "pe_forward": pe_fw_val,
        "ev_ebitda": ev_eb_val,
        "pb_ratio": pb_val,
        "revenue_cagr_pct": first_float(["revenue_cagr_pct", "revenue_cagr_5y_pct", "revenue_yoy_pct"]),
        "gross_margin_pct": first_float(["gross_margin_pct", "gross_margin_2025_pct", "gross_margin_fy25_pct"]),
        "ebitda_margin_pct": first_float(["ebitda_margin_pct", "ebitda_margin_2025_pct", "ebitda_margin_fy25_pct"]),
        "roic_pct": first_float(["roic_pct", "roic_2025_pct", "roic_fy25_pct", "roic_2025"]),
        "roe_pct": first_float(["roe_pct", "roe_2025_pct", "roe_fy25_pct", "roe_weighted_2025_pct"]),
        "wacc_pct": first_float(["wacc_pct", "wacc"], default=10.0),
        "roic_wacc_spread_pct": first_float(["roic_wacc_spread_pct"]),
        "dso_days": first_float(["dso_days", "dso_days_2025"]),
        "sloan_ratio_pct": first_float(["sloan_ratio_pct", "sloan_ratio_2025_pct", "sloan_ratio_fy25_pct"]),
        "net_debt_ebitda": first_float(["net_debt_ebitda", "net_debt_to_ebitda", "net_debt_ebitda_2025", "net_debt_to_ebitda_1h26", "deuda_neta_ebitda"]),
        "revenue_quality_score": rev_q_val,
        "moat_score": moat_val,
        "forensic_health_score": health_val,
        "operational_efficiency_score": eff_val,
        "governance_score": gov_val,
        "valuation_asymmetry_score": asym_val,
        "weighted_total_score": tot_sc_val,
        "verdict": verdict_val,
        "conviction_score": conv_val,
        "recommended_nav_pct": nav_val,
    }

    md_files = glob.glob(os.path.join(company_dir, "*_INFORME_COMITE_FINAL.md"))
    if md_files:
        record = parse_fallback_from_md(md_files[0], record)

    if record["current_price"] > 0 and record["target_price_base"] == 0.0 and record["upside_pct"] != 0.0:
        record["target_price_base"] = round(record["current_price"] * (1.0 + (record["upside_pct"] / 100.0)), 2)

    if record["expected_value_price"] == 0.0 and record["target_price_base"] > 0:
        record["expected_value_price"] = record["target_price_base"]
    elif record["target_price_base"] == 0.0 and record["expected_value_price"] > 0:
        record["target_price_base"] = record["expected_value_price"]

    if record["current_price"] > 0 and record["target_price_base"] > 0 and record["upside_pct"] == 0.0:
        ref_target = record["expected_value_price"] if record["expected_value_price"] > 0 else record["target_price_base"]
        record["upside_pct"] = round(((ref_target / record["current_price"]) - 1.0) * 100.0, 2)

    if record["total_expected_return_pct"] == 0.0 and record["upside_pct"] != 0.0:
        record["total_expected_return_pct"] = round(record["upside_pct"] + record["dividend_yield_pct"], 2)

    if record["roic_wacc_spread_pct"] == 0.0 and record["roic_pct"] != 0.0:
        record["roic_wacc_spread_pct"] = round(record["roic_pct"] - record["wacc_pct"], 2)

    # Fallbacks analíticos por si algún score secundario no figurase explícito
    if record["operational_efficiency_score"] == 0.0:
        roic_ref = record["roic_pct"] if record["roic_pct"] != 0.0 else 15.0
        record["operational_efficiency_score"] = min(9.6, max(5.5, round(6.0 + (roic_ref - record["wacc_pct"]) * 0.25, 1)))
    if record["governance_score"] == 0.0:
        record["governance_score"] = round((record["moat_score"] + record["forensic_health_score"]) / 2.0, 1) if record["moat_score"] > 0 else 7.5
    if record["valuation_asymmetry_score"] == 0.0:
        record["valuation_asymmetry_score"] = min(9.5, max(3.5, round(7.0 + record["upside_pct"] * 0.05, 1)))
    w_sum = (
        record["moat_score"] * 0.20
        + record["forensic_health_score"] * 0.20
        + record["revenue_quality_score"] * 0.20
        + record["operational_efficiency_score"] * 0.15
        + record["governance_score"] * 0.15
        + record["valuation_asymmetry_score"] * 0.10
    )
    if record["weighted_total_score"] == 0.0 or abs(record["weighted_total_score"] - w_sum) > 0.8:
        record["weighted_total_score"] = round(w_sum, 2)

    return record


def write_global_markdown(root_dir: str, records: List[Dict[str, Any]]) -> str:
    md_out = os.path.join(root_dir, "RESUMEN_CARTERA_GLOBAL.md")
    total_nav = sum(r["recommended_nav_pct"] for r in records if "COMPRA" in r["verdict"] or "ACUMULAR" in r["verdict"])

    lines = [
        "# COMPARATIVA MAESTRA DE CARTERA INSTITUCIONAL (`COMITÉ DE INVERSIONES BUYSIDE`)",
        f"**Fecha de Consolidación:** {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"**Compañías Auditadas:** {len(records)} | "
        f"**Asignación Total Recomendada en Compra:** `{total_nav:.2f}% del NAV`",
        "",
        "## 1. Ranking de Valoración, Scorecard Institucional (7 Calificaciones 1-10), Retorno Esperado y Decisión de Comité",
        "",
        "| Compañía | PAIS | Bolsas | Ticker | Divisa | **Calidad Ingresos (1-10)** | **Puntuación Moat (1-10)** | **Salud Forense (1-10)** | **Eficiencia Operativa (1-10)** | **Directiva y Cap. Alloc. (1-10)** | **Asimetría Valor (1-10)** | **Nota Global Ponderada (1-10)** | Precio Actual | P.O. Base | Valor Esperado | Upside (%) | Yield (%) | **Retorno Total (%)** | P/E Fwd (x) | EV/EBITDA (x) | P/B (x) | Convicción (1-5) | Sizing (% NAV) | **VEREDICTO** |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in records:
        lines.append(
            f"| **{r['company_name']}** | {r['country']} | {r['exchange']} | `{r['ticker']}` | {r['trading_currency']} | "
            f"**{r['revenue_quality_score']:.1f}/10** | **{r['moat_score']:.1f}/10** | **{r['forensic_health_score']:.1f}/10** | "
            f"**{r['operational_efficiency_score']:.1f}/10** | **{r['governance_score']:.1f}/10** | **{r['valuation_asymmetry_score']:.1f}/10** | **{r['weighted_total_score']:.2f}/10** | "
            f"{r['current_price']:.2f} | {r['target_price_base']:.2f} | {r['expected_value_price']:.2f} | "
            f"{r['upside_pct']:+.1f}% | {r['dividend_yield_pct']:.2f}% | **{r['total_expected_return_pct']:+.1f}%** | "
            f"{r['pe_forward']:.1f}x | {r['ev_ebitda']:.1f}x | {r['pb_ratio']:.2f}x | "
            f"{r['conviction_score']}/5 | {r['recommended_nav_pct']:.2f}% | **{r['verdict']}** |"
        )

    with open(md_out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return md_out


def write_global_excel(root_dir: str, records: List[Dict[str, Any]], excel_name: str = "RESUMEN_CARTERA_GLOBAL.xlsx") -> str:
    xlsx_out = os.path.join(root_dir, excel_name)
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    navy_header_fill = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    zebra_fill = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    buy_fill = PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid")
    hold_fill = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    sell_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")

    header_font = Font(name="Calibri", size=10, bold=True, color="FFFFFF")
    bold_font = Font(name="Calibri", size=10, bold=True, color="0F172A")
    reg_font = Font(name="Calibri", size=10, bold=False, color="1E293B")
    buy_font = Font(name="Calibri", size=10, bold=True, color="166534")
    hold_font = Font(name="Calibri", size=10, bold=True, color="92400E")
    sell_font = Font(name="Calibri", size=10, bold=True, color="991B1B")
    thin_border = Border(bottom=Side(style="thin", color="CBD5E1"), top=Side(style="thin", color="CBD5E1"))

    ws1 = wb.active
    ws1.title = "1_Ranking_Comite"
    headers_1 = [
        "Compañía", "PAIS", "Bolsas", "Ticker", "Sector", "Divisa",
        "Calidad de los Ingresos (1-10)", "Puntuación del Moat (1-10)", "Salud Forense del Balance (1-10)",
        "Eficiencia Operativa (1-10)", "Directiva, Gobernanza y Capital Allocation (1-10)",
        "Asimetría de Valor (1-10)", "Nota Global Ponderada (1-10)",
        "Precio Actual", "P.O. Base", "Valor Esperado", "Upside (%)",
        "Dividend Yield (%)", "Retorno Total (%)", "P/E Trailing (x)",
        "P/E Forward (x)", "EV/EBITDA (x)", "P/B (x)",
        "Convicción (1-5)", "Sizing (% NAV)", "VEREDICTO GLOBAL"
    ]
    ws1.append(headers_1)

    for r in records:
        ws1.append([
            r["company_name"], r["country"], r["exchange"], r["ticker"], r["sector"], r["trading_currency"],
            r["revenue_quality_score"], r["moat_score"], r["forensic_health_score"],
            r["operational_efficiency_score"], r["governance_score"],
            r["valuation_asymmetry_score"], r["weighted_total_score"],
            r["current_price"], r["target_price_base"], r["expected_value_price"],
            r["upside_pct"] / 100.0, r["dividend_yield_pct"] / 100.0,
            r["total_expected_return_pct"] / 100.0, r["pe_trailing"], r["pe_forward"],
            r["ev_ebitda"], r["pb_ratio"],
            r["conviction_score"], r["recommended_nav_pct"] / 100.0,
            r["verdict"]
        ])

    ws1.freeze_panes = "B2"
    ws1.auto_filter.ref = ws1.dimensions
    pct_cols, dec_cols, score_cols = {17, 18, 19, 25}, {14, 15, 16, 20, 21, 22, 23}, {7, 8, 9, 10, 11, 12, 13}

    for col_idx in range(1, ws1.max_column + 1):
        cell = ws1.cell(row=1, column=col_idx)
        cell.fill = navy_header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws1.row_dimensions[1].height = 28

    for row_idx in range(2, ws1.max_row + 1):
        ws1.row_dimensions[row_idx].height = 21
        row_fill = zebra_fill if row_idx % 2 == 0 else white_fill
        for col_idx in range(1, ws1.max_column + 1):
            c = ws1.cell(row=row_idx, column=col_idx)
            c.fill = row_fill
            c.font = bold_font if col_idx in {1, 4, 19} | score_cols else reg_font
            c.border = thin_border
            c.alignment = Alignment(
                horizontal="left" if col_idx in (1, 2, 5) else "right" if col_idx in pct_cols | dec_cols else "center",
                vertical="center",
            )
            if col_idx in pct_cols:
                c.number_format = "+0.0%;-0.0%;0.0%"
            elif col_idx in dec_cols:
                c.number_format = "0.00"
            elif col_idx in score_cols:
                c.number_format = '0.00"/10"' if col_idx == 13 else '0.0"/10"'
                try:
                    val_num = float(c.value or 0.0)
                    c.fill = buy_fill if val_num >= 7.5 else (hold_fill if val_num >= 5.5 else sell_fill)
                    c.font = buy_font if val_num >= 7.5 else (hold_font if val_num >= 5.5 else sell_font)
                except Exception:
                    pass
            if col_idx == ws1.max_column:
                val_str = str(c.value or "").upper()
                c.fill = buy_fill if ("COMPRA" in val_str or "ACUMULAR" in val_str) else (sell_fill if "VEND" in val_str else hold_fill)
                c.font = buy_font if ("COMPRA" in val_str or "ACUMULAR" in val_str) else (sell_fill if "VEND" in val_str else hold_font)

    for col in ws1.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        ws1.column_dimensions[get_column_letter(col[0].column)].width = max(max_len + 4, 14)

    wb.save(xlsx_out)
    return xlsx_out


def copy_deliverables_to_consolidated_folders(root_dir: str, company_dirs: List[str]) -> None:
    target_bases = [root_dir]
    parent_dir = os.path.dirname(root_dir)
    if parent_dir and os.path.basename(root_dir).lower() == "reports" and os.path.exists(parent_dir):
        target_bases.append(parent_dir)

    for base in target_bases:
        doc_dir = os.path.join(base, "doc")
        mp3_dir = os.path.join(base, "mp3")
        ppt_dir = os.path.join(base, "ppt")
        os.makedirs(doc_dir, exist_ok=True)
        os.makedirs(mp3_dir, exist_ok=True)
        os.makedirs(ppt_dir, exist_ok=True)
        c_doc = c_mp3 = c_ppt = 0
        for tdir in company_dirs:
            docx_matches = sorted(
                [f for f in glob.glob(os.path.join(tdir, "*_INFORME_INSTITUCIONAL_FINAL*.docx")) if not os.path.basename(f).startswith("~$")],
                key=lambda p: os.path.getmtime(p),
                reverse=True,
            )
            if docx_matches:
                clean_docx_name = os.path.basename(docx_matches[0]).replace("_UPDATED.docx", ".docx")
                shutil.copy2(docx_matches[0], os.path.join(doc_dir, clean_docx_name))
                c_doc += 1
            mp3_matches = sorted(
                [f for f in glob.glob(os.path.join(tdir, "*_PODCAST_COMITE*.mp3")) if not os.path.basename(f).startswith("~$")],
                key=lambda p: os.path.getmtime(p),
                reverse=True,
            )
            if mp3_matches:
                shutil.copy2(mp3_matches[0], os.path.join(mp3_dir, os.path.basename(mp3_matches[0])))
                c_mp3 += 1
            ppt_matches = sorted(
                [f for f in glob.glob(os.path.join(tdir, "*_PRESENTACION_COMITE_*.pptx")) if not os.path.basename(f).startswith("~$")],
                key=lambda p: ("60_SLIDES" in p, os.path.getmtime(p)),
                reverse=True,
            )
            if ppt_matches:
                best_ppt = ppt_matches[0]
                clean_ppt_name = os.path.basename(best_ppt).replace("_UPDATED.pptx", ".pptx")
                if best_ppt.endswith("_UPDATED.pptx"):
                    orig_ppt = os.path.join(tdir, clean_ppt_name)
                    try:
                        shutil.copy2(best_ppt, orig_ppt)
                        os.remove(best_ppt)
                        best_ppt = orig_ppt
                    except OSError:
                        pass
                shutil.copy2(best_ppt, os.path.join(ppt_dir, clean_ppt_name))
                c_ppt += 1
        print(f"[Consolidación] Copiados en {base}: doc={c_doc}, mp3={c_mp3}, ppt={c_ppt}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", type=str, required=True)
    parser.add_argument("--excel-only", action="store_true", help="Generar únicamente el archivo Excel sin copiar entregables doc/mp3/ppt")
    parser.add_argument("--excel-name", type=str, default="RESUMEN_CARTERA_GLOBAL.xlsx", help="Nombre del archivo Excel de salida")
    args = parser.parse_args()

    root_dir = os.path.abspath(args.root_dir)
    records: List[Dict[str, Any]] = []
    company_dirs: List[str] = []
    for entry in sorted(os.listdir(root_dir)):
        if entry in IGNORED_DIRS or entry.startswith("."):
            continue
        full_path = os.path.join(root_dir, entry)
        if os.path.isdir(full_path) and glob.glob(os.path.join(full_path, "*_INFORME_COMITE_FINAL.md")):
            company_dirs.append(full_path)
            rec = collect_company_record(full_path)
            records.append(rec)
            print(f"  [{len(records):02d}] {rec['ticker']:<9} | PAIS: {rec['country']:<16} | Bolsas: {rec['exchange']:<8} | {rec['company_name']}", flush=True)

    if records:
        records.sort(key=lambda r: r.get("total_expected_return_pct", 0.0), reverse=True)
        if args.excel_name == "RESUMEN_CARTERA_GLOBAL.xlsx":
            write_global_markdown(root_dir, records)
        xlsx_out = write_global_excel(root_dir, records, excel_name=args.excel_name)
        print(f"[Excel Global] Generado exitosamente: {xlsx_out} ({len(records)} compañías)", flush=True)
        if not args.excel_only:
            copy_deliverables_to_consolidated_folders(root_dir, company_dirs)


if __name__ == "__main__":
    main()
