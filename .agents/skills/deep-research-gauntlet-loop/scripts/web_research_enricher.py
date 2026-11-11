#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
web_research_enricher.py — Motor de Búsqueda Activa en Internet (DuckDuckGo + yfinance Peers + Web Scraping).
Complementa los PDFs locales extrayendo de Internet:
1. Últimas noticias corporativas y regulatorias (2025-2026 y últimos 90 días) en inglés y chino.
2. Catalizadores futuros (Corto, Medio y Largo plazo), TAM/SAM/SOM y CAGR sectorial.
3. Reputación laboral (Glassdoor / Kanzhun 看准网 / Maimai 脉脉) y sentimiento en foros (Xueqiu 雪球 / Eastmoney).
4. Consenso de analistas Sell-Side y precios objetivo actuales.
5. Datos en vivo y múltiplos de los 4 a 5 competidores cotizados reales (peers).
Guarda el resultado en <COMPANY_DIR>/extracted_ocr_cache/web_research_cache.json.
"""

import os
import sys
import json
import argparse
from datetime import datetime
import yfinance as yf


def fetch_peers_live(peer_tickers):
    peers_data = {}
    for tk in peer_tickers:
        try:
            t = yf.Ticker(tk)
            info = t.info or {}
            peers_data[tk] = {
                "ticker": tk,
                "name": info.get("longName") or info.get("shortName") or tk,
                "currency": info.get("currency"),
                "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
                "market_cap": info.get("marketCap"),
                "enterprise_value": info.get("enterpriseValue"),
                "pe_trailing": info.get("trailingPE"),
                "pe_forward": info.get("forwardPE"),
                "ev_ebitda": info.get("enterpriseToEbitda"),
                "pb_ratio": info.get("priceToBook"),
                "gross_margin_pct": round(float(info.get("grossMargins") or 0.0) * 100.0, 2),
                "ebitda_margin_pct": round(float(info.get("ebitdaMargins") or 0.0) * 100.0, 2),
                "operating_margin_pct": round(float(info.get("operatingMargins") or 0.0) * 100.0, 2),
                "roe_pct": round(float(info.get("returnOnEquity") or 0.0) * 100.0, 2),
                "revenue_growth_pct": round(float(info.get("revenueGrowth") or 0.0) * 100.0, 2),
                "dividend_yield_pct": round(float(info.get("dividendYield") or 0.0) * (100.0 if (info.get("dividendYield") or 0.0) < 1 else 1.0), 2),
            }
        except Exception as e:
            peers_data[tk] = {"ticker": tk, "error": str(e)}
    return peers_data


def run_ddg_queries(company_name: str, ticker: str):
    results = {}
    try:
        from duckduckgo_search import DDGS
        queries = {
            "latest_news_2026": f'"{company_name}" OR "{ticker}" news announcement 2025 2026 HKEX',
            "catalysts_and_outlook": f'"{company_name}" "{ticker}" catalyst target price analyst consensus 2025 2026',
            "tam_sam_sector_cagr": f'"{company_name}" market share TAM CAGR industry report',
            "employer_glassdoor_kanzhun": f'"{company_name}" Glassdoor OR 看准网 OR 脉脉 employee review culture',
            "investor_sentiment_xueqiu": f'"{ticker}" 雪球 OR 东方财富 OR broker target price rating',
        }
        with DDGS() as ddgs:
            for key, q in queries.items():
                try:
                    hits = list(ddgs.text(q, max_results=6))
                    results[key] = [
                        {"title": h.get("title", ""), "href": h.get("href", ""), "body": h.get("body", "")}
                        for h in hits
                    ]
                except Exception as e:
                    results[key] = [{"error": str(e)}]
    except Exception as e:
        results["ddg_error"] = str(e)

    # Also pull yfinance news if available
    try:
        padded = ticker.split(".")[0].zfill(4) + ".HK" if ticker.endswith(".HK") else ticker
        t = yf.Ticker(padded)
        yf_news = t.news or []
        results["yfinance_recent_news"] = [
            {
                "title": n.get("title") or (n.get("content") or {}).get("title"),
                "publisher": n.get("publisher") or ((n.get("content") or {}).get("provider") or {}).get("displayName"),
                "summary": (n.get("content") or {}).get("summary", ""),
            }
            for n in yf_news[:10]
        ]
        # Analyst recommendations / price targets from yfinance
        try:
            info = t.info or {}
            results["yfinance_analyst_targets"] = {
                "targetHighPrice": info.get("targetHighPrice"),
                "targetLowPrice": info.get("targetLowPrice"),
                "targetMeanPrice": info.get("targetMeanPrice"),
                "targetMedianPrice": info.get("targetMedianPrice"),
                "recommendationKey": info.get("recommendationKey"),
                "numberOfAnalystOpinions": info.get("numberOfAnalystOpinions"),
            }
        except Exception:
            pass
    except Exception:
        pass

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-dir", type=str, required=True)
    parser.add_argument("--peers", nargs="*", default=[])
    args = parser.parse_args()

    target_dir = os.path.abspath(args.target_dir)
    cache_dir = os.path.join(target_dir, "extracted_ocr_cache")
    os.makedirs(cache_dir, exist_ok=True)

    meta_path = os.path.join(cache_dir, "company_meta.json")
    meta = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    company_name = meta.get("company_name") or os.path.basename(target_dir)
    ticker = meta.get("primary_ticker") or os.path.basename(target_dir)

    web_data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "company_name": company_name,
        "ticker": ticker,
        "peers_live_data": fetch_peers_live(args.peers) if args.peers else {},
        "web_search_intelligence": run_ddg_queries(company_name, ticker),
    }

    out_path = os.path.join(cache_dir, "web_research_cache.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(web_data, f, ensure_ascii=False, indent=2)
    print(f"[WebResearch] Saved active web intelligence & peers to {out_path}")


if __name__ == "__main__":
    main()
