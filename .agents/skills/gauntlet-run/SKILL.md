---
name: gauntlet-run
description: Lanzador del pipeline Deep-Research Gauntlet sobre un ROOT_DIR de empresas. Úsalo cuando el usuario diga "lanza gauntlet", "analiza las empresas de <carpeta>", "procesa ROOT_DIR" o similar. Ejecuta en modo 100% autónomo el skill deep-research-gauntlet-loop con las reglas operativas V3.2 Ultra-Lean Hybrid del workspace.
---

# gauntlet-run (V3.6 Ultra-Lean Hybrid)

Atajo para lanzar el pipeline institucional completo sobre `ROOT_DIR` (carpeta con una subcarpeta de PDFs por empresa).

## Parámetros opcionales que el usuario puede indicar en el prompt
- **Paralelismo (`PARALLEL`):** nº de empresas/agentes simultáneos (por defecto `4`; recomendado `12–16` en lotes grandes).
  - **Aviso y Sugerencia de TTL de Caché (`> 16` subagentes — Estrategia 3 sin bloqueo):** Si el usuario solicita `> 16` subagentes simultáneos (ej. `24` o `32`), el orquestador **muestra un breve `[WARNING TTL CACHÉ]`** indicando que la franja óptima para evitar que las colas del proveedor superen el TTL de 5 min de caché (y disparen tokens de input fresco) es **`12–16` subagentes**, pero **ejecuta inmediatamente el número exacto de threads/subagentes pedido por el usuario (`16`, `24`, `32`+)** si así lo indica o confirma.
- **Selección de empresas:** lista opcional de tickers o `sin podcast`.
- **Dos niveles de LLM (`CORE_MODEL` + `LIGHT_MODEL`) con Fallback Automático Multi-LLM:**
  - En Antigravity, `invoke_subagent` admite los selectores `inherit | pro | flash | flash_lite` (`inherit` usa siempre el LLM activo que hayas seleccionado arriba en el chat: Gemini, Claude, GPT, etc.).
  - **Por defecto (si no se especifica):** `CORE_MODEL = "inherit"` (para `SA-1`, `SA-2`, `SA-3` y `SA-5`) y `LIGHT_MODEL = "flash"` (para `SA-4` y `SA-6`).
  - **Personalizable en el prompt:** el usuario puede escribir:
    - `"modelos: pro + flash"` -> `CORE_MODEL="pro"`, `LIGHT_MODEL="flash"`
    - `"modelos: inherit + flash_lite"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="flash_lite"`
    - `"modelo_unico: inherit"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="inherit"` (fuerza 100% el mismo LLM de la sesión en todas las fases).
    - `"modo: ultra-ahorro"` -> incluye también `SA-1` en `LIGHT_MODEL`.
  - **Regla de Fallback Automático:** si ejecutas el pipeline con otro LLM distinto de Gemini o si `LIGHT_MODEL` (`flash`/`flash_lite`) no está disponible, agota cuota o devuelve error al invocar el subagente, **cambia inmediatamente `LIGHT_MODEL = "inherit"` (el mismo LLM activo de la sesión)** y continúa sin interrumpir el lote.

## Procedimiento autónomo
1. Lee `.agents/skills/deep-research-gauntlet-loop/SKILL.md` y `.agents/skills/deep-research-gauntlet-loop/references/ORCHESTRATION_V2_PHASE_SPLIT.md` en `UNATTENDED DEEP-RESEARCH MODE`.
2. Define `ENGINE = c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts` y despliega los scripts actualizados en `ROOT_DIR\_shared_engine\` y en cada subcarpeta de empresa.
3. Reinicia/arranca el profiler: `python "ENGINE\token_gauntlet_profiler.py" --checkpoint "inicio"`.
4. **Palanca #4 — Subagente Ligero (`gauntlet_writer` con Parallel Tool Calling, Escritura en 1 o 2 Bloques Atómicos `Overwrite` + `Append`, Prohibición de Re-Overwrite y Respuesta de 1 Línea) + Sub-Orquestadores por Tandas de 25–30 Empresas (Estrategia 5):**
   - Define una sola vez `gauntlet_writer` mediante `define_subagent(Name="gauntlet_writer", EnableWriteTools=True, EnableSubagentTools=False, EnableMCPTools=False, ...)` con prompt compacto de redacción institucional, Regla Cero Consola, prohibición de leer `_raw_ocr_archive`, **Parallel Tool Calling obligatorio** (emitir `write_file` del `.json` y del borrador en el mismo turno), **escritura en 1 bloque (`Overwrite=true`) para archivos `<= 64 KB`** (`parte3`, `parte4`, `parte5`, `guion`) y en 2 bloques (`Overwrite=true` + `Append=true`) para `parte1` y `parte2`, **prohibición estricta de llamar a `write_file(Overwrite=true)` una segunda vez sobre el mismo borrador**, y respuesta final obligatoria de **1 sola línea (`<= 25 palabras`)**: `PASS | <TICKER> | <ARCHIVO> | <BYTES> bytes`.
   - Si el lote supera las **30 empresas**, aplica la **Estrategia 5**: delega en **Sub-Orquestadores efímeros (`TypeName="self"`) por tandas de 25–30 empresas** (haciendo `kill` al terminar cada tanda en `f5-guion EXIT 0`) para que ningún orquestador acumule más de 400–500 pasos de contexto.
5. **Triage (`SKIP` vs `PENDING`):** ejecuta `gauntlet_gatekeeper.py --target-dir <empresa> --target all` en cada empresa -> salta (`SKIP`) las que devuelvan `EXIT 0`.
6. **Fase 0 determinista en lote (0 tokens LLM — Palanca #1 Micro-Packs en Lectura Única `<= 740L / <= 44.5 KB` + Pre-Extracción Web `web_research_digest.md` + Inyección Canónica First-Time Right + Archivo de OCR Crudo):**
   - Ejecuta `prepare_company_ocr_and_market.py --root-dir "ROOT_DIR" --workers <N> --tickers <pendientes>` (genera también `web_research_digest.md` con consenso Sell-Side, insiders y noticias 2025–2026 de yFinance + Google News RSS en 0 tokens LLM).
   - Ejecuta `build_company_financial_model.py --company-dir <empresa> --export` (consolida la base canónica) y a continuación `gauntlet_memory_wiki.py --target-dir "ROOT_DIR" --build` (genera `facts_sa1.md`..`facts_sa4.md` compactados a `<= 740 líneas` y `<= 44,500 bytes` para lectura en **1 sola llamada `read_file`**, inyectando `web_research_digest.md` y el bloque canónico `# 0.C` en `facts_sa3.md`).
7. **Fases 1 a 5A con Pool Dinámico de `PARALLEL` Hilos (Sin subagentes monolíticos de >10 pasos — Estrategias 1, 2 y 4):**
   - **Prohibido que 1 solo subagente haga M01–M18 + Guion en la misma sesión** (evita el "Efecto Mochila" de arrastrar 250 KB en el historial). Usa los **6 Micro-Agentes (`SA-1..SA-6`, `<= 3 pasos` c/u)** o el **Split Dual Efímero (`SA-A` [M01–M15 + JSONs en `<= 6 pasos`] -> `f2-digest` -> `SA-B` [M16–M18 + Guion en `<= 4 pasos`])**:
     - **Fase 1 (`SA-1..SA-4` con Parallel Tool Calling):** `SA-1` (`CORE_MODEL`, lee `facts_sa1.md` -> `borrador_parte1.md` `76–92 KB` en 2 bloques: M01–M02 `Overwrite=true` + M03–M04 `Append=true`), `SA-2` (`CORE_MODEL`, lee `facts_sa2.md` -> en **1 mismo turno paralelo** escribe `sa2_forensic.json` + Bloque 1 M05–M06 `Overwrite=true`, y en el turno 2 Bloque 2 M07–M08 `Append=true` `66–80 KB`), `SA-3` (`CORE_MODEL`, lee `facts_sa3.md` -> en **1 mismo turno paralelo** escribe `sa3_valuation.json` + `borrador_parte3.md` `52–64 KB` en 1 bloque `Overwrite=true` o 2 bloques), `SA-4` (`LIGHT_MODEL` con fallback a `CORE_MODEL`, lee `facts_sa4.md` ya con noticias pre-extraídas -> escribe `borrador_parte4.md` `41–52 KB` en **1 sola llamada `Overwrite=true`**).
     - **Fase 2 (Digest `<740L` + Conclusiones en 1 bloque):** ejecuta `gauntlet_gatekeeper.py --batch-phase-root "ROOT_DIR" --run-phase f2-digest` -> lanza `SA-5` (`CORE_MODEL`, lee `m01_m15_digest.md` en 1 llamada -> escribe `borrador_parte5.md` `38–48 KB` en **1 sola llamada `Overwrite=true`**).
     - **Fase 3 y 4 (Batch determinista en 1 llamada, 0 tokens):** ejecuta `--batch-phase-root "ROOT_DIR" --run-phase f3-master` (`md` EXIT 0, `273–336 KB`) y `--batch-phase-root "ROOT_DIR" --run-phase f4-derivatives` (10 charts con scorecard > 0.0 verificado + Word + PPTX **60 slides exactas** EXIT 0).
     - **Fase 5A (Guion en 1 bloque sin bloquear caché):** lanza `SA-6` (`LIGHT_MODEL` con fallback a `CORE_MODEL`, lee `brief_ppt_podcast.md` -> escribe `<PREFIX>_PODCAST_GUION.md` `58–70 KB` en **1 sola llamada `Overwrite=true`**) y valida toda la oleada en `0.2s` con `--batch-phase-root "ROOT_DIR" --run-phase f5-guion` (`EXIT 0`).
   - Si un subagente queda en `errored` por timeout/cuota, reanúdalo con `send_message` (nunca duplicar); haz `kill` tras validar su salida.
8. **Fase 5B — Cola Batch Final de Audio Kokoro (0 tokens LLM — Palanca #3 Anti-Ruptura de Caché):**
   - Una vez terminados **todos** los subagentes LLM de todas las empresas, sintetiza todos los MP3 en paralelo sin romper ninguna caché LLM:
     `python "ROOT_DIR\_shared_engine\gauntlet_gatekeeper.py" --batch-podcast-root "ROOT_DIR" --min-seconds 2460 --podcast-workers <N>` *(4 por defecto, o 12–16 si el usuario pide más threads)*.
   - Verifica `gauntlet_gatekeeper.py --target-dir <empresa> --target all` (`EXIT 0` en el 100% de empresas y `slides=60` verificado).
9. **Cierre Global:**
   - `python "ROOT_DIR\_shared_engine\build_global_portfolio_summary.py" --root-dir "ROOT_DIR"` (genera `RESUMEN_CARTERA_GLOBAL.xlsx` + copias en `doc/`, `mp3/`, `ppt/`).
   - `python "ENGINE\token_gauntlet_profiler.py" --export-report` y entrega tabla resumen final (empresa | gatekeeper | palabras md/docx | 60 slides | duración MP3).
