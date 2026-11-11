# ORQUESTACIÓN V3.6 ULTRA-LEAN HYBRID — SPLIT EFÍMERO ANTI-MOCHILA + PRE-WEB F0 + PARALLEL TOOL CALLING + SUB-ORQUESTADORES + WARNING TTL

> **Propósito:** reducir el consumo de tokens de entrada y caché un **45%–57% adicional** (bajando de ~11,000 pasos por cada 100 empresas a **~4,800 pasos** y eliminando el crecimiento cuadrático de subagentes de >10 pasos) con **0% de pérdida de extensión ni rigor analítico**, manteniendo compatibilidad total con cualquier LLM activo en Antigravity.

---

## 1. Las Palancas V3.6 Integradas en el Motor

1. **Palanca #1 — Micro-Packs por Rol (`<= 740L / <= 44.5 KB`) + Pre-Extracción Web Determinista (`web_research_digest.md`) + Inyección Canónica First-Time Right en Fase 0 (`f0`):**
   - `prepare_company_ocr_and_market.py` descarga automáticamente en Fase 0 (0 tokens LLM) el consenso Sell-Side (`targetMeanPrice`, `targetHigh/LowPrice`, `recommendationKey`, nº analistas), insiders/institucionales y las noticias recientes 2025–2026 (vía yFinance News + Google News RSS), generando `web_research_digest.md`.
   - `build_company_financial_model.py --export` se ejecuta inmediatamente tras el mercado para consolidar la base canónica (ingresos reales del último año fiscal, WACC canónico y múltiplos clave).
   - `gauntlet_memory_wiki.py --build` genera en Fase 0 (0 tokens LLM) cuatro dossieres específicos (`facts_sa1.md` ~32 KB, `facts_sa2.md` ~40 KB, `facts_sa3.md` ~30 KB, `facts_sa4.md` ~24 KB) ya con `web_research_digest.md` inyectado y **el bloque canónico `# 0.C CIFRAS CANÓNICAS Y BASE HISTÓRICA` inyectado en `facts_sa3.md`**, garantizando que las proyecciones DCF arranquen desde el año fiscal real sin desajustes y ahorrando 3 a 5 turnos de `search_web` interactivo a mitad de sesión.
   - Todos incluyen en su `Sección 0.B` la misma **Cabecera Transversal Compartida** (`company_meta.json`, snapshot bursátil/múltiplos `market_data_live.json` y comparables `peers_market_live.json`).
2. **Palanca #2 — Prohibición de Subagentes Monolíticos ("Efecto Mochila" — Estrategia 1) y Bandas Objetivo de Extensión:**
   - **Prohibido que un único subagente redacte M01–M18 + Guion en la misma sesión** (evita acumular >20 pasos y arrastrar 250 KB de borradores previos en cada turno). Todo subagente se cierra en **`<= 8 pasos`** usando el **Modo 6 Micro-Agentes (`SA-1..SA-6`, 2–3 pasos c/u)** o el **Modo Split Dual Efímero (`SA-A` [M01–M15 + JSONs en `<= 6 pasos`] -> `f2-digest` -> `SA-B` [M16–M18 + Guion en `<= 4 pasos`, naciendo con contexto 0])**:
      - `SA-1` (`borrador_parte1.md`): **`76,000 – 92,000 bytes`** (`~10,000 – 12,000 palabras`; **prohibido resumir tablas o el catálogo `2.2`**).
      - `SA-2` (`borrador_parte2.md`): **`66,000 – 80,000 bytes`** (`~8,500 – 10,200 palabras`).
      - `SA-3` (`borrador_parte3.md`): **`52,000 – 64,000 bytes`** (`~6,500 – 8,000 palabras`).
      - `SA-4` (`borrador_parte4.md`): **`41,000 – 52,000 bytes`** (`~5,500 – 6,800 palabras`).
      - `SA-5` (`borrador_parte5.md`): **`38,000 – 48,000 bytes`** (`~6,200 – 7,600 palabras`).
      - **Informe Maestro resultante:** **`273,000 – 336,000 bytes`** (`31,000 – 38,000 palabras` -> ~100–110 páginas limpias, sobre el mínimo de `256 KB / 29,250 palabras`).
      - `SA-6` (`*_PODCAST_GUION.md`): **`58,000 – 70,000 bytes`** (`8,600 – 9,800 palabras`, `90 – 110 intervenciones`, `~43 – 48 min` de audio).
3. **Palanca #3 — Protección del TTL de Caché (`--run-phase f5-guion` + `--batch-podcast-root`) + Política de Concurrencia con Warning/Sugerencia (`> 16 threads` — Estrategia 3 sin bloqueo):**
   - **Aviso y Sugerencia de Concurrencia (`> 16` subagentes):** La banda óptima para evitar que las colas del proveedor superen el TTL de 5 min de la caché de prompt (y re-facturen el contexto como input fresco) es **`12 a 16 subagentes simultáneos`**. Si el usuario pide subir a `> 16` subagentes (ej. `24` o `32`), el orquestador **muestra un breve `[WARNING TTL CACHÉ]` con esta sugerencia**, pero **NO impone ningún bloqueo: si el usuario pide o confirma usar más threads/subagentes, ejecuta inmediatamente el número exacto ordenado**.
   - Durante las oleadas LLM **no se lanza la síntesis pesada de Kokoro TTS** (que tarda 4–8 min de CPU y caduca el TTL de 5 min de la caché del orquestador).
   - Tras `SA-6` se ejecuta `--run-phase f5-guion` (`0.2s`), que aplica el autofix oral determinista ampliado (`P32 Burstiness` garantizado matemáticamente) y valida el guion al instante.
   - Al terminar **todos los subagentes LLM de todas las empresas**, se ejecuta en 1 comando `--batch-podcast-root "<ROOT_DIR>" --podcast-workers <N>` (4 por defecto, o 12–16+ si el usuario lo indica, 0 tokens LLM).
4. **Palanca #4 — Subagente Ligero (`gauntlet_writer` con Parallel Tool Calling — Estrategia 4) + Sub-Orquestadores por Tandas de 25–30 Empresas (Estrategia 5):**
   - Al arrancar la sesión, el orquestador registra una sola vez el tipo `gauntlet_writer` (`EnableWriteTools=True`, `EnableSubagentTools=False`, `EnableMCPTools=False`, system prompt de ~350 tokens).
   - **Parallel Tool Calling (Estrategia 4):** `SA-2` y `SA-3` emiten su `write_file(saX.json)` y su primer `write_file(borrador_parteX.md)` **en el mismo turno paralelo**; `SA-3`, `SA-4`, `SA-5` y `SA-6` redactan su archivo completo (`<= 64–68 KB`) en **1 sola llamada `write_file(Overwrite=true)`**, reduciendo los pasos por subagente a `2–3 pasos`.
   - **Sub-Orquestadores por Tandas de 25–30 Empresas (Estrategia 5):** en carteras de `> 30 empresas`, el orquestador principal delega en **Sub-Orquestadores efímeros (`TypeName="self"`) de 25–30 empresas por tanda** (cerrándolos con `kill` al completar su tanda en `f5-guion EXIT 0`), reduciendo un ~60% el crecimiento de caché del orquestador.
5. **Palanca #5 — Enrutamiento Híbrido de Modelos (`CORE_MODEL` + `LIGHT_MODEL`) con Fallback Automático Multi-LLM:**
   - En Antigravity, `invoke_subagent` admite los selectores `inherit | pro | flash | flash_lite` (`"inherit"` utiliza siempre el LLM activo elegido por el usuario en la interfaz: Gemini, Claude, GPT, etc.).
   - **Asignación por defecto (0% pérdida analítica):**
     - `CORE_MODEL = "inherit"` -> **`SA-1` (M01–M04 Negocio/Catálogo/Moat)**, **`SA-2` (M05–M08 Forense/NOPLAT)**, **`SA-3` (M09–M11 Valoración DCF/SOTP)** y **`SA-5` (M16–M18 Debate/Veredicto)**.
     - `LIGHT_MODEL = "flash"` -> **`SA-4` (M12–M15 Técnico/Consenso/Noticias)** y **`SA-6` (Guion de Podcast desde `brief_ppt_podcast.md`)** *(y `SA-1` únicamente si el usuario pide `modo: ultra-ahorro`)*.
   - **Especificación de los dos LLM en el prompt del usuario:**
     - `"modelos: pro + flash"` -> `CORE_MODEL="pro"`, `LIGHT_MODEL="flash"`
     - `"modelos: inherit + flash_lite"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="flash_lite"`
     - `"modelo_unico: inherit"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="inherit"` (fuerza el mismo LLM de la sesión en las 6 fases).
   - **Protocolo de Fallback Automático (si usas un LLM no-Gemini o `flash` no está disponible):**
     - Si la llamada `invoke_subagent(..., Model=LIGHT_MODEL)` devuelve cualquier error de herramienta, modelo no disponible, restricción de proveedor o entra inmediatamente en `state: "errored"`, el orquestador **reasigna automáticamente `LIGHT_MODEL = CORE_MODEL` (`"inherit"`)** y relanza/continúa con el mismo LLM principal de la sesión sin detener la ejecución.

---

## 2. Arquitectura de Ejecución V3.6 (por lote de N empresas)

```
ORQUESTADOR PRINCIPAL (si N > 30 empresas: delega en Sub-Orquestadores efímeros de 25-30 empresas por tanda)
│
├─ F0 LOTE DETERMINISTA (0 tokens LLM):
│    prepare_company_ocr_and_market.py --root-dir <ROOT_DIR> --workers <W>  # OCR + yFinance + web_research_digest.md
│    build_company_financial_model.py --company-dir <CO> --export           # consolida modelo financiero canónico
│    gauntlet_memory_wiki.py --target-dir <ROOT_DIR> --build                # crea facts_sa1..4.md (con canónicas en sa3) + _raw_ocr_archive.zip
│
├─ POR CADA EMPRESA PENDIENTE (Modo 6 Micro-Agentes <=3 pasos c/u o Modo Split Dual SA-A + SA-B <=6 pasos c/u):
│  ├─ F1: 4 Subagentes en Paralelo (`TypeName="gauntlet_writer"`, Cero Consola, Parallel Tool Calling, 2-3 pasos c/u):
│  │    ├─ SA-1 (`Model=CORE_MODEL`):  lee facts_sa1.md -> borrador_parte1.md (76–92 KB, 2 bloques Overwrite+Append)
│  │    ├─ SA-2 (`Model=CORE_MODEL`):  lee facts_sa2.md -> Turno 1 paralelo: sa2_forensic.json + Bloque 1 M05-M06 | Turno 2: Bloque 2 M07-M08
│  │    ├─ SA-3 (`Model=CORE_MODEL`):  lee facts_sa3.md -> Turno 1 paralelo: sa3_valuation.json + borrador_parte3.md (52–64 KB, 1 bloque)
│  │    └─ SA-4 (`Model=LIGHT_MODEL` [fallback CORE_MODEL]): lee facts_sa4.md (con web_research_digest) -> borrador_parte4.md (41–52 KB, 1 bloque)
│  │
│  ├─ F2: `--batch-phase-root <ROOT_DIR> --run-phase f2-digest` (0 tokens) -> `m01_m15_digest.md` (~35 KB)
│  │    └─ SA-5 (`Model=CORE_MODEL`):  lee m01_m15_digest.md -> borrador_parte5.md (38–48 KB, M16-M18 en 1 bloque Overwrite=true)
│  │
│  ├─ F3: `--batch-phase-root <ROOT_DIR> --run-phase f3-master` (0 tokens): ensambla + autofix humanamente + brief + gate `md` EXIT 0
│  ├─ F4: `--batch-phase-root <ROOT_DIR> --run-phase f4-derivatives` (0 tokens): 10 charts (scores > 0) + DOCX + PPTX 60 slides exactas EXIT 0
│  └─ F5A: SA-6 (`Model=LIGHT_MODEL` [fallback CORE_MODEL]): lee brief_ppt_podcast.md -> `<PREFIX>_PODCAST_GUION.md` (58–70 KB en 1 bloque)
│          + `--batch-phase-root <ROOT_DIR> --run-phase f5-guion` (0.2s, 0 tokens): autofix oral P32 + validación instantánea
│
└─ F5B COLA BATCH FINAL KOKORO + CIERRE DE CARTERA (0 tokens LLM, tras terminar TODOS los subagentes):
     gauntlet_gatekeeper.py --batch-podcast-root "<ROOT_DIR>" --min-seconds 2460 --podcast-workers <W_MP3>
     build_global_portfolio_summary.py --root-dir "<ROOT_DIR>"
     token_gauntlet_profiler.py --export-report
```

---

## 3. Definición del Subagente Ligero (`define_subagent`) al inicio de sesión (V3.6)

```json
{
  "Name": "gauntlet_writer",
  "Description": "Redactor institucional financiero y forense del pipeline Gauntlet-Loop en castellano natural (humanamente) bajo Regla Cero Consola, Parallel Tool Calling, Escritura Atómica sin Re-Overwrite y Respuesta de 1 Línea.",
  "EnableWriteTools": true,
  "EnableSubagentTools": false,
  "EnableMCPTools": false,
  "SystemPrompt": "Eres un analista institucional senior Buyside y auditor contable forense. Redactas en castellano natural, preciso y directo siguiendo las reglas editoriales de humanamente: sentence case en titulares (solo mayúscula inicial y nombres propios/siglas), comillas latinas « », cero emojis, cero rayas inglesas espaciadas (' — '), cero paralelismos 'no solo... sino', cero gerundios de posteridad tras coma, cero muletillas de IA y alta variedad de ritmo entre frases cortas (5-10 palabras) y frases analíticas. REGLA CERO CONSOLA, PARALLEL TOOL CALLING, LECTURA ÚNICA Y CERO REESCRITURA CON OVERWRITE (V3.6): tienes PROHIBIDO llamar a run_command y PROHIBIDO leer informes anuales crudos en extracted_ocr_cache/_raw_ocr_archive. Solo usas 1 llamada read_file sobre tu micro-pack (facts_saX.md o m01_m15_digest.md, ya compactado a <=740 líneas y con noticias/consenso pre-extraídos). Cuando debas escribir un archivo .json y el primer bloque de tu borrador, EMITE AMBAS LLAMADAS write_file EN EL MISMO TURNO PARALELO. En borradores <=64 KB (parte3, parte4, parte5, guion) escribe en 1 sola llamada write_file(Overwrite=true); en parte1 y parte2 divide en Bloque 1 (Overwrite=true) y Bloque 2 (Append=true). Tienes ESTRICTAMENTE PROHIBIDO llamar a write_file con Overwrite=true una segunda vez sobre el mismo borrador (cualquier ampliación adicional usa exclusivamente Append=true). Cero datos inventados, cero etiquetas [EXTRAÍDO]/[ESTIMADO], cero bloques ```. RESPUESTA FINAL ULTRACORTA OBLIGATORIA: tu mensaje final al orquestador debe tener EXACTAMENTE 1 LÍNEA (máximo 25 palabras): 'PASS | <TICKER> | <ARCHIVO> | <BYTES> bytes'."
}
```

---

## 4. Plantillas Ultra-Lean de Prompts para `SA-1` a `SA-6` (V3.6)

### Regla común en todos (`SA-1`..`SA-6`)
- **Cero Consola y Cero OCR Crudo:** prohibido invocar `run_command` y prohibido abrir archivos dentro de `_raw_ocr_archive`.
- **Lectura Única (`<= 740 líneas / <= 44.5 KB`) + Noticias Pre-Extraídas:** todos los micro-packs `facts_sa1..4.md` y `m01_m15_digest.md` están compactados para devolverse íntegros en **1 sola llamada `read_file`** (`StartLine=1, EndLine=800`) e incluyen `web_research_digest.md` (cero `search_web` redundante).
- **Parallel Tool Calling y Prohibición de Bucle `Overwrite`:** emite el `write_file` del `.json` y el `write_file` del borrador en el **mismo turno paralelo**. NUNCA reescribas un borrador entero desde cero con `Overwrite=true` una segunda vez.
- **Respuesta Final de 1 Línea (`<= 25 palabras`):** `PASS | <TICKER> | <ARCHIVO> | <BYTES> bytes`.

### `SA-1` (`Model=CORE_MODEL`, `borrador_parte1.md`: `76,000 – 92,000 bytes`, 3 pasos)
1. `read_file` en **1 sola llamada** de `<COMPANY_DIR>/facts_sa1.md`.
2. **Bloque 1 (`write_file` con `Overwrite=True`, ~42–48 KB):** `# PERFIL EXTRAÍDO` + `## Módulo 01` + `## Módulo 02` completo (con catálogo `2.2` íntegro sin resumir).
3. **Bloque 2 (`write_file` con `Append=True`, ~35–42 KB):** `## Módulo 03` + `## Módulo 04` (sin `RESUMEN PARTE 1`). Prohibido volver a usar `Overwrite=True`. Responde en 1 línea.

### `SA-2` (`Model=CORE_MODEL`, `borrador_parte2.md`: `66,000 – 80,000 bytes`, 3 pasos con Parallel Tool Calling)
1. `read_file` en **1 sola llamada** de `<COMPANY_DIR>/facts_sa2.md`.
2. **Turno de escritura 1 (2 `write_file` simultáneos en paralelo):** guarda `<COMPANY_DIR>/sa2_forensic.json` (`Overwrite=True`, con `historical_financials` e `institutional_scores` todos `> 0.0`) **Y AL MISMO TIEMPO** escribe el **Bloque 1 de `borrador_parte2.md`** (`Overwrite=True`, ~36–42 KB: `## Módulo 05` + `## Módulo 06` completos).
3. **Turno de escritura 2 (`write_file` con `Append=True`, ~31–37 KB):** `## Módulo 07` + `## Módulo 08` completos (con nombres reales de directivos y auditor, sin `RESUMEN PARTE 2`). Prohibido volver a usar `Overwrite=True`. Responde en 1 línea.

### `SA-3` (`Model=CORE_MODEL`, `borrador_parte3.md`: `52,000 – 64,000 bytes`, 2–3 pasos con Parallel Tool Calling)
1. `read_file` en **1 sola llamada** de `<COMPANY_DIR>/facts_sa3.md` (revisa la sección `# 0.C CIFRAS CANÓNICAS Y BASE HISTÓRICA` para alinear ingresos base, WACC canónico y múltiplos al 100%).
2. **Turno de escritura 1 (2 `write_file` simultáneos en paralelo):** guarda `<COMPANY_DIR>/sa3_valuation.json` (`Overwrite=True`, con `projected_financials_5y` y `valuation_triangulation` exactamente alineados con las cifras canónicas de `facts_sa3.md`) **Y AL MISMO TIEMPO** escribe `<COMPANY_DIR>/borrador_parte3.md` (`Overwrite=True`, 52–64 KB con Módulos 09, 10 y 11 completos en 1 solo bloque, o Bloque 1 M09–M10 `Overwrite=True` + Bloque 2 M11 `Append=True`; `11.2 Sección B` 100% prosa sin caracteres `|`, sin `RESUMEN PARTE 3`). Prohibido volver a usar `Overwrite=True`. Responde en 1 línea.

### `SA-4` (`Model=LIGHT_MODEL` con fallback a `CORE_MODEL`, `borrador_parte4.md`: `41,000 – 52,000 bytes`, 2 pasos)
1. `read_file` en **1 sola llamada** de `<COMPANY_DIR>/facts_sa4.md` (ya incluye noticias 2025–2026 y consenso Sell-Side pre-extraídos en Fase 0; no llames a `search_web` salvo que falte todo dato).
2. `write_file` en **1 sola llamada `Overwrite=True`** de `<COMPANY_DIR>/borrador_parte4.md` (Módulos 12 a 15 completos; Módulo 12 100% prosa sin caracteres `|`, sin `RESUMEN PARTE 4`; prohibido repetir `Overwrite=True`). Responde en 1 línea.

### `SA-5` (`Model=CORE_MODEL`, tras `--run-phase f2-digest`, `borrador_parte5.md`: `38,000 – 48,000 bytes`, 2 pasos)
1. `read_file` en **1 sola llamada** de `<COMPANY_DIR>/m01_m15_digest.md`.
2. `write_file` en **1 sola llamada `Overwrite=True`** de `<COMPANY_DIR>/borrador_parte5.md` (Módulos 16, 17 y 18 completos: `16.2` en prosa sin `|`, `17.1` con los 10 pilares `> 0.0`, `17.5` con `VEREDICTO GLOBAL`, `18.1..18.4` con 8–10 viñetas `- ` cada una y `18.5` con exactamente 5 puntos numerados `1.` a `5.`; prohibido repetir `Overwrite=True`). Responde en 1 línea.

### `SA-6` (`Model=LIGHT_MODEL` con fallback a `CORE_MODEL`, tras `f3-master`, `<PREFIX>_PODCAST_GUION.md`: `58,000 – 70,000 bytes`, 2 pasos)
1. `read_file` de `<COMPANY_DIR>/brief_ppt_podcast.md`.
2. `write_file` en **1 sola llamada `Overwrite=True`** de `<COMPANY_DIR>/<PREFIX>_PODCAST_GUION.md` (`8,600 – 9,800 palabras`, `90 – 110 intervenciones` `DIRECTOR:` / `ELENA:` / `MARCOS:`, **recorriendo obligatoriamente en orden desde el Módulo 01 hasta el Módulo 17 + cierre Tear Sheet del Módulo 18** [prohibido detenerse o cortar en el Módulo 8], para producir un audio `.mp3` entre **40 y 70 minutos (`2,400s–4,200s`)**, incluyendo Moat, QoE/FCF, Valoración DCF/Múltiplos, Catalizadores, Riesgos/Debate y Veredicto; números >1,000 sin decimales, `por ciento` en lugar de `%`, cero siglas inglesas crudas, alternando réplicas breves de 5–10 palabras con análisis profundo). Responde en 1 línea.

---

## 5. Comandos Exactos del Orquestador por Fase (Individual o en Lote con `--batch-phase-root`)

```powershell
$py = "C:\Users\david\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
$SE = "<ROOT_DIR>\_shared_engine"
$CO = "<COMPANY_DIR>"

# Fase 0 (sobre ROOT_DIR entero en paralelo o por empresa)
& $py "$SE\gauntlet_gatekeeper.py" --batch-phase-root "<ROOT_DIR>" --run-phase f0 --podcast-workers 4

# Fase 2 (tras SA-1..SA-4: fusiona sa2_forensic.json + sa3_valuation.json y extrae m01_m15_digest.md en lote)
& $py "$SE\gauntlet_gatekeeper.py" --batch-phase-root "<ROOT_DIR>" --run-phase f2-digest --podcast-workers 4

# Fase 3 (tras SA-5: fusiona sa5_verdict.json, ensambla, autofix humanamente, extrae brief y valida md EXIT 0 en lote)
& $py "$SE\gauntlet_gatekeeper.py" --batch-phase-root "<ROOT_DIR>" --run-phase f3-master --podcast-workers 4

# Fase 4 (10 charts + DOCX + PPTX 60 slides exactas + gate docx/pptx EXIT 0 en lote)
& $py "$SE\gauntlet_gatekeeper.py" --batch-phase-root "<ROOT_DIR>" --run-phase f4-derivatives --podcast-workers 4

# Fase 5A (tras SA-6: valida guiones de la oleada en 0.2s sin romper caché TTL)
& $py "$SE\gauntlet_gatekeeper.py" --batch-phase-root "<ROOT_DIR>" --run-phase f5-guion --podcast-workers 4

# Fase 5B (AL FINAL DE TODAS LAS EMPRESAS: sintetiza todos los MP3 Kokoro con 4 workers concurrentes por defecto y borra WAV)
& $py "$SE\gauntlet_gatekeeper.py" --batch-podcast-root "<ROOT_DIR>" --min-seconds 2460 --podcast-workers 4
```

---

## 6. Presupuesto de tokens medido (V3.8) — una empresa, 326 KB de informe

Medición real de una ejecución completa (LKNCY, 4 borradores en paralelo + SA-5 + SA-6, gate `all` en EXIT 0), leída de los eventos `assistant/message.usage` de la sesión:

| Bloque | Pasos | Input fresco | Cache-read | Output | Minutos |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Orquestador | 117 | 155.817 | 14.082.176 | 64.674 | 45 |
| SA-1 (M01–M04) | 32 | 22.200 | 2.176.896 | 62.958 | 6 |
| SA-2 (M05–M08) | 50 | 36.388 | 4.773.376 | 89.268 | 8 |
| SA-3 (M09–M11) | 52 | 35.486 | 6.304.000 | 132.959 | 11 |
| SA-4 (M12–M15) | 27 | 15.043 | 1.371.648 | 47.714 | 5 |
| SA-5 (M16–M18) | 29 | 23.979 | 2.280.192 | 78.898 | 7 |
| SA-6 (guion) | 79 | 45.088 | 8.915.328 | 109.516 | 12 |
| **Total** | **385** | **333.320** | **39.694.080** | **585.507** | **45 en pared** |

- **Hit ratio de caché 99,1 %**, cero rupturas de caché >50k: el coste no está en leer, está en escribir.
- A tarifa valle (`deepseek-v4.1-flash`: 0,15 / 0,003 / 0,60 USD por millón): ≈ **0,53 USD** por informe; en tarifa pico, ≈1,06 USD.
- **Output = 67 % del coste.** Relación output/KB entregado: SA-1 0,72k, SA-4 0,92k, SA-2 1,12k, SA-5 1,66k, SA-6 1,88k, SA-3 2,00k. Los dos últimos son los que reescribieron el archivo completo a mitad de fase.

### Palancas que reducen coste sin tocar la calidad del texto

1. **Centinela obligatorio (ya en el pack V3.8).** Prohibir `write` después de la primera llamada elimina la segunda pasada completa: en la medición, SA-3 y SA-5 gastaron ~60–70k tokens de output en reescrituras que no aportaron texto. Ahorro esperado: **12–18 % del output**.
2. **Escribir en la banda baja del rango**, no en el techo: cada KB de más son ~250 tokens de salida. El informe salió 326 KB (banda 273–336), con margen para bajar sin perder módulos ni tablas.
3. **Partir SA-3 si su borrador supera 60 KB** (SA-3a M09–M10 / SA-3b M11, en paralelo). El contexto por paso de un solo agente crece linealmente y arrastra relecturas; dos agentes de ~30 pasos cuestan menos caché y menos salida que uno de 52.
4. **Un solo digest por ejecución.** Relanzar `f2-digest` para regenerar `m01_m15_digest.md` reinyecta 37 KB de contexto y puede invalidar la caché del orquestador.
5. **No intercalar compute largo entre pasos LLM.** Kokoro, DOCX y PPTX se lanzan en background y se recogen al final; en esta ejecución se hizo así y no hubo ninguna ruptura de caché.
6. **Orquestador: esperar por job, no sondear.** Cada sondeo vuelve a enviar el contexto completo; con 117 pasos, el orquestador procesó 14M de caché para 64k de salida.

Lo que **no** debe recortarse: extensión de los 18 módulos, catálogo `2.2`, tablas multianuales, debate M16 y veredicto M17. El output es el producto; el ahorro viene de no repetirlo.

### 6.1 Segunda medición (CAML.L, 318 KB, con centinela activo)

| Bloque | Pasos | Input fresco | Cache-read | Output | Output/KB entregado |
| :--- | ---: | ---: | ---: | ---: | ---: |
| Orquestador | 73 | 45.324 | 23.947.520 | 57.448 | — |
| SA-1 (M01–M04) | 29 | 38.343 | 2.284.672 | 80.676 | 0,98k |
| SA-2 (M05–M08) | 76 | 89.061 | 8.241.536 | 103.268 | 1,30k |
| SA-3 (M09–M11) | 30 | 24.499 | 1.908.352 | 61.360 | **1,02k** |
| SA-4 (M12–M15) | 99 | 50.705 | 10.377.856 | **114.188** | **2,28k** |
| SA-5 (M16–M18) | 79 | 46.814 | 7.984.896 | 95.334 | **2,12k** |
| SA-6 (guion) | 56 | 29.042 | 5.438.208 | 94.125 | 1,61k |
| **Total** | **442** | **323.788** | **60.183.040** | **606.399** | **1,91k medio** |

Lectura: el centinela funcionó donde se aplicó (SA-3 bajó de 2,00k a 1,02k tokens de output por KB, la mitad). El coste se desplazó a **SA-4 y SA-5**, que no reescribieron el archivo pero multiplicaron los turnos (99 y 79 pasos para 50 y 45 KB). El orquestador, además, triplicó su contexto por paso (327k de media frente a 120k en la primera ejecución) porque acumuló salidas largas de consola y guiones de parcheo.

### 6.2 Palancas medidas para la próxima ejecución

1. **Partir SA-4 y SA-5 cuando su banda supere 45 KB.** Cuatro agentes (M12 / M13–M14 / M15 / M16–M18) con 25–45 KB cada uno deberían bajar el ratio de 2,2k a ~1,3k: ahorro estimado **60–80k tokens de output** (−10–13 % del total).
2. **Higiene de contexto del orquestador.** No volcar logs completos ni el texto de los parches al hilo; leer solo el final (`-Tail`) y dejar los artefactos en disco. Cada 100k de contexto extra se pagan en todos los pasos siguientes.
3. **No repetir fases deterministas.** En la segunda ejecución, `f3-master` se lanzó tres veces y `generate_10_charts.py` cuatro, por depuración del motor: eso no cuesta tokens de modelo pero sí contexto de orquestador y tiempo.
4. **Mantener el centinela y la banda baja**: son las dos únicas palancas con efecto medido y sin merma de contenido.
5. **Techo de output por subagente**: si un borrador supera 2,5k tokens de output por KB, es señal de que está iterando; conviene cortarlo y relanzar la parte restante como agente nuevo en vez de dejarlo girar.

### 6.3 Higiene del orquestador (medida en la 2.ª ejecución)

El orquestador de CAML.L gastó 23,9 M de cache-read en 73 pasos (327k de contexto por paso) frente a 14,1 M en 117 pasos de la primera (120k por paso). No fue por trabajar más, sino por arrastrar salidas largas en el hilo. Reglas:

1. **Leer solo el final**: `Select-Object -Last N` en cada ejecución; nunca volcar un log completo ni el texto de un script al hilo.
2. **Un `job_output` por job**, con `wait` cuando se esté bloqueado; prohibido sondear en bucle con `Start-Sleep`.
3. **No repetir fases ya superadas**: si `f3-master` dio EXIT 0, no se relanza por cosmética; los retoques se hacen sobre el borrador y se vuelve a pasar una sola vez.
4. **Los artefactos viven en disco**: los parches y scripts auxiliares se escriben con la herramienta de ficheros, se ejecutan y se borran; no se pegan en el prompt.
5. **Presupuesto de pasos del orquestador**: ~1 paso por fase determinista, 2 por oleada de agentes y 3–4 de supervisión. Si se supera el doble, hay un bucle de depuración y conviene parar y replanificar.
6. **Imágenes**: cada render que se inspecciona con `read_image` añade tokens al contexto de todos los pasos siguientes; se revisan una vez al final, no en cada iteración.
