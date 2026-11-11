#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_company_ocr_and_market.py
Prepara una carpeta <COMPANY_DIR>:
1. Copia gauntlet_gatekeeper.py, build_podcast_kokoro.py y build_institutional_docx.py desde _shared_engine/
2. Filtra los PDFs aplicando la Regla Institucional de Selección Documental:
   - Lee TODOS los Informes Anuales (Annual Reports) y Prospectos.
   - Lee TODOS los Informes Semestrales/Intermedios (Interim Reports).
   - Lee ÚNICAMENTE el último Informe Trimestral (Quarterly Report más reciente por año y trimestre),
     ignorando todos los informes trimestrales más antiguos.
3. Genera y ejecuta <COMPANY_DIR>/extract_pdfs_paddleocr.py extrayendo los PDFs seleccionados en extracted_ocr_cache/
   y limpiando cualquier transcripción de trimestrales antiguos.
4. Genera un resumen indexado de tablas clave en extracted_ocr_cache/financial_digest.md (y copia en <COMPANY_DIR>/financial_digest.md).
5. Obtiene datos bursátiles e indicadores técnicos en vivo con yfinance en extracted_ocr_cache/market_data_live.json.
"""

import os
import re
import sys
import glob
import json
import time
import shutil
import random
import subprocess
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import pymupdf as fitz
import yfinance as yf
import pandas as pd
import numpy as np


def select_relevant_pdfs(pdf_files: list) -> tuple:
    """
    Filtra la lista de nombres de archivo PDF de una empresa:
    - Conserva TODOS los Informes Anuales (ANNUAL REPORT) y Prospectos (excepto GREEN APPLICATION FORM).
    - Conserva TODOS los Informes Intermedios/Semestrales (INTERIM REPORT).
    - De los Informes Trimestrales (QUARTERLY REPORT / Q1 / Q2 / Q3 / Q4), conserva ÚNICAMENTE
      el del último trimestre disponible (mayor (año, trimestre)), ignorando trimestrales antiguos.
    Devuelve (selected_pdfs, ignored_quarterly_pdfs).
    """
    non_quarterly = []
    quarterly_by_period = {}

    q_regex = re.compile(r"(\d{4})\s*Q([1-4])?\b.*QUARTERLY|\bQ([1-4])\s*(\d{4})\b|(\d{4}).*QUARTERLY\s+REPORT", re.IGNORECASE)

    for f in sorted(pdf_files):
        up = f.upper()
        if "PRESENTACION_COMITE_40_SLIDES" in up or "GREEN APPLICATION FORM" in up:
            continue
        is_quarterly = ("QUARTERLY" in up) or bool(re.search(r"\bQ[1-4]\b", up))
        if is_quarterly and "ANNUAL" not in up and "INTERIM" not in up:
            m_yr = re.search(r"(20\d{2})", up)
            yr = int(m_yr.group(1)) if m_yr else 0
            m_q = re.search(r"\bQ([1-4])\b", up)
            q_num = int(m_q.group(1)) if m_q else 0
            key = (yr, q_num)
            quarterly_by_period.setdefault(key, []).append(f)
        else:
            non_quarterly.append(f)

    selected_quarterly = []
    ignored_quarterly = []
    if quarterly_by_period:
        max_period = max(quarterly_by_period.keys())
        q4_periods = [p for p in quarterly_by_period.keys() if p[1] == 4]
        max_q4_period = max(q4_periods) if q4_periods else None
        for period, files in sorted(quarterly_by_period.items()):
            if period == max_period or (max_q4_period and period == max_q4_period):
                selected_quarterly.extend(files)
            else:
                ignored_quarterly.extend(files)

    selected = sorted(non_quarterly + selected_quarterly)
    return selected, sorted(ignored_quarterly)


EXTRACT_SCRIPT_TEMPLATE = r'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import json
import time
import io
import shutil

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

import pymupdf as fitz
import numpy as np
from PIL import Image

TARGET_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(TARGET_DIR, "extracted_ocr_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

_ocr_engine = None
_ocr_initialized = False

def get_ocr_engine():
    global _ocr_engine, _ocr_initialized
    if _ocr_initialized:
        return _ocr_engine
    _ocr_initialized = True
    try:
        from paddleocr import PaddleOCR
        try:
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
        except Exception:
            try:
                _ocr_engine = PaddleOCR(lang='ch')
            except Exception:
                pass
    except Exception:
        pass
    return _ocr_engine

def run_paddle_on_page(page):
    eng = get_ocr_engine()
    if eng is None:
        return ""
    try:
        pix = page.get_pixmap(dpi=110)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_np = np.array(img)
        res = eng.ocr(img_np)
        lines = []
        if res:
            for block in res:
                if isinstance(block, list):
                    for line in block:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            txt_info = line[1]
                            if isinstance(txt_info, (list, tuple)) and len(txt_info) >= 1:
                                lines.append(str(txt_info[0]))
                elif isinstance(block, dict) and "rec_texts" in block:
                    lines.extend([str(t) for t in block["rec_texts"]])
        return "\n".join(lines)
    except Exception:
        return ""

KEY_DIGEST_PATTERNS = [
    "financial summary", "five year", "five-year", "four year", "financial highlights",
    "consolidated statement of profit", "consolidated income statement",
    "consolidated statement of comprehensive", "consolidated statement of financial position",
    "consolidated balance sheet", "consolidated statement of cash flows",
    "condensed consolidated", "segment information", "operating segment", "disaggregated",
    "trade and bills receivables", "trade receivables", "ageing analysis", "aging analysis",
    "trade and bills payables", "trade payables", "contract liabilities",
    "bank borrowings", "borrowings", "cash and cash equivalents", "pledged bank",
    "dividends", "auditor's remuneration", "auditors' remuneration", "research and development",
    "share award", "share option", "contingent liabilities"
]

def select_relevant_pdfs(pdf_files):
    non_quarterly = []
    quarterly_by_period = {}
    for f in sorted(pdf_files):
        up = f.upper()
        if "PRESENTACION_COMITE_40_SLIDES" in up or "GREEN APPLICATION FORM" in up:
            continue
        is_quarterly = ("QUARTERLY" in up) or bool(re.search(r"\bQ[1-4]\b", up))
        if is_quarterly and "ANNUAL" not in up and "INTERIM" not in up:
            m_yr = re.search(r"(20\d{2})", up)
            yr = int(m_yr.group(1)) if m_yr else 0
            m_q = re.search(r"\bQ([1-4])\b", up)
            q_num = int(m_q.group(1)) if m_q else 0
            key = (yr, q_num)
            quarterly_by_period.setdefault(key, []).append(f)
        else:
            non_quarterly.append(f)

    selected_quarterly = []
    ignored_quarterly = []
    if quarterly_by_period:
        max_period = max(quarterly_by_period.keys())
        q4_periods = [p for p in quarterly_by_period.keys() if p[1] == 4]
        max_q4_period = max(q4_periods) if q4_periods else None
        for period, files in sorted(quarterly_by_period.items()):
            if period == max_period or (max_q4_period and period == max_q4_period):
                selected_quarterly.extend(files)
            else:
                ignored_quarterly.extend(files)

    return sorted(non_quarterly + selected_quarterly), sorted(ignored_quarterly)

def process_all_pdfs():
    all_files = sorted(os.listdir(TARGET_DIR))
    all_pdfs = [
        f for f in all_files
        if f.lower().endswith(".pdf") and "PRESENTACION_COMITE_40_SLIDES" not in f.upper()
    ]
    pdf_files, ignored_pdfs = select_relevant_pdfs(all_pdfs)

    # Eliminar de extracted_ocr_cache los archivos .md/.json de trimestrales antiguos ignorados
    for ign_pdf in ignored_pdfs:
        base_ign = os.path.splitext(ign_pdf)[0].replace(" ", "_")
        for ext in (".md", ".json", "_key_pages.md"):
            stale_path = os.path.join(CACHE_DIR, f"{base_ign}{ext}")
            if os.path.exists(stale_path):
                try:
                    os.remove(stale_path)
                except Exception:
                    pass

    summary_index = {}
    digest_lines = [
        f"# FINANCIAL DIGEST FOR {os.path.basename(TARGET_DIR)}",
        f"# Documentos incluidos (Anuales + Intermedios + Último Trimestral): {', '.join(pdf_files)}",
        f"# Trimestrales antiguos ignorados: {', '.join(ignored_pdfs) if ignored_pdfs else 'Ninguno'}\n"
    ]

    for pdf_name in pdf_files:
        t0 = time.time()
        pdf_path = os.path.join(TARGET_DIR, pdf_name)
        base_name = os.path.splitext(pdf_name)[0].replace(" ", "_")
        md_out = os.path.join(CACHE_DIR, f"{base_name}.md")
        json_out = os.path.join(CACHE_DIR, f"{base_name}.json")

        doc = fitz.open(pdf_path)
        num_pages = len(doc)

        # Si ya existe el .md en cache y no está vacío, reutilizar texto para reconstruir el digest rápidamente
        if os.path.exists(md_out) and os.path.getsize(md_out) > 200:
            pdf_digest_chunks = []
            for idx in range(num_pages):
                text = doc[idx].get_text("text") or ""
                low_text = text.lower()
                if idx < 12 or any(k in low_text for k in KEY_DIGEST_PATTERNS):
                    if len(pdf_digest_chunks) < 65:
                        pdf_digest_chunks.append(f"### [{pdf_name} - Page {idx+1}]\n{text}")
            doc.close()
            if pdf_digest_chunks:
                digest_lines.append(f"\n==================== {pdf_name} ({num_pages} pages) ====================\n")
                digest_lines.extend(pdf_digest_chunks[:45])
            summary_index[pdf_name] = {
                "num_pages": num_pages,
                "md_file": md_out,
                "json_file": json_out,
                "paddle_ocr_pages": 0,
                "elapsed_sec": round(time.time() - t0, 2)
            }
            continue

        md_lines = [f"# DOCUMENT: {pdf_name}\nTotal Pages: {num_pages}\n"]
        pages_data = []
        ocr_count = 0
        pdf_digest_chunks = []

        sample_text_len = sum(len(doc[p].get_text("text") or "") for p in range(min(10, num_pages)))
        is_scanned_pdf = (sample_text_len < 300)

        for idx in range(num_pages):
            page = doc[idx]
            text = page.get_text("text") or ""
            low_text = text.lower()

            ocr_text = ""
            if is_scanned_pdf and len(text.strip()) < 25 and ocr_count < 8:
                ocr_text = run_paddle_on_page(page)
                ocr_count += 1

            combined_text = text
            if ocr_text:
                combined_text += f"\n[OCR p.{idx+1}]:\n" + ocr_text

            md_lines.append(f"\n---\n## PAGE {idx+1}\n{combined_text}")
            pages_data.append({
                "page": idx + 1,
                "text": text,
                "paddle_ocr": ocr_text
            })

            if idx < 12 or any(k in low_text for k in KEY_DIGEST_PATTERNS):
                if len(pdf_digest_chunks) < 65:
                    pdf_digest_chunks.append(f"### [{pdf_name} - Page {idx+1}]\n{text}")

        doc.close()
        with open(md_out, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))
        with open(json_out, "w", encoding="utf-8") as f:
            json.dump({
                "pdf_name": pdf_name,
                "num_pages": num_pages,
                "paddle_ocr_pages_processed": ocr_count,
                "pages": pages_data
            }, f, ensure_ascii=False)

        if pdf_digest_chunks:
            digest_lines.append(f"\n==================== {pdf_name} ({num_pages} pages) ====================\n")
            digest_lines.extend(pdf_digest_chunks[:45])

        summary_index[pdf_name] = {
            "num_pages": num_pages,
            "md_file": md_out,
            "json_file": json_out,
            "paddle_ocr_pages": ocr_count,
            "elapsed_sec": round(time.time() - t0, 2)
        }
        print(f"  -> Extracted {pdf_name} ({num_pages} pages) in {round(time.time() - t0, 1)}s", flush=True)

    with open(os.path.join(CACHE_DIR, "index.json"), "w", encoding="utf-8") as f:
        json.dump(summary_index, f, ensure_ascii=False, indent=2)

    digest_path = os.path.join(CACHE_DIR, "financial_digest.md")
    with open(digest_path, "w", encoding="utf-8") as f:
        f.write("\n".join(digest_lines))
    try:
        shutil.copyfile(digest_path, os.path.join(TARGET_DIR, "financial_digest.md"))
    except Exception:
        pass

if __name__ == "__main__":
    process_all_pdfs()
'''


def fetch_live_market_data(ticker: str, cache_dir: str) -> dict:
    padded_ticker = ticker.strip()
    if padded_ticker.upper().endswith(".HK"):
        num_part = padded_ticker.split(".")[0]
        if num_part.isdigit() and len(num_part) < 4:
            padded_ticker = num_part.zfill(4) + ".HK"
    elif padded_ticker.isdigit():
        padded_ticker = padded_ticker.zfill(4) + ".HK"

    candidates = [padded_ticker, ticker.strip()]
    try:
        search_res = yf.Search(ticker, max_results=3)
        for q in getattr(search_res, "quotes", []) or []:
            sym = q.get("symbol")
            if sym and sym not in candidates:
                candidates.append(sym)
    except Exception:
        pass

    market_info = {
        "ticker": padded_ticker,
        "yf_ticker": padded_ticker,
        "symbol": padded_ticker,
        "country": "N/D",
        "exchange": "N/D",
        "fullExchangeName": "N/D",
    }
    for tk_try in candidates:
        try:
            t = yf.Ticker(tk_try)
            info = t.info or {}
            hist = t.history(period="2y")
            if not hist.empty or info.get("symbol"):
                yf_symbol = info.get("symbol") or tk_try
                yf_country = info.get("country") or info.get("region") or "N/D"
                yf_exchange = info.get("fullExchangeName") or info.get("exchange") or "N/D"
                market_info.update({
                    "ticker": yf_symbol,
                    "yf_ticker": yf_symbol,
                    "symbol": yf_symbol,
                    "yf_verified": True,
                    "country": yf_country,
                    "exchange": yf_exchange,
                    "exchange_code": info.get("exchange") or yf_exchange,
                    "fullExchangeName": yf_exchange,
                    "shortName": info.get("shortName") or info.get("longName") or yf_symbol,
                    "longName": info.get("longName") or info.get("shortName") or yf_symbol,
                    "sector": info.get("sector") or "Industrial / Tech",
                    "industry": info.get("industry") or "Equity",
                    "currency": info.get("currency") or "HKD",
                    "financialCurrency": info.get("financialCurrency") or info.get("currency") or "CNY",
                })
            if not hist.empty:
                close = hist["Close"]
                vol = hist["Volume"]
                high = hist["High"]
                low = hist["Low"]
                mm50 = float(close.rolling(50).mean().iloc[-1]) if len(close) >= 50 else float(close.mean())
                mm200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else float(close.mean())
                delta = close.diff()
                gain = (delta.where(delta > 0, 0)).rolling(14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
                rs = gain / loss
                rsi14 = float((100 - (100 / (1 + rs))).iloc[-1]) if len(close) >= 15 else 50.0
                ema12 = close.ewm(span=12, adjust=False).mean()
                ema26 = close.ewm(span=26, adjust=False).mean()
                macd_line = ema12 - ema26
                signal_line = macd_line.ewm(span=9, adjust=False).mean()
                tr1 = high - low
                tr2 = (high - close.shift()).abs()
                tr3 = (low - close.shift()).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr14 = float(tr.rolling(14).mean().iloc[-1]) if len(close) >= 15 else 0.1
                w52_high = float(high.tail(252).max())
                w52_low = float(low.tail(252).min())
                last_price = float(close.iloc[-1])
                last_date = str(hist.index[-1].date())
                adtv_shares = float(vol.tail(30).mean())
                adtv_val_m = float((vol.tail(30) * close.tail(30)).mean() / 1e6)
                monthly_closes = {str(k.date()): round(float(v), 2) for k, v in close.resample("ME").last().tail(13).items()}

                div_yield = info.get("dividendYield")
                if div_yield and div_yield < 1.0:
                    div_yield_pct = round(div_yield * 100.0, 2)
                elif div_yield:
                    div_yield_pct = round(float(div_yield), 2)
                else:
                    div_yield_pct = 0.0

                insiders_pct = round(float(info.get("heldPercentInsiders") or 0.0) * 100.0, 2)
                inst_pct = round(float(info.get("heldPercentInstitutions") or 0.0) * 100.0, 2)

                # Normalización determinista de divisas en ADRs / Dual-Currency (ej. USD vs CNY/IDR/GBp)
                trade_cur = str(info.get("currency") or "USD").strip()
                fin_cur = str(info.get("financialCurrency") or trade_cur).strip()
                fx_fin_to_trade = 1.0
                if trade_cur.upper() != fin_cur.upper():
                    if trade_cur == "GBp" and fin_cur.upper() == "GBP":
                        fx_fin_to_trade = 100.0
                    elif trade_cur.upper() == "GBP" and fin_cur == "GBp":
                        fx_fin_to_trade = 0.01
                    else:
                        t_up = "GBP" if trade_cur == "GBp" else trade_cur.upper()
                        f_up = "CNY" if fin_cur.upper() in ("RMB", "CNH") else fin_cur.upper()
                        fx_fallbacks = {
                            ("CNY", "USD"): 0.138, ("IDR", "USD"): 0.000063, ("HKD", "USD"): 0.128,
                            ("JPY", "USD"): 0.0065, ("EUR", "USD"): 1.08, ("GBP", "USD"): 1.27,
                            ("BRL", "USD"): 0.18, ("KRW", "USD"): 0.00073, ("TWD", "USD"): 0.031,
                            ("INR", "USD"): 0.012, ("MXN", "USD"): 0.050, ("CAD", "USD"): 0.72,
                        }
                        fx_fin_to_trade = fx_fallbacks.get((f_up, t_up), 1.0)
                        try:
                            fx_hist = yf.Ticker(f"{f_up}{t_up}=X").history(period="5d")
                            if not fx_hist.empty:
                                fx_fin_to_trade = float(fx_hist["Close"].iloc[-1])
                            else:
                                fx_inv = yf.Ticker(f"{t_up}{f_up}=X").history(period="5d")
                                if not fx_inv.empty and float(fx_inv["Close"].iloc[-1]) > 0:
                                    fx_fin_to_trade = 1.0 / float(fx_inv["Close"].iloc[-1])
                        except Exception:
                            pass
                        if trade_cur == "GBp" and t_up == "GBP":
                            fx_fin_to_trade *= 100.0

                mcap_raw = float(info.get("marketCap") or 0.0)
                ev_raw = float(info.get("enterpriseValue") or 0.0)
                tcash_raw = float(info.get("totalCash") or 0.0)
                tdebt_raw = float(info.get("totalDebt") or 0.0)
                fcf_raw = info.get("freeCashflow")
                ocf_raw = info.get("operatingCashflow")
                ebitda_raw = float(info.get("ebitda") or 0.0)
                rev_raw = float(info.get("totalRevenue") or 0.0)

                ev_ebitda_clean = round(float(info.get("enterpriseToEbitda") or 0.0), 2)
                ev_rev_clean = round(float(info.get("enterpriseToRevenue") or 0.0), 2)
                ev_clean_trade = int(ev_raw) if ev_raw else None

                # Si la divisa bursátil difiere de la contable, recalcular EV y múltiplos en moneda homogénea
                if trade_cur.upper() != fin_cur.upper() and fx_fin_to_trade > 0 and mcap_raw > 0:
                    mcap_in_Trade = mcap_raw / 100.0 if trade_cur == "GBp" and mcap_raw > 1e10 else mcap_raw
                    ev_calc_trade = mcap_in_Trade + (tdebt_raw - tcash_raw) * fx_fin_to_trade
                    if ev_calc_trade > 0:
                        ev_clean_trade = int(round(ev_calc_trade))
                        ev_in_fin = ev_calc_trade / fx_fin_to_trade
                        if ebitda_raw > 0:
                            ev_ebitda_clean = round(ev_in_fin / ebitda_raw, 2)
                        if rev_raw > 0:
                            ev_rev_clean = round(ev_in_fin / rev_raw, 2)

                currency_note = (
                    f"Cotización y MarketCap en {trade_cur}; magnitudes de balance/flujos (totalCash, totalDebt, FCF, OCF) reportadas en {fin_cur}"
                    + (f" (tipo de cambio aplicado: 1 {fin_cur} = {fx_fin_to_trade:.5f} {trade_cur}; múltiplos EV/EBITDA y EV/Ventas ya normalizados a divisa homogénea)." if trade_cur.upper() != fin_cur.upper() else ".")
                )

                raw_beta = info.get("beta")
                raw_beta_f = round(float(raw_beta), 2) if raw_beta is not None else None
                exch_up = str(info.get("exchange") or market_info.get("exchange") or "").upper()
                is_otc = any(k in exch_up for k in ("PNK", "OTC", "PINK"))
                if raw_beta_f is None or raw_beta_f < 0.35 or raw_beta_f > 3.0 or (is_otc and raw_beta_f < 0.60):
                    adj_beta = 0.95 if is_otc else 1.00
                    beta_note = (
                        f"Beta cruda yFinance ({raw_beta_f}) distorsionada por baja correlación/liquidez OTC ({exch_up}); "
                        f"se aplica beta sectorial ajustada ({adj_beta:.2f}) para CAPM/WACC."
                    )
                else:
                    adj_beta = raw_beta_f
                    beta_note = "Beta de mercado estadísticamente representativa."

                market_info.update({
                    "last_date": last_date,
                    "current_price": round(last_price, 2),
                    "currentPrice": round(last_price, 2),
                    "marketCap": info.get("marketCap"),
                    "enterpriseValue": ev_clean_trade,
                    "sharesOutstanding": info.get("sharesOutstanding"),
                    "floatShares": info.get("floatShares"),
                    "pe_trailing": round(float(info.get("trailingPE") or 0.0), 2),
                    "pe_forward": round(float(info.get("forwardPE") or 0.0), 2),
                    "pb_ratio": round(float(info.get("priceToBook") or 0.0), 2),
                    "ev_ebitda": ev_ebitda_clean,
                    "ev_revenue": ev_rev_clean,
                    "dividend_yield_pct": div_yield_pct,
                    "beta": adj_beta,
                    "beta_raw_yfinance": raw_beta_f,
                    "beta_adjusted_wacc": adj_beta,
                    "beta_adjustment_note": beta_note,
                    "52WeekHigh": round(w52_high, 2),
                    "52WeekLow": round(w52_low, 2),
                    "MM50": round(mm50, 2),
                    "MM200": round(mm200, 2),
                    "RSI14": round(rsi14, 2),
                    "MACD": round(float(macd_line.iloc[-1]), 4),
                    "MACD_Signal": round(float(signal_line.iloc[-1]), 4),
                    "ATR14": round(atr14, 3),
                    "ADTV_shares_30d": int(adtv_shares),
                    "ADTV_currency_m_30d": round(adtv_val_m, 2),
                    "monthly_closes_12m": monthly_closes,
                    # Sell-Side Consensus & Ownership (Estrategia 2: 0-Token Pre-Extraction)
                    "targetMeanPrice": info.get("targetMeanPrice"),
                    "targetMedianPrice": info.get("targetMedianPrice"),
                    "targetHighPrice": info.get("targetHighPrice"),
                    "targetLowPrice": info.get("targetLowPrice"),
                    "recommendationKey": info.get("recommendationKey") or "N/D",
                    "recommendationMean": info.get("recommendationMean"),
                    "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions") or 0,
                    "heldPercentInsiders_pct": insiders_pct,
                    "heldPercentInstitutions_pct": inst_pct,
                    "shortRatio": info.get("shortRatio"),
                    "shortPercentOfFloat": info.get("shortPercentOfFloat"),
                    "financial_figures_currency": fin_cur,
                    "fx_rate_financial_to_trading": round(fx_fin_to_trade, 6),
                    "currency_normalization_note": currency_note,
                    "totalCash": info.get("totalCash"),
                    "totalDebt": info.get("totalDebt"),
                    "freeCashflow": fcf_raw,
                    "operatingCashflow": ocf_raw,
                    "totalCash_trading_ccy": int(round(tcash_raw * fx_fin_to_trade)) if tcash_raw else None,
                    "totalDebt_trading_ccy": int(round(tdebt_raw * fx_fin_to_trade)) if tdebt_raw else None,
                    "returnOnEquity": info.get("returnOnEquity"),
                    "returnOnAssets": info.get("returnOnAssets"),
                    "revenueGrowth": info.get("revenueGrowth"),
                    "earningsGrowth": info.get("earningsGrowth"),
                    "businessSummary": (info.get("longBusinessSummary") or "")[:1800],
                })
                # Extraer noticias de yFinance si están disponibles
                yf_news_items = []
                try:
                    raw_news = getattr(t, "news", None) or []
                    for item in raw_news[:10]:
                        if isinstance(item, dict):
                            content_obj = item.get("content") if isinstance(item.get("content"), dict) else item
                            title = content_obj.get("title") or item.get("title") or ""
                            pub_time = (
                                content_obj.get("pubDate")
                                or content_obj.get("providerPublishTime")
                                or item.get("providerPublishTime")
                                or ""
                            )
                            if isinstance(pub_time, (int, float)) and pub_time > 1e8:
                                pub_time = time.strftime("%Y-%m-%d", time.gmtime(pub_time))
                            publisher = ""
                            prov = content_obj.get("provider") or item.get("publisher")
                            if isinstance(prov, dict):
                                publisher = prov.get("displayName") or ""
                            elif isinstance(prov, str):
                                publisher = prov
                            summary = content_obj.get("summary") or content_obj.get("description") or ""
                            if title:
                                yf_news_items.append({
                                    "date": str(pub_time)[:10],
                                    "publisher": publisher or "Yahoo Finance",
                                    "title": title.strip(),
                                    "summary": str(summary).strip()[:280],
                                })
                except Exception:
                    pass
                market_info["recent_news"] = yf_news_items
                break
        except Exception as e:
            print(f"  [yfinance warn] {tk_try}: {e}", flush=True)

    # Complementar con Google News RSS (0 tokens LLM, timeout corto de 4s) para Módulos 14 y 15
    rss_news_items = []
    try:
        import urllib.parse
        import urllib.request
        import xml.etree.ElementTree as ET
        q_name = market_info.get("shortName") or market_info.get("longName") or padded_ticker
        q_str = urllib.parse.quote(f"{q_name} {padded_ticker} stock")
        rss_url = f"https://news.google.com/rss/search?q={q_str}&hl=en-US&gl=US&ceid=US:en"
        req = urllib.request.Request(rss_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4.0) as resp:
            xml_bytes = resp.read()
        root_el = ET.fromstring(xml_bytes)
        for item_el in root_el.findall(".//item")[:10]:
            t_el = item_el.find("title")
            d_el = item_el.find("pubDate")
            s_el = item_el.find("source")
            if t_el is not None and t_el.text:
                rss_news_items.append({
                    "date": (d_el.text or "")[:16] if d_el is not None else "",
                    "publisher": (s_el.text or "Google News") if s_el is not None else "Google News",
                    "title": t_el.text.strip(),
                })
    except Exception:
        pass
    if rss_news_items:
        existing_titles = {n.get("title", "").lower()[:40] for n in market_info.get("recent_news", [])}
        for rn in rss_news_items:
            if rn["title"].lower()[:40] not in existing_titles:
                market_info.setdefault("recent_news", []).append(rn)

    out_market = os.path.join(cache_dir, "market_data_live.json")
    with open(out_market, "w", encoding="utf-8") as f:
        json.dump(market_info, f, ensure_ascii=False, indent=2)

    # Generar web_research_digest.md determinista en Fase 0 (Estrategia 2: ahorra 3-5 pasos de search_web por subagente)
    try:
        cur = market_info.get("currency") or "USD"
        cp = market_info.get("current_price") or "N/D"
        t_mean = market_info.get("targetMeanPrice") or "N/D"
        t_med = market_info.get("targetMedianPrice") or "N/D"
        t_high = market_info.get("targetHighPrice") or "N/D"
        t_low = market_info.get("targetLowPrice") or "N/D"
        rec_key = str(market_info.get("recommendationKey") or "N/D").upper()
        n_analysts = market_info.get("numberOfAnalystOpinions") or 0
        ins_pct = market_info.get("heldPercentInsiders_pct", 0.0)
        inst_pct = market_info.get("heldPercentInstitutions_pct", 0.0)
        short_r = market_info.get("shortRatio") or "N/D"

        web_lines = [
            f"# DOSSIER PRE-EXTRAÍDO DE MERCADO, CONSENSO SELL-SIDE Y NOTICIAS RECIENTES (0 TOKENS) — {market_info.get('longName', padded_ticker)} ({padded_ticker})",
            "",
            "## 1. CONSENSO DE ANALISTAS SELL-SIDE Y PRECIO OBJETIVO (YFINANCE LIVE)",
            f"- **Precio Actual de Cotización:** {cp} {cur} (Fecha corte: {market_info.get('last_date', 'N/D')})",
            f"- **Recomendación de Consenso Sell-Side:** `{rec_key}` (Nº de analistas en cobertura: `{n_analysts}`)",
            f"- **Precio Objetivo Medio (Target Mean):** `{t_mean}` {cur} | **Mediana:** `{t_med}` {cur}",
            f"- **Rango de Precios Objetivo Sell-Side:** Mínimo `{t_low}` {cur} — Máximo `{t_high}` {cur}",
            f"- **Múltiplos en Vivo:** PER Trailing `{market_info.get('pe_trailing', 'N/D')}x` | PER Forward `{market_info.get('pe_forward', 'N/D')}x` | P/B `{market_info.get('pb_ratio', 'N/D')}x` | EV/EBITDA `{market_info.get('ev_ebitda', 'N/D')}x` | EV/Ventas `{market_info.get('ev_revenue', 'N/D')}x` | Dividend Yield `{market_info.get('dividend_yield_pct', 0.0)}%`",
            "",
            "## 2. ESTRUCTURA ACCIONARIAL, INSIDERS Y LIQUIDEZ BURSÁTIL",
            f"- **Participación de Insiders (% Held by Insiders):** `{ins_pct}%`",
            f"- **Participación Institucional (% Held by Institutions):** `{inst_pct}%`",
            f"- **Short Ratio (Days to Cover):** `{short_r}` | **ADTV 30 días:** `{market_info.get('ADTV_currency_m_30d', 'N/D')}M {cur}` ({market_info.get('ADTV_shares_30d', 'N/D')} acciones/día)",
            f"- **Indicadores Técnicos Clave:** MM50 `{market_info.get('MM50', 'N/D')}` | MM200 `{market_info.get('MM200', 'N/D')}` | RSI(14) `{market_info.get('RSI14', 'N/D')}` | MACD `{market_info.get('MACD', 'N/D')}` (Señal `{market_info.get('MACD_Signal', 'N/D')}`) | ATR(14) `{market_info.get('ATR14', 'N/D')}` | Rango 52 Semanas `{market_info.get('52WeekLow', 'N/D')} - {market_info.get('52WeekHigh', 'N/D')}`",
            "",
            "## 3. DESCRIPCIÓN CORPORATIVA OFICIAL Y PERFIL DE NEGOCIO",
            market_info.get("businessSummary") or "Ver memoria anual en micro-pack.",
            "",
            "## 4. CRONOLOGÍA DE NOTICIAS Y HECHOS RELEVANTES RECIENTES (2025–2026)",
        ]
        news_list = market_info.get("recent_news") or []
        if news_list:
            for idx_n, n_item in enumerate(news_list[:15], 1):
                dt_str = n_item.get("date") or "2025/2026"
                pub_str = n_item.get("publisher") or "Prensa Financiera"
                tit_str = n_item.get("title") or ""
                sum_str = n_item.get("summary") or ""
                line_n = f"{idx_n}. **[{dt_str}] ({pub_str})** — {tit_str}"
                if sum_str:
                    line_n += f": {sum_str}"
                web_lines.append(line_n)
        else:
            web_lines.append("- Sin titulares RSS adicionales; utilizar los hechos relevantes del último informe anual/intermedio/trimestral.")

        web_md_content = "\n".join(web_lines) + "\n"
        with open(os.path.join(cache_dir, "web_research_digest.md"), "w", encoding="utf-8") as fw:
            fw.write(web_md_content)
        company_root_dir = os.path.dirname(cache_dir)
        with open(os.path.join(company_root_dir, "web_research_digest.md"), "w", encoding="utf-8") as fw2:
            fw2.write(web_md_content)
    except Exception as e_web:
        print(f"  [web_digest warn] {padded_ticker}: {e_web}", flush=True)

    yf_ticker_final = market_info.get("symbol") or market_info.get("yf_ticker") or padded_ticker
    clean_name = re.sub(r"[^A-Za-z0-9]+", "_", (market_info.get("longName") or yf_ticker_final).upper()).strip("_")
    for suffix in ["_LIMITED", "_LTD", "_INC", "_CORP", "_CORPORATION", "_COMPANY", "_CO"]:
        if clean_name.endswith(suffix) and len(clean_name) > len(suffix) + 4:
            clean_name = clean_name[:-len(suffix)]
    file_prefix = f"{clean_name}_{ticker}"

    meta_path = os.path.join(cache_dir, "company_meta.json")
    existing_meta = {}
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing_meta = json.load(f)
        except Exception:
            existing_meta = {}

    meta = {
        **existing_meta,
        "company_name": market_info.get("longName") or existing_meta.get("company_name") or yf_ticker_final,
        "clean_company_name": clean_name,
        "primary_ticker": yf_ticker_final,
        "ticker": yf_ticker_final,
        "country": market_info.get("country") or existing_meta.get("country") or "N/D",
        "exchange": market_info.get("fullExchangeName") or market_info.get("exchange") or existing_meta.get("exchange") or "N/D",
        "file_prefix": existing_meta.get("file_prefix") or file_prefix,
        "sector": f"{market_info.get('sector', '')} / {market_info.get('industry', '')}".strip(" /"),
        "reporting_currency": market_info.get("financialCurrency") or existing_meta.get("reporting_currency") or "RMB",
        "trading_currency": market_info.get("currency") or existing_meta.get("trading_currency") or "HKD",
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return meta


def prepare_company(company_dir: str, shared_engine_dir: str, force: bool = False, skip_market_if_exists: bool = False):
    company_dir = os.path.abspath(company_dir)
    ticker = os.path.basename(company_dir)
    print(f"=== Preparing {ticker} ({company_dir}) ===", flush=True)

    for script_name in ("gauntlet_gatekeeper.py", "build_podcast_kokoro.py", "build_institutional_docx.py"):
        src = os.path.join(shared_engine_dir, script_name)
        if os.path.exists(src):
            shutil.copyfile(src, os.path.join(company_dir, script_name))

    cache_dir = os.path.join(company_dir, "extracted_ocr_cache")
    os.makedirs(cache_dir, exist_ok=True)

    extract_py = os.path.join(company_dir, "extract_pdfs_paddleocr.py")
    with open(extract_py, "w", encoding="utf-8") as f:
        f.write(EXTRACT_SCRIPT_TEMPLATE)

    all_pdfs = [f for f in os.listdir(company_dir) if f.lower().endswith(".pdf") and "PRESENTACION_COMITE_40_SLIDES" not in f.upper()]
    selected_pdfs, ignored_pdfs = select_relevant_pdfs(all_pdfs)

    # Limpiar siempre trimestrales antiguos de extracted_ocr_cache/ y actualizar index.json / financial_digest.md
    subprocess.run([sys.executable, extract_py], check=True)
    print(f"  -> Selected PDFs ({len(selected_pdfs)} kept, {len(ignored_pdfs)} old quarterlies ignored)", flush=True)

    if skip_market_if_exists and os.path.exists(os.path.join(cache_dir, "market_data_live.json")) and os.path.exists(os.path.join(cache_dir, "company_meta.json")):
        with open(os.path.join(cache_dir, "company_meta.json"), "r", encoding="utf-8-sig") as f:
            meta = json.load(f)
    else:
        meta = fetch_live_market_data(ticker, cache_dir)
    print(f"  -> Market data & meta ready: {meta.get('company_name')} -> FILE_PREFIX={meta.get('file_prefix')}", flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root-dir", type=str, default=".")
    parser.add_argument("--target-dir", "--company-dir", dest="company_dir", type=str, default="", help="Procesar una única carpeta de empresa")
    parser.add_argument("--tickers", nargs="*", default=[])
    parser.add_argument("--force", action="store_true", help="Forzar re-extracción de PDFs y datos de mercado")
    parser.add_argument("--skip-market-if-exists", action="store_true", help="No volver a consultar yFinance si market_data_live.json ya existe")
    parser.add_argument("--workers", type=int, default=4, help="Número de empresas a procesar en paralelo concurrente")
    args = parser.parse_args()

    if args.company_dir:
        cdir = os.path.abspath(args.company_dir)
        shared_dir = os.path.join(os.path.dirname(cdir), "_shared_engine")
        prepare_company(cdir, shared_dir, force=args.force, skip_market_if_exists=args.skip_market_if_exists)
        return

    root_dir = os.path.abspath(args.root_dir)
    shared_dir = os.path.join(root_dir, "_shared_engine")
    ignored = {"_shared_engine", ".git", "__pycache__", ".venv", "venv", "node_modules", "kokoro_models", "doc", "mp3", "ppt"}

    targets = args.tickers if args.tickers else sorted([
        d for d in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, d)) and d not in ignored and not d.startswith(".")
    ])

    valid_dirs = [os.path.join(root_dir, tk) for tk in targets if os.path.isdir(os.path.join(root_dir, tk))]

    if not valid_dirs:
        print(f"No se encontraron carpetas de empresa en {root_dir}")
        return

    workers = max(1, min(args.workers, len(valid_dirs)))
    print(f"=== Procesando {len(valid_dirs)} empresas con {workers} worker(s) en paralelo concurrente ===", flush=True)

    def _worker_task(cdir):
        try:
            time.sleep(random.uniform(0.05, 0.35))
            prepare_company(cdir, shared_dir, force=args.force, skip_market_if_exists=args.skip_market_if_exists)
            return (cdir, True, None)
        except Exception as e:
            return (cdir, False, str(e))

    if workers == 1:
        for cdir in valid_dirs:
            _worker_task(cdir)
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_worker_task, cdir): cdir for cdir in valid_dirs}
            for fut in as_completed(futures):
                cdir, ok, err = fut.result()
                tk = os.path.basename(cdir)
                if ok:
                    print(f"  [PARALLEL OK] Completada preparación de {tk}", flush=True)
                else:
                    print(f"  [PARALLEL ERROR] Error en preparación de {tk}: {err}", flush=True)


if __name__ == "__main__":
    main()
