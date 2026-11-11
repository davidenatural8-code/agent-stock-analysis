#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gauntlet_memory_wiki.py
Conector oficial + Auto-Instalador/Daemon para TencentDB-Agent-Memory (MemoryCore :8420).
- Verifica si el Gateway (http://127.0.0.1:8420/health) está activo.
- Si no está instalado o corriendo, lo instala automáticamente en _shared_engine/
  y levanta el demonio en segundo plano con bloqueo anti-colisión para multi-agente.
- Aplica la regla institucional de selección documental (100% Anuales + 100% Intermedios
  + SOLO último Trimestral) y aísla cada empresa mediante x-tdai-service-id y agent_id.
- Captura por lotes (batch) hacia /v2/conversation/add y búsqueda semántica en /v2/conversation/search.
- Expansión trilingüe (Español / Inglés / Chino) para mercados globales (HKEX, NYSE, SSE, SZSE).
- Espejo SQLite FTS5 BM25 + RRF local para respaldo 100% determinista sin dependencias externas.
"""

import argparse
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

TDAI_HOST = os.environ.get("TDAI_GATEWAY_HOST", "127.0.0.1")
TDAI_PORT = int(os.environ.get("TDAI_GATEWAY_PORT", "8420"))
TDAI_BASE_URL = f"http://{TDAI_HOST}:{TDAI_PORT}"
TDAI_REPO_URL = "https://github.com/TencentCloud/TencentDB-Agent-Memory.git"


# ==============================================================================
# 1. GESTOR DEL DEMONIO E INSTALADOR AUTOMÁTICO DE TENCENTDB-AGENT-MEMORY
# ==============================================================================

def is_daemon_healthy(timeout: float = 1.0) -> bool:
    """Comprueba si el Gateway de TencentDB-Agent-Memory responde en /health."""
    try:
        req = urllib.request.Request(f"{TDAI_BASE_URL}/health", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def resolve_shared_engine_dir(target_dir: Path) -> Path:
    """Localiza ROOT_DIR/_shared_engine/ desde <COMPANY_DIR> o ROOT_DIR."""
    if (target_dir / "_shared_engine").exists():
        return target_dir / "_shared_engine"
    if (target_dir.parent / "_shared_engine").exists():
        return target_dir.parent / "_shared_engine"
    shared = target_dir / "_shared_engine"
    shared.mkdir(parents=True, exist_ok=True)
    return shared


def ensure_tdai_daemon(target_dir: Path) -> bool:
    """
    Garantiza que el demonio MemoryCore (:8420) esté instalado y corriendo.
    Usa un lockfile para evitar condiciones de carrera cuando arrancan 8 subagentes.
    """
    if os.environ.get("GAUNTLET_FAST_FTS5", "1") == "1":
        return False
    if is_daemon_healthy():
        return True

    shared_dir = resolve_shared_engine_dir(target_dir)
    lock_file = shared_dir / "tdai_daemon.lock"
    install_dir = shared_dir / "tencentdb_agent_memory"
    data_dir = shared_dir / "tdai_memory_data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Si otro subagente ya está levantando el demonio, esperar hasta 45s
    if lock_file.exists() and (time.time() - lock_file.stat().st_mtime < 90):
        for _ in range(45):
            time.sleep(1.0)
            if is_daemon_healthy():
                return True

    try:
        lock_file.write_text(str(os.getpid()), encoding="utf-8")

        # 1. Instalar SDK Python oficial si no está presente
        try:
            import tencentdb_agent_memory  # noqa: F401
        except ImportError:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "tencentdb-agent-memory-sdk-python"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        # 2. Clonar e instalar MemoryCore si no existe en _shared_engine
        memory_core_dir = install_dir / "MemoryCore"
        if not memory_core_dir.exists():
            print("[TDAI-DAEMON] Clonando TencentCloud/TencentDB-Agent-Memory...", file=sys.stderr)
            subprocess.run(
                ["git", "clone", "--depth", "1", TDAI_REPO_URL, str(install_dir)],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if memory_core_dir.exists():
                npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
                print("[TDAI-DAEMON] Instalando dependencias Node.js de MemoryCore...", file=sys.stderr)
                subprocess.run(
                    [npm_cmd, "install", "--no-audit", "--no-fund"],
                    cwd=str(memory_core_dir),
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

        # 3. Arrancar el demonio en segundo plano (Node.js tsx server.ts)
        server_entry = memory_core_dir / "src" / "gateway" / "server.ts"
        if server_entry.exists():
            env = os.environ.copy()
            env["TDAI_GATEWAY_HOST"] = TDAI_HOST
            env["TDAI_GATEWAY_PORT"] = str(TDAI_PORT)
            env["TDAI_DATA_DIR"] = str(data_dir)
            env.setdefault("TDAI_LLM_API_KEY", os.environ.get("OPENAI_API_KEY", "local-bm25-only"))
            env.setdefault("TDAI_LLM_BASE_URL", os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))

            log_path = shared_dir / "tdai_gateway.log"
            log_file = open(log_path, "a", encoding="utf-8")

            tsx_cli = memory_core_dir / "node_modules" / "tsx" / "dist" / "cli.mjs"
            if tsx_cli.exists():
                cmd = ["node", str(tsx_cli), "src/gateway/server.ts"]
            else:
                npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
                cmd = [npx_cmd, "tsx", "src/gateway/server.ts"]

            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS if os.name == "nt" else 0
            subprocess.Popen(
                cmd,
                cwd=str(memory_core_dir),
                env=env,
                stdout=log_file,
                stderr=log_file,
                creationflags=creation_flags,
                shell=(os.name == "nt"),
                start_new_session=(os.name != "nt"),
            )

            # Esperar hasta 20 segundos a que /health responda 200 OK
            for _ in range(40):
                time.sleep(0.5)
                if is_daemon_healthy():
                    print(f"[TDAI-DAEMON] Gateway activo en {TDAI_BASE_URL}", file=sys.stderr)
                    return True

    except Exception as exc:
        print(f"[WARN] No se pudo iniciar MemoryCore daemon ({exc}). Usando motor BM25 local.", file=sys.stderr)
    finally:
        if lock_file.exists():
            try:
                lock_file.unlink()
            except OSError:
                pass

    return is_daemon_healthy()


def tdai_http_request(endpoint: str, payload: Dict, service_id: str, timeout: float = 15.0) -> Optional[Dict]:
    """Envía una petición JSON al Gateway :8420 aislada por empresa (x-tdai-service-id y Bearer token)."""
    url = f"{TDAI_BASE_URL}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    api_key = os.environ.get("TDAI_GATEWAY_API_KEY", "tdai-local-token")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "x-tdai-service-id": service_id,
    }

    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="ignore"))
    except Exception:
        return None


# ==============================================================================
# 2. FILTRO DOCUMENTAL INSTITUCIONAL Y TROCEADO DE TABLAS MARKDOWN
# ==============================================================================

def classify_and_filter_ocr_files(ocr_dir: Path) -> List[Tuple[Path, str]]:
    """
    Selecciona: 100% Informes Anuales + 100% Intermedios + ÚNICAMENTE el último Trimestral.
    Incluye soporte para subcarpeta _raw_ocr_archive/ y archivo comprimido _raw_ocr_archive.zip (V3.4).
    """
    archive_dir = ocr_dir / "_raw_ocr_archive"
    archive_zip = ocr_dir / "_raw_ocr_archive.zip"
    if archive_zip.exists() and not archive_dir.exists():
        import zipfile
        try:
            archive_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(archive_zip, "r") as zf:
                zf.extractall(archive_dir)
        except Exception:
            pass
    raw_candidates = list(ocr_dir.glob("*.md"))
    if archive_dir.exists():
        raw_candidates.extend(archive_dir.glob("*.md"))
    by_name = {fp.name: fp for fp in raw_candidates}
    md_files = [by_name[k] for k in sorted(by_name.keys())]
    selected: List[Tuple[Path, str]] = []
    quarterly_candidates: List[Tuple[Tuple[int, int, str], Path]] = []

    for fp in md_files:
        name_lower = fp.name.lower()
        if name_lower in (
            "financial_digest.md", "brief_ppt_podcast.md", "web_research_digest.md",
            "company_facts_pack.md", "m01_m15_digest.md",
            "facts_sa1.md", "facts_sa2.md", "facts_sa3.md", "facts_sa4.md",
        ):
            continue

        years = [int(y) for y in re.findall(r"(20[1-3]\d)", name_lower)]
        year = max(years) if years else 0

        is_quarterly = bool(re.search(r"(quarter|trimestr|\bq[1-4]\b|[1-4]q|3m|9m)", name_lower))
        is_interim = bool(re.search(r"(interim|semestr|half[\s_-]*year|\bh1\b|\b1h\b|6m)", name_lower))
        is_annual = bool(re.search(r"(annual|anual|10-k|20-f|prospectus|folleto)", name_lower))

        if is_quarterly and not is_annual and not is_interim:
            q_match = re.search(r"(?:q([1-4])|([1-4])q)", name_lower)
            q_num = int(q_match.group(1) or q_match.group(2)) if q_match else 1
            quarterly_candidates.append(((year, q_num, fp.name), fp))
        elif is_interim and not is_annual:
            selected.append((fp, "INTERIM"))
        else:
            selected.append((fp, "ANNUAL"))

    if quarterly_candidates:
        quarterly_candidates.sort(key=lambda x: x[0], reverse=True)
        selected.append((quarterly_candidates[0][1], "LATEST_QUARTERLY"))
        # Conservar también el último Q4 si es distinto del último trimestral (contiene cierre FY completo en emisores 6-K)
        q4_cands = [c for c in quarterly_candidates[1:] if c[0][1] == 4]
        if q4_cands:
            selected.append((q4_cands[0][1], "LATEST_QUARTERLY"))

    return selected


def chunk_markdown_document(text: str, doc_name: str, doc_type: str, max_chunk_chars: int = 2400) -> List[Dict[str, str]]:
    lines = text.splitlines()
    chunks: List[Dict[str, str]] = []
    current_title = "Sección general"
    current_lines: List[str] = []
    current_len = 0
    header_regex = re.compile(r"^(#{1,4})\s+(.+)$")

    def flush(title: str, body_lines: List[str]):
        body = "\n".join(body_lines).strip()
        if len(body) >= 40:
            chunks.append({
                "doc_name": doc_name,
                "doc_type": doc_type,
                "section_title": title[:180],
                "content": body,
            })

    for line in lines:
        hdr = header_regex.match(line.strip())
        if hdr:
            if current_lines and current_len >= 300:
                flush(current_title, current_lines)
                current_lines, current_len = [], 0
            current_title = hdr.group(2).strip()

        current_lines.append(line)
        current_len += len(line) + 1
        if current_len >= max_chunk_chars and not line.lstrip().startswith("|"):
            flush(current_title, current_lines)
            overlap = current_lines[-2:] if len(current_lines) >= 2 else []
            current_lines = overlap
            current_len = sum(len(x) + 1 for x in current_lines)

    if current_lines:
        flush(current_title, current_lines)
    return chunks


# ==============================================================================
# 3. INDEXACIÓN Y CONSULTA HÍBRIDA (TENCENTDB GATEWAY + ESPEJO SQLITE FTS5)
# ==============================================================================

BILINGUAL_EXPANSION = {
    "segmentos": ["segments", "revenue", "operating segments", "分部", "主营业务", "行业"],
    "ingresos": ["revenue", "turnover", "sales", "营业收入", "收入"],
    "catalogo": ["products", "services", "portfolio", "brands", "产品", "阴极铜", "铜杆", "铜材", "黄金", "白银", "硫酸"],
    "cobre": ["copper", "铜", "阴极铜", "铜材"],
    "clientes": ["customers", "major customers", "receivables", "主要客户", "前五名客户", "应收账款"],
    "proveedores": ["suppliers", "payables", "procurement", "供应商", "前五名供应商", "应付账款"],
    "leases": ["lease liabilities", "right-of-use", "ifrs 16", "租赁负债", "使用权资产"],
    "contingencias": ["contingent", "litigation", "commitments", "guarantees", "或有事项", "诉讼", "对外担保"],
    "pensiones": ["pension", "defined benefit", "retirement", "辞退福利", "离退休"],
    "recompras": ["repurchase", "buyback", "treasury shares", "股份回购", "回购"],
    "dividendos": ["dividend", "distribution", "利润分配", "分红", "股利"],
    "directiva": ["directors", "remuneration", "compensation", "management", "董监高", "董事", "薪酬"],
    "accionistas": ["shareholders", "substantial shareholders", "ownership", "前十名股东", "股东持股", "控股股东"],
    "deuda": ["borrowings", "bank loans", "bonds", "senior notes", "maturity", "借款", "应付债券", "短期借款", "长期借款"],
    "guidance": ["outlook", "prospects", "guidance", "target", "经营计划", "发展战略", "未来展望"],
    "capex": ["capital expenditure", "additions to property", "pp&e", "资本性支出", "购建固定资产", "在建工程"],
}


def expand_bilingual_tokens(raw_query: str) -> List[str]:
    stopwords = {"de", "la", "el", "en", "y", "a", "los", "del", "por", "para", "con"}
    base_tokens = [
        t for t in re.findall(r"[a-zA-ZáéíóúñÁÉÍÓÚÑ0-9\u4e00-\u9fff]{2,}", raw_query.lower())
        if t not in stopwords
    ]
    expanded = list(base_tokens)
    for t in base_tokens:
        for extra in BILINGUAL_EXPANSION.get(t, []):
            expanded.extend([x.lower() for x in extra.split() if x.strip()])
    return list(dict.fromkeys(expanded))


def build_company_memory(target_dir: Path) -> int:
    ocr_dir = target_dir / "extracted_ocr_cache"
    if not ocr_dir.exists():
        print(f"[ERROR] No existe {ocr_dir}", file=sys.stderr)
        return 1

    daemon_up = ensure_tdai_daemon(target_dir)
    service_id = re.sub(r"[^a-zA-Z0-9_-]", "_", target_dir.name)
    selected_files = classify_and_filter_ocr_files(ocr_dir)

    db_path = ocr_dir / "wiki_bm25.sqlite"
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    cur.execute("""
        CREATE VIRTUAL TABLE wiki_chunks USING fts5(
            doc_name, doc_type, section_title, content,
            tokenize='unicode61 remove_diacritics 2'
        );
    """)

    total_chunks = 0
    tdai_synced = 0

    for fp, doc_type in selected_files:
        raw_text = fp.read_text(encoding="utf-8", errors="ignore")
        chunks = chunk_markdown_document(raw_text, fp.name, doc_type)
        if not chunks:
            continue

        # Inserción determinista en espejo SQLite FTS5
        for ch in chunks:
            cur.execute(
                "INSERT INTO wiki_chunks (doc_name, doc_type, section_title, content) VALUES (?, ?, ?, ?)",
                (ch["doc_name"], ch["doc_type"], ch["section_title"], ch["content"]),
            )
        total_chunks += len(chunks)

        # Captura por lotes (batches) hacia el Gateway TencentDB-Agent-Memory
        if daemon_up:
            batch_size = 35
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                payload = {
                    "session_id": f"{service_id}_{fp.name}_{i//batch_size}",
                    "team_id": "team_gauntlet",
                    "agent_id": service_id,
                    "user_id": "analyst",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"[{c['doc_type']}] {c['doc_name']} :: {c['section_title']}\n{c['content']}",
                        }
                        for c in batch
                    ],
                }
                res = tdai_http_request("/v2/conversation/add", payload, service_id=service_id)
                if res and res.get("code") == 0:
                    tdai_synced += len(batch)

    conn.commit()
    conn.close()
    mode_label = f"TDAI-DAEMON (:8420, synced={tdai_synced}) + FTS5" if daemon_up else "FTS5-LOCAL"
    print(
        f"=== MEMORY WIKI INDEX PASS (EXIT 0) | Motor: {mode_label} "
        f"| Archivos: {len(selected_files)} | Chunks: {total_chunks} ==="
    )
    # Optimización V3: Pre-generar company_facts_pack.md en Fase 0 (0 tokens LLM)
    try:
        build_facts_pack(target_dir)
    except Exception as e:
        print(f"[WARN] No se pudo pre-generar company_facts_pack.md: {e}")
    return 0


def _query_to_string(target_dir: Path, raw_query: str, max_chars: int = 2400, top_k: int = 4, only_recent_years: bool = False) -> str:
    """Versión interna silenciosa de query_company_memory que devuelve el texto para empaquetado.
    Si only_recent_years=True, excluye informes antiguos (< max_year - 1) para evitar mezclar consejeros/comités de 2019-2022 con los actuales."""
    ocr_dir = target_dir / "extracted_ocr_cache"
    db_path = ocr_dir / "wiki_bm25.sqlite"
    if not db_path.exists():
        return ""
    tokens = expand_bilingual_tokens(raw_query)
    if not tokens:
        return ""
    output_blocks: List[str] = []
    used_chars = 0
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    rrf_scores: Dict[int, float] = {}
    chunk_store: Dict[int, Tuple[str, str, str, str]] = {}

    # Determinar el año documental más reciente indexado para filtrar obsolescencia (ej. 2019-2023 cuando existen 2025/2026)
    max_doc_yr = 0
    try:
        doc_names_all = [r[0] for r in cur.execute("SELECT DISTINCT doc_name FROM wiki_chunks;").fetchall()]
        for dn_i in doc_names_all:
            yrs_i = [int(y) for y in re.findall(r"(20[1-3]\d)", dn_i)]
            if yrs_i and max(yrs_i) > max_doc_yr:
                max_doc_yr = max(yrs_i)
    except Exception:
        max_doc_yr = 0

    sub_queries = [tokens[i:i + 4] for i in range(0, min(12, len(tokens)), 4)]
    for q_terms in sub_queries:
        fts_terms = [f'"{t}"' if re.search(r"[\u4e00-\u9fff]", t) else f'"{t}"*' for t in q_terms]
        fts_expr = " OR ".join(fts_terms)
        try:
            rows = cur.execute(
                """
                SELECT rowid, doc_name, doc_type, section_title, content,
                       bm25(wiki_chunks, 1.0, 0.5, 3.5, 1.0) AS score
                FROM wiki_chunks WHERE wiki_chunks MATCH ?
                ORDER BY score ASC LIMIT ?;
                """,
                (fts_expr, top_k * 3),
            ).fetchall()
        except sqlite3.OperationalError:
            continue
        for rank, (rowid, d_name, d_type, s_title, content, _) in enumerate(rows, start=1):
            d_yrs = [int(y) for y in re.findall(r"(20[1-3]\d)", d_name)]
            doc_yr = max(d_yrs) if d_yrs else max_doc_yr
            if only_recent_years and max_doc_yr >= 2024 and doc_yr < (max_doc_yr - 1):
                continue
            yr_boost = 0.45 if "2026" in d_name else (0.35 if "2025" in d_name else (0.15 if "2024" in d_name else -0.25))
            boost = (1.15 if d_type in ("ANNUAL", "LATEST_QUARTERLY") else 1.0) + yr_boost
            rrf_scores[rowid] = rrf_scores.get(rowid, 0.0) + (boost / (30.0 + rank))
            chunk_store[rowid] = (d_name, d_type, s_title, content)
    conn.close()

    for rid in sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]:
        d_name, d_type, s_title, content = chunk_store[rid]
        header = f"\n#### [{d_type}] {d_name} :: {s_title}\n"
        avail = max_chars - used_chars - len(header)
        if avail <= 120:
            break
        snippet = content[:avail] + (" [...]" if len(content) > avail else "")
        block = f"{header}{snippet}\n"
        output_blocks.append(block)
        used_chars += len(block)
    return "".join(output_blocks)


def _build_shared_core_header(target_dir: Path) -> str:
    """
    Construye una cabecera común transversal (~4-6 KB) compartida por facts_sa1..4.md y company_facts_pack.md.
    Evita pérdida de contexto cruzado (escala, caja/deuda, múltiplos en vivo, peers y concentración)
    sin duplicar anexos contables completos en los 4 subagentes.
    """
    ocr_dir = target_dir / "extracted_ocr_cache"
    parts: List[str] = ["## 0.B CABECERA TRANSVERSAL COMPARTIDA (IDENTIDAD, MERCADO EN VIVO Y COMPARABLES)\n"]

    # Detectar todos los años documentales disponibles en los PDFs de la carpeta (incluyendo 2025 y 2026)
    pdf_years = sorted({
        int(m.group(1))
        for p in list(target_dir.glob("*.pdf")) + list(target_dir.glob("*.PDF"))
        for m in re.finditer(r"(20[1-3]\d)", p.name)
    })

    meta_p = ocr_dir / "company_meta.json"
    if meta_p.exists():
        try:
            meta = json.loads(meta_p.read_text(encoding="utf-8", errors="ignore"))
            compact_meta = {
                k: meta.get(k)
                for k in (
                    "company_name", "primary_ticker", "exchange", "country", "currency",
                    "reporting_currency", "sector", "industry", "fiscal_year_end", "file_prefix",
                )
                if meta.get(k) not in (None, "")
            }
            if pdf_years:
                compact_meta["mandatory_years_coverage_in_tables"] = pdf_years
            if meta.get("summary_kpis"):
                compact_meta["summary_kpis"] = meta["summary_kpis"]
            parts.append("### Identidad, años obligatorios y metadatos (`company_meta.json`)\n")
            parts.append(json.dumps(compact_meta, ensure_ascii=False, indent=2)[:1800] + "\n\n")
        except Exception:
            pass

    mkt_p = ocr_dir / "market_data_live.json"
    if mkt_p.exists():
        try:
            mkt = json.loads(mkt_p.read_text(encoding="utf-8", errors="ignore"))
            compact_mkt = {
                k: v for k, v in mkt.items()
                if not isinstance(v, list) or len(v) <= 8
            }
            # Calcular bandas de anclaje deterministas F0 (0 tokens) para converger puntuaciones entre distintos LLMs
            ocf_v = float(mkt.get("operatingCashflow") or 0.0)
            fcf_v = float(mkt.get("freeCashflow") or 0.0)
            tcash_v = float(mkt.get("totalCash") or 0.0)
            tdebt_v = float(mkt.get("totalDebt") or 0.0)
            roe_v = float(mkt.get("returnOnEquity") or 0.0)
            revg_v = float(mkt.get("revenueGrowth") or 0.0)
            qoe_mid = round(max(6.0, min(9.2, 7.8 + (0.5 if (ocf_v > 0 and fcf_v >= ocf_v * 0.45) else 0.0) + (0.3 if revg_v > 0.12 else 0.0))), 1)
            moat_mid = round(max(6.0, min(9.0, 7.4 + (0.4 if roe_v > 0.20 else (0.2 if roe_v > 0.12 else 0.0)) + (0.2 if revg_v > 0.15 else 0.0))), 1)
            bs_mid = round(max(5.8, min(9.2, 8.4 if (tcash_v > tdebt_v * 1.2 and tcash_v > 0) else (6.9 if tdebt_v > tcash_v * 2.0 else 7.8))), 1)
            # Etiquetar explícitamente la divisa contable en los saldos de balance/flujos para impedir el error de rotularlos en USD en ADRs
            t_ccy = str(mkt.get("currency") or "USD").strip()
            f_ccy = str(mkt.get("financial_figures_currency") or mkt.get("financialCurrency") or t_ccy).strip()
            fx_r = float(mkt.get("fx_rate_financial_to_trading") or 1.0)
            if t_ccy.upper() != f_ccy.upper():
                for fld in ("totalCash", "totalDebt", "operatingCashflow", "freeCashflow"):
                    raw_v = mkt.get(fld)
                    if isinstance(raw_v, (int, float)) and raw_v != 0:
                        m_f = raw_v / 1e6
                        m_t = (raw_v * fx_r) / 1e6 if fx_r > 0 else 0.0
                        compact_mkt[fld] = f"{m_f:,.1f}M {f_ccy} (≈ {m_t:,.1f}M {t_ccy} — ¡ATENCIÓN: CIFRA ORIGINAL EN {f_ccy}, NO EN {t_ccy}!)"
            compact_mkt["ANCHOR_SCORES_F0"] = {
                "qoe_2_5_band": f"{round(qoe_mid - 0.3, 1)} - {round(qoe_mid + 0.3, 1)} / 10 (ancla central: {qoe_mid})",
                "moat_2_6_band": f"{round(moat_mid - 0.3, 1)} - {round(moat_mid + 0.3, 1)} / 10 (ancla central: {moat_mid})",
                "forensic_balance_5_5_band": f"{round(bs_mid - 0.3, 1)} - {round(bs_mid + 0.3, 1)} / 10 (ancla central: {bs_mid})",
            }
            parts.append("### Snapshot bursátil, múltiplos, divisas blindadas y anclas F0 (`market_data_live.json`)\n")
            parts.append(json.dumps(compact_mkt, ensure_ascii=False, indent=2)[:2450] + "\n\n")
        except Exception:
            pass

    peers_p = ocr_dir / "peers_market_live.json"
    if peers_p.exists():
        try:
            peers_raw = peers_p.read_text(encoding="utf-8", errors="ignore")
            parts.append("### Comparables cotizados reales (`peers_market_live.json`)\n")
            parts.append(peers_raw[:1850] + "\n\n")
        except Exception:
            pass

    return "".join(parts)


def _extract_high_density_forensic_and_quarterly_digest(ocr_dir: Path, max_chars: int = 2900) -> str:
    """
    Extrae de forma 100% determinista (0 tokens LLM, presupuesto compacto <= 2.9 KB):
    1) Último trimestre disponible (6-K / 10-Q / Q1-Q4),
    2) Auditor independiente (PCAOB / HKICPA), ingresos diferidos (contract liabilities / wallet) y recompras,
    3) Glosario de siglas reales definidas en el 20-F/10-K (evitando confusiones como SOE = Single Origin Espresso).
    """
    skip_jsons = {
        "company_meta.json", "market_data_live.json", "peers_market_live.json",
        "index.json", "forensic_metrics.json", "company_financial_model.json", "slides_deck.json",
        "sa2_forensic.json", "sa3_valuation.json", "sa5_verdict.json",
    }
    json_files = list(ocr_dir.glob("*.json"))
    archive_dir = ocr_dir / "_raw_ocr_archive"
    if archive_dir.exists():
        json_files.extend(archive_dir.glob("*.json"))

    seen_names = set()
    docs: List[Tuple[str, List[Dict]]] = []
    for jf in sorted(json_files, key=lambda x: x.name, reverse=True):
        if jf.name in skip_jsons or jf.name in seen_names:
            continue
        seen_names.add(jf.name)
        try:
            data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
            docs.append((jf.stem, data.get("pages", [])))
        except Exception:
            continue

    q_snippets: List[str] = []
    key_op_snippets: List[str] = []
    sbc_rnd_hits: List[str] = []
    litigation_hits: List[str] = []
    auditor_hits: List[str] = []
    deferred_hits: List[str] = []
    acronym_hits: Dict[str, str] = {}

    acronym_re = re.compile(r'([A-Z][A-Za-z0-9\-\s]{3,42}?)\s*\(\s*["“«]?([A-Z]{2,6})["”»]?\s*\)')
    common_stop_acronyms = {"SEC", "USA", "USD", "RMB", "CNY", "HKD", "GBP", "EUR", "NYSE", "NASDAQ", "GAAP", "IFRS", "PCAOB", "CEO", "CFO", "VIE", "ADR", "ADS"}

    for stem, pages in docs:
        s_low = stem.lower()
        is_recent_25_26 = ("2026" in s_low or "2025" in s_low)
        is_q_or_int = is_recent_25_26 and bool(re.search(r"(\bq[1-4]\b|quarter|interim|6-k|10-q|trimestr|semestr)", s_low))
        for idx, p in enumerate(pages):
            txt = (p.get("text") or "").strip()
            if not txt:
                continue
            pnum = p.get("page_num") or (idx + 1)
            t_low = txt.lower()
            if "pursuant to the requirements of the securities exchange act" in t_low[:260] and len(txt) < 900:
                continue
            # 1) Key Operating Data y Unaudited Statements of Operations (Q2/Q3 2026 y 2025)
            if is_q_or_int and len(key_op_snippets) < 3 and any(k in t_low for k in ("key operating data", "unaudited condensed consolidated statements of operations", "total stores", "monthly transacting customers", "same-store sales")):
                key_op_snippets.append(f"[{stem} P.{pnum}] " + re.sub(r"\s+", " ", txt[:620]))
            elif is_q_or_int and len(q_snippets) < 2 and any(k in t_low for k in ("total net revenues", "operating income", "balance sheet", "ebitda", "production", "kounrad", "sasa")):
                q_snippets.append(f"[{stem} P.{pnum}] " + re.sub(r"\s+", " ", txt[:480]))
            # 2) Consolidated Statements of Operations del último Annual Report (2025)
            if is_recent_25_26 and "annual" in s_low and len(q_snippets) < 3 and ("consolidated statements of operations" in t_low or "results of operations\nthe following table sets forth our consolidated" in t_low):
                q_snippets.append(f"[{stem} P.{pnum}] " + re.sub(r"\s+", " ", txt[:620]))

            for ln in txt.splitlines():
                ls = ln.strip()
                if len(ls) < 12 or len(ls) > 230:
                    continue
                ll = ls.lower()
                if len(auditor_hits) < 2 and any(k in ll for k in ("registered public accounting firm", "independent auditor", "centurion zd", "bdo ", "shu lun pan", "ernst & young", "pricewaterhouse", "deloitte", "kpmg", "pcaob")):
                    auditor_hits.append(f"[{stem} P.{pnum}] {ls}")
                if is_recent_25_26 and len(sbc_rnd_hits) < 4 and any(k in ll for k in ("share-based compensation", "research and development", "product development", "general and administrative")):
                    if re.search(r"\d", ls):
                        sbc_rnd_hits.append(f"[{stem} P.{pnum}] {ls}")
                if is_recent_25_26 and len(litigation_hits) < 4 and any(k in ll for k in ("singapore", "opt-out", "class action", "department of justice", "doj", "ministry of finance", "provisional liquidators", "alvarez & marsal", "145.8", "180.0", "149,")):
                    litigation_hits.append(f"[{stem} P.{pnum}] {ls}")
                if is_recent_25_26 and len(deferred_hits) < 3 and any(k in ll for k in ("deferred revenue", "contract liabilities", "coffee wallet", "vouchers", "unredeemed", "share repurchase", "treasury shares", "senior preferred")):
                    deferred_hits.append(f"[{stem} P.{pnum}] {ls}")
                for m_ac in acronym_re.finditer(ls):
                    full_t, acr = m_ac.group(1).strip(), m_ac.group(2).strip()
                    if acr not in common_stop_acronyms and acr not in acronym_hits and len(acronym_hits) < 10:
                        if len(full_t.split()) >= 2:
                            acronym_hits[acr] = full_t

    lines_out = []
    if key_op_snippets:
        lines_out.append("- **KPIs Operativos Trimestrales y P&L Condensado (`KEY OPERATING DATA` 2025–2026):** " + " // ".join(key_op_snippets))
    if q_snippets:
        lines_out.append("- **Cierres de Cuenta de Resultados (`CONSOLIDATED STATEMENTS OF OPERATIONS` 2025 y Q2/Q3 2026):** " + " // ".join(q_snippets))
    if sbc_rnd_hits:
        lines_out.append("- **Compensación en Acciones (`SBC`) e I+D (`G&A / Nota 15`):** " + " | ".join(dict.fromkeys(sbc_rnd_hits)))
    if litigation_hits:
        lines_out.append("- **Contingencias Legales Vivas (Singapur, DOJ/MOF, Liquidadores JPLs y SEC):** " + " | ".join(dict.fromkeys(litigation_hits)))
    if auditor_hits:
        lines_out.append("- **Auditoría / Control Interno (`PCAOB`):** " + " | ".join(dict.fromkeys(auditor_hits)))
    if deferred_hits:
        lines_out.append("- **Ingresos Diferidos (Wallet/Contract Liabilities), Recompras y Preferentes:** " + " | ".join(dict.fromkeys(deferred_hits)))
    if acronym_hits:
        acr_str = "; ".join(f"`{k}` = {v}" for k, v in acronym_hits.items())
        lines_out.append(f"- **Glosario de Siglas Oficiales del Reporte (usar definición exacta):** {acr_str}")

    res = "\n".join(lines_out)
    return (res[:max_chars] + "\n") if res else ""


def _extract_prioritized_financial_pages(ocr_dir: Path, keywords: Tuple[str, ...], max_total_chars: int = 24000, max_pages_per_doc: int = 4, snippet_cap: int = 1900) -> str:
    """
    Extrae páginas financieras clave garantizando cobertura de TODOS los años disponibles:
    combina el último Anual (2025/2024, que trae 3-5 años históricos), el último Trimestral/Intermedio (2026/2025)
    y anuales previos (2023/2022) dentro del mismo presupuesto fijo de bytes (0 tokens extra).
    Prioriza páginas con alta densidad numérica (tablas reales de P&L, Balance, Cash Flow y Key Operating Data)
    descartando páginas meramente narrativas o de índice.
    """
    skip_jsons = {
        "company_meta.json", "market_data_live.json", "peers_market_live.json",
        "index.json", "forensic_metrics.json", "company_financial_model.json", "slides_deck.json",
        "sa2_forensic.json", "sa3_valuation.json", "sa5_verdict.json",
    }
    annual_cands: List[Tuple[int, Path]] = []
    recent_q_cands: List[Tuple[int, Path]] = []
    json_files = list(ocr_dir.glob("*.json"))
    archive_dir = ocr_dir / "_raw_ocr_archive"
    if archive_dir.exists():
        json_files.extend(archive_dir.glob("*.json"))
    seen_jnames = set()
    for jf in json_files:
        if jf.name in skip_jsons or jf.name in seen_jnames:
            continue
        seen_jnames.add(jf.name)
        name_low = jf.name.lower()
        yrs = [int(y) for y in re.findall(r"(20[1-3]\d)", name_low)]
        yr = max(yrs) if yrs else 0
        is_annual = bool(re.search(r"(annual|anual|10-k|20-f|prospectus)", name_low))
        if is_annual:
            annual_cands.append((yr, jf))
        else:
            recent_q_cands.append((yr, jf))

    annual_cands.sort(key=lambda x: (x[0], x[1].name), reverse=True)
    recent_q_cands.sort(key=lambda x: (x[0], x[1].name), reverse=True)

    # Intercalar: 1º Último Anual (ej. 2025 Annual), 2º Último Trimestral/Interim 2026, 3º Penúltimo Anual (2024/2023), 4º Segundo doc 2026/2025
    ordered_docs: List[Tuple[Path, int]] = []
    if annual_cands:
        ordered_docs.append((annual_cands[0][1], max(1, max_pages_per_doc)))
    for _, qf in recent_q_cands[:2]:
        ordered_docs.append((qf, 2))
    for _, af in annual_cands[1:]:
        ordered_docs.append((af, max(1, max_pages_per_doc - 1)))
    for _, qf in recent_q_cands[2:]:
        ordered_docs.append((qf, 1))

    out: List[str] = []
    used = 0
    seen_hashes = set()
    high_value_headers = (
        "consolidated statements of operations", "consolidated statement of profit",
        "consolidated balance sheets", "consolidated statement of financial position",
        "consolidated statements of cash flows", "key operating data",
        "unaudited condensed consolidated statements of operations",
        "results of operations\nthe following table", "five-year financial", "financial summary",
    )

    for jf, doc_page_cap in ordered_docs:
        if used >= max_total_chars:
            break
        try:
            data = json.loads(jf.read_text(encoding="utf-8", errors="ignore"))
            pages = data.get("pages", [])
            scored_pages: List[Tuple[int, int, str]] = []
            for idx, p in enumerate(pages):
                txt = (p.get("text") or "").strip()
                if not txt:
                    continue
                txt_low = txt.lower()
                if "pursuant to the requirements of the securities exchange act" in txt_low[:260] and len(txt) < 900:
                    continue
                if "index to consolidated financial statements" in txt_low:
                    continue
                if any(k.lower() in txt_low for k in keywords):
                    num_hits = len(re.findall(r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b", txt))
                    if num_hits < 3 and len(re.findall(r"\b\d+\.\d+\b", txt)) < 4:
                        continue
                    hdr_bonus = 60 if any(h in txt_low for h in high_value_headers) else 0
                    score_p = hdr_bonus + min(50, num_hits)
                    pnum = p.get("page_num") or (idx + 1)
                    scored_pages.append((score_p, pnum, txt))

            scored_pages.sort(key=lambda x: x[0], reverse=True)
            matched_pages = 0
            for _, pnum, txt in scored_pages:
                sig = re.sub(r"\s+", "", txt[:400])
                if sig in seen_hashes:
                    continue
                seen_hashes.add(sig)
                snippet = txt[:snippet_cap].strip().replace("```", "'''")
                entry = f"\n### {jf.stem} (Pág. {pnum})\n{snippet}\n"
                if used + len(entry) > max_total_chars:
                    break
                out.append(entry)
                used += len(entry)
                matched_pages += 1
                if matched_pages >= doc_page_cap:
                    break
        except Exception:
            continue

    return "".join(out)


def _compact_ocr_lines_for_single_read(text: str, max_bytes: int = 44500, max_lines: int = 740) -> str:
    """
    Mejora V3.5 (Palanca #2 — Lectura Única <= 750 líneas y <= 44.5 KB):
    Compacta secuencias de líneas vacías y celdas OCR cortas para que read_file / view_file
    (límite duro: 800 líneas / 46,080 bytes) devuelva el 100% del micro-pack en 1 sola llamada.
    """
    raw_lines = [ln.rstrip() for ln in text.splitlines()]
    compacted: List[str] = []
    pending_cells: List[str] = []

    def flush_cells():
        nonlocal pending_cells
        if pending_cells:
            compacted.append(" | ".join(pending_cells))
            pending_cells = []

    for ln in raw_lines:
        s = ln.strip()
        if not s:
            flush_cells()
            if compacted and compacted[-1] != "":
                compacted.append("")
            continue
        is_structural = (
            s.startswith(("#", ">", "- ", "* ", "|", "{", "}", "[", "]", "```", "---"))
            or re.match(r"^\d+\.\s", s)
            or s.startswith('"')
        )
        if not is_structural and len(s) <= 46:
            curr_len = sum(len(x) + 3 for x in pending_cells)
            if curr_len + len(s) <= 115 and len(pending_cells) < 5:
                pending_cells.append(s)
            else:
                flush_cells()
                pending_cells.append(s)
        else:
            flush_cells()
            compacted.append(ln)
    flush_cells()

    # Si tras compactar celdas aún supera max_lines, eliminar líneas en blanco no críticas
    if len(compacted) > max_lines:
        no_blank: List[str] = []
        for ln in compacted:
            if ln == "" and no_blank and not no_blank[-1].startswith("#"):
                continue
            no_blank.append(ln)
        compacted = no_blank

    if len(compacted) > max_lines:
        compacted = compacted[:max_lines]

    result = "\n".join(compacted) + "\n"
    encoded = result.encode("utf-8")
    if len(encoded) > max_bytes:
        trimmed = encoded[:max_bytes].decode("utf-8", errors="ignore")
        last_nl = trimmed.rfind("\n")
        if last_nl > 0:
            trimmed = trimmed[:last_nl + 1]
        result = trimmed
    return result


def _build_canonical_figures_block(target_dir: Path) -> str:
    """P7 (V3.7): bloque compacto (~15 líneas) con las cifras canónicas de company_financial_model.json
    que SA-3 y SA-5 deben copiar LITERALMENTE en M09–M18 (evita 46,50 vs 45,80, WACC 10,25 vs 10,50, proyecciones desfasadas, etc.)."""
    fp = target_dir / "company_financial_model.json"
    if not fp.exists():
        return ""
    try:
        cfm = json.loads(fp.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        return ""
    prof = cfm.get("company_profile", {}) or {}
    tri = cfm.get("valuation_triangulation", {}) or {}
    sc = cfm.get("institutional_scores", {}) or {}
    k = cfm.get("canonical_kpis", {}) or {}
    proj = cfm.get("projected_financials_5y", {}) or {}
    ccy = prof.get("currency", "")
    rccy = prof.get("reporting_currency", ccy)

    def f(v, d=2):
        try:
            v = float(v)
            return "N/D" if v == 0 else f"{v:,.{d}f}"
        except Exception:
            return "N/D"

    rev_last = k.get("revenue_last_fy") or {}
    bands = sc.get("phase0_anchor_bands") or {}
    cyc = cfm.get("cyclicality_profile") or {}
    lines = [
        "## 0.B CIFRAS CANÓNICAS OBLIGATORIAS (copiar LITERALMENTE en M01–M18; prohibido recalcular, redondear distinto o usar otro valor)",
        f"- Precio spot: {f(prof.get('share_price_spot'))} {ccy} | Capitalización: {f(prof.get('market_cap_m'), 0)} M {ccy} | Acciones: {f(prof.get('shares_diluted_m'), 2)} M",
        f"- Valor intrínseco DCF base: {f(tri.get('dcf_fair_value') or tri.get('dcf_intrinsic_base'))} {ccy} | SOTP: {f(tri.get('sotp_fair_value') or tri.get('sotp_value_per_share'))} | Múltiplos: {f(tri.get('multiples_fair_value'))}",
        f"- Escenarios Bear / Bull: {f(tri.get('bear_target'))} / {f(tri.get('bull_target'))} {ccy} | WACC: {f(tri.get('wacc_pct'))}% | g terminal: {f(tri.get('terminal_growth_g_pct'))}% | Beta CAPM ajustada: {f(k.get('beta_adjusted_wacc'))} (beta cruda yFinance: {f(k.get('beta_raw_yfinance'))})",
        f"- Bandas de anclaje F0 obligatorias: QoE (2.5) [{bands.get('qoe_target_band', 'N/D')}] | Moat (2.6) [{bands.get('moat_target_band', 'N/D')}] | Salud forense (5.5) [{bands.get('forensic_balance_target_band', 'N/D')}]",
        f"- Scores de origen consolidados (no modificar en M17): QoE (2.5) {f(sc.get('revenue_quality_qoe'), 1)} | Moat (2.6) {f(sc.get('moat_score'), 1)} | Salud forense (5.5) {f(sc.get('balance_sheet_forensic_health'), 1)}",
        f"- Ingresos último ejercicio real FY{rev_last.get('year', 'N/D')}: {f(rev_last.get('value'), 1)} M {rccy} (la proyección 2026E DEBE ser >= esta cifra; y las tablas de M11 y 18.5 DEBEN citar este ejercicio)",
        f"- Proyección ingresos {proj.get('years', [])}: {proj.get('revenue') or (proj.get('base') or {}).get('revenue_m') or 'N/D'}",
        f"- Beneish M-Score: {f(k.get('beneish_m_score'))} | ROIC: {f(k.get('roic_pct'))}% | CCC: {f(k.get('ccc_days'), 1)} días ({'POSITIVO: prohibido decir ciclo de caja negativo' if (k.get('ccc_days') or 0) > 0 else 'negativo/nulo'}) | Unidades/tiendas último corte oficial: {f(k.get('store_units_latest'), 0)} (prohibido usar cifras obsoletas como '20.000 tiendas')",
    ]
    if cyc:
        lines.append(
            f"- Perfil cuantitativo de ciclicidad (incluir en 3.2): {cyc.get('classification', 'N/D')} | Rango YoY ingresos: {cyc.get('revenue_yoy_pct_range', [])}% | Rango margen operativo pico-valle: {cyc.get('operating_margin_range_pct', [])}% (drawdown máx: {cyc.get('max_margin_drawdown_bps', 0)} pb) | SSSG: {cyc.get('sssg_range_pct', [])}%"
        )
    warns = cfm.get("validation_warnings") or []
    if warns:
        lines.append("- ⚠ AVISOS DEL MODELO (menciónalos como limitación en 16.1, no los ocultes): " + " | ".join(str(w)[:160] for w in warns[:3]))
    return "\n".join(lines) + "\n\n"



def _interim_income_excerpt(target_dir: Path, max_chars: int = 6000) -> str:
    """Extrae del digest OCR el estado de resultados del último informe interino.

    V3.8.1: sin este bloque los subagentes no ven las lineas de Revenue / Cost of sales /
    Profit for the period del interino y rellenan el Modulo 01 con N/D, lo que deja
    chart1 y chart1b sin los datos del ultimo periodo.
    """
    digest = target_dir / "extracted_ocr_cache" / "financial_digest.md"
    if not digest.exists():
        return ""
    try:
        txt = digest.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    docs = []
    for m in re.finditer(r"\[(20\d{2})\s+INTERIM REPORT[^\]]*?Page\s+(\d+)\]", txt, re.IGNORECASE):
        docs.append((int(m.group(1)), int(m.group(2)), m.start()))
    if not docs:
        return ""

    latest_year = max(d[0] for d in docs)
    latest = [d for d in docs if d[0] == latest_year]
    first_page = min(d[1] for d in latest)
    start_pos = [d[2] for d in latest if d[1] == first_page][0]

    after = [d[2] for d in docs if d[2] > start_pos and d[1] == 1]
    end_pos = min(after) if after else min(len(txt), start_pos + 150000)
    seg = txt[start_pos:end_pos]
    if len(seg) < 200:
        return ""

    window = ""
    for needle in ("Profit for the period", "Net cash generated from operating activities",
                   "Free cash flow", "Group cost of sales", "Gross profit", "Revenue"):
        m = re.search(needle, seg, re.IGNORECASE)
        if m:
            a = max(0, m.start() - 700)
            b = min(len(seg), m.end() + 1000)
            window += seg[a:b] + "\n\n"
        if len(window) > max_chars:
            break
    if not window.strip():
        return ""
    window = re.sub(r"\n{3,}", "\n\n", window)[:max_chars]
    return (
        "\n## 0.C ESTADO DE RESULTADOS DEL ULTIMO INTERINO (extracto literal del OCR)\n"
        "> Rellena con estas lineas las filas `Ingresos totales`, `Beneficio bruto`, `Coste de materiales` y "
        "`Resultado neto` de la columna del periodo intermedio del Modulo 01; el resto de tablas tambien puede usarlas. "
        "Si el interino no imprime `Gross profit`, derivalo como ingresos menos coste de ventas y marcalo `(derivado)`. "
        "El beneficio neto del periodo es la linea `Profit for the period`; la caja operativa, en `Net cash generated from operating activities`, y el flujo libre en `Free cash flow`.\n\n"
        + window + "\n\n"
    )


def build_facts_pack(target_dir: Path, max_chars_per_topic: int = 3800) -> int:
    """
    Optimización V3.5 Role-Specific Micro-Packs + Lectura Única (<750 líneas / <44.5 KB) + Escritura 2 Bloques:
    Genera en Fase 0 (0 tokens LLM):
      1. `facts_sa1.md` (~28-38 KB, <=740 líneas): Cabecera transversal + Anclas M01-M04 + Negocio/Catálogo/Moat/Sector/Cultura.
      2. `facts_sa2.md` (~34-44 KB, <=740 líneas): Cabecera transversal + Anclas M05-M08 + Estados Financieros/Notas/Directiva.
      3. `facts_sa3.md` (~26-36 KB, <=740 líneas): Cabecera transversal + Anclas M09-M11 + Accionariado/Valoración/Peers/Riesgos.
      4. `facts_sa4.md` (~20-28 KB, <=740 líneas): Cabecera transversal + Anclas M12-M15 + Catalizadores/Técnico/Consenso/Noticias.
      5. `company_facts_pack.md` (~52-64 KB): Dossier consolidado completo por retrocompatibilidad.
    """
    ocr_dir = target_dir / "extracted_ocr_cache"
    if not ocr_dir.exists():
        return 1

    dsh_write_protocol = (
        "> **PROTOCOLO DE ESCRITURA EN DEEPSEEK HARNESS (V3.8) — OBLIGATORIO:** esta plataforma no tiene `Append=true`; el equivalente exacto es el centinela.\n"
        "> 1. Primera llamada: `write(ruta, content='<!--CONT-->')`.\n"
        "> 2. Cada llamada siguiente: `edit(ruta, old_string='<!--CONT-->', new_string='<fragmento nuevo>\\n<!--CONT-->')`, aportando 10.000–18.000 bytes nuevos y continuando exactamente donde acabó el fragmento anterior, sin repetir ni resumir.\n"
        "> 3. Última llamada: `edit(ruta, old_string='<!--CONT-->', new_string='')`.\n"
        "> 4. PROHIBIDO volver a usar `write` sobre el borrador tras la primera llamada: cada reescritura completa duplica el coste de salida y puede perder módulos ya escritos.\n"
        "> 5. Si un fragmento se corta por límite de tokens, retómalo en la llamada siguiente con un fragmento más corto; nunca reinicies el archivo.\n\n"
    )

    rule_zero_console = (
        "> **REGLA CERO CONSOLA + DISCIPLINA EPISTEMOLÓGICA BUY-SIDE (ESTILO LING) + COBERTURA 2025–2026 + PARALLEL TOOL CALLING (V3.6):**\n"
        "> - PROHIBIDO ejecutar `run_command`, leer `_raw_ocr_archive`, releer tu `borrador_parteX.md`, usar bloques ``` o cajas ASCII (`+---+`/`┌──┐`), o incluir etiquetas `[EXTRAÍDO]`/`[ESTIMADO]`.\n"
        "> - **DISCIPLINA EPISTEMOLÓGICA ESTRICTA (CERO ALUCINACIÓN):** (1) Distingue siempre entre cifra **Consolidada** y cifra de **Segmento (ej. PRC)**; (2) En ADRs, respeta la divisa contable real (`CNY`/`RMB`/`IDR`) en saldos de caja, deuda y FCF; (3) Si reconstruyes una cifra a partir de notas parciales márcala como `(derivado)`, y si un desglose micro no figura en el pack declara `N/D` (PROHIBIDO inventar escandallos por taza/unidad, porcentajes `SBC/EBITDA` falsos, intentos de salida a bolsa inexistentes o dar por extinguidos litigios vivos en Singapur/EE.UU.).\n"
        "> - **COBERTURA MULTIANUAL OBLIGATORIA (`mandatory_years_coverage_in_tables`):** TODAS las tablas y series históricas (Módulos 01, 02, 05, 06, 07, 08 y 09) **DEBEN cubrir todos los años disponibles en los PDFs hasta 2025 y el corte acumulado/trimestral de 2026 (H1/Q3 2026)**. Prohibido truncar tablas en 2023 o 2024.\n"
        "> - **CERO SOBREESCRITURA Y CERO `search_web` REDUNDANTE:** emite el `.json` y el primer fragmento en el MISMO turno paralelo; después solo `edit` con centinela. `web_research_digest.md` ya viene inyectado en el pack.\n"
        "> - **PRESUPUESTO DE ESCRITURA (V3.8.1):** cada `edit` debe aportar **>= 12.000 bytes**; una parte de 50 KB se escribe en 3-4 llamadas, no en diez. PROHIBIDO releer el propio borrador, verificar con comandos o hacer micro-ediciones: cada llamada extra reenvía todo el contexto y se paga dos veces.\n"
        "> - **RESPUESTA FINAL DE 1 SOLA LÍNEA (`<= 25 palabras`):** `PASS | <TICKER> | <ARCHIVO> | <BYTES> bytes`.\n\n"
    )

    cheat_sa1 = (
        "## 0. PLANTILLA CANÓNICA Y BANDA OBJETIVO PARA SA-1 (`borrador_parte1.md`: 76,000 a 92,000 bytes | ~10,000–12,000 palabras)\n"
        + rule_zero_console
        + dsh_write_protocol
        + "- **ORDEN DE MÓDULOS:** `# PERFIL EXTRAÍDO` + `### Tabla de control institucional` + `## Módulo 01` + `## Módulo 02` (catálogo `2.2` íntegro) + `## Módulo 03` + `## Módulo 04`. **PROHIBIDO añadir `### Anexo` dentro de M01–M04**.\n"
        + "- **CONTRATO DEL PERIODO INTERMEDIO (chart1):** la tabla de M01 debe etiquetar la columna del último periodo exactamente `2026H1` (o `1H2026`/`9M2026`; nunca solo `Q3 2026`) e incluir las filas `Ingresos totales`, `Beneficio bruto` y `Coste de materiales`. Si el periodo no publica beneficio neto, escribe `N/D` en esa celda: el gráfico rotula `N/D` y no dibuja la barra.\n"
        + "- `## Módulo 01 — Contexto, Historia y Últimos Resultados Auditados` (1,650–2,050 pal.): `### 1.1 Posicionamiento`, `### 1.2 Cronología`, `### 1.3 Desempeño`, `### 1.4 Perspectiva Institucional` (100% histórico auditado + último trimestre reportado; cero proyecciones futuras y cero confundir divisas ADR).\n"
        + "- `## Módulo 02 — Modelo de Negocio, Catálogo de Productos/Servicios, Calidad de Ingresos y Moat` (3,600–4,400 pal.; **PROHIBIDO resumir catálogo 2.2 y PROHIBIDO inventar unit economics por taza/unidad no auditados**):\n"
        + "  - `### 2.1 Anatomía Profunda del Modelo de Negocio`, `### 2.2 Catálogo Exhaustivo de Productos y Servicios` (tabla >= 12 filas reales), `### 2.3 Desglose Cuantitativo por Segmento y Geografía`, `### 2.4 Estructura de Ingresos`.\n"
        + "  - `### 2.5 Puntuación de Calidad de Ingresos` (incluir literal `Puntuación de Calidad de Ingresos (1 a 10): X.X / 10` dentro de la banda `ANCHOR_SCORES_F0.qoe_2_5_band` usando **obligatoriamente estos 5 bloques canónicos = 10.0 pts**: `[1] Crecimiento Orgánico y Recurrencia (0–2.5 pts: en negocios B2C/Retail evaluar frecuencia mensual, retención de cohortes e ingresos diferidos/wallet; PROHIBIDO penalizar a un B2C por carecer de backlog contratado B2B)`, `[2] Conversión de Caja CFO/NI (0–2.5 pts)`, `[3] Salud de Cobros DSO/DSRI (0–2.0 pts)`, `[4] Calidad de Devengos/Sloan (0–1.5 pts)`, `[5] Dilución SBC/EBITDA y Limpieza Contable (0–1.5 pts)`. Prohibido mezclar riesgo geopolítico o gobernanza histórica dentro de QoE).\n"
        + "  - `### 2.6 Evaluación Multidimensional del Moat` (incluir literal `Calificación del Moat Global (1 a 10): X.X / 10` y `Pricing Power` dentro de `ANCHOR_SCORES_F0.moat_2_6_band` usando **obligatoriamente estos 5 pilares ponderados = 100%**: `[1] Ventaja de Costes y Economías de Escala/Densidad (30%)`, `[2] Costes de Cambio / Fricción de Salida o Hábito Digital (25%)`, `[3] Pricing Power / Elasticidad Demostrada (20%)`, `[4] Activos Intangibles, Marca o Concesiones (15%)`, `[5] Efecto Red y Ecosistema (10%)`).\n"
        + "- `## Módulo 03 — Inteligencia Sectorial, TAM/SAM/SOM, Sensibilidades y Posicionamiento Competitivo` (2,100–2,600 pal.): `### 3.1 Determinación de TAM, SAM, SOM`, `### 3.2 Vientos de Cola` (incluir diagnóstico cuantitativo de ciclicidad de la Sección 0.B: clasificación frente al ciclo económico, rango YoY de ingresos, compresión pico-valle de margen operativo en puntos básicos y sensibilidad a materias primas/divisas), `### 3.3 Análisis de las 5 Fuerzas de Porter`, `### 3.4 Mapa Competitivo` (usar cifra exacta de tiendas/unidades de la Sección 0.B; prohibido redondear a '> 20.000 tiendas').\n"
        + "- `## Módulo 04 — Cultura Corporativa, Eficiencia de I+D y Perfil ESG Operativo` (1,500–1,950 pal., sin inflar con anexos): `### 4.1 Valores Declarados`, `### 4.2 Cultura de Innovación`, `### 4.3 Perfil ESG` (incluir dictamen explícito separado para `Ambiental/Social` y `Gobernanza/Cultura` usando literales `Activo diferenciador`, `Factor neutro` o `Riesgo latente`).\n"
        + "- **NO escribas `## RESUMEN PARTE 1` ni `### Anexo` al final**.\n\n"
    )

    cheat_sa2 = (
        "## 0. PLANTILLA CANÓNICA Y BANDA OBJETIVO PARA SA-2 (`borrador_parte2.md`: 66,000 a 80,000 bytes | ~8,500–10,200 palabras)\n"
        + rule_zero_console
        + dsh_write_protocol
        + "- **ORDEN:** guarda `sa2_forensic.json` (con `historical_financials` e `institutional_scores` > 0) **en el mismo turno** que el primer fragmento del borrador; después `## Módulo 05`, `## Módulo 06`, `## Módulo 07` y `## Módulo 08` por orden.\n"
        + "- **`sa2_forensic.json` — `segments_breakdown` OBLIGATORIO:** entre 3 y 6 filas con las claves exactas `name`, `pct` y `revenue_m`, cubriendo **todas** las líneas reales (bebidas, alimentación, otros ingresos y canal de socios) y sumando 100% sobre los ingresos totales. `chart2` consume esas tres claves; el desglose agregado de dos canales deja el panel vacío o pobre. `historical_financials` no admite `null`: usa solo ejercicios con serie completa.\n"
        + "- `## Módulo 05 — Auditoría Forense del Balance, Notas Críticas Contables y Solvencia` (objetivo: 2,950–3,500 pal.): `### 5.1 Serie Multianual de Balance`, `### 5.2 Calendario de Vencimientos y Auditoría de Notas`, `### 5.3 Señales de Alerta Rojas` (incluir literales `Ratio de Sloan` y `Beneish`), `### 5.4 Stress Test Cuantificado`, `### 5.5 Puntuación de Salud Forense` (incluir literal `Puntuación de Salud Forense del Balance (1 a 10): X.X / 10` y dictamen `TRAYECTORIA EN MEJORA` / `TRAYECTORIA EN DETERIORO` / `LISTA DE VIGILANCIA`).\n"
        + "- `## Módulo 06 — Cuenta de Resultados Histórica, Unit Economics y Calidad del Flujo de Caja` (objetivo: 2,250–2,750 pal.): `### 6.1 Cuenta de Resultados`, `### 6.2 Evolución de Márgenes`.\n"
        + "- `## Módulo 07 — KPIs Operativos Sectoriales, Capital Circulante (CCC) y Benchmarking de Eficiencia` (objetivo: 1,600–2,000 pal.): `### 7.1 Tabla Histórica de KPIs Operativos`, `### 7.2 Benchmarking Operativo` (incluir literal `POR ENCIMA`, `DENTRO` o `POR DEBAJO`).\n"
        + "- `## Módulo 08 — Directiva, Gobernanza, Partes Vinculadas y Asignación Histórica de Capital` (objetivo: 1,650–2,100 pal.): `### 8.1 Perfiles Directivos` (con nombres reales de CEO/Chairman/CFO), `### 8.2 Guidance vs. Ejecución`, `### 8.3 Recompras, Emisiones y ROIC Incremental` (mencionar literal `ROIC Incremental`).\n"
        + "- **NO escribas `## RESUMEN PARTE 2` al final**.\n\n"
    )

    cheat_sa3 = (
        "## 0. PLANTILLA CANÓNICA Y BANDA OBJETIVO PARA SA-3 (`borrador_parte3.md`: 52,000 a 64,000 bytes | ~6,500–8,000 palabras)\n"
        + rule_zero_console
        + dsh_write_protocol
        + "- **ORDEN:** `sa3_valuation.json` en el mismo turno que el primer fragmento; después `## Módulo 09`, `## Módulo 10` y `## Módulo 11` por orden. Es el borrador más largo del pipeline: dosifica los fragmentos y no reinicies el archivo.\n"
        + "- **`sa3_valuation.json` OBLIGATORIO (candado P5):** `valuation_triangulation` con `dcf_fair_value`, `sotp_fair_value`, `multiples_fair_value`, `bear_target`, `bull_target`, `wacc_pct`, `terminal_growth_g_pct` y `current_price` = precio spot exacto de la cabecera; incluye también `wacc_pct` en la raíz; `projected_financials_5y.revenue[0]` >= ingresos del último ejercicio real y coherente con el run-rate. En M11 la fila del último FY real debe usar exactamente los ingresos y tiendas de las cifras canónicas 0.B. Usa en M09–M11 exactamente esos mismos valores (un solo WACC, un solo DCF).\n"
        + "- **COHERENCIA NUMÉRICA ESTRICTA (CERO REINTENTOS DE GATEKEEPER):** (1) En la tabla de M11, la columna del último año real debe usar exactamente la cifra de ingresos reales y unidades/tiendas totales indicadas en la Sección 0.B; (2) La proyección de ingresos 2026E DEBE ser superior o igual al último ejercicio real; (3) El DCF base, SOTP, Bear, Bull y WACC deben coincidir al 100% con los declarados en `sa3_valuation.json`.\n"
        + "- `## Módulo 09 — Estructura Accionarial, Liquidez Bursátil, Smart Money e Insiders` (objetivo: 1,300–1,650 pal.): `### 9.1 Estructura Accionarial` (con nombres reales y % exactos de accionistas), `### 9.2 Transacciones de Insiders`.\n"
        + "- `## Módulo 10 — Valoración Avanzada (DCF + SOTP + Múltiplos + Escenarios)` (objetivo: 2,750–3,400 pal.): `### 10.1 Sección A: WACC, DCF` (incluir literal `Reverse DCF` y matriz 5x5 numérica), `### 10.2 Sección B: Valoración por Suma de las Partes`, `### 10.3 Sección C: Múltiplos Comparables`, `### 10.4 Sección D: Escenarios Probabilísticos`.\n"
        + "- `## Módulo 11 — Potencial de Crecimiento Futuro, Proyecciones Operativas a 5 Años y Matriz de Riesgos` (objetivo: 2,000–2,600 pal.): `### 11.1 Sección A: Potencial de Crecimiento y Proyecciones Operativas a 5 Años` (con tablas Bear/Base/Bull vs Consenso), `### 11.2 Sección B: Matriz de Riesgos` (**100% prosa y viñetas; CERO caracteres `|` de tabla en toda la Sección B 11.2**).\n"
        + "- **NO escribas `## RESUMEN PARTE 3` al final**.\n\n"
    )

    cheat_sa4 = (
        "## 0. PLANTILLA CANÓNICA Y BANDA OBJETIVO PARA SA-4 (`borrador_parte4.md`: 41,000 a 52,000 bytes | ~5,500–6,800 palabras)\n"
        + rule_zero_console
        + dsh_write_protocol
        + "- La Sección 1 de este archivo YA incluye el consenso Sell-Side, indicadores técnicos y las noticias 2025–2026 pre-extraídas en Fase 0 (**NO llames a `search_web`** salvo que falte todo dato de noticias).\n"
        + "- **ORDEN:** `## Módulo 12`, `## Módulo 13`, `## Módulo 14` y `## Módulo 15` por orden.\n"
        + "- `## Módulo 12 — Catalizadores Futuros y Eventos Kill-Switch` (objetivo: 1,700–2,100 pal.; **100% prosa y viñetas, CERO caracteres `|` en todo el Módulo 12**; incluir >=4 veces `Fecha esperada`, `Naturaleza`, `Probabilidad`, `Impacto`, `Grado de asimilación`): `### 12.1 Catalizadores de Corto Plazo`, `### 12.2 Catalizadores de Medio Plazo`, `### 12.3 Catalizadores de Largo Plazo`, `### 12.4 Catalizadores Ocultos`, `### 12.5 Anti-catalizadores`.\n"
        + "- `## Módulo 13 — Análisis Técnico y Flujo de Órdenes Institucional` (objetivo: 1,250–1,550 pal.): `### 13.1 Estructura de Tendencia`, `### 13.2 Mapa de Soportes y Resistencias`.\n"
        + "- `## Módulo 14 — Sentimiento de Mercado y Cobertura de Analistas` (objetivo: 1,150–1,450 pal.): `### 14.1 Consenso Sell-Side`, `### 14.2 Cobertura de Prensa`.\n"
        + "- `## Módulo 15 — Matriz de Tesis de Inversión y Factores Críticos de Seguimiento` (objetivo: 1,550–1,950 pal.): `### 15.1 Marco Temporal y Contexto`, `### 15.2 Matriz de Impacto`, `### 15.3 Checklist de Vigencia Trimestral`.\n"
        + "- **NO escribas `## RESUMEN PARTE 4` al final**.\n\n"
    )

    shared_header = _build_shared_core_header(target_dir)

    kw_highlights = (
        "CONSOLIDATED STATEMENTS OF OPERATIONS", "KEY OPERATING DATA",
        "UNAUDITED CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS",
        "Results of Operations", "主要会计数据", "Key Financial", "Financial Highlights",
        "FINANCIAL SUMMARY", "Five-Year Financial", "Operating revenue", "营业收入",
        "Total net revenues", "Selected Consolidated Financial",
    )
    kw_accounting = (
        "CONSOLIDATED STATEMENTS OF OPERATIONS", "CONSOLIDATED BALANCE SHEETS",
        "CONSOLIDATED STATEMENTS OF CASH FLOWS",
        "合并资产负债表", "合并利润表", "合并现金流量表",
        "CONSOLIDATED STATEMENT OF COMPREHENSIVE INCOME",
        "CONSOLIDATED STATEMENT OF PROFIT OR LOSS",
        "CONSOLIDATED STATEMENT OF FINANCIAL POSITION",
        "CONSOLIDATED BALANCE SHEET",
        "CONSOLIDATED STATEMENT OF CASH FLOWS",
        "UNAUDITED CONDENSED CONSOLIDATED",
        "CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS",
        "Key Audit Matters",
    )
    kw_shareholders = (
        "Substantial Shareholders", "Directors' and Chief Executive", "前十名股东", "前10名股东", "Shareholding",
    )
    kw_forensic_notes = (
        "SHARE BASED COMPENSATION", "COMMITMENTS AND CONTINGENCIES", "Legal proceedings",
        "Ageing analysis", "Aging analysis", "Expected credit loss", "Trade and bills receivables",
        "Bank borrowings", "Maturity", "Goodwill", "Impairment assessment",
        "Directors' emoluments", "Directors' remuneration", "Auditor's remuneration", "Auditors' remuneration",
        "Independent Auditor's Report", "Certified Public Accountants", "Practising Certificate",
        "Related party transactions", "Balances with related", "应收账款", "短期借款", "长期借款", "商誉", "关联方",
    )

    highlights_txt = _extract_prioritized_financial_pages(ocr_dir, kw_highlights, max_total_chars=8200, max_pages_per_doc=2, snippet_cap=1750)
    accounting_txt = _extract_prioritized_financial_pages(ocr_dir, kw_accounting, max_total_chars=17200, max_pages_per_doc=4, snippet_cap=1900)
    shareholders_txt = _extract_prioritized_financial_pages(ocr_dir, kw_shareholders, max_total_chars=5200, max_pages_per_doc=2, snippet_cap=1700)
    forensic_notes_txt = _extract_prioritized_financial_pages(ocr_dir, kw_forensic_notes, max_total_chars=9000, max_pages_per_doc=4, snippet_cap=1800)
    high_density_q_forensic = _extract_high_density_forensic_and_quarterly_digest(ocr_dir, max_chars=3100)

    t_seg = _query_to_string(target_dir, "segmentos ingresos productos catálogo clientes modelo negocio", max_chars=4800, top_k=5, only_recent_years=True)
    t_bal = _query_to_string(target_dir, "deuda vencimientos liquidez balance auditor contingencias arrendamientos", max_chars=4500, top_k=5, only_recent_years=True)
    t_pnl = _query_to_string(target_dir, "margen bruto operativo flujo de caja inventario cuentas por cobrar", max_chars=4500, top_k=5, only_recent_years=True)
    t_rnd = _query_to_string(target_dir, "investigación desarrollo patentes empleados cultura emisiones ESG", max_chars=3800, top_k=4, only_recent_years=True)
    t_gov = _query_to_string(target_dir, "directiva consejo accionistas remuneración partes vinculadas", max_chars=4500, top_k=5, only_recent_years=True)
    t_cli = _query_to_string(target_dir, "clientes proveedores concentración cinco mayores cartera pedidos backlog", max_chars=3500, top_k=4, only_recent_years=True)
    t_rsk = _query_to_string(target_dir, "riesgos contingencias litigios sanciones aranceles divisas", max_chars=4200, top_k=5, only_recent_years=True)
    t_cat = _query_to_string(target_dir, "dividendos recompras adquisiciones perspectivas guidance expansión", max_chars=4000, top_k=4, only_recent_years=True)

    web_dig = ""
    for wp in (ocr_dir / "web_research_digest.md", target_dir / "web_research_digest.md"):
        if wp.exists():
            web_dig = wp.read_text(encoding="utf-8", errors="ignore")[:6500]
            break

    hd_block = ("## 0.C DATOS DE ALTA DENSIDAD FORENSE Y CIERRES 2025–2026 (ÚLTIMOS TRIMESTRES/INTERIM, AUDITOR PCAOB, INGRESOS DIFERIDOS Y GLOSARIO DE SIGLAS)\n" + high_density_q_forensic + "\n") if high_density_q_forensic else ""
    canon_block = _build_canonical_figures_block(target_dir)

    sa1_pack = (
        f"# MICRO-PACK SA-1 (MÓDULOS 01–04: NEGOCIO, CATÁLOGO, MOAT, SECTOR Y CULTURA) — {target_dir.name}\n\n"
        + cheat_sa1
        + canon_block
        + shared_header
        + hd_block
        + "## 1. RESUMEN FINANCIERO MULTIANUAL EXTRAÍDO (TODOS LOS AÑOS HASTA 2025/2026)\n" + (highlights_txt or "(Ver company_financial_model.json)\n")
        + "\n## 2. SEGMENTOS, PRODUCTOS, CATÁLOGO Y MODELO DE NEGOCIO\n" + t_seg
        + "\n## 3. CLIENTES, PROVEEDORES, CONCENTRACIÓN Y BACKLOG\n" + t_cli
        + "\n## 4. I+D, PATENTES, CAPITAL HUMANO Y ESG\n" + t_rnd
        + ("\n## 5. NOTAS WEB / CATÁLOGO Y SECTOR\n" + web_dig[:3200] if web_dig else "")
    )

    sa2_pack = (
        f"# MICRO-PACK SA-2 (MÓDULOS 05–08: BALANCE FORENSE, RESULTADOS, KPIS Y DIRECTIVA) — {target_dir.name}\n\n"
        + cheat_sa2
        + canon_block
        + shared_header
        + hd_block
        + "## 1. ESTADOS FINANCIEROS CONSOLIDADOS Y AUDITORÍA (SERIE COMPLETA HASTA 2025/2026)\n" + (accounting_txt or highlights_txt)
        + "\n## 2. NOTAS CRÍTICAS FORENSES EXTRAÍDAS (AGING CUENTAS POR COBRAR, VENCIMIENTOS DEUDA, GOODWILL, AUDITOR Y REMUNERACIÓN CONSEJO)\n" + (forensic_notes_txt or t_bal)
        + "\n## 3. BALANCE, DEUDA, VENCIMIENTOS Y NOTAS CONTABLES (BM25)\n" + t_bal
        + "\n## 4. RESULTADOS, MÁRGENES, FLUJO DE CAJA Y CAPITAL CIRCULANTE\n" + t_pnl
        + "\n## 5. DIRECTIVA, GOBERNANZA, REMUNERACIÓN Y PARTES VINCULADAS\n" + t_gov
        + "\n## 6. ASIGNACIÓN DE CAPITAL, RECOMPRAS Y GUIDANCE\n" + t_cat
    )

    sa3_pack = (
        f"# MICRO-PACK SA-3 (MÓDULOS 09–11: ACCIONARIADO, VALORACIÓN DCF/MÚLTIPLOS Y RIESGOS) — {target_dir.name}\n\n"
        + cheat_sa3
        + canon_block
        + shared_header
        + hd_block
        + "## 1. SÍNTESIS FINANCIERA Y ESTRUCTURA ACCIONARIAL (SERIE HASTA 2025/2026)\n" + highlights_txt + "\n" + shareholders_txt
        + "\n## 2. NOTAS DE DEUDA, CAPITAL Y AUDITORÍA PARA PUENTE EV-EQUITY\n" + forensic_notes_txt[:4800]
        + "\n## 3. ACCIONISTAS, INSIDERS Y GOBERNANZA DE CAPITAL\n" + t_gov
        + "\n## 4. CONCENTRACIÓN DE CLIENTES/PROVEEDORES Y VISIBILIDAD (BACKLOG)\n" + t_cli
        + "\n## 5. DIVIDENDOS, RECOMPRAS, CAPEX Y PERSPECTIVAS (GUIDANCE)\n" + t_cat
        + "\n## 6. RIESGOS OPERATIVOS, FINANCIEROS, REGULATORIOS Y CONTINGENCIAS\n" + t_rsk
    )

    sa4_pack = (
        f"# MICRO-PACK SA-4 (MÓDULOS 12–15: CATALIZADORES, TÉCNICO, CONSENSO Y NOTICIAS) — {target_dir.name}\n\n"
        + cheat_sa4
        + shared_header
        + ("\n## 1. DOSSIER DE PRENSA, CONSENSO Y EVENTOS RECIENTES\n" + web_dig if web_dig else "")
        + "\n## 2. CATALIZADORES, LANZAMIENTOS, DIVIDENDOS/RECOMPRAS Y GUIDANCE\n" + t_cat
        + "\n## 3. EVENTOS REGULATORIOS, RIESGOS Y TRIGGERS TRIMESTRALES\n" + t_rsk
        + "\n## 4. HITOS RECIENTES DE SEGMENTOS Y PRODUCTOS\n" + t_seg[:2600]
    )

    interim_block = _interim_income_excerpt(target_dir)
    if interim_block:
        sa1_pack = interim_block + sa1_pack
        sa2_pack = interim_block + sa2_pack

    micro_packs = {
        "facts_sa1.md": _compact_ocr_lines_for_single_read(sa1_pack, max_bytes=44500, max_lines=740),
        "facts_sa2.md": _compact_ocr_lines_for_single_read(sa2_pack, max_bytes=44500, max_lines=740),
        "facts_sa3.md": _compact_ocr_lines_for_single_read(sa3_pack, max_bytes=44500, max_lines=740),
        "facts_sa4.md": _compact_ocr_lines_for_single_read(sa4_pack, max_bytes=44500, max_lines=740),
    }
    sizes_msg = []
    for fname, content in micro_packs.items():
        (ocr_dir / fname).write_text(content, encoding="utf-8")
        (target_dir / fname).write_text(content, encoding="utf-8")
        n_lines = len(content.splitlines())
        sizes_msg.append(f"{fname}={len(content.encode('utf-8')):,}B/{n_lines}L")

    full_pack = (
        f"# COMPANY FACTS PACK (CONSOLIDADO DETERMINISTA 0 TOKENS) — {target_dir.name}\n\n"
        + cheat_sa1 + cheat_sa2 + cheat_sa3 + cheat_sa4
        + shared_header
        + "## 1. RESUMEN E INFORMACIÓN CONTABLE PRIORIZADA\n"
        + highlights_txt + "\n" + accounting_txt[:14000] + "\n" + shareholders_txt[:4000]
        + f"\n## 2. SEGMENTOS Y CATÁLOGO\n{t_seg}\n"
        + f"\n## 3. BALANCE Y DEUDA\n{t_bal}\n"
        + f"\n## 4. RESULTADOS Y CAJA\n{t_pnl}\n"
        + f"\n## 5. I+D Y CULTURA\n{t_rnd}\n"
        + f"\n## 6. DIRECTIVA Y ACCIONARIADO\n{t_gov}\n"
        + f"\n## 7. CLIENTES Y BACKLOG\n{t_cli}\n"
        + f"\n## 8. RIESGOS Y REGULACIÓN\n{t_rsk}\n"
        + f"\n## 9. DIVIDENDOS, RECOMPRAS Y GUIDANCE\n{t_cat}\n"
    )
    (ocr_dir / "company_facts_pack.md").write_text(full_pack, encoding="utf-8")
    (target_dir / "company_facts_pack.md").write_text(full_pack, encoding="utf-8")

    # V3.4: Empaquetar los .md gigantes del OCR crudo en _raw_ocr_archive.zip y eliminar los .md sueltos
    # para que sea físicamente imposible que ningún subagente abra 250k tokens de OCR crudo con view_file/read_file.
    import zipfile
    keep_in_ocr_root = {
        "facts_sa1.md", "facts_sa2.md", "facts_sa3.md", "facts_sa4.md",
        "company_facts_pack.md", "m01_m15_digest.md", "brief_ppt_podcast.md",
        "financial_digest.md", "web_research_digest.md",
    }
    archive_dir = ocr_dir / "_raw_ocr_archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archived_count = 0
    for md_fp in list(ocr_dir.glob("*.md")):
        if md_fp.name.lower() not in keep_in_ocr_root:
            dest_fp = archive_dir / md_fp.name
            try:
                if dest_fp.exists():
                    dest_fp.unlink()
                md_fp.rename(dest_fp)
                archived_count += 1
            except OSError:
                pass

    archive_zip = ocr_dir / "_raw_ocr_archive.zip"
    raw_mds_in_archive = list(archive_dir.glob("*.md"))
    if raw_mds_in_archive:
        try:
            with zipfile.ZipFile(archive_zip, "a", compression=zipfile.ZIP_DEFLATED) as zf:
                existing_names = set(zf.namelist())
                for r_md in raw_mds_in_archive:
                    if r_md.name not in existing_names:
                        zf.write(r_md, arcname=r_md.name)
                    r_md.unlink()
        except Exception:
            pass

    print(
        f"=== FACTS PACKS GENERADOS (EXIT 0) | company_facts_pack.md={len(full_pack.encode('utf-8')):,}B "
        f"| {', '.join(sizes_msg)} | raw_ocr_archivados_zip={archived_count} ==="
    )
    return 0


def query_company_memory(target_dir: Path, raw_query: str, max_chars: int = 6000, top_k: int = 8) -> int:
    ocr_dir = target_dir / "extracted_ocr_cache"
    db_path = ocr_dir / "wiki_bm25.sqlite"
    if not db_path.exists():
        build_company_memory(target_dir)

    daemon_up = ensure_tdai_daemon(target_dir)
    service_id = re.sub(r"[^a-zA-Z0-9_-]", "_", target_dir.name)
    tokens = expand_bilingual_tokens(raw_query)

    output_blocks: List[str] = [
        f"### RESULTADOS TENCENTDB-AGENT-MEMORY (Presupuesto: {max_chars} chars | Query: {raw_query})\n"
    ]
    used_chars = len(output_blocks[0])

    # 1. Consultar primero al Gateway oficial TencentDB-Agent-Memory (:8420) si está activo
    if daemon_up:
        # Extraer hasta 8 tokens más representativos para la búsqueda semántica
        q_str = " ".join(tokens[:8]) if tokens else raw_query
        tdai_payload = {
            "query": q_str,
            "team_id": "team_gauntlet",
            "agent_id": service_id,
            "user_id": "analyst",
            "limit": top_k,
        }
        tdai_resp = tdai_http_request("/v2/conversation/search", tdai_payload, service_id=service_id)
        items = ((tdai_resp or {}).get("data") or {}).get("messages") or []
        for item in items:
            text = item.get("content") or ""
            score = item.get("score", 0.0)
            header = f"\n--- [TDAI:RELEVANCIA {score:.4f}] ---\n"
            avail = max_chars - used_chars - len(header)
            if avail <= 120:
                break
            snippet = text[:avail] + (" [...]" if len(text) > avail else "")
            block = f"{header}{snippet}\n"
            output_blocks.append(block)
            used_chars += len(block)

    # 2. Completar presupuesto de caracteres con fusión RRF sobre wiki_bm25.sqlite
    if used_chars < max_chars - 300 and db_path.exists() and tokens:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        rrf_scores: Dict[int, float] = {}
        chunk_store: Dict[int, Tuple[str, str, str, str]] = {}

        sub_queries = [tokens[i:i + 4] for i in range(0, min(12, len(tokens)), 4)]
        for q_terms in sub_queries:
            fts_terms = []
            for t in q_terms:
                if re.search(r"[\u4e00-\u9fff]", t):
                    fts_terms.append(f'"{t}"')
                else:
                    fts_terms.append(f'"{t}"*')
            fts_expr = " OR ".join(fts_terms)
            try:
                rows = cur.execute(
                    """
                    SELECT rowid, doc_name, doc_type, section_title, content,
                           bm25(wiki_chunks, 1.0, 0.5, 3.5, 1.0) AS score
                    FROM wiki_chunks WHERE wiki_chunks MATCH ?
                    ORDER BY score ASC LIMIT ?;
                    """,
                    (fts_expr, top_k * 2),
                ).fetchall()
            except sqlite3.OperationalError:
                continue

            for rank, (rowid, d_name, d_type, s_title, content, _) in enumerate(rows, start=1):
                boost = 1.15 if d_type in ("ANNUAL", "LATEST_QUARTERLY") else 1.0
                rrf_scores[rowid] = rrf_scores.get(rowid, 0.0) + (boost / (30.0 + rank))
                chunk_store[rowid] = (d_name, d_type, s_title, content)
        conn.close()

        for rid in sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)[:top_k]:
            d_name, d_type, s_title, content = chunk_store[rid]
            header = f"\n--- [{d_type}] {d_name} :: {s_title} ---\n"
            avail = max_chars - used_chars - len(header)
            if avail <= 120:
                break
            snippet = content[:avail] + (" [...]" if len(content) > avail else "")
            block = f"{header}{snippet}\n"
            output_blocks.append(block)
            used_chars += len(block)

    print("".join(output_blocks))
    return 0


def extract_m1_to_m15_digest(target_dir: Path, max_chars: int = 34000) -> int:
    """
    Destila los borradores 1 a 4 (Módulos 01 a 15) en un archivo compacto (~28-34 KB)
    para que el 5º subagente (SA-5: Módulos 16, 17 y 18 con Síntesis de Partes 1..4 y Tear Sheet)
    disponga del 100% de las cifras, puntuaciones, tablas y tesis de los Módulos 01 a 15
    en 1 sola lectura sin cargar 220 KB de texto crudo.
    """
    ocr_dir = target_dir / "extracted_ocr_cache"
    ocr_dir.mkdir(parents=True, exist_ok=True)
    meta_fp = ocr_dir / "company_meta.json"
    file_prefix = target_dir.name
    if meta_fp.exists():
        try:
            m_data = json.loads(meta_fp.read_text(encoding="utf-8", errors="ignore"))
            file_prefix = m_data.get("file_prefix") or target_dir.name
        except Exception:
            pass
    cheat_sheet_m16_m18 = (
        f"## 0. PLANTILLA CANÓNICA Y BANDA OBJETIVO PARA SA-5 / SA-B (`borrador_parte5.md`: 38,000 a 48,000 bytes | `FILE_PREFIX`: `{file_prefix}` — CERO CONSOLA)\n"
        "> **REGLA CERO CONSOLA + ESCRITURA POR CENTINELA + RESPUESTA 1 LÍNEA (V3.8):** Prohibido llamar a `run_command`. Escribe `borrador_parte5.md` (38–48 KB) con `write` sobre el contenido `<!--CONT-->` y añade cada tramo con `edit(old_string='<!--CONT-->', new_string='<tramo>\\n<!--CONT-->')`; la última llamada deja el centinela vacío. PROHIBIDO reescribir el archivo completo tras la primera llamada. *(Si actúas en Modo Split Dual `SA-B`, tras escribir `borrador_parte5.md` puedes escribir en el turno siguiente `{file_prefix}_PODCAST_GUION.md` [58–70 KB, 8,600–9,800 palabras, 90–110 turnos `DIRECTOR:`/`ELENA:`/`MARCOS:`] o en paralelo, cerrando en <= 3 pasos totales)*. Al terminar, responde al orquestador en 1 sola línea (`<= 25 palabras`): `PASS | <TICKER> | borrador_parte5.md | <BYTES> bytes`.\n"
        "- `## Módulo 16 — Ajustes Forenses en Valoración y El Debate del Comité de Inversiones (Bull vs. Bear)` (objetivo: 1,750–2,150 palabras):\n"
        "  - `### 16.1 Sección A: Síntesis de Banderas Rojas Forenses`\n"
        "  - `### 16.2 Sección B: El Debate del Comité de Inversiones` (**100% en prosa fluida y viñetas; CERO caracteres `|` de tabla en toda la Sección B 16.2**).\n"
        "- `## Módulo 17 — Veredicto Final Ejecutable, Scorecard Institucional y Plan Táctico de Cartera` (objetivo: 1,950–2,450 palabras):\n"
        "  - `### 17.1 Scorecard Institucional Ponderado` (tabla canónica de 6 pilares: Moat 20%, Salud Forense 20%, QoE 20%, ROIC vs WACC 15%, Gobernanza 15%, Asimetría 10% = 100%; Moat/Salud/QoE = valores del bloque 0.B)\n"
        "  - `### 17.2 Anatomía del Retorno Total Esperado`\n"
        "  - `### 17.3 Factores para Comprar Hoy`\n"
        "  - `### 17.4 Plan de Ejecución en Tramos`\n"
        "  - `### 17.5 Tabla de Veredicto Ejecutable` (tabla de 12 filas incluyendo literal `VEREDICTO GLOBAL`: Recomendación Institucional, Nivel de Convicción, Puntuación Ponderada Total, Precio Actual de Mercado, Valor Intrínseco Base, Rango Bull/Bear, Margen de Seguridad, E[TR] Anualizado, Rango Acumulación Tramo 1/2/3, Nivel de Invalidación, Tamaño Inicial/Máximo, Catalizador Principal 6-12M).\n"
        "- `## Módulo 18 — RESUMEN EJECUTIVO FINAL: Síntesis Integral por Bloques (Partes 1 a 4) y Tear Sheet` (objetivo: 2,500–3,000 palabras):\n"
        "  - `### 18.1 Síntesis Ejecutiva de la Parte 1` (8 a 10 viñetas `- ` densas de Módulos 01–04)\n"
        "  - `### 18.2 Síntesis Ejecutiva de la Parte 2` (8 a 10 viñetas `- ` densas de Módulos 05–08)\n"
        "  - `### 18.3 Síntesis Ejecutiva de la Parte 3` (8 a 10 viñetas `- ` densas de Módulos 09–11)\n"
        "  - `### 18.4 Síntesis Ejecutiva de la Parte 4` (8 a 10 viñetas `- ` densas de Módulos 12–15)\n"
        "  - `### 18.5 Tear Sheet Ejecutivo Final` (exactamente 5 puntos numerados `1.` a `5.` al final del documento).\n\n"
    )
    blocks = [
        "# DOSSIER DE SÍNTESIS DE LOS MÓDULOS 01 A 15 (INPUT PARA BORRADOR PARTE 5: MÓDULOS 16, 17 Y 18)\n\n",
        cheat_sheet_m16_m18,
        _build_canonical_figures_block(target_dir),
    ]

    for idx in (1, 2, 3, 4):
        dp = target_dir / f"borrador_parte{idx}.md"
        if not dp.exists():
            print(f"[ERROR] Falta {dp.name} para destilar el resumen de Módulos 01-15", file=sys.stderr)
            return 1
        raw = dp.read_text(encoding="utf-8", errors="ignore")
        blocks.append(f"\n## === EXTRACTO ESTRUCTURADO DE BORRADOR PARTE {idx} ({dp.name}) ===\n")
        sections = re.split(r"(?m)^(?=##\s+|###\s+)", raw)
        budget_per_draft = max_chars // 4
        used = 0
        for sec in sections:
            s = sec.strip()
            if not s:
                continue
            lines = s.splitlines()
            hdr = lines[0]
            # Conservar encabezados, tablas, viñetas con cifras/puntuaciones y primer/último párrafo de cada subsección
            keep_lines = [hdr]
            for ln in lines[1:]:
                ls = ln.strip()
                if ls.startswith("|") or ls.startswith("-") or ls.startswith("*") or re.match(r"^\d+\.", ls):
                    keep_lines.append(ln)
                elif any(k in ls.lower() for k in ("puntuaci", "calificaci", "moat", "sloan", "beneish", "altman", "roic", "wacc", "noplat", "dcf", "sotp", "cagr", "catalizador", "soporte", "resistencia", "consenso", "/ 10", "/10")):
                    keep_lines.append(ln)
            if len(keep_lines) <= 2 and len(lines) > 1:
                keep_lines.extend(lines[1:4])
            chunk = "\n".join(keep_lines)
            if len(chunk) > 1800:
                chunk = chunk[:1800] + "\n[...]\n"
            if used + len(chunk) <= budget_per_draft:
                blocks.append(chunk + "\n\n")
                used += len(chunk)

    out_text = _compact_ocr_lines_for_single_read("".join(blocks), max_bytes=44500, max_lines=740)
    out_cache = ocr_dir / "m01_m15_digest.md"
    out_root = target_dir / "m01_m15_digest.md"
    out_cache.write_text(out_text, encoding="utf-8")
    out_root.write_text(out_text, encoding="utf-8")
    n_lines = len(out_text.splitlines())
    print(f"=== DIGEST M01-M15 GENERADO (EXIT 0) | m01_m15_digest.md ({len(out_text.encode('utf-8')):,}B/{n_lines}L) ===")
    return 0


def extract_brief_for_ppt_and_podcast(target_dir: Path, max_chars: int = 42000) -> int:
    final_mds = [p for p in target_dir.glob("*_INFORME_COMITE_FINAL.md") if not p.name.startswith("borrador_")]
    if not final_mds:
        print("[ERROR] No se encontró *_INFORME_COMITE_FINAL.md", file=sys.stderr)
        return 1

    import unicodedata

    def norm(s: str) -> str:
        return unicodedata.normalize("NFC", s).casefold()

    text = final_mds[0].read_text(encoding="utf-8", errors="ignore")
    sections = re.split(r"(?m)^(?=#\s+|##\s+|###\s+)", text)

    # Dos niveles: FULL (núcleo del guion: PERFIL, Módulos 01/11/12/17/18, RESUMENES, subs clave)
    # y SKELETON (resto de módulos, ~900 chars, para que el guion cubra los 18 módulos).
    tier_full = re.compile(
        r"^(#\s+perfil\s+extra[ií]do|##\s+m[oó]dulo\s+(0?1|11|12|17|18)\b|##\s+resumen\s+parte\s+[1-4])"
    )
    tier_sub = re.compile(r"^###\s+(?:subsecci[oó]n\s+)?\**((2\.[1256])|(5\.5)|(6\.[12])|(10\.[134])|(16\.[12])|(17\.[1-5])|(18\.[1-5]))")
    tier_skeleton = re.compile(r"^##\s+m[oó]dulo\s+(\d{1,2})\b")

    CAP_FULL, CAP_SKEL, CAP_SUB = 2600, 900, 1400
    podcast_guide = (
        "> **REGLA CERO CONSOLA Y BANDA OBJETIVO PARA SA-6 (`*_PODCAST_GUION.md`: 58,000 a 70,000 bytes | 8,600 a 9,800 palabras | 90 a 110 intervenciones):**\n"
        "> - PROHIBIDO llamar a `run_command`. Redacta en 1 llamada `write_file` limpia y responde en 1 sola línea (`<= 25 palabras`): `PASS | <TICKER> | <ARCHIVO_GUION> | <BYTES> bytes`.\n"
        "> - Formato estricto `DIRECTOR: ...`, `ELENA: ...`, `MARCOS: ...`. Alterna réplicas ágiles y frases breves (4–12 palabras) con análisis numérico para mantener ritmo oral natural (~43–48 min, sin irte a 16,000 palabras).\n"
        "> - Español fonético limpio: cero siglas inglesas crudas (`ebitda`, `coste medio ponderado de capital`), cero `%` (escribe `por ciento`), cero decimales en cifras > 1,000 y todas las tildes/`ñ` correctas.\n\n"
    )
    extracted = [f"# BRIEF EJECUTIVO DESTILADO ({final_mds[0].name})\n\n" + podcast_guide]
    curr_len = len(extracted[0])
    counts = {"full": 0, "skel": 0, "sub": 0}

    for sec in sections:
        first_line = sec.strip().splitlines()[0] if sec.strip() else ""
        if not first_line:
            continue
        f = norm(first_line)
        snippet = sec.strip()
        cap = 0
        if tier_full.search(f):
            cap = 0 if ("módulo 17" in f or "módulo 18" in f or "resumen parte" in f) else CAP_FULL
            counts["full"] += 1
        elif tier_sub.search(f):
            cap = CAP_SUB
            counts["sub"] += 1
        elif tier_skeleton.search(f):
            cap = CAP_SKEL
            counts["skel"] += 1
        else:
            continue
        if cap and len(snippet) > cap:
            snippet = snippet[:cap] + "\n[...]\n"
        if curr_len + len(snippet) <= max_chars:
            extracted.append(snippet + "\n\n")
            curr_len += len(snippet) + 2

    full_brief = "".join(extracted)
    out_file = target_dir / "extracted_ocr_cache" / "brief_ppt_podcast.md"
    out_root = target_dir / "brief_ppt_podcast.md"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(full_brief, encoding="utf-8")
    out_root.write_text(full_brief, encoding="utf-8")
    print(
        f"=== BRIEF PPT/PODCAST GENERADO (EXIT 0) | {out_file.name} ({curr_len} bytes) "
        f"| full={counts['full']} skel={counts['skel']} sub={counts['sub']} ==="
    )
    return 0


def main():
    parser = argparse.ArgumentParser(description="Cliente + Auto-Daemon TencentDB-Agent-Memory para Gauntlet-Loop")
    parser.add_argument("--target-dir", required=True, help="Ruta a <COMPANY_DIR> o ROOT_DIR")
    parser.add_argument("--build", action="store_true", help="Asegura el demonio activo e indexa los PDFs")
    parser.add_argument("--query", type=str, default=None, help="Consulta híbrida bilingüe con límite de caracteres")
    parser.add_argument("--max-chars", type=int, default=6000, help="Presupuesto máximo de caracteres")
    parser.add_argument("--top-k", type=int, default=8, help="Bloques máximos a recuperar")
    parser.add_argument("--extract-brief", action="store_true", help="Destila brief_ppt_podcast.md")
    parser.add_argument("--brief-chars", type=int, default=42000, help="Presupuesto de chars del brief (independiente de --max-chars)")
    parser.add_argument("--build-facts-pack", action="store_true", help="Genera company_facts_pack.md con todos los datos clave en una sola llamada")
    parser.add_argument("--extract-m1-m15-digest", action="store_true", help="Destila borrador_parte1..4.md en m01_m15_digest.md para el 5º subagente (Módulos 16-18)")
    parser.add_argument("--ensure-daemon", action="store_true", help="Verifica/instala y arranca el demonio :8420")

    args = parser.parse_args()
    target = Path(args.target_dir).resolve()

    if args.ensure_daemon:
        ok = ensure_tdai_daemon(target)
        print(f"=== TDAI DAEMON STATUS: {'ONLINE (:8420)' if ok else 'FALLBACK LOCAL FTS5'} ===")
        sys.exit(0)

    if args.build_facts_pack:
        sys.exit(build_facts_pack(target))

    if args.extract_m1_m15_digest:
        sys.exit(extract_m1_to_m15_digest(target))

    if args.build:
        if (target / "extracted_ocr_cache").exists():
            sys.exit(build_company_memory(target))
        rc = 0
        for sub in sorted(target.iterdir()):
            if sub.is_dir() and (sub / "extracted_ocr_cache").exists():
                rc |= build_company_memory(sub)
        sys.exit(rc)

    if args.query:
        sys.exit(query_company_memory(target, args.query, max_chars=args.max_chars, top_k=args.top_k))

    if args.extract_brief:
        sys.exit(extract_brief_for_ppt_and_podcast(target, max_chars=args.brief_chars))

    parser.print_help()


if __name__ == "__main__":
    main()
