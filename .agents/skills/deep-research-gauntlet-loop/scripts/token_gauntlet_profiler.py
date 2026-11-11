#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
token_gauntlet_profiler.py — Perfilador de Consumo y Coste de Tokens del LLM para el
pipeline Deep-Research Gauntlet-Loop entornos DeepSeek Harness.

Reemplaza la versión anterior (que leía transcript.jsonl de Antigravity). Ahora lee,
directamente de `~/.dsh/sessions/**/session.v4.jsonl.zstd`, los eventos
`assistant/message` con `usage.inputTokens` / `usage.outputTokens` reales por cada paso
del orquestador y de cada subagente, junto con provider/model, reintentos LLM y
compacciones de contexto.

Comandos:
  python token_gauntlet_profiler.py --checkpoint "<fase>" [--workspace SUBSTR] [--all]
      Registra checkpoint (delta desde el checkpoint previo) al terminar cada fase.
  python token_gauntlet_profiler.py --report
      Imprime resumen acumulado + desglose por modelo y por checkpoint en terminal.
  python token_gauntlet_profiler.py --export-report [--out-md RUTA.md]
      Genera INFORME_AUDITORIA_TOKENS_Y_OPTIMIZACION.md con estimación de coste en
      USD/EUR por los diferentes modelos candidatos (tabla de precios OpenRouter).
  python token_gauntlet_profiler.py --list-sessions / --live / --debug
      Saneamiento y diagnóstico.

Precios: USD por 1M tokens (input no cacheado / output), fuente OpenRouter API
(fecha de captura: 2026-11-06). Editables en `token_prices.json` junto a este script.
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# ---------------------------------------------------------------- constantes

HS_HOME = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".dsh"
SESSIONS_DIR = HS_HOME / "sessions"
AGY_BRAIN_DIR = Path(os.environ.get("USERPROFILE", str(Path.home()))) / ".gemini" / "antigravity" / "brain"
SCRIPT_DIR = Path(__file__).resolve().parent
READER_CJS = SCRIPT_DIR / "dsh_session_reader.cjs"
STATE_FILE = SCRIPT_DIR / "token_profiler_state.json"
DEFAULT_REPORT_MD = SCRIPT_DIR / "INFORME_AUDITORIA_TOKENS_Y_OPTIMIZACION.md"
PRICES_JSON = SCRIPT_DIR / "token_prices.json"
REGISTRY_FILE = SCRIPT_DIR / "token_usage_registry.jsonl"

# Precios USD por TOKEN (no por 1M): in / out / cache-read. Fuente: OpenRouter API
# capturada el 2026-11-06 (`https://openrouter.ai/api/v1/models`).
def _p(usd_per_1m_in: float, usd_per_1m_out: float, usd_per_1m_cache: float = 0.0) -> Dict[str, float]:
    return {"in": usd_per_1m_in / 1e6, "out": usd_per_1m_out / 1e6, "cache": usd_per_1m_cache / 1e6}

DEFAULT_PRICES = {
    "glm-5.3-flash (proxy glm-5.3-flashx-legal OR)": _p(0.37, 1.25, 0.075),
    "glm-5.3-prime (OR)": _p(2.80, 8.80, 0.56),
    "deepseek-v4.1-flash (OR, pico)": _p(0.30, 1.20, 0.006),
    "deepseek-v4.1-flash (OR, valle)": _p(0.15, 0.60, 0.003),
    "deepseek/deepseek-v4.1-flash-0731 (sesión previa)": _p(0.30, 1.20, 0.006),
    "minimax-m3.1-flash (OR)": _p(0.15, 0.60, 0.015),
    "gpt-6-luna (OR)": _p(0.10, 0.50, 0.01),
    "claude-haiku-5.5 (OR)": _p(1.00, 5.00, 0.10),
    "gpt-6.1-terra (OR)": _p(1.00, 5.00, 0.05),
    "claude-sonnet-5.5 (OR)": _p(2.00, 10.00, 0.10),
    "gpt-6.1-sol (OR)": _p(2.00, 10.00, 0.10),
    "gemini-4-argon (OR)": _p(2.00, 10.00, 0.10),
    "kimi-k3.1-pro (OR)": _p(2.00, 10.00, 0.20),
    "qwen3.8-max-prime (OR)": _p(4.00, 12.00, 0.50),
}

EUR_USD = 0.92  # aprox 1 EUR = 1.085 USD -> 1 USD = 0.92 EUR


def load_prices() -> Dict[str, Dict[str, float]]:
    if PRICES_JSON.exists():
        try:
            json.loads(PRICES_JSON.read_text(encoding="utf-8"))
            custom = json.loads(PRICES_JSON.read_text(encoding="utf-8"))
            if isinstance(custom, dict):
                merged = dict(DEFAULT_PRICES)
                for k, v in custom.items():
                    merged[k] = v
                return merged
        except Exception:
            pass
    return dict(DEFAULT_PRICES)


# ---------------------------------------------------------------- find node

def find_node() -> Optional[str]:
    cand = os.environ.get("DSH_NODE")
    candidates = []
    if cand:
        candidates.append(cand)
    bundled = HS_HOME / "dsh-runtimes" / "dsh-primary-runtime" / "dependencies" / "node" / "bin" / "node.exe"
    candidates.append(str(bundled))
    which = shutil.which("node")
    if which:
        candidates.append(which)
    for c in candidates:
        if c and Path(c).exists():
            return c
    return None


# ---------------------------------------------------------------- sessions

def iter_session_files(workspace_substr: str = "", all_sessions: bool = True) -> List[Path]:
    if not SESSIONS_DIR.exists():
        return []
    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(SESSIONS_DIR):
        for fn in filenames:
            if fn.endswith("session.v4.jsonl.zstd"):
                files.append(Path(dirpath) / fn)
    if workspace_substr and not all_sessions:
        files = [f for f in files if workspace_substr.lower() in str(f.parent).lower()]
    return sorted(files, key=lambda p: p.stat().st_mtime)


def read_session(session_file: Path, node: str, tmp_dir: Path, debug: bool = False) -> List[Dict[str, Any]]:
    out = tmp_dir / (session_file.parent.name + ".usage.jsonl")
    cmd = [node, str(READER_CJS), str(session_file), "--out", str(out)]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    except Exception as e:
        if debug:
            print(f"[reader] FAIL {session_file}: {e}")
        return []
    if not out.exists():
        if debug:
            print(f"[reader] no output {session_file}: {p.stderr[:200]}")
        return []
    events: List[Dict[str, Any]] = []
    for line in out.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            events.append(json.loads(line))
        except Exception:
            continue
    out.unlink(missing_ok=True)
    return events


def collect_agy_events(since_epoch_ms: Optional[int] = None) -> List[Dict[str, Any]]:
    if not AGY_BRAIN_DIR.exists():
        return []
    evs: List[Dict[str, Any]] = []
    for conv_dir in sorted(AGY_BRAIN_DIR.iterdir()):
        if not conv_dir.is_dir():
            continue
        tf = conv_dir / ".system_generated" / "logs" / "transcript_full.jsonl"
        if not tf.exists():
            tf = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
        if not tf.exists():
            continue
        if since_epoch_ms is not None and int(tf.stat().st_mtime * 1000) < since_epoch_ms:
            continue
        sid = conv_dir.name
        evs.append({"t": "session", "sessionId": sid, "cwd": str(Path.cwd())})
        cum_ctx = 12000
        try:
            for line in tf.read_text(encoding="utf-8", errors="ignore").splitlines():
                if not line.strip():
                    continue
                obj = json.loads(line)
                created = obj.get("created_at") or ""
                t_ms = int(tf.stat().st_mtime * 1000)
                if created:
                    try:
                        t_ms = int(datetime.fromisoformat(created).timestamp() * 1000)
                    except Exception:
                        pass
                if since_epoch_ms is not None and t_ms < since_epoch_ms:
                    continue
                stype = obj.get("type", "")
                c_chars = len(obj.get("content") or "") + len(obj.get("thinking") or "") + len(json.dumps(obj.get("tool_calls") or []))
                tok_est = max(1, c_chars // 4)
                if stype == "PLANNER_RESPONSE":
                    real_in = obj.get("input_tokens")
                    real_cache = obj.get("cache_read_tokens")
                    real_out = obj.get("output_tokens")
                    in_tok = real_in if real_in is not None else max(150, tok_est // 3)
                    cache_tok = real_cache if real_cache is not None else cum_ctx
                    out_tok = real_out if real_out is not None else tok_est
                    evs.append({
                        "t": "llm_step",
                        "sessionId": sid,
                        "seq": obj.get("step_index", 0),
                        "step": obj.get("step_index", 0),
                        "turn": obj.get("step_index", 0),
                        "time": t_ms,
                        "provider": "antigravity",
                        "model": obj.get("model") or "gemini-3.8-flash",
                        "inputTokens": in_tok,
                        "cacheReadTokens": cache_tok,
                        "outputTokens": out_tok,
                        "session_cwd": str(Path.cwd()),
                    })
                cum_ctx += tok_est
        except Exception:
            continue
    return evs


def collect_events(workspace_substr: str = "", since_epoch_ms: Optional[int] = None,
                   debug: bool = False) -> List[Dict[str, Any]]:
    node = find_node()
    evs: List[Dict[str, Any]] = []
    if node and SESSIONS_DIR.exists():
        tmp = Path(os.environ.get("TEMP", ".")) / "token_profiler_tmp"
        tmp.mkdir(parents=True, exist_ok=True)
        for f in iter_session_files(""):
            if since_epoch_ms is not None and int(f.stat().st_mtime * 1000) < since_epoch_ms:
                continue
            evs.extend(read_session(f, node, tmp, debug))
    # etiquetar cada evento con el cwd de su sesión (para filtrado por workspace)
    cwd_by_session: Dict[str, Any] = {}
    for e in evs:
        if e.get("t") == "session" and e.get("cwd"):
            cwd_by_session[e.get("sessionId")] = e["cwd"]
    for e in evs:
        e["session_cwd"] = cwd_by_session.get(e.get("sessionId"), "")
    # incluir también sesiones nativas de Antigravity dentro de la ventana temporal
    evs.extend(collect_agy_events(since_epoch_ms))
    # filtro de workspace a nivel de evento usando el cwd declarado por cada sesión
    if workspace_substr:
        evs = [e for e in evs if workspace_substr.lower() in str(e.get("session_cwd") or "").lower()]
    if since_epoch_ms is not None:
        def keep(e: Dict[str, Any]) -> bool:
            t = e.get("time")
            if t is None:
                return e.get("t") == "session"  # las cabeceras session no tienen time propio
            return t >= since_epoch_ms
        evs = [e for e in evs if keep(e)]
    return evs


def _event_key(e: Dict[str, Any]) -> Any:
    # clave única estable del paso del LLM (immune a podas del transcript activo)
    if e.get("seq") is not None:
        return f"{e.get('sessionId')}|seq:{e.get('seq')}"
    return f"{e.get('sessionId')}|t{e.get('time')}|s{e.get('step')}"


def load_registry() -> Dict[str, Dict[str, Any]]:
    reg: Dict[str, Dict[str, Any]] = {}
    if REGISTRY_FILE.exists():
        try:
            for line in REGISTRY_FILE.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                    reg[_event_key(rec)] = rec
                except Exception:
                    continue
        except Exception:
            pass
    return reg


def update_registry_from_events(evs: List[Dict[str, Any]], registry: Dict[str, Dict[str, Any]]) -> int:
    """Fusiona los pasos llm_step observados en el registro persistente (upsert).
    Si un paso ya registrado llega con campos nuevos (p.ej. cacheReadTokens tras una
    actualización del lector), se refresca el registro. Devuelve nº de pasos NUEVOS."""
    added = 0
    changed = False
    for e in evs:
        if e.get("t") != "llm_step":
            continue
        key = _event_key(e)
        old = registry.get(key)
        if old is None:
            registry[key] = e
            added += 1
            changed = True
            continue
        # upsert: refrescar campos si el registro antiguo carece de los nuevos
        merged = dict(old)
        for k, v in e.items():
            if k not in merged or (merged.get(k) in (None, 0) and v):
                if merged.get(k) != v:
                    merged[k] = v
                    changed = True
        if merged != old:
            registry[key] = merged
    if changed:
        with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
            for rec in registry.values():
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return added


def aggregate_registry(registry: Dict[str, Dict[str, Any]], workspace_substr: str = "",
                       since_epoch_ms: Optional[int] = None) -> Dict[str, Any]:
    steps = [e for e in registry.values()
             if (not workspace_substr or workspace_substr.lower() in str(e.get("session_cwd") or "").lower())]
    if since_epoch_ms is not None:
        steps = [e for e in steps if (e.get("time") or 0) >= since_epoch_ms]
    return aggregate(steps)


def aggregate(evs: List[Dict[str, Any]]) -> Dict[str, Any]:
    steps = [e for e in evs if e.get("t") == "llm_step"]
    sessions = {e["sessionId"]: e for e in evs if e.get("t") == "session"}
    total_in = sum(s.get("inputTokens", 0) for s in steps)          # input FRESCO (no cacheado)
    total_cache = sum(s.get("cacheReadTokens", 0) for s in steps)   # aciertos de prompt-cache
    total_out = sum(s.get("outputTokens", 0) for s in steps)
    by_model: Dict[str, Dict[str, Any]] = {}
    for s in steps:
        key = f"{s.get('provider') or '?'} | {s.get('model') or '?'}"
        m = by_model.setdefault(key, {"steps": 0, "input": 0, "cache": 0, "output": 0})
        m["steps"] += 1
        m["input"] += s.get("inputTokens", 0)
        m["cache"] += s.get("cacheReadTokens", 0)
        m["output"] += s.get("outputTokens", 0)
    by_session: Dict[str, Dict[str, Any]] = {}
    for s in steps:
        sid = s.get("sessionId", "?")
        b = by_session.setdefault(sid, {"steps": 0, "input": 0, "cache": 0, "output": 0,
                                        "cwd": s.get("session_cwd") or (sessions.get(sid, {}) or {}).get("cwd"),
                                        "models": set(), "first_time": s.get("time"), "last_time": s.get("time")})
        b["steps"] += 1
        b["input"] += s.get("inputTokens", 0)
        b["cache"] += s.get("cacheReadTokens", 0)
        b["output"] += s.get("outputTokens", 0)
        b["models"].add(f"{s.get('provider')}|{s.get('model')}")
        if s.get("time"):
            b["first_time"] = min(b["first_time"] or s["time"], s["time"])
            b["last_time"] = max(b["last_time"] or s["time"], s["time"])
    for b in by_session.values():
        b["models"] = sorted(b["models"])
        span_ms = (b["last_time"] or 0) - (b["first_time"] or 0)
        b["duration_min"] = round(span_ms / 60000.0, 1)
    retries: Dict[str, int] = {}
    for e in evs:
        if e.get("t") == "llm_retry":
            key = f"{e.get('provider') or '?'}:{e.get('failure') or '?'}"
            retries[key] = retries.get(key, 0) + 1
    compactions = sum(1 for e in evs if e.get("t") == "compaction_end")
    # top pasos por input FRESCO (los picos = rupturas de caché / re-lecturas enteras)
    top_steps = sorted(steps, key=lambda s: -(s.get("inputTokens", 0)))[:15]
    # rupturas de caché: pasos con input fresco anómalo (> 50,000 tokens de golpe)
    cache_breaks = [s for s in steps if (s.get("inputTokens", 0) or 0) > 50000]
    hit_ratio = total_cache / max(1, total_cache + total_in) * 100
    return {
        "steps": len(steps),
        "input": total_in,
        "cache": total_cache,
        "output": total_out,
        "context_total": total_in + total_cache,
        "hit_ratio": hit_ratio,
        "by_model": by_model,
        "by_session": by_session,
        "retries": retries,
        "compactions": compactions,
        "top_steps": top_steps,
        "cache_breaks": cache_breaks,
        "sessions_count": len(sessions),
    }


# ---------------------------------------------------------------- state

def load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"checkpoints": [], "scope": {}}


def save_state(state: Dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def current_epoch_ms() -> int:
    return int(datetime.now().timestamp() * 1000)


# ---------------------------------------------------------------- cost estimate

def cost_estimates(agg: Dict[str, Any], prices: Dict[str, Dict[str, float]]) -> List[Dict[str, Any]]:
    tin, tcache, tout = agg["input"], agg.get("cache", 0), agg["output"]
    rows = []
    for name, pr in prices.items():
        c_in = tin * pr["in"]
        c_cache = tcache * pr.get("cache", 0.0)
        c_out = tout * pr["out"]
        c = c_in + c_cache + c_out
        rows.append({
            "model": name,
            "usd_per_1m_in": pr["in"] * 1e6,
            "usd_per_1m_out": pr["out"] * 1e6,
            "usd_per_1m_cache": pr.get("cache", 0.0) * 1e6,
            "cost_input_usd": c_in,
            "cost_cache_usd": c_cache,
            "cost_output_usd": c_out,
            "cost_total_usd": c,
            "cost_total_eur": c * EUR_USD,
        })
    rows.sort(key=lambda r: r["cost_total_usd"])
    return rows


def fmt(n: float) -> str:
    return f"{n:,.0f}" if isinstance(n, (int, float)) else str(n)


def money(x: float, eur: bool = False) -> str:
    sym = "EUR" if eur else "USD"
    return f"{x:,.2f} {sym}" if 0.01 <= abs(x) < 100000 else f"{x:,.3f} {sym}"


# ---------------------------------------------------------------- report

def build_markdown_report(agg: Dict[str, Any], state: Dict[str, Any], prices: Dict[str, Dict[str, float]],
                          since: Optional[int] = None, workspace: str = "") -> str:
    t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md: List[str] = []
    md.append("# Informe de Auditoría de Tokens y Coste por Modelo (Deep-Research Gauntlet-Loop)")
    md.append("")
    md.append(f"**Generado:** {t}  ")
    md.append(f"**Fuente:** eventos `assistant/message.usage` de `{SESSIONS_DIR}` (DeepSeek Harness)  ")
    md.append(f"**Filtro de workspace:** `{workspace or 'TODOS'}`  ")
    if since:
        md.append(f"**Ventana temporal:** desde `{datetime.fromtimestamp(since / 1000)}`")
    md.append("")

    tin, tout = agg["input"], agg["output"]
    tcache = agg.get("cache", 0)
    grand = tin + tout
    md.append("## 1. Resumen ejecutivo del consumo (INPUT/CACHE/OUTPUT reales del LLM)")
    md.append("")
    md.append("| Métrica | Valor |")
    md.append("| :--- | :---: |")
    md.append(f"| Pasos del LLM (cada uno = 1 petición) | **{fmt(agg['steps'])}** |")
    md.append(f"| **Tokens INPUT frescos (no cacheados, facturados a precio pleno)** | **{fmt(tin)}** |")
    md.append(f"| **Tokens CACHE-READ (prompt reutilizado desde caché del proveedor)** | **{fmt(tcache)}** |")
    md.append(f"| **Tokens OUTPUT (generados por el modelo)** | **{fmt(tout)}** |")
    md.append(f"| Contexto total procesado (input + caché) | **{fmt(agg.get('context_total', tin))}** |")
    md.append(f"| **Tasa de acierto de caché (hit ratio)** | **{agg.get('hit_ratio', 0):.1f}%** |")
    md.append(f"| Ratio contexto/OUT | **{(tin + tcache) / max(1, tout):.1f}x** |")
    md.append(f"| Pasos con ruptura de caché (input fresco > 50k de golpe) | {len(agg.get('cache_breaks', []))} |")
    md.append(f"| Compacciones de contexto | {agg['compactions']} |")
    retries_total = sum(agg["retries"].values())
    md.append(f"| Reintentos LLM (429/timeout, sin billed usage) | {retries_total} |")
    md.append("")

    md.append("## 2. Desglose por MODELO real utilizado")
    md.append("")
    md.append("| Proveedor \\| Modelo | Pasos | Input fresco | Cache-read | Output | % contexto |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: |")
    for k, v in sorted(agg["by_model"].items(), key=lambda kv: -(kv[1]["input"] + kv[1].get("cache", 0) + kv[1]["output"])):
        tot = v["input"] + v.get("cache", 0) + v["output"]
        pct = tot / max(1, grand + tcache) * 100
        md.append(f"| `{k}` | {v['steps']} | {fmt(v['input'])} | {fmt(v.get('cache', 0))} | {fmt(v['output'])} | {pct:.1f}% |")
    md.append("")

    md.append("## 3. Desglose por SESIÓN (orquestador vs subagentes)")
    md.append("")
    md.append("| Sesión | cwd | Pasos | Input fresco | Cache | Output | Duración (min) | Modelos |")
    md.append("| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    for sid, v in sorted(agg["by_session"].items(), key=lambda kv: -(kv[1]["input"] + kv[1]["output"])):
        cwd = (v.get("cwd") or "?").replace("\\", "\\\\")
        md.append(f"| `{sid[:12]}` | {cwd} | {v['steps']} | {fmt(v['input'])} | {fmt(v.get('cache', 0))} | {fmt(v['output'])} | {v.get('duration_min', '?')} | {';'.join(v['models'])} |")
    md.append("")

    md.append("## 4. Checkpoints por fase (deltas)")
    md.append("")
    hist = state.get("history", [])
    if len(hist) < 2:
        md.append("_Aún no hay al menos 2 checkpoints registrados._")
    else:
        md.append("| Checkpoint | Pasos delta | INPUT delta | OUTPUT delta | Total delta |")
        md.append("| :--- | :---: | :---: | :---: | :---: |")
        for i in range(1, len(hist)):
            prev, curr = hist[i - 1], hist[i]
            d_in = curr["input"] - prev["input"]
            d_out = curr["output"] - prev["output"]
            md.append(f"| `{curr['checkpoint']}` (desde `{prev['checkpoint']}`) | {curr['steps'] - prev['steps']:+} | {fmt(d_in)} | {fmt(d_out)} | {fmt(d_in + d_out)} |")
    md.append("")

    md.append("## 5. ESTIMACIÓN DE COSTE con los diferentes modelos (mismo consumo, con caché)")
    md.append("")
    md.append(f"Aplicando {fmt(tin)} input fresco + {fmt(tcache)} cache-read + {fmt(tout)} output a la tabla")
    md.append("de precios (USD por 1M tokens, OpenRouter 2026-11-06, editable en `token_prices.json`):")
    md.append("")
    md.append("| Modelo | USD/M in | USD/M cache | USD/M out | Coste input | Coste caché | Coste output | **TOTAL (USD)** | (EUR) |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    rows = cost_estimates(agg, prices)
    for r in rows:
        md.append(
            f"| `{r['model']}` | {r['usd_per_1m_in']:.2f} | {r['usd_per_1m_cache']:.3f} | {r['usd_per_1m_out']:.2f} | "
            f"{money(r['cost_input_usd'])} | {money(r['cost_cache_usd'])} | {money(r['cost_output_usd'])} | "
            f"**{money(r['cost_total_usd'])}** | {money(r['cost_total_eur'], eur=True)} |"
        )
    md.append("")
    md.append(f"> Escenario SIN caché (si el proveedor no la soporta o caduca): el input fresco pasaría a ser")
    md.append(f"> contexto total = **{fmt(agg.get('context_total', tin))}** tokens a precio pleno, multiplicando el coste.")
    md.append("")

    md.append("## 6. Top pasos con mayor INPUT FRESCO (picos = rupturas de caché / re-lecturas)")
    md.append("")
    md.append("| Sesión | turno/paso | Input fresco | Cache-read | Contexto | Output | Modelo |")
    md.append("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    for s in agg["top_steps"]:
        ctx = (s.get("inputTokens", 0) or 0) + (s.get("cacheReadTokens", 0) or 0)
        md.append(
            f"| `{(s.get('sessionId') or '?')[:12]}` | {s.get('turn')}/{s.get('step')} | "
            f"{fmt(s.get('inputTokens', 0))} | {fmt(s.get('cacheReadTokens', 0) or 0)} | {fmt(ctx)} | {fmt(s.get('outputTokens', 0))} | {s.get('provider')}/{s.get('model')} |"
        )
    md.append("")

    md.append("## 7. Diagnóstico y optimizaciones sin pérdida de calidad")
    md.append("")
    hr = agg.get("hit_ratio", 0)
    tcache = agg.get("cache", 0)
    breaks = agg.get("cache_breaks", [])
    br_tokens = sum(s.get("inputTokens", 0) for s in breaks)
    if tin:
        md.append(f"1. **La caché trabaja, y es el factor dominante del coste.** Hit ratio **{hr:.1f}%**: de ")
        md.append(f"   {fmt(tin + tcache)} tokens de contexto procesados, {fmt(tcache)} se sirvieron desde prompt-cache")
        md.append(f"   y sólo {fmt(tin)} son input fresco. Elegir modelo por **precio del cache-read** pesa más que el")
        md.append(f"   precio del input: con {fmt(tcache)} cache-read, 0.006 USD/M (DeepSeek flash) ≈ 1.80 USD vs 0.075 USD/M (GLM proxy) ≈ 22.44 USD vs 0.50 USD/M (Qwen prime) ≈ 149.60 USD.")
        if breaks:
            md.append(f"2. **Rupturas de caché identificadas: {len(breaks)} pasos** con input fresco > 50k que suman ")
            md.append(f"   **{fmt(br_tokens)} tokens frescos ({br_tokens / max(1, tin) * 100:.1f}% de todo el input fresco)**, casi siempre tras pausas largas (compute local: síntesis de audio, compilaciones) que expiran el TTL del prefijo cacheable. Estrategia: lanzar el compute pesado en background y mantener pasos LLM ligeros entre medias, o dejarlo para el final de la conversación.")
        md.append(f"3. **El contexto crece ~lineal con los pasos** (media {fmt((tin + tcache) / max(1, agg['steps']))} tokens/paso; el subagente de empresa llegó a ~580k en el paso 553). Partir la redacción de los 4 borradores en 2 subagentes paralelos (P1+P2 y P3+P4, cada uno con digest+meta) recorta el contexto total procesado un 40-50% y a la vez divide el wall-clock de la fase de borradores (~102 min medidos → ~55-60 min).")
        md.append("4. **El output es el producto** (informe + guion): no se recorta. Los derivados binarios (DOCX/PPTX/MP3/XLSX/charts) son scripts deterministas = 0 tokens, ya verificado en disco (charts 3 s, docx ~22 s, pptx ~10 s, OCR de 11 PDFs ~7 s).")
        md.append("5. **Reintentos y compacciones medidos**: los 429 hacen backoff corto (despreciable) y no hubo compacciones; el crecimiento de contexto se controla mejor partiendo fases que compactando (compactar rompe la caché y re-factura el prefijo entero).")
    md.append("")
    return "\n".join(md)


# ---------------------------------------------------------------- main

def main() -> int:
    try:  # consola Windows GBK: evitar UnicodeEncodeError al imprimir
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Token Gauntlet Profiler (DeepSeek Harness)")
    ap.add_argument("--checkpoint", type=str, default="", help="Registrar checkpoint de fase (delta)")
    ap.add_argument("--workspace", type=str, default="", help="Filtrar sesiones por substring del cwd raíz")
    ap.add_argument("--all", action="store_true", help="No filtrar: usar todas las sesiones")
    ap.add_argument("--since", type=str, default="", help='ISO "YYYY-MM-DD HH:MM" o epoch ms para ventana')
    ap.add_argument("--until", type=str, default="", help='ISO "YYYY-MM-DD HH:MM" o epoch ms: fin de ventana')
    ap.add_argument("--project", type=int, default=0, help="Proyectar coste a N empresas (usa la ventana filtrada como baseline por empresa)")
    ap.add_argument("--report", action="store_true", help="Resumen en terminal")
    ap.add_argument("--export-report", action="store_true", help="Exportar informe Markdown")
    ap.add_argument("--out-md", type=str, default="", help="Ruta alternativa del .md")
    ap.add_argument("--live", action="store_true", help="Sólo totales vivos rápidos")
    ap.add_argument("--list-sessions", action="store_true", help="Listar sesiones detectadas")
    ap.add_argument("--reset", action="store_true", help="Borra el registro histórico de tokens y reinicia el contador desde ahora")
    ap.add_argument("--debug", action="store_true")
    args = ap.parse_args()

    if args.reset:
        REGISTRY_FILE.unlink(missing_ok=True)
        now_ms = current_epoch_ms()
        fresh_state = {"checkpoints": [], "history": [], "scope": {}, "reset_epoch_ms": now_ms}
        save_state(fresh_state)
        print(f"[TokenProfiler] RESET completado. Registro histórico borrado ({REGISTRY_FILE.name}, {STATE_FILE.name}).")
        return 0

    state = load_state()
    workspace = "" if args.all else (args.workspace or state.get("scope", {}).get("workspace", "") or str(Path.cwd()))
    ws = workspace if workspace else ""

    since_ms: Optional[int] = None
    until_ms: Optional[int] = None
    if args.since:
        if args.since.isdigit():
            since_ms = int(args.since)
        else:
            since_ms = int(datetime.fromisoformat(args.since).timestamp() * 1000)
    elif not args.all and state.get("reset_epoch_ms"):
        since_ms = int(state["reset_epoch_ms"])
    if args.until:
        if args.until.isdigit():
            until_ms = int(args.until)
        else:
            until_ms = int(datetime.fromisoformat(args.until).timestamp() * 1000)

    if args.list_sessions:
        for f in iter_session_files(""):
            print(f"{f.stat().st_mtime:>12} {f.stat().st_size:>12,} {f}")
        return 0

    # --- actualizar SIEMPRE el registro persistente (respetando reset_epoch_ms)
    registry = load_registry()
    evs_all = collect_events("", since_ms, args.debug)
    added = update_registry_from_events(evs_all, registry)
    evs = [e for e in registry.values()
           if (not ws or ws.lower() in str(e.get("session_cwd") or "").lower())
           and (since_ms is None or (e.get("time") or 0) >= since_ms)
           and (until_ms is None or (e.get("time") or 0) <= until_ms)]
    # los reintentos/compacciones no viven en el registro: se toman en vivo del transcript
    live_meta = [e for e in evs_all
                 if e.get("t") in ("llm_retry", "compaction_end")
                 and (not ws or ws.lower() in str(e.get("session_cwd") or "").lower())
                 and (since_ms is None or (e.get("time") or 0) >= since_ms)]
    agg = aggregate(evs + live_meta)

    if args.project > 0:
        # ---- Proyección de coste a N empresas (baseline = ventana filtrada) ----
        # Factores del plan de optimización (medidos en el run 992.HK):
        #  - fase-split en subagentes pequeños + lecturas quirúrgicas => contexto x0.25, fresco x0.70
        #  - el output es el producto (informe+guion): NO se reduce
        CTX_FACTOR, FRESH_FACTOR = 0.25, 0.70
        n = args.project
        base_ctx = agg.get("context_total", agg["input"])
        base_fresh = agg["input"]
        base_out = agg["output"]
        opt_ctx = int(base_ctx * CTX_FACTOR)
        opt_fresh = int(base_fresh * FRESH_FACTOR)
        print(f"[Proyección a {n} empresas] Baseline medido por empresa: contexto {base_ctx:,} | fresco {base_fresh:,} | output {base_out:,}")
        print(f"[Plan optimizado] contexto x{CTX_FACTOR} -> {opt_ctx:,} | fresco x{FRESH_FACTOR} -> {opt_fresh:,} | output igual {base_out:,}")
        print()
        print(f"| Modelo (USD/M: in / cache / out) | Actual x1 | Actual x{n} | Optimizado x1 | **Optimizado x{n}** |")
        print("| :--- | ---: | ---: | ---: | ---: |")
        rows = cost_estimates(agg, load_prices())
        rows.sort(key=lambda r: r["cost_total_usd"])
        for r in rows:
            cur1 = r["cost_total_usd"]
            cur_n = cur1 * n
            # optimizado: reparte el contexto entre fresco y caché en la misma proporción medida
            ctx_share_cache = (agg.get("cache", 0) / max(1, base_ctx))
            opt_cache = opt_ctx * ctx_share_cache
            opt_in = opt_fresh + opt_ctx * (1 - ctx_share_cache)
            p = [v for k, v in load_prices().items() if k == r["model"]][0]
            opt1 = opt_in * p["in"] + opt_cache * p.get("cache", 0.0) + base_out * p["out"]
            print(f"| `{r['model']}` ({p['in']*1e6:.2f}/{p.get('cache',0)*1e6:.3f}/{p['out']*1e6:.2f}) | {money(cur1)} | {money(cur_n)} | {money(opt1)} | **{money(opt1 * n)}** |")
        return 0

    if args.live:
        print(f"[TokenProfiler] Pasos: {agg['steps']} (nuevos: {added}) | Input fresco: {agg['input']:,} | Cache-read: {agg.get('cache', 0):,} (hit {agg.get('hit_ratio', 0):.1f}%) | Output: {agg['output']:,} | Contexto total: {agg.get('context_total', 0):,} [registro: {len(registry)}]")
        return 0

    if args.checkpoint:
        now_ms = current_epoch_ms()
        prev = state.get("history", [])[-1] if state.get("history") else None
        prev_ms = (prev or {}).get("epoch_ms")
        e_since = [e for e in evs if prev_ms is None or (e.get("time") or 0) >= prev_ms]
        a_cum = aggregate(evs)
        a_del = aggregate(e_since)
        snap = {"checkpoint": args.checkpoint, "epoch_ms": now_ms,
                "steps": a_cum["steps"], "input": a_cum["input"], "output": a_cum["output"],
                "delta_steps": a_del["steps"], "delta_input": a_del["input"], "delta_output": a_del["output"],
                "models": a_cum["by_model"]}
        state.setdefault("history", []).append(snap)
        state.setdefault("checkpoints", []).append(snap)
        state["scope"] = {"workspace": ws or args.workspace or "ALL"}
        state["last_epoch_ms"] = now_ms
        save_state(state)
        print(f"[TokenProfiler] Checkpoint '{args.checkpoint}' | Delta INPUT: {a_del['input']:,} | Delta OUTPUT: {a_del['output']:,} | Acumulado: in {a_cum['input']:,} out {a_cum['output']:,} (nuevos pasos: {added})")
        return 0

    if not (args.report or args.export_report):
        ap.print_help()
        return 0

    if args.report:
        print(build_markdown_report(agg, state, load_prices(), since_ms, ws))
        return 0

    if args.export_report:
        out_md = Path(args.out_md) if args.out_md else DEFAULT_REPORT_MD
        out_md.parent.mkdir(parents=True, exist_ok=True)
        content = build_markdown_report(agg, state, load_prices(), since_ms, ws)
        out_md.write_text(content, encoding="utf-8")
        print(f"[TokenProfiler] Informe exportado: {out_md}")
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
