---
name: deep-research-gauntlet-loop
description: >-
  Use this skill when the user wants to execute an autonomous institutional equity research and forensic analysis pipeline (Deep-Research Gauntlet-Loop) for one or multiple company folders containing financial PDFs. Generates per company: a 95-110 page (>=256 KB / >=29,250 words) Markdown report across 18 optimized modules (without redundant appendices) with an exhaustive product catalog, live web search, and a 5-block Executable Final Verdict, a styled Word (.docx >= 27,000 words) report with 10 300-DPI charts (strictly separating historical performance in Module 01 from future scenario projections in Module 11), a 60-slide 16:9 PowerPoint (.pptx) pitch deck (without PDF export), a 3-voice podcast script (>= 8,000 words, >= 85 turns) and Kokoro-ONNX audio (.mp3 >= 40 min / 2,400s, deleting the temporary .wav file after MP3 generation), a global portfolio comparative Excel (.xlsx) and Markdown summary across all companies (without Rank, Freeze Panes at B2 on Compañía, and including PAIS, Bolsas, and Ticker directly from yFinance), and final consolidated deliverable directories (doc/, mp3/, ppt/) containing copies of all generated Word, MP3, and PowerPoint files.
---

# Deep-Research Gauntlet-Loop Skill (Estándar Institucional 95–110 Páginas — 18 Módulos Optimizados sin Anexos + Multi-Formato + Cartera Global)

Este skill codifica de principio a fin el flujo autónomo multi-empresa **`DEEP-RESEARCH GAUNTLET-LOOP`**, diseñado para auditar carpetas de compañías cotizadas (por ejemplo, en HKEX, NYSE, NASDAQ o bolsas europeas) combinando la extracción del 100% de sus PDFs financieros con búsqueda activa en Internet y validación determinista (`EXIT 0`).

---

## Estructura de este Skill

- [SKILL.md](./SKILL.md): Guía operativa paso a paso (Fases 0 a 7).
- [references/MODULES_01_TO_18_SPECIFICATION.md](./references/MODULES_01_TO_18_SPECIFICATION.md): Especificación detallada de los 18 Módulos Optimizados (sin anexos redundantes al final), Catálogo Exhaustivo de Productos (`2.1` y `2.2`), Auditoría de Notas Críticas integrada en el Módulo 05 (`5.2`), separación estricta entre historia auditada (`Módulo 01` / `chart1`) y proyecciones futuras a 5 años (`Módulo 11` / `chart8`), Veredicto Final Ejecutable en 5 bloques (`Módulo 17`), mínimos de palabras por módulo (`MODULE_MIN_WORDS`) y anclajes obligatorios (`REQUIRED_MD_ANCHORS`).
- [references/PPTX_60_SLIDES_7_ACTS_SPECIFICATION.md](./references/PPTX_60_SLIDES_7_ACTS_SPECIFICATION.md): Especificación integral de la **Nueva Arquitectura Narrativa en 7 Actos (60 Diapositivas con Hilo Conductor)**, mapeo riguroso de cada diapositiva (Slides 1 a 40) a los 18 módulos del informe, asignación de los 10 gráficos institucionales, anclajes obligatorios (Slide 7: Modelo de Negocio y Unit Economics, Slide 8: Catálogo Exhaustivo de Productos, Slide 39: Plan Táctico Ejecutable en 2 Columnas, Slide 40: Tear Sheet Ejecutivo en Cuadrícula 3x2) y estándares de diseño visual (McKinsey editorial, 16:9, humanamente).
- [references/SUBAGENT_ORCHESTRATION_GUIDE.md](./references/SUBAGENT_ORCHESTRATION_GUIDE.md): Plantilla exacta de prompt para lanzar subagentes nativos en paralelo (oleadas de hasta 8 subagentes) y protocolo de recuperación ante límites de cuota (`429 RESOURCE_EXHAUSTED`) o *stream timeouts* mediante `send_message`.
- [references/ORCHESTRATION_V2_PHASE_SPLIT.md](./references/ORCHESTRATION_V2_PHASE_SPLIT.md): **MODO OPTIMIZADO DE TOKENS Y COSTE V3.6 ULTRA-LEAN HYBRID (predeterminado para ejecuciones nuevas).** Implementa las 8 palancas: (1) Micro-packs por rol `facts_sa1..4.md` (`<= 740L / <= 44.5 KB`) + Pre-extracción web determinista `web_research_digest.md` en Fase 0 (0 tokens LLM, ahorrando 3–5 turnos de `search_web`), (2) Prohibición de subagentes monolíticos (>10 pasos) mediante 6 Micro-Agentes (`SA-1..SA-6`) o Split Dual Efímero (`SA-A` [M01–M15] + `SA-B` [M16–M18 + Guion] tras `f2-digest`) + Bandas Objetivo suelo+techo (`273–336 KB` en informe maestro y `58–70 KB` en guion podcast, eximiendo tablas y catálogo `2.2`), (3) Validación instantánea `--run-phase f5-guion` + Cola batch final Kokoro `--batch-podcast-root` + **Warning/Sugerencia de TTL de Caché cuando se piden `> 16` subagentes simultáneos (sugiriendo `12–16`, pero permitiendo escalar a `16, 24, 32+` si el usuario lo ordena)**, (4) Subagente ligero `gauntlet_writer` con **Parallel Tool Calling** (`write_file` de JSON + borrador en el mismo turno y escritura en 1 bloque `Overwrite=true` para `<= 64 KB`), (5) **Sub-Orquestadores por Tandas de 25–30 Empresas** en carteras grandes (`> 30` empresas), y (6) Enrutamiento híbrido `CORE_MODEL` (`inherit` por defecto) + `LIGHT_MODEL` (`flash` por defecto) con **fallback automático a `inherit`**.
- [references/EXTERNAL_SKILLS_AND_DEPENDENCIES.md](./references/EXTERNAL_SKILLS_AND_DEPENDENCIES.md): Catálogo y especificación de todas las skills externas de Antigravity (`humanamente`, `claude-pptx-skills`, `academic-pptx-skill`), herramientas de plataforma, librerías de Python y dependencias de sistema necesarias para la ejecución.
- **Motores ejecutables en [`scripts/`](./scripts/):**
  - [gauntlet_gatekeeper.py](./scripts/gauntlet_gatekeeper.py): Validador determinista de los 4 subsistemas (`md`, `docx`, `pptx`, `podcast` y `all`).
  - [gauntlet_memory_wiki.py](./scripts/gauntlet_memory_wiki.py): Conector oficial + Auto-Instalador/Daemon para TencentDB-Agent-Memory (`MemoryCore :8420`), indexación de PDFs y consultas híbridas semánticas/BM25 acotadas.
  - [build_company_financial_model.py](./scripts/build_company_financial_model.py): Generador y validador del Modelo Financiero Canónico unificado (`company_financial_model.json`), fuente única de verdad cuantitativa.
  - [build_institutional_docx.py](./scripts/build_institutional_docx.py): Compilador determinista ultrarrápido de `*_INFORME_COMITE_FINAL.md` + `charts/chart1..10.png` a `*_INFORME_INSTITUCIONAL_FINAL.docx` en ~2 segundos.
  - [build_institutional_pptx.py](./scripts/build_institutional_pptx.py): Compilador determinista de Pitch Deck (60 diapositivas 16:9 en 7 Actos) con diseño editorial McKinsey, integración de gráficos nativos/PNG 300 DPI y validación estructural OOXML.
  - [build_podcast_kokoro.py](./scripts/build_podcast_kokoro.py): Sintetizador acústico a 3 voces (`DIRECTOR`, `ELENA`, `MARCOS`) con Kokoro-ONNX, empaquetado prosódico, auto-descubrimiento de modelos y caché de audio en disco (`.cache_audio/`).
  - [build_global_portfolio_summary.py](./scripts/build_global_portfolio_summary.py): Consolidador global de cartera (`RESUMEN_CARTERA_GLOBAL.md` y `RESUMEN_CARTERA_GLOBAL.xlsx`), integrando automáticamente `company_financial_model.json`.
  - [prepare_company_ocr_and_market.py](./scripts/prepare_company_ocr_and_market.py): Extractor selectivo de PDFs (100% de Informes Anuales e Intermedios + **únicamente el último Informe Trimestral**, ignorando trimestrales antiguos) y descarga de datos bursátiles en vivo.
  - [web_research_enricher.py](./scripts/web_research_enricher.py): Enriquecedor auxiliar de noticias, consenso y múltiplos de mercado.
  - [build_deliverables_reference.py](./scripts/build_deliverables_reference.py): Implementación de referencia para generar los 10 gráficos PNG a `300 DPI`, el documento Word OOXML (`.docx >= 27,000 palabras`) y la presentación de 60 diapositivas en 7 Actos (`.pptx`, sin generar PDF desde el PPT).
  - [merge_split_parts.py](./scripts/merge_split_parts.py): Fusiona los borradores troceados (`borrador_parte4a/4b`, `borrador_parte5a/5b`, etc.) en los ficheros canónicos que espera `f3-master`. Determinista, 0 tokens; paso obligatorio del reparto en 7 agentes descrito en [references/SPLIT_6_AGENTS.md](./references/SPLIT_6_AGENTS.md).

---

## Reglas Inquebrantables de Calidad

1. **Prohibición Absoluta de Plantillas de Texto en Python para Informes `.md` y Guiones de Podcast:**
   - **Queda terminantemente prohibido** usar scripts de Python (`f-strings`, plantillas o concatenadores automáticos de frases) para redactar `borrador_parte1.md`, `borrador_parte2.md`, `borrador_parte3.md`, `borrador_parte4.md`, `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` o `[FILE_PREFIX]_PODCAST_GUION.md`.
   - Los 5 borradores y el guion de podcast **deben ser escritos directamente por el LLM** (preferentemente mediante el subagente ligero `TypeName="gauntlet_writer"` registrado con `define_subagent`, o fallback `TypeName="self"`) usando `write_file` y `edit_file`.
2. **Estándar de Extensión y Bandas Objetivo en 5 Partes (`273,000 a 336,000 bytes` / `31,000 a 38,000 palabras` — sobre el suelo obligatorio de `>= 256,000 bytes` y `>= 29,250 palabras`, eximiendo tablas y catálogo `2.2` de cualquier recorte):**
   - **Oleada Paralela (4 Subagentes Concurrentes `SA-1` a `SA-4`, Módulos 01 a 15, leyendo cada uno su micro-pack `facts_sa1..4.md` con cabecera común de 5 KB, SIN `## RESUMEN PARTE X` al final):**
     - `borrador_parte1.md` en banda **`76,000–92,000 bytes`** (`SA-1`, `Model=CORE_MODEL`): `# PERFIL EXTRAÍDO` + **Módulos 01 (`>= 1,500 pal.`), 02 (`>= 3,400 pal.`, catálogo `2.2` íntegro sin resumir), 03 (`>= 2,000 pal.`) y 04 (`>= 1,350 pal.`)**.
     - `borrador_parte2.md` en banda **`66,000–80,000 bytes`** (`SA-2`, `Model=CORE_MODEL`): **Módulos 05 (`>= 2,800 pal.`), 06 (`>= 2,100 pal.`), 07 (`>= 1,500 pal.`) y 08 (`>= 1,550 pal.`)**.
     - `borrador_parte3.md` en banda **`52,000–64,000 bytes`** (`SA-3`, `Model=CORE_MODEL`): **Módulos 09 (`>= 1,200 pal.`), 10 (`>= 2,600 pal.`, Secciones A–D) y 11 (`>= 1,850 pal.`, Proyecciones a 5 Años y Matriz de Riesgos en prosa sin `|`)**.
     - `borrador_parte4.md` en banda **`41,000–52,000 bytes`** (`SA-4`, `Model=LIGHT_MODEL` con fallback automático a `CORE_MODEL`): **Módulos 12 (`>= 1,600 pal.`, Catalizadores en prosa sin `|`), 13 (`>= 1,150 pal.`), 14 (`>= 1,050 pal.`) y 15 (`>= 1,450 pal.`, Noticias Recientes 2025–2026 y Monitorización Trimestral)**.
   - **Subagente Secuencial de Conclusiones y Síntesis Integral (`SA-5`, `Model=CORE_MODEL`, tras `--run-phase f2-digest`):**
     - `borrador_parte5.md` en banda **`38,000–48,000 bytes`** (`SA-5`): **Módulos 16 (`>= 1,650 pal.`), 17 (`>= 1,850 pal.`) y 18 (`>= 2,400 pal.`, con `18.1..18.4` [8–10 viñetas cada una] + `18.5` Tear Sheet con 5 puntos numerados `1.` a `5.`)**.
   - **Regla Cero Consola (`SA-1` a `SA-6`) y Enrutamiento Multi-LLM con Fallback:** Los subagentes tienen **PROHIBIDO llamar a `run_command`**. Por defecto `CORE_MODEL="inherit"` (el LLM elegido en la interfaz de Antigravity: Gemini, Claude, GPT...) y `LIGHT_MODEL="flash"` (parametrizables en el prompt como `modelos: <core> + <light>` o `modelo_unico: inherit`); si `LIGHT_MODEL` devuelve error o no está disponible en el proveedor activo, el orquestador **cae automáticamente a `Model="inherit"`**.
   - El archivo consolidado `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` debe superar obligatoriamente **`256,000 bytes`** y **`29,250 palabras`**.
3. **Cero Etiquetas Prohibidas y Reglas Estrictas de Formato:**
   - Prohibido incluir etiquetas entre corchetes como `[EXTRAÍDO]`, `[DERIVADO]`, `[ESTIMADO]`, `[VERIFICADO]` o similares en cualquier parte del informe.
   - Prohibido incluir secciones de `GAUNTLET LOG` o Anexos (`Anexo A`, `Anexo B`, `Anexo C`) al final del informe.
   - En el **Módulo 11 (Sección B: Matriz de Riesgos)**, en todo el **Módulo 12 (Catalizadores y Kill-Switches)** y en el **Módulo 16 (Sección B: El Debate del Comité Bull vs. Bear)** está **prohibido usar tablas Markdown o el carácter pipe (`|`)**: todo debe redactarse en prosa analítica profunda y viñetas estructuradas.
   - En el **Módulo 18 (Tear Sheet Ejecutivo)** debe haber **exactamente 5 puntos numerados (`1.` a `5.`)**.
4. **Separación Estricta entre Historia Auditada (`Módulo 01`) y Proyecciones Futuras (`Módulo 11`):**
   - El **Módulo 01 (`chart1`)** muestra **exclusivamente el desempeño histórico real auditado** (últimos 5 ejercicios cerrados + último periodo intermedio), sin mezclar estimaciones futuras.
   - Las **proyecciones operativas futuras a 5 años (`chart8`)** se presentan y justifican en el **Módulo 11 (`Sección A`)**, explicando su procedencia exacta: contraste entre Consenso Sell-Side / Guidance de la Directiva y las proyecciones propias del Comité (Escenarios Bear, Base y Bull derivados del `TAM/CAGR` del Módulo 03, la cartera de pedidos/`Backlog` del Módulo 07 y la estructura de márgenes del Módulo 06).
5. **Prohibido Usar Nombres Genéricos o Placeholders:**
   - Todos los segmentos de ingresos, nombres de plantas, clientes/proveedores, firma auditora y los 4 a 5 competidores cotizados (con sus Tickers reales) deben ser 100% reales y extraídos de los informes anuales/intermedios y de la búsqueda web.
6. **Contrato de Datos para los Gráficos (V3.8):**
   - **`chart1` / `chart1b` (Módulo 01):** el informe maestro debe contener una tabla con columna del último periodo intermedio etiquetada como `2026H1`, `1H2026` o `2026 9M` (nunca solo `Q3 2026`), con fila `Ingresos totales` y, en la misma tabla, `Coste de materiales` o `Beneficio bruto`. `generate_10_charts.py` la incorpora automáticamente como última columna; si el periodo no publica beneficio neto o caja, el gráfico rotula `N/D` y no dibuja la barra.
   - **`chart1b` nunca recorta el último periodo.** Si faltan caja operativa, capex o FCF, dibuja el periodo con `N/D` en las series ausentes y mantiene el FCF si viene publicado aunque falten las otras dos (fila `Flujo de caja libre ajustado` incluida). Prohibido volver a terminar la serie en el último ejercicio cerrado.
   - **`chart2` adapta los paneles al modelo de negocio.** El panel A es siempre el mix de ingresos por línea de producto; el panel B es el mix red propia/socios solo si `company_financial_model.json` trae `last_official_store_cut` con ambos canales, y en caso contrario un **Pareto** (peso por línea + acumulado). Los títulos de ambos paneles se eligen en función del que se dibuja: prohibido dejar rótulos de «red propia / red de socios» en una empresa minera o industrial.
   - **`segments_breakdown` de `sa2_forensic.json`:** cada fila debe usar exactamente las claves `"name"` (línea de producto o canal), `"pct"` (peso sobre ingresos) y `"revenue_m"` (millones de la divisa de reporte). `chart2` tolera variantes (`segment`, `mix_2025_pct`, `2025_m_cny`) pero la fuente canónica son esas tres. El desglose debe sumar 100% y cubrir todas las líneas reales (bebidas, alimentación, otros ingresos, canal de socios), no solo los dos canales agregados.
7. **Escritura por Centinela y Presupuesto de Tokens (V3.8):**
   - En DeepSeek Harness **no existe `Append=true`**. Toda instrucción de `write_file(Overwrite/Append)` de este skill se implementa con el centinela: `write(ruta, '<!--CONT-->')` → sucesivos `edit(old_string='<!--CONT-->', new_string='<fragmento>\n<!--CONT-->')` → `edit(..., '')` al cerrar. **Prohibido volver a usar `write` sobre el borrador** tras la primera llamada: duplica el coste de salida y ya ha provocado pérdidas de módulos.
   - **Presupuesto de escritura:** cada `edit` debe aportar **≥ 12.000 bytes**; una parte de 50 KB se escribe en 3–4 llamadas, no en diez. Prohibido releer el borrador propio, verificarlo con comandos o hacer micro-ediciones.
   - Presupuesto medido por empresa (326 KB de informe, 4 borradores en paralelo): 385 pasos, 333k input fresco, 39,7M cache-read (99,1 % de acierto), **585k output**, ≈0,53 USD a tarifa valle. El output es el 67 % del coste; el ahorro sale de no repetirlo, nunca de recortar módulos. Detalle y palancas en `references/ORCHESTRATION_V2_PHASE_SPLIT.md`, sección 6.
8. **Reparto de Agentes según el Desbordamiento (V3.8.1):**
   - La ejecución de un solo turno con 4 agentes es la opción por defecto. **Se trocea SA-4 y/o SA-5** cuando en la ejecución anterior ese agente supere **1,8k tokens de output por KB entregado** o **45 pasos**.
   - El reparto canónico (SA-4a M12 / SA-4b M13–M15 / SA-5a M16–M17 / SA-5b M18), las bandas, los encabezados de cada trozo, el orden de oleadas y el esqueleto de prompt están en `references/SPLIT_6_AGENTS.md`.
   - Antes de `f3-master` hay que fusionar los trozos con `scripts/merge_split_parts.py --target-dir <COMPANY_DIR>` (determinista, 0 tokens).
   - **Higiene del orquestador:** leer solo el final de los logs (`-Tail`), no volcar comandos ni parches al hilo, esperar los jobs con `job_output` en vez de sondear en bucle, y no repetir fases deterministas ya superadas. Cada 100k de contexto extra se pagan en todos los pasos siguientes.

---

## Paso a Paso Exacto del Flujo de Trabajo (Fases 0 a 7)

### Fase 0: Protocolo de Inicialización del Directorio Raíz (`STOP & ASK`) y Despliegue de Motores
1. **Verificación de `ROOT_DIR`:** Si el usuario no ha indicado la ruta de la carpeta raíz (`ROOT_DIR`) que contiene las subcarpetas de las empresas con sus PDFs, detén la ejecución y pregúntale la ruta antes de iniciar.
2. **Despliegue de Motores Compartidos (`ROOT_DIR/_shared_engine/`):**
   - Copia los scripts de la carpeta [`scripts/`](./scripts/) de este skill hacia `ROOT_DIR/_shared_engine/`.
   - Propaga `gauntlet_gatekeeper.py` y `build_podcast_kokoro.py` a cada subcarpeta de empresa `<COMPANY_DIR>`.
   - Verifica que los modelos acústicos de Kokoro (`kokoro-v1.0.onnx` y `voices-v1.0.bin`) estén en `ROOT_DIR/_shared_engine/kokoro_models/` (si no existen, `build_podcast_kokoro.py` los descarga automáticamente en la primera ejecución).
3. **Escaneo de Estado (`SKIP` vs. `RESUME`):**
   - Ejecuta `gauntlet_gatekeeper.py --target-dir "<COMPANY_DIR>" --target all` sobre las carpetas existentes.
   - Las carpetas que devuelvan `=== GAUNTLET PASS (EXIT 0) ===` se marcan como `SKIP (COMPLETED)`. Las demás pasan a la cola de ejecución (`RESUME` o `NEW`).

### Fase 1: Extracción Selectiva de PDFs (Anuales + Intermedios + Último Trimestral) y Datos de Mercado en Vivo
1. Para todas las carpetas pendientes, ejecuta [prepare_company_ocr_and_market.py](./scripts/prepare_company_ocr_and_market.py) (admite ejecución multiproceso/hilos paralela con `--workers N`, óptimo para lotes de hasta 100 empresas):
   ```powershell
   python "ROOT_DIR/_shared_engine/prepare_company_ocr_and_market.py" --root-dir "ROOT_DIR" --workers 6
   ```
2. **Regla Institucional de Selección Documental (Filtro Anti-Ruido Trimestral):**
   - **Lee y extrae TODOS los Informes Anuales (`ANNUAL REPORT`)** y Prospectos de todos los años disponibles.
   - **Lee y extrae TODOS los Informes Semestrales/Intermedios (`INTERIM REPORT`)** de todos los años disponibles.
   - **Lee y extrae ÚNICAMENTE el último Informe Trimestral (`QUARTERLY REPORT` / `Q1..Q4` más reciente por año y trimestre).** Todos los informes trimestrales más antiguos se ignoran estrictamente tanto en la extracción a `extracted_ocr_cache/` como en `financial_digest.md` y en el análisis del agente, evitando saturar la ventana de contexto con trimestrales obsoletos ya subsumidos en los informes anuales/intermedios.
3. Además, genera `company_meta.json` (con el nombre oficial, `primary_ticker`, `country` [PAIS] y `exchange` [Bolsas] con los valores exactos que aparecen en `yFinance`, divisa de reporte y `file_prefix`), `market_data_live.json` y copia `financial_digest.md` tanto en `extracted_ocr_cache/financial_digest.md` como en `<COMPANY_DIR>/financial_digest.md`.

### Fase 2: Búsqueda Web Activa (`search_web`) y Auditoría Forense Previa
Para cada empresa `<COMPANY_DIR>`:
1. Lee `<COMPANY_DIR>/extracted_ocr_cache/company_meta.json`, `market_data_live.json`, `financial_digest.md` y las transcripciones de **todos los Informes Anuales, todos los Informes Intermedios y únicamente el último Informe Trimestral** en `extracted_ocr_cache/*.md` (ignorando cualquier informe trimestral antiguo).
2. Ejecuta búsquedas activas en Internet con `search_web` para obtener:
   - **Catálogo comercial exhaustivo de productos, servicios, marcas y SKUs** de la web oficial de la compañía.
   - **Últimas noticias (2025–2026)**, lanzamientos de productos, contratos, litigios, recompras de acciones, dividendos y cambios regulatorios.
   - **Precio actual verificado, múltiplos de valoración en vivo y consenso de analistas Sell-Side** (compras/mantener/ventas y precio objetivo medio).
   - **Métricas comparables actualizadas** de sus 4–5 competidores cotizados reales.

### Fase 3: Redacción Directa de los 4 Borradores (`borrador_parte1..5.md`) y Consolidación del `.md` (`>= 256 KB` / `>= 29,250 palabras`)
Lee [references/MODULES_01_TO_18_SPECIFICATION.md](./references/MODULES_01_TO_18_SPECIFICATION.md), [references/PLANTILLA_ANCLAS_DRAFT.md](./references/PLANTILLA_ANCLAS_DRAFT.md) y redacta directamente mediante `write_file` / `edit_file`:

**PLANTILLA DE ANCLAS OBLIGATORIA (Optimización 1):** antes de escribir cada parte, abre `references/PLANTILLA_ANCLAS_DRAFT.md` y copia **literal y textualmente** (sin reordenar, traducción, abreviación ni cambio de mayúsculas/`—`) cada encabezado de módulo (`## Módulo NN — ...`), subsección (`Subsección X.Y ...`), `## RESUMEN PARTE 1/2/3` y campo de texto literal que su parte exige; respeta sus mínimos de palabras por módulo y reglas de formato. El validador (REQUIRED_MD_ANCHORS) hace `match` exacto contra esas cadenas; una variante fuerza un FAIL y re-itera el borrador completo. Los encabezados exactos a la primera evitan ese bucle costoso en tokens.
1. **`borrador_parte1.md` (`>= 78,000 bytes`):**
   - Portada Institucional + Índice General + `# PERFIL EXTRAÍDO` + **Módulos 01, 02, 03 y 04** + `## RESUMEN PARTE 1`.
   - El **Módulo 01 (`>= 1,750 palabras`)** cubre exclusivamente el desempeño histórico real auditado (últimos 5 años cerrados + último periodo intermedio) sin proyecciones futuras.
   - El **Módulo 02 (`>= 3,300 palabras`)** debe incluir obligatoriamente `### 2.1 Anatomía Profunda del Modelo de Negocio` y `### 2.2 Catálogo Exhaustivo de Productos y Servicios` con una tabla maestra de al menos 12 filas de líneas de producto/SKUs reales y desglose narrativo línea por línea.
   - El **Módulo 03 (`>= 1,550 palabras`)** se centra 100% en `TAM/SAM/SOM`, Sensibilidades Macro/FX/Commodities, 5 Fuerzas de Porter y Mapa Competitivo (sin pre-auditoría contable redundante), mientras que el **Módulo 04 (`>= 1,550 palabras`)** integra el Moat, la Huella Industrial/R&D y el análisis ESG operativo (`4.3`).
2. **`borrador_parte2.md` (`>= 66,000 bytes`):**
   - **Módulos 05, 06, 07 y 08** (Análisis Forense del Balance con **Auditoría de Notas Críticas a los Estados Financieros e Ítems Fuera de Balance integrada en `5.2`**, Gestión de Liquidez y Deuda en `5.6`, Cuenta de Resultados y Flujos de Caja con **Unit Economics, Apalancamiento Operativo, Owner Earnings y FCF ex-SBC**, DuPont de 5 pasos y ROIC vs. WACC en `Módulo 06`, KPIs Operativos Sectoriales en `Módulo 07`, y Directiva, Gobernanza y ROIC Incremental en `Módulo 08`) + `## RESUMEN PARTE 2`.
3. **`borrador_parte3.md` (`>= 62,000 bytes`):**
   - **Módulos 09, 10, 11 y 12** (Estructura Accionarial e Insiders en `Módulo 09`; Valoración Multi-Método con Secciones A [DCF + Reverse DCF + Matriz 5x5], B [SOTP], C [Múltiplos] y D [Escenarios Probabilísticos] en `Módulo 10`; **Proyecciones Operativas Futuras a 5 Años explicando su origen exacto [Consenso Sell-Side / Guidance vs. Escenarios Bear/Base/Bull del Comité] en `Módulo 11 Sección A`** + Matriz de Riesgos en prosa sin `|` en `Sección B`; Catalizadores Corto/Medio/Largo plazo + Ocultos + Kill-Switches en prosa sin `|` en `Módulo 12`) + `## RESUMEN PARTE 3`.
4. **`borrador_parte4.md` (`>= 50,000 bytes`):**
   - **Módulos 13, 14, 15, 16, 17 y 18** (Análisis Técnico en `Módulo 13`; Sentimiento Institucional y Consenso Sell-Side en `Módulo 14`; **Noticias Recientes 2025–2026, Matriz de Impacto y Checklist de Monitorización Trimestral en `Módulo 15`**; **Ajustes Forenses de Valoración (`16.1 Sección A`) + El Debate del Comité Bull vs. Bear en prosa sin `|` (`16.2 Sección B`) en `Módulo 16`**; **Veredicto Final Ejecutable del Comité estructurado en 5 Bloques (`17.1 Scorecard Ponderado`, `17.2 Anatomía del TSR e IRR`, `17.3 Comprar Hoy vs. Reservar Liquidez`, `17.4 Plan en 3 Tramos + Kelly + Stop-Loss`, `17.5 Tabla de Veredicto Ejecutable`) en `Módulo 17`**; y **Tear Sheet Ejecutivo con exactamente 5 puntos numerados (`1.` a `5.`) en `Módulo 18`**, cerrando el informe sin anexos posteriores).
5. **Consolidación y Validación del Informe Maestro (`.md`):**
   - Concatena en orden exacto `borrador_parte1.md` + `borrador_parte2.md` + `borrador_parte3.md` + `borrador_parte4.md` en `<COMPANY_DIR>/[FILE_PREFIX]_INFORME_COMITE_FINAL.md` (`>= 256,000 bytes` y `>= 29,250 palabras`).
   - Ejecuta la validación determinista (REGLA DE BLOQUEO: prohibido avanzar a Fase 4 hasta obtener `EXIT 0`):
     ```powershell
     python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target md
     ```
   - Corrige cualquier módulo o anclaje con `edit_file` hasta obtener `=== GAUNTLET PASS (EXIT 0) (... | target=md) ===`.

### Fase 4: Generación de los 10 Gráficos (`300 DPI`) y Compilación del Word Institucional (`.docx >= 27,000 palabras`)
1. Adapta [build_deliverables_reference.py](./scripts/build_deliverables_reference.py) con los datos reales auditados de la empresa para generar en `<COMPANY_DIR>/charts/` los **10 gráficos PNG a 300 DPI (`>25 KB` cada uno)** e incrustarlos en su módulo exacto del Word y en su diapositiva correspondiente del PPTX:
   - `chart1` (**Módulo 01** / **Slide 5**): Desempeño Histórico Auditado de Ingresos, EBITDA y Beneficio Neto (últimos 5 años cerrados + último periodo intermedio; **100% histórico, cero proyecciones futuras**).
   - `chart2` (**Módulo 02** / **Slide 6**): Desglose de Ingresos por Segmento de Negocio y Geografía (mix divisional y peso relativo).
   - `chart3` (**Módulo 03** / **Slide 13**): Benchmarking Competitivo de Múltiplos y Márgenes frente a los 4–5 competidores cotizados reales.
   - `chart4` (**Módulo 05** / **Slide 15**): Radiografía de Liquidez Total No Restringida vs. Deuda Financiera, Capital Circulante (DSO, DIO, DPO, CCC) y Caja Neta Forense.
   - `chart5` (**Módulo 06** / **Slide 19**): Evolución Multianual de Márgenes Operativos (`Bruto`, `EBITDA`, `EBIT`, `Neto`), Apalancamiento Operativo y Spread de Creación de Valor (`ROIC vs. WACC`).
   - `chart6` (**Módulo 07** / **Slide 20**): Ciclo de Conversión de Caja (DSO, DIO, DPO, CCC) y cómo el capital circulante negativo financia el negocio gratis.
   - `chart7` (**Módulo 10** / **Slide 30**): Triangulación del Precio Objetivo y Escenarios Probabilísticos (Campo de Fútbol / *Valuation Football Field*: DCF, SOTP, Múltiplos, Escenarios vs. Precio Spot).
   - `chart8` (**Módulo 11** / **Slide 26**): Proyecciones Operativas Futuras a 5 Años de Ingresos, EBITDA y Cosecha de FCF (comparativa explícita de Escenarios Bear, Base y Bull del Comité frente al Consenso Sell-Side / Guidance).
   - `chart9` (**Módulo 13** / **Slide 36**): Estructura Técnica del Precio (12 meses), Medias Móviles (`MM50`/`MM200`), Soportes/Resistencias y Niveles de Ejecución en 3 Tramos.
   - `chart10` (**Módulo 17** / **Slide 38**): Scorecard Institucional de los 6 Pilares, Puente SOTP y Anatomía de la Rentabilidad Esperada (TSR / TIR Asimétrico Bear/Base/Bull vs. Spot).
2. Compila `<COMPANY_DIR>/[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` ejecutando directamente el compilador compartido [build_institutional_docx.py](./scripts/build_institutional_docx.py) (`python "<COMPANY_DIR>/build_institutional_docx.py" --target-dir "<COMPANY_DIR>"`), que convierte en ~2 segundos el 100% del Markdown consolidado a OOXML nativo:
   - Portada ejecutiva Navy (`#0A192F`) y Dorado (`#B8860B`).
   - Tablas nativas con `<w:tblHeader/>` (repetición de cabecera) y `<w:cantSplit/>` (no partir filas entre páginas).
   - Incrustación automática de los **10 gráficos PNG** en sus módulos correspondientes (`Módulos 01, 02, 03, 05, 06, 07, 10, 11, 13 y 17`).
   - Limpieza total de sintaxis Markdown (`**`, `###`, `|`) y LaTeX (`$`, `\times`, `\approx`).
   - Al menos **`27,000 palabras`** (~95–110 páginas) y `>= 92%` del conteo de palabras del `.md`.
3. Valida con:
   ```powershell
   python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target docx
   ```

### Fase 5: Construcción y Auditoría del Pitch Deck de 60 Diapositivas 16:9 (Nueva Arquitectura Narrativa en 7 Actos — `.pptx` únicamente, sin `.pdf`)
1. Genera únicamente `<COMPANY_DIR>/[FILE_PREFIX]_PRESENTACION_COMITE_60_SLIDES.pptx` (queda eliminada la generación de `.pdf` a partir del PPT) ejecutando el compilador determinista:
   ```powershell
   python "<COMPANY_DIR>/build_institutional_pptx.py" --target-dir "<COMPANY_DIR>"
   ```
   o ejecutando `build_deliverables_reference.py` adaptado con los datos de la empresa.

2. **Estructura Arquitectónica Inquebrantable de las 60 Diapositivas en 7 Actos:**
   Cada presentación debe estructurarse siguiendo de forma estricta los 7 Actos narrativos que responden paso a paso a las preguntas de un inversor institucional y reflejan el orden natural del informe de 18 módulos:

    - **ACTO I — Quién es la empresa, escala, qué hace y desempeño histórico (Diapositivas 1 a 6 | Módulo 01):**
     * **Slide 1:** Portada ejecutiva Hero con 4 KPIs macro (Veredicto vinculante, Precio Spot, Precio Objetivo Base, Calificación de Moat) + viñetas de tesis institucional.
     * **Slide 2 *(Identidad y Perfil Corporativo)*:** Perfil corporativo de la compañía: qué hace, actividad nuclear, fecha de fundación (desde cuándo), sede social, mercados de cotización y escala operativa (Subsección 1.1; tabla institucional de dimensiones corporativas y viñetas de perfil).
     * **Slide 3 *(Oferta Comercial y Dónde Opera)*:** Catálogo nuclear de productos/servicios y presencia geográfica: qué soluciones vende, clientes, modelo de monetización y distribución territorial de operaciones (Subsecciones 1.1 y 2.2; tarjetas editoriales duales de productos y huella geográfica).
     * **Slide 4 *(Ancla obligatoria)*:** Desempeño histórico auditado de los últimos 5 años cerrados + último intermedio (**chart1** | Subsecciones 1.3 y 1.4; 100% histórico, cero proyecciones).
     * **Slide 5 *(Ancla obligatoria)*:** Cascada y dinámica de Cash Flow histórico auditado (**chart1b** | Subsecciones 1.3 y 1.4; barras OCF, CapEx, FCF + líneas de márgenes CFO% y FCF%).
     * **Slide 6:** Tesis central de inversión y pilares estratégicos de la recomendación Buyside (Subsección 1.2; tabla de 4 pilares estratégicos: Escala de Mercado, Eficiencia Operativa, Conversión a Caja Libre y Margen de Seguridad/Valoración).
   - **ACTO II — Cómo lo hace: catálogo, tecnología, calidad de ingresos, mercado y ventaja competitiva (Diapositivas 7 a 17 | Módulos 02, 03 y 04):**
     * **Slide 7 *(Ancla obligatoria SKILL.md)*:** Catálogo exhaustivo de productos y servicios comerciales (Subsección 2.2 Parte I; tabla de 8-12 líneas con SKUs, plataformas y monetización).
     * **Slide 8:** Tecnología diferencial, arquitectura técnica e infraestructura crítica (Subsección 2.2 Parte II; patentes, centros operativos y ventajas fabriles).
     * **Slide 9:** Mix de ingresos por división operativa y diversificación geográfica (**chart2** | Subsección 2.3; gráficos de tarta/barras).
     * **Slide 10:** Calidad de los ingresos (QoE) forense: recurrencia, visibilidad contractual, DSO/DSRI y nota QoE 1-10 (Subsecciones 2.4 y 2.5).
     * **Slide 11:** Política de reconocimiento contable de ingresos, devengos y ciclo de cobro (Subsección 2.5; divergencias CFO vs NI).
     * **Slide 12:** Evaluación multidimensional del Moat: las 5 fuentes de Dorsey y diagnóstico Mauboussin/Greenblatt (Subsección 2.6; nota 1-10 y vector dinámico).
     * **Slide 13:** Candados tecnológicos (Lock-ins), costes de cambio y análisis de red radial vs. bilateral (Subsección 2.6).
     * **Slide 14:** Proyección futura del mercado de crecimiento: TAM / SAM / SOM hacia 2030, CAGR por segmento y pista de expansión secular (Módulo 03: Subsecciones 3.1–3.3; tabla cuantitativa de 5 columnas).
     * **Slide 15 *(Ancla obligatoria)*:** Benchmarking competitivo frente a rivales cotizados (**chart3** | Subsección 3.4; doble panel horizontal McKinsey de EV/EBITDA y ROIC%).
     * **Slide 16:** Comparativa cualitativa y unit economics frente a peers globales (Subsección 3.4; fortalezas relativas).
     * **Slide 17:** Diagnóstico de ciclicidad del mercado, fase del ciclo, sensibilidades macroeconómicas (tipos, commodities, FX) y resiliencia en recesión (Módulo 03; tarjetas editoriales en 3 columnas).

   - **ACTO III — Cultura, capital humano, I+D y perfil ESG (Diapositivas 18 a 20 | Módulo 04):**
     * **Slide 18:** Cultura corporativa, incentivos de plantilla y retención de talento clave (Subsección 4.1).
     * **Slide 19:** Propiedad intelectual, pipeline de innovación e intensidad de I+D sobre ventas (Subsección 4.2).
     * **Slide 20:** Perfil ESG operativo: huella ambiental, seguridad laboral y gobernanza corporativa (Subsección 4.3).

  - **ACTO IV — Los números y la calidad financiera: balance, resultados, caja y eficiencia (Diapositivas 20 a 31 | Módulos 05, 06 y 07):**
     * **Slide 20:** Radiografía de liquidez, caja neta, deuda financiera y vencimientos (**chart4** | Subsección 5.2).
     * **Slide 21:** Reorganización McKinsey del balance: capital invertido operativo (IC) vs. activos no operativos (Subsección 5.1).
     * **Slide 22:** Auditoría forense de notas contables críticas: contingencias, arrendamientos y provisiones (Subsección 5.2).
     * **Slide 23:** Métricas de integridad contable y solvencia: Sloan Accruals, Beneish M-Score, Altman Z'' y nota de Salud Forense 1-10 (Subsección 5.5).
     * **Slide 24:** Capital de trabajo operativo (OWC), pasivos por contrato y anticipos de clientes como escudo de financiación (Subsecciones 5.3 y 5.4).
     * **Slide 25:** Cascada y puente de conversión de flujo de caja libre (OCF -> CapEx -> FCF ex-SBC) (**chart5** | Subsección 6.1).
     * **Slide 26:** Reorganización McKinsey de la cuenta de resultados: NOPLAT auditado y tasa impositiva efectiva (Subsección 6.1).
     * **Slide 27:** Apalancamiento operativo (DOL), estructura de costes fijos vs. variables y margen de contribución (Subsección 6.2).
     * **Slide 28:** Descomposición DuPont de 5 pasos y análisis de rotación de activos (Subsección 6.3).
     * **Slide 29:** Evolución histórica de márgenes operativos y spread de creación de valor ROIC - WACC (**chart6** | Módulo 07).
     * **Slide 30:** Ciclo de conversión de efectivo (CCC) y eficiencia de capital circulante (DSO, DIO, DPO) (Módulo 07).
     * **Slide 31:** Infraestructura industrial, especificidad de activos y retorno sobre activos productivos (Módulo 07).

   - **ACTO V — Gobernanza, equipo directivo y asignación de capital (Diapositivas 32 a 34 | Módulos 08 y 09):**
     * **Slide 32:** Equipo directivo clave (*The Big Boss*), remuneración ligada a creación de valor e historial de guidance (Subsecciones 8.1 y 8.2).
     * **Slide 33:** Asignación histórica del capital (5 años): CapEx orgánico, M&A, dividendos y recompras de acciones (Subsección 8.3).
     * **Slide 34:** Estructura accionarial, compras/ventas de insiders, concentración institucional y posiciones cortas (Módulo 09).

   - **ACTO VI — Valoración intrínseca unificada, múltiplos y proyecciones a 5 años (Diapositivas 35 a 42 | Módulos 10 y 11A):**
     * **Slide 35:** Modelo de valoración Enterprise DCF unificado (McKinsey-Damodaran): NOPLAT, reinversión y puente EV a Equity (Subsección 10.1).
     * **Slide 36:** Matriz de sensibilidad bidireccional DCF (WACC vs. crecimiento terminal g y márgenes) (Subsección 10.1).
     * **Slide 37:** Triangulación metodológica y Campo de Fútbol de valoración (**chart7** | Subsección 10.4).
     * **Slide 38:** Reverse DCF de Mauboussin: expectativas de crecimiento y márgenes implícitas en la cotización actual (Subsección 10.1).
     * **Slide 39:** Valoración por Suma de las Partes (SOTP) y valor oculto en activos no operativos (Subsección 10.2).
     * **Slide 40:** Valoración por múltiplos históricos frente a comparables y potencial de re-rating (Subsección 10.3).
     * **Slide 41:** Proyecciones operativas futuras a 5 años: escenarios Bear, Base y Bull frente al consenso (**chart8** | Módulo 11A).
     * **Slide 42:** Cuenta de resultados proyectada a 5 años y cosecha acumulada de caja libre (Módulo 11A).

   - **ACTO VII — Riesgos, catalizadores, debate dialéctico y veredicto ejecutable (Diapositivas 43 a 60 | Módulos 11B a 18):**
     * **Slide 43:** Matriz integral de riesgos operativos, tecnológicos y competitivos con probabilidad e impacto (Módulo 11B).
     * **Slide 44:** Gestión del riesgo de concentración de clientes y proveedores: contratos y mitigantes (Módulo 11B).
     * **Slide 45:** Riesgos macroeconómicos, regulatorios, aranceles y exposición de divisas (Módulo 11B).
     * **Slide 46:** Riesgos de disrupción tecnológica y sustitución de productos (Módulo 11B).
     * **Slide 47:** Mapa integral de catalizadores a corto, medio y largo plazo (Subsecciones 12.1–12.4).
     * **Slide 48:** Catalizador 1: Innovaciones de producto, nuevos lanzamientos y tracción comercial (Subsección 12.1).
     * **Slide 49:** Catalizador 2: Expansión geográfica y penetración en mercados internacionales (Subsección 12.2).
     * **Slide 50:** Catalizador 3: Aceleración de beneficios, dividendos/recompras y re-rating por flujos (Subsección 12.3).
     * **Slide 51:** Disciplina de venta forzosa y eventos Kill-Switch: criterios cuantitativos de salida (Subsección 12.5).
     * **Slide 52:** Análisis técnico institucional de los últimos 12 meses: soportes, medias móviles y liquidez (**chart9** | Módulo 13).
     * **Slide 53:** Consenso Sell-Side frente al sentimiento de mercado y posicionamiento institucional (Módulo 14).
     * **Slide 54:** Cronología de hechos relevantes 2025–2026 y semáforo de monitorización trimestral (Módulo 15).
     * **Slide 55:** Ajustes forenses aplicados y el gran debate del Comité: argumentos Bull vs. argumentos Bear (Módulo 16).
     * **Slide 56:** Scorecard institucional de los 6 pilares y perfil de retorno asimétrico (**chart10** | Subsección 17.1).
     * **Slide 57:** Rúbrica forense consolidada: Calidad de Ingresos (1-10), Moat (1-10) y Salud del Balance (1-10) (Subsección 17.1).
     * **Slide 58 *(Ancla obligatoria SKILL.md)*:** Plan táctico ejecutable: compra en 3 tramos, criterio de Kelly y Stop-Loss duro (Subsección 17.4; Ficha Contractual en 2 Columnas).
     * **Slide 59:** Dictamen vinculante del Comité de Inversiones: asignación de capital (% NAV) y veredicto final (Subsección 17.5).
     * **Slide 60 *(Ancla obligatoria SKILL.md)*:** Tear Sheet ejecutivo final con las 5 conclusiones numeradas que resumen toda la historia (Módulo 18; Cuadrícula 3x2 con exactamente los 5 puntos numerados 1. a 5. + tarjeta destacada de Dictamen Final).

3. **Reglas de Auditoría y Verificación:**
   - Exactamente **60 diapositivas** en formato panorámico 16:9 (`13.333" x 7.50"`).
   - Al menos **20 diapositivas** con evidencia visual (tablas nativas o gráficos PNG incrustados).
   - Cero frases truncadas ni cuadros de texto duplicados.
   - Action Titles en *sentence case* español según `humanamente` (P17).
   - Valida con:
     ```powershell
     python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target pptx
     ```

### Fase 6: Guion de Podcast a 3 Voces (`f5-guion` en 0.2s) y Cola Batch Final de Síntesis Acústica Kokoro-ONNX (`.mp3` entre 40 y 70 Minutos, Cobertura Completa M01–M17/M18, Borrado Físico del `.wav`)
1. Redacta directamente con `write_file` (mediante `SA-6`, `Model=LIGHT_MODEL` con fallback a `CORE_MODEL`, leyendo únicamente `brief_ppt_podcast.md`) el archivo `<COMPANY_DIR>/[FILE_PREFIX]_PODCAST_GUION.md`:
   - **Banda Objetivo y Ventana de Duración (`[40 min, 70 min]`):** **`58,000 a 70,000 bytes` (`8,600 a 9,800 palabras`, `90 a 110 intervenciones`)** — el audio `.mp3` resultante debe durar **como mínimo 40 minutos (`>= 2,400s`) y menos de 70 minutos (`<= 4,200s`)**.
   - **Cobertura Integral Obligatoria desde el Módulo 01 hasta el Módulo 17 (+ Cierre Módulo 18):** El guion y el audio MP3 deben recorrer **todos los módulos del informe en orden desde el Módulo 01 hasta el Módulo 17 (y el cierre Tear Sheet del Módulo 18)** sin detenerse jamás a mitad de informe (p. ej. en el Módulo 8) ni saltar turnos intermedios. Si el audio supera los 40 minutos para cubrir todos los módulos (p. ej. 48–62 minutos), es totalmente válido siempre que se mantenga por debajo de 70 minutos (`build_podcast_kokoro.py` condensa proporcionalmente las frases secundarias por turno si un guion excede el presupuesto de caracteres, garantizando que el 100% de los turnos y módulos M01–M18 sean locutados). Además, debe incluir los 4 debates clave: **(1) El Moat (Ventaja Competitiva)**, **(2) Calidad de los Ingresos**, **(3) Catalizadores** y **(4) Riesgos y Red Flags**.
   - **Regla de Formato Numérico en Guion:** Si un número supera `1,000` o se refiere a millones/billones, elimina todos los decimales para evitar errores de locución en el TTS.
   - Formato estricto de líneas de diálogo: `DIRECTOR: ...`, `ELENA: ...`, `MARCOS: ...`.
   - Español fonéticamente limpio: **cero siglas en inglés ni símbolos financieros** (`EBITDA` -> *ebitda*, `ROE` -> *retorno sobre el capital*, `WACC` -> *coste medio ponderado de capital*, `YoY` -> *interanual*, `HKD` -> *dólares de Hong Kong*, `%` -> *por ciento*, sin tickers con punto como `9988.HK`).
2. **En lotes multi-empresa (Protección de Caché TTL):**
   - Valida el guion inmediatamente en `0.2s` sin bloquear con CPU ejecutando:
     ```powershell
     python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --run-phase f5-guion
     ```
   - Y **al finalizar todos los subagentes LLM de todas las empresas**, ejecuta la síntesis acústica Kokoro en cola batch con **4 workers concurrentes por defecto** (0 tokens LLM, borrando `.wav` automáticamente):
     ```powershell
     python "ROOT_DIR/_shared_engine/gauntlet_gatekeeper.py" --batch-podcast-root "ROOT_DIR" --min-seconds 2460 --podcast-workers 4
     ```
   *(En ejecuciones de una sola empresa también puedes usar directamente `--run-phase f5-podcast` o `build_podcast_kokoro.py`).*
3. Valida con:
   ```powershell
   python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target podcast
   ```

### Fase 7: Verificación Integral (`--target all`), Orquestación Multi-Agente y Consolidación Global
1. **Verificación Final por Empresa:**
   ```powershell
   python "<COMPANY_DIR>/gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target all
   ```
   No des por terminada ninguna empresa hasta que devuelva `=== GAUNTLET PASS (EXIT 0) (<TICKER> | target=all) ===`.
2. **Orquestación Paralela Multi-Empresa:**
   - Cuando existan múltiples empresas en `ROOT_DIR`, lanza oleadas paralelas de hasta **8 subagentes simultáneos** (`invoke_subagent` con `TypeName="self"`, `Model="inherit"`) siguiendo la guía de [references/SUBAGENT_ORCHESTRATION_GUIDE.md](./references/SUBAGENT_ORCHESTRATION_GUIDE.md).
   - Si algún subagente se detiene en `state: "errored"` por un límite de cuota temporal (`429 RESOURCE_EXHAUSTED`) o *stream idle timeout*, **no lances un subagente nuevo**: reanúdalo inmediatamente con `send_message` usando su `conversationId` existente para conservar el 100% de su progreso.
3. **Consolidación Global de Cartera (`RESUMEN_CARTERA_GLOBAL.xlsx` y `.md`):**
   - Actualiza `<COMPANY_DIR>/extracted_ocr_cache/forensic_metrics.json` (o `company_meta.json` / `company_summary.json`) con las métricas definitivas (`summary_kpis`).
   - Ejecuta [build_global_portfolio_summary.py](./scripts/build_global_portfolio_summary.py):
     ```powershell
     python "ROOT_DIR/_shared_engine/build_global_portfolio_summary.py" --root-dir "ROOT_DIR"
     ```
   - Verifica que `ROOT_DIR/RESUMEN_CARTERA_GLOBAL.md` y `ROOT_DIR/RESUMEN_CARTERA_GLOBAL.xlsx` contengan el 100% de las empresas ordenadas por Retorno Total Esperado, incluyendo las columnas **`PAIS`** y **`Bolsas`** inmediatamente después del nombre de la empresa (`Compañía`), y que **`Ticker`**, **`PAIS`** y **`Bolsas`** tengan exactamente el valor que aparece en **`yFinance`**.
4. **Copia Final Consolidada de Entregables en las Carpetas `doc`, `mp3` y `ppt` (¡COPIAR, NUNCA MOVER!):**
   - Inmediatamente después de generar `RESUMEN_CARTERA_GLOBAL.xlsx`, crea las 3 carpetas consolidadas `doc/`, `mp3/` y `ppt/` (tanto en `ROOT_DIR` como en el directorio de trabajo padre si aplica) y **copia** (`shutil.copy2`, manteniendo intactos los archivos originales dentro de la subcarpeta de cada empresa) todos los entregables finales:
     - Todos los informes Word (`*_INFORME_INSTITUCIONAL_FINAL.docx`) -> hacia `doc/`
     - Todos los podcasts en audio (`*_PODCAST_COMITE.mp3`) -> hacia `mp3/`
     - Todas las presentaciones de 40 diapositivas (`*_PRESENTACION_COMITE_60_SLIDES.pptx`) -> hacia `ppt/`
   - Nota: [build_global_portfolio_summary.py](./scripts/build_global_portfolio_summary.py) ejecuta automáticamente esta función (`copy_deliverables_to_consolidated_folders`) al terminar de construir el Excel global; verifica siempre al final que el número de archivos en `doc/`, `mp3/` y `ppt/` coincida exactamente con el total de empresas procesadas.
