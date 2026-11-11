"""
Script determinista de regeneración batch de podcasts MP3 con 16 hilos.
Procesa las 6 carpetas principales:
- TO_PROCESS/AI
- TO_PROCESS/_Cartera_1
- TO_PROCESS/_Cartera_2
- TO_PROCESS/INDUSTRIA
- TO_PROCESS/SERVICIO
- FLASH_TO_PROCESS/REMAINING

Garantiza:
1. Cobertura completa del Módulo 01 al 18 sin saltar intervenciones.
2. Duración en ventana [40 min, 70 min] (2,400s - 4,200s).
3. Copia automática del MP3 generado a <root>/mp3/.
4. Eliminación física de archivos temporales .wav.
5. Ejecución concurrente con exactamente 16 workers independientes (1 por núcleo de CPU).
"""

import os
import sys
import glob
import json
import time
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT_DIRS = [
    r"C:\Users\david\Desktop\Momentum\TO_PROCESS\AI",
    r"C:\Users\david\Desktop\Momentum\TO_PROCESS\_Cartera_1",
    r"C:\Users\david\Desktop\Momentum\TO_PROCESS\_Cartera_2",
    r"C:\Users\david\Desktop\Momentum\TO_PROCESS\INDUSTRIA",
    r"C:\Users\david\Desktop\Momentum\TO_PROCESS\SERVICIO",
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\REMAINING",
]

SKIP_NAMES = {"_shared_engine", "doc", "mp3", "ppt", "charts", "extracted_ocr_cache", "gauntlet_logs", "logs"}
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BUILD_PODCAST_SCRIPT = os.path.join(SCRIPT_DIR, "build_podcast_kokoro.py")
PYTHON_EXE = sys.executable


def is_company_completed(company_dir: str) -> bool:
    manifest_path = os.path.join(company_dir, "podcast_synthesis_manifest.json")
    mp3_files = glob.glob(os.path.join(company_dir, "*_PODCAST_COMITE.mp3"))
    if not mp3_files or not os.path.exists(manifest_path):
        return False
    try:
        with open(manifest_path, "r", encoding="utf-8") as mf:
            mdata = json.load(mf)
        skipped = int(mdata.get("skipped_turns", 999))
        dur_sec = float(mdata.get("duration_seconds", 0.0))
        full_cov = bool(mdata.get("full_module_coverage_m01_m18", False))
        if skipped == 0 and full_cov and (2400.0 <= dur_sec <= 4200.0) and os.path.getsize(mp3_files[0]) > 20_000_000:
            return True
    except Exception:
        pass
    return False


def process_single_company(item) -> dict:
    idx, total_items, root_name, company_dir, ticker = item
    start_t = time.time()
    
    # Comprobar si ya está completada
    if is_company_completed(company_dir):
        mp3_files = glob.glob(os.path.join(company_dir, "*_PODCAST_COMITE.mp3"))
        dur_min = 0.0
        if mp3_files:
            try:
                import soundfile as sf
                dur_min = sf.info(mp3_files[0]).duration / 60.0
            except Exception:
                pass
        return {
            "status": "SKIPPED_ALREADY_DONE",
            "ticker": ticker,
            "root": root_name,
            "company_dir": company_dir,
            "duration_min": dur_min,
            "elapsed_s": time.time() - start_t,
        }

    env = os.environ.copy()
    env["KOKORO_THREADS"] = "1"
    env["KOKORO_SENTENCE_WORKERS"] = "1"
    env["PYTHONUNBUFFERED"] = "1"

    cmd = [
        PYTHON_EXE,
        BUILD_PODCAST_SCRIPT,
        "--target-dir", company_dir,
        "--force-rebuild-mp3",
        "--min-seconds", "2460",
        "--max-seconds", "4020",
    ]

    try:
        proc = subprocess.run(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        rc = proc.returncode
    except Exception as e:
        return {
            "status": "ERROR_LAUNCHING",
            "ticker": ticker,
            "root": root_name,
            "company_dir": company_dir,
            "error": str(e),
            "elapsed_s": time.time() - start_t,
        }

    # Limpiar .wav residual si quedase
    for wf in glob.glob(os.path.join(company_dir, "*.wav")):
        try:
            os.remove(wf)
        except Exception:
            pass

    if rc != 0:
        tail = "\n".join(proc.stdout.strip().split("\n")[-10:])
        return {
            "status": "FAILED",
            "ticker": ticker,
            "root": root_name,
            "company_dir": company_dir,
            "returncode": rc,
            "log_tail": tail,
            "elapsed_s": time.time() - start_t,
        }

    # Copiar MP3 a <root>/mp3/
    mp3_files = glob.glob(os.path.join(company_dir, "*_PODCAST_COMITE.mp3"))
    if not mp3_files:
        return {
            "status": "FAILED_NO_MP3",
            "ticker": ticker,
            "root": root_name,
            "company_dir": company_dir,
            "elapsed_s": time.time() - start_t,
        }

    mp3_path = mp3_files[0]
    root_mp3_dir = os.path.join(os.path.dirname(company_dir), "mp3")
    if os.path.isdir(root_mp3_dir):
        try:
            shutil.copy2(mp3_path, os.path.join(root_mp3_dir, os.path.basename(mp3_path)))
        except Exception as ce:
            print(f"[WARN] Error copiando a {root_mp3_dir}: {ce}")

    # Extraer duración final
    dur_min = 0.0
    try:
        import soundfile as sf
        dur_min = sf.info(mp3_path).duration / 60.0
    except Exception:
        pass

    return {
        "status": "SUCCESS",
        "ticker": ticker,
        "root": root_name,
        "company_dir": company_dir,
        "duration_min": dur_min,
        "elapsed_s": time.time() - start_t,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("================================================================================")
    print("   REGENERACIÓN MASIVA DE PODCASTS MP3 KOKORO (16 THREADS CONCURRENTES)")
    print("   Estándar: Cobertura Completa M01 a M18 | Ventana [40 min, 70 min]")
    print("================================================================================")

    all_companies = []
    for r in ROOT_DIRS:
        if not os.path.isdir(r):
            print(f"[WARN] Directorio no encontrado: {r}")
            continue
        rname = os.path.basename(r)
        subdirs = [
            os.path.join(r, d)
            for d in sorted(os.listdir(r))
            if os.path.isdir(os.path.join(r, d)) and d not in SKIP_NAMES and not d.startswith(".")
        ]
        with_guion = [c for c in subdirs if glob.glob(os.path.join(c, "*_PODCAST_GUION.md"))]
        for cdir in with_guion:
            ticker = os.path.basename(cdir)
            all_companies.append((rname, cdir, ticker))

    total = len(all_companies)
    print(f"\n[Init] Total de empresas con guion encontradas: {total}")
    for r in ROOT_DIRS:
        cnt = sum(1 for (rn, cd, tk) in all_companies if rn == os.path.basename(r))
        print(f"  - {os.path.basename(r)}: {cnt} empresas")

    items = [
        (i + 1, total, rn, cd, tk)
        for i, (rn, cd, tk) in enumerate(all_companies)
    ]

    num_threads = 16
    print(f"\n[Launch] Iniciando ThreadPoolExecutor con {num_threads} threads concurrentes...\n")
    sys.stdout.flush()

    completed_count = 0
    success_count = 0
    skipped_count = 0
    failed_count = 0
    failures = []
    start_global = time.time()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        future_map = {executor.submit(process_single_company, item): item for item in items}
        for future in as_completed(future_map):
            completed_count += 1
            res = future.result()
            tk = res["ticker"]
            rn = res["root"]
            status = res["status"]
            elapsed = res["elapsed_s"]

            if status == "SUCCESS":
                success_count += 1
                dur = res.get("duration_min", 0.0)
                print(
                    f"[{completed_count:3d}/{total:3d}] PASS | {rn:12s} | {tk:10s} | {dur:.1f} min ({dur*60.0:.0f}s) | Took: {elapsed:.1f}s",
                    flush=True,
                )
            elif status == "SKIPPED_ALREADY_DONE":
                skipped_count += 1
                dur = res.get("duration_min", 0.0)
                print(
                    f"[{completed_count:3d}/{total:3d}] SKIP (ya OK) | {rn:12s} | {tk:10s} | {dur:.1f} min",
                    flush=True,
                )
            else:
                failed_count += 1
                failures.append(res)
                err_msg = res.get("log_tail") or res.get("error") or "Unknown error"
                print(
                    f"[{completed_count:3d}/{total:3d}] FAIL | {rn:12s} | {tk:10s} | {err_msg[:90]}",
                    flush=True,
                )

    total_time = time.time() - start_global
    print("\n================================================================================")
    print(f"   RESUMEN FINAL DE EJECUCIÓN (Tiempo total: {total_time/60.0:.1f} min)")
    print(f"   Total procesadas: {completed_count}/{total}")
    print(f"   Éxitos nuevos   : {success_count}")
    print(f"   Ya completadas  : {skipped_count}")
    print(f"   Fallos          : {failed_count}")
    if failures:
        print("\n   Detalle de fallos:")
        for f in failures:
            print(f"     - {f['root']}/{f['ticker']}: {f.get('status')} | {f.get('log_tail', '')[:100]}")
    print("================================================================================")


if __name__ == "__main__":
    main()
