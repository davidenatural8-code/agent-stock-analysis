# Guía de Prompts Operativos — `deep-research-gauntlet-loop`

Este documento contiene los **4 prompts operativos listos para copiar y pegar** (desde el **Caso 0: Prompt Maestro Multi-Empresa** hasta los **Casos 1, 2 y 3** para operaciones puntuales). Solo tienes que sustituir las rutas entre `<...>` por la carpeta que quieras procesar.

---

## Caso 0: Prompt Maestro — Pipeline Completo Multi-Empresa en Paralelo (`UNATTENDED DEEP-RESEARCH MODE`)

> **Cuándo usarlo:** Cuando quieres lanzar el pipeline autónomo completo sobre una carpeta raíz (`ROOT_DIR`) con múltiples subcarpetas de empresas, saltando las ya terminadas (`SKIP`), completando las pendientes en paralelo (`RESUME / NEW`) y generando al final el Excel global y las carpetas consolidadas `doc/`, `mp3/` y `ppt/`.

```markdown
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo y desatendido (`UNATTENDED DEEP-RESEARCH MODE`).

### 1. Configuración de Entorno, Modelos (`CORE_MODEL` + `LIGHT_MODEL`) y Despliegue V3.6
* **Directorio Raíz (`ROOT_DIR`):** `C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\Informe_2026_10_31-16-17`
* **Configuración de Modelos LLM (con Fallback Automático Multi-LLM):**
  * `CORE_MODEL`: `inherit` *(cámbialo a `pro` si quieres forzar tier Pro, o déjalo en `inherit` para usar exactamente el LLM elegido en Antigravity: Gemini, Claude, GPT, etc.)* -> se usa en `SA-1` (M01–M04), `SA-2` (M05–M08), `SA-3` (M09–M11) y `SA-5` (M16–M18).
  * `LIGHT_MODEL`: `flash` *(o `flash_lite`, o cámbialo a `inherit` si quieres un único LLM en todo)* -> se usa en `SA-4` (M12–M15) y `SA-6` (Guion de Podcast).
  * **Fallback Automático:** Si ejecutas con un LLM distinto de Gemini o `LIGHT_MODEL` no está disponible / devuelve error de cuota o proveedor, **conmuta automáticamente `LIGHT_MODEL = "inherit"`** (el mismo LLM activo de la sesión) sin detener el pipeline.
* **Subagente Ligero (`gauntlet_writer` con Parallel Tool Calling) y Sub-Orquestadores (>30 empresas):** Registra una sola vez al inicio `define_subagent(Name="gauntlet_writer", EnableWriteTools=True, EnableSubagentTools=False, EnableMCPTools=False, ...)` con Regla Cero Consola, Parallel Tool Calling (escribir JSON + borrador en el mismo turno) y escritura en 1 bloque (`Overwrite=true`) para archivos `<= 64 KB`. Si la cartera supera las 30 empresas, delega en Sub-Orquestadores efímeros de 25–30 empresas por tanda.
* **Concurrencia de Subagentes (`Warning TTL > 16 threads` sin bloqueo):** La banda recomendada para minimizar rupturas de caché por TTL (5 min) es `12–16` subagentes simultáneos; si pides `> 16` (ej. `24` o `32`), el orquestador mostrará un breve aviso/sugerencia de TTL pero **ejecutará el número exacto de threads/subagentes que indiques**.
* **Motor Compartido:** Despliega los scripts actualizados del skill en `ROOT_DIR\_shared_engine\` y propágalos a cada subcarpeta de empresa.
* **Procesamiento en Paralelo + Pre-Web en Fase 0 + Cola Kokoro al Final:**
  * **SKIP:** Empresas que ya pasen `gauntlet_gatekeeper.py --target all` con `EXIT 0`.
  * **RESUME / NEW:** Ejecuta Fase 0 en lote (generando `web_research_digest.md` con consenso Sell-Side/noticias 2025–2026 y `facts_sa1..4.md` compactados a `<= 740L`), lanza las oleadas LLM (prohibido que un solo subagente acumule M01–M18 + Guion en la misma sesión; usa `SA-1..SA-6` o el Split Dual `SA-A` + `SA-B` en `<= 6` pasos), y **deja toda la síntesis de audio MP3 de Kokoro para el final absoluto** con `gauntlet_gatekeeper.py --batch-podcast-root "ROOT_DIR" --min-seconds 2460`. Si un subagente entra en `state: "errored"`, reanúdalo con `send_message` sin duplicar, y haz `kill` tras validar.

---

### 2. Flujo de Trabajo Secuencial por Empresa (Orden Estricto y Bloqueante)
Para cada empresa, ejecuta las siguientes fases en **orden estrictamente secuencial**. **PROHIBIDO** avanzar a la siguiente fase sin haber completado y verificado en disco los archivos de la fase anterior:

#### FASE 2.1 — Extracción Selectiva de PDFs y Búsqueda Activa
* Ejecuta `prepare_company_ocr_and_market.py` aplicando la **Regla de Selección Documental**: extrae el **100% de los Informes Anuales (`ANNUAL`)**, el **100% de los Informes Intermedios (`INTERIM`)** y **únicamente el último Informe Trimestral (`QUARTERLY` más reciente)**, ignorando trimestrales antiguos.
* Verifica que `company_meta.json` conserve los valores exactos de `yFinance` para `country` (`PAIS`), `exchange` (`Bolsas`), `primary_ticker` (`Ticker`) y `currency` (`Divisa`).
* Ejecuta búsqueda activa en Internet (`search_web`) para obtener catálogo comercial completo de productos/SKUs, noticias 2025–2026, múltiplos en vivo y consenso de analistas Sell-Side.

#### FASE 2.2 — Borradores e Informe Maestro Optimizado (BLOQUEANTE)
1. **Borradores:** Redacta directamente los 4 borradores (`borrador_parte1..4.md`) con `write_file` en 2 bloques limpios por archivo (`Overwrite=True` + `Append=True`), integrando el **Evaluador Maestro del Moat** (`references/MASTER_MOAT_AND_VALUE_EVALUATOR.md`) y el **Motor Unificado de Valoración y Auditoría Forense McKinsey & Damodaran** (`references/MCKINSEY_DAMODARAN_VALUATION_AND_FORENSIC_QOE.md`):
   * `borrador_parte1.md` (`>= 84,000 bytes`): Módulos 01 a 04. El **Módulo 01** es **100% histórico auditado** (sin proyecciones futuras); el **Módulo 02** (`>= 3,400 palabras`) incluye `2.1`, `2.2 Catálogo Exhaustivo de Productos y Servicios` (tabla >= 12 filas), `2.5 Calidad de Ingresos (QoE)` con Rúbrica Cuantitativa en 5 Bloques (Orgánico vs M&A `2.5`, DSO/DSRI `2.0`, Conversión CFO/NI y FCF/NOPLAT 80-120% `2.5`, Ratio Sloan `1.5`, Purificación SBC/EBITDA `1.5`) dando la **`Puntuación de Calidad de Ingresos (1 a 10): X.X / 10`**, y `2.6 Evaluación Multidimensional del Moat` aplicando el **Evaluador Maestro de Mauboussin, Dorsey y Greenblatt** (`ROIC-WACC`, `ROC`, Filtro Falsos Fosos, Ciclo Vida, Christensen, `WTP - OC`, 5 Fuentes Dorsey [0 a 3], 7 Lock-Ins, Red Radial vs. Bilateral y Tabla en 5 Bloques Ponderados `15+20+10+40+15=100 pts/10` con `Calificación del Moat Global (1 a 10): X.X / 10` + Vector Dinámico `[+ / = / -]`); el **Módulo 03** (`>= 2,000 palabras`) cubre `TAM/SAM/SOM`, Sensibilidades Macro/FX/Commodities, 5 Fuerzas de Porter + Estructura Industrial de Mauboussin (*Profit Pools*, Estabilidad de Cuota $\Delta < 1.5\%$, Velocidad de Ciclo de Precios, Especificidad de Activos, $\text{MES}$, $HHI$, Complementadores y Teoría de Juegos); el **Módulo 04** cubre Cultura, I+D y ESG operativo (`4.3`).
   * `borrador_parte2.md` (`>= 64,000 bytes`): Módulos 05 a 08. El **Módulo 05** integra la **Reorganización del Balance según McKinsey** (Caja Operativa al 1.5-2.0%, Capital de Trabajo Operativo OWC, Capital Invertido IC con I+D y arrendamientos capitalizados según Damodaran, Activos No Operativos y Deuda Neta Total) y en `5.5` la **Rúbrica Forense y Solvencia en 5 Bloques** (Solvencia y caja libre `2.0`, Activos fantasma y Goodwill <40% `2.0`, Fuera de balance `2.0`, Beneish M-Score y Altman Z `2.0`, Test de estrés -20% `2.0`) dando la **`Puntuación de Salud Forense del Balance (1 a 10): X.X / 10`** + Trayectoria; el **Módulo 06** integra la **Reorganización de Resultados según McKinsey** (NOPLAT sin escudos fiscales de deuda, árbol de ROIC, DuPont 5 pasos, EVA), **Unit Economics**, **Apalancamiento Operativo**, **Owner Earnings**, **FCF ex-SBC** y **ROC de Greenblatt**; el **Módulo 08** evalúa directiva (*The Big Boss*) y asignación de capital.
   * `borrador_parte3.md` (`>= 62,000 bytes`): Módulos 09 a 12. El **Módulo 10** integra la **Valoración Intrínseca Unificada McKinsey-Damodaran** (Modelo Enterprise DCF basado en NOPLAT y FCF Operativo; Valor de Continuación CV con fórmula Key Value Driver `[NOPLAT*(1-g/RONIC)]/(WACC-g)` con convergencia `RONIC -> WACC` y `g <= PIB`; Puente institucional de 10 pasos EV a Equity Value por acción; Múltiplos con Variables Acompañantes de Damodaran; Reverse DCF de Mauboussin; y Fórmula Mágica de Greenblatt `EY = EBIT/EV` vs `ROC`); el **Módulo 11 (`Sección A`)** desarrolla las **Proyecciones Operativas Futuras a 5 Años** ligadas a la reinversión de Damodaran (`g = IR * ROIC`) superando el Triple Test (Posible, Plausible, Probable) frente a Consenso Sell-Side + `Sección B` (Riesgos en prosa sin `|`).
   * `borrador_parte4.md` (`>= 46,000 bytes`): Módulos 13 a 18 (**sin Anexos A, B ni C al final**). **Módulo 15:** Noticias Recientes y Monitorización Trimestral; **Módulo 16:** Ajustes Forenses (`16.1`: Sloan Accruals, Beneish, Altman Z, normalización cíclica Damodaran) + Debate Bull vs. Bear en prosa sin `|` (`16.2`); **Módulo 17 (`>= 1,850 palabras`):** Veredicto Final Ejecutable en 5 Bloques (`17.1 Scorecard Ponderado` integrando Moat 1-10, QoE 1-10 y Salud Forense 1-10 + Matriz Moat vs. Precio, `17.2 Anatomía del TSR e IRR`, `17.3 Comprar Hoy vs. Reservar Liquidez`, `17.4 Plan en 3 Tramos + Kelly + Stop-Loss + Disciplina de Venta de Dorsey/Greenblatt`, `17.5 Tabla de Veredicto Ejecutable`); **Módulo 18:** Tear Sheet Ejecutivo (exactamente 5 puntos numerados `1.` a `5.`).
   * **Prohibido usar plantillas de Python** para redactar archivos `.md`.
2. **Informe Maestro:** Ensambla `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` cumpliendo `>= 256,000 bytes` y `>= 29,250 palabras` (18 módulos sin anexos finales) y valida con `gauntlet_gatekeeper.py --target md` hasta obtener `EXIT 0`.
* **REGLA DE BLOQUEO:** Prohibido iniciar los gráficos, el Word, la presentación o el podcast hasta que `gauntlet_gatekeeper.py --target md` devuelva `EXIT 0`.

#### FASE 2.3 — Derivados Visuales (Separación Estricta Historia vs. Futuro), Word (`>= 27,000 palabras`) y Pitch Deck (Sin PDF)
Tomando como **fuente única de verdad** el archivo `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` ya validado en la Fase 2.2:
1. Genera los **10 gráficos institucionales** a **300 DPI** en `charts/`, asegurando que:
   * `chart1` (**Módulo 01**) muestre **exclusivamente datos históricos auditados** (5 años cerrados + último intermedio, cero proyecciones).
   * `chart8` (**Módulo 11**) muestre las **proyecciones operativas futuras a 5 años** (Escenarios Bear/Base/Bull del Comité frente a Consenso Sell-Side).
   * `chart10` (**Módulo 17**) muestre el Scorecard Institucional, Puente SOTP y Perfil de Retorno Asimétrico del Veredicto Ejecutable.
2. Compila `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` ejecutando `build_institutional_docx.py --target-dir "<COMPANY_DIR>"`, garantizando **`>= 27,000 palabras`** (~95–110 páginas) y `>= 92%` de las palabras del `.md`, con los 10 gráficos incrustados en los Módulos `01, 02, 03, 05, 06, 07, 10, 11, 13 y 17`. Valida con `gauntlet_gatekeeper.py --target docx`.
3. Genera **únicamente** el Pitch Deck `[FILE_PREFIX]_PRESENTACION_COMITE_60_SLIDES.pptx` (**60 slides, formato 16:9**, **sin generar archivo `.pdf`**). Valida con `gauntlet_gatekeeper.py --target pptx`.

#### FASE 2.4 — Guion y Producción de Podcast (3 Voces, Solo `.mp3`, Borrando `.wav`)
Únicamente tras haber completado las Fases 2.2 y 2.3, redacta directamente `[FILE_PREFIX]_PODCAST_GUION.md` y genera el audio a 3 voces (`[FILE_PREFIX]_PODCAST_COMITE.mp3`, **eliminando físicamente el archivo temporal `.wav`** inmediatamente después de crear el `.mp3`) ejecutando:
`build_podcast_kokoro.py --target-dir "<COMPANY_DIR>" --min-seconds <SEGUNDOS_OBJETIVO>`

* **Cobertura Integral del Informe + 4 Bloques Innegociables:** El guion debe cubrir todos los módulos del informe e incluir obligatoriamente bloques dedicados donde las 3 voces (`DIRECTOR`, `ELENA`, `MARCOS`) debatan a fondo:
  1. **El Moat (Ventaja Competitiva)**
  2. **Calidad de los Ingresos y Conversión a Caja Libre (FCF)**
  3. **Catalizadores y Proyecciones Futuras**
  4. **Riesgos y Red Flags Forenses**
* **Regla de Formato Numérico en Guion:** Si un número supera `1,000` o se refiere a millones/billones, **elimina todos los decimales** para evitar errores de locución en el TTS.
* **Escalado según Complejidad:**
  * **Estándar / Estructura Simple:** `40 – 45+ min` (`--min-seconds 2460`), `>= 8,000 palabras`, `85 – 100+` intervenciones.
  * **Media-Alta / Multi-Segmento:** `45 – 52+ min` (`--min-seconds 2850`), `>= 8,500 – 9,500+ palabras`, `100 – 115+` intervenciones.
  * **Máxima / Conglomerado o Forense:** `52 – 60+ min` (`--min-seconds 3300`), `>= 9,500 – 11,000+ palabras`, `115 – 135+` intervenciones.

---

### 3. Validación y Control de Calidad (`Gatekeeper`)
* Verifica que el **100% de las empresas** devuelvan `EXIT 0` al ejecutar `gauntlet_gatekeeper.py --target all`. Si alguna falla, corrige únicamente los artefactos afectados hasta obtener `EXIT 0`.

---

### 4. Consolidación Global de Cartera
Al finalizar todas las empresas con `EXIT 0`:
1. Ejecuta `build_global_portfolio_summary.py --root-dir "ROOT_DIR"` para generar `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md` (sin columna `Rank`, con Freeze Panes en `B2` sobre `Compañía`, e incluyendo `PAIS`, `Bolsas`, `Ticker` y `Divisa` con los valores exactos de `yFinance`).
2. Verifica que se hayan **copiado** (sin mover ni eliminar los originales de sus subcarpetas) todos los entregables finales a las carpetas consolidadas dentro de `ROOT_DIR`:
   * Todos los `.docx` ➔ `doc/`
   * Todos los `.mp3` ➔ `mp3/`
   * Todos los `.pptx` ➔ `ppt/`
```

---

## Caso 1: Pipeline Completo para UNA Sola Empresa (Recreando TODO desde Cero / Force Overwrite)

> **Cuándo usarlo:** Cuando quieres procesar una única carpeta de empresa (`COMPANY_DIR`) y obligar al agente a **borrar/sobrescribir cualquier archivo previo** para regenerar desde cero los 4 borradores, el Informe Maestro `.md`, los 10 gráficos, el Word `.docx`, la presentación `.pptx` y el podcast `.mp3`.

```markdown
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo (`SINGLE-COMPANY FORCE REBUILD MODE`).

### 1. Alcance Exclusivo y Recreación Desde Cero (`FORCE OVERWRITE`)
* **Carpeta Objetivo (`COMPANY_DIR`):** `C:\Ruta\A\Tu\Carpeta\<TICKER_EMPRESA>`
* **Regla de Aislamiento:** Trabaja **EXCLUSIVAMENTE** dentro de `COMPANY_DIR`. Prohibido tocar otras carpetas de empresas.
* **Regla de Recreación Total (`NO SKIP`):** Ignora cualquier validación previa. Aunque los archivos ya existan en disco, **elimina o sobrescribe desde cero** todos los artefactos previos (`borrador_parte1..4.md`, `*_INFORME_COMITE_FINAL.md`, `charts/*.png`, `*_INFORME_INSTITUCIONAL_FINAL.docx`, `*_PRESENTACION_COMITE_60_SLIDES.pptx`, `*_PODCAST_GUION.md`, `*_PODCAST_COMITE.mp3` y cualquier `.wav` temporal).

### 2. Secuencia de Ejecución Obligatoria (Desde Cero)
1. **Extracción Selectiva y Búsqueda Web Activa:**
   * Ejecuta `prepare_company_ocr_and_market.py` sobre `COMPANY_DIR` (extrayendo el 100% de los Informes Anuales, el 100% de los Informes Intermedios y **únicamente el último Informe Trimestral**, ignorando trimestrales antiguos).
   * Verifica que `company_meta.json` y `forensic_metrics.json` contengan `country` (`PAIS`), `exchange` (`Bolsas`), `primary_ticker` (`Ticker`) y `currency` (`Divisa`) con los valores exactos de `yFinance`.
   * Ejecuta `search_web` para obtener el catálogo comercial exhaustivo de productos/SKUs, noticias 2025–2026, múltiplos en vivo y consenso de analistas.
2. **Redacción Directa de Borradores e Informe Maestro (`.md >= 256 KB` y `>= 29,250 palabras`):**
   * Redacta desde cero con `write_file` (`Overwrite=True` + `Append=True`) los 4 borradores (`borrador_parte1.md >= 84 KB`, `borrador_parte2.md >= 64 KB`, `borrador_parte3.md >= 62 KB`, `borrador_parte4.md >= 46 KB` sin anexos finales).
    * **Módulo 01 (`chart1`):** 100% datos históricos auditados (cero proyecciones futuras).
    * **Módulo 02 (`>= 3,400 palabras`):** Incluye `2.1`, `2.2 Catálogo Exhaustivo de Productos y Servicios` (tabla >= 12 filas), `2.5 Calidad de Ingresos (QoE)` con Rúbrica Cuantitativa en 5 Bloques (Orgánico vs M&A `2.5`, DSO/DSRI `2.0`, Conversión CFO/NI y FCF/NOPLAT 80-120% `2.5`, Ratio Sloan `1.5`, Purificación SBC/EBITDA `1.5`) dando la **`Puntuación de Calidad de Ingresos (1 a 10): X.X / 10`**, y `2.6 Evaluación Multidimensional del Moat` aplicando íntegramente el **Evaluador Maestro de Mauboussin, Dorsey y Greenblatt** (`references/MASTER_MOAT_AND_VALUE_EVALUATOR.md`: Diagnóstico base `ROIC-WACC` y `ROC`, Filtro de Falsos Fosos, Ciclo de Vida Competitivo, Disrupción/*Overshooting* de Christensen, Ecuación de Valor `WTP - OC`, Tabla de las **5 Fuentes de Dorsey [0 a 3]** y **Tabla de Puntuación Cuantitativa en 5 Bloques Ponderados [`15 + 20 + 10 + 40 + 15 = 100 pts / 10`]** con `Calificación del Moat Global (1 a 10): X.X / 10` + Vector Dinámico `[+ / = / -]`).
    * **Módulo 03 (`>= 2,000 palabras`):** Incluye *Profit Pools*, Estabilidad de Cuota a 5 años ($\Delta < 1.5\%$), Velocidad del Ciclo de Precios, Especificidad de Activos, Escala Mínima Eficiente ($\text{MES}$), Índice $HHI$, Complementadores y Teoría de Juegos (*Tit-for-Tat* vs. Dilema del Prisionero).
    * **Módulo 05:** Reorganización del Balance según McKinsey (OWC aislando caja operativa al 1.5-2.0%, IC con intangibles y capitalización de I+D/arrendamientos según Damodaran, Activos No Operativos y Deuda Neta Total) y en `5.5` la **Rúbrica Forense y Solvencia en 5 Bloques** dando la **`Puntuación de Salud Forense del Balance (1 a 10): X.X / 10`** + Trayectoria.
    * **Módulo 06:** Reorganización de Resultados según McKinsey (NOPLAT sin escudos fiscales de deuda, árbol de ROIC, DuPont 5 pasos, EVA), Unit Economics, Apalancamiento Operativo, Owner Earnings, FCF ex-SBC y `ROC` de Greenblatt.
    * **Módulo 10:** Valoración Intrínseca Unificada McKinsey-Damodaran (Enterprise DCF sobre NOPLAT/FCF; Valor de Continuación CV con fórmula Key Value Driver `[NOPLAT*(1-g/RONIC)]/(WACC-g)` con convergencia `RONIC -> WACC` y `g <= PIB`; Puente institucional de 10 pasos EV a Equity; Múltiplos con Variables Acompañantes de Damodaran; Reverse DCF de Mauboussin; y Fórmula Mágica de Greenblatt `EY` vs. `ROC`).
    * **Módulo 11 (`Sección A` + `chart8`):** Proyecciones Operativas Futuras a 5 Años ligadas a reinversión según Damodaran (`g = IR * ROIC`) superando el Triple Test (Posible, Plausible, Probable) frente a Consenso Sell-Side + `Sección B` (Riesgos en prosa sin `|`).
    * **Módulo 17 (`>= 1,850 palabras` + `chart10`):** Veredicto Final Ejecutable en 5 Bloques (`17.1` integrando Moat 1-10, QoE 1-10 y Salud Forense 1-10 + Matriz Moat vs. Precio, hasta `17.5` con la Disciplina de Venta de Dorsey/Greenblatt).
   * **Módulo 18:** Tear Sheet Ejecutivo (5 puntos numerados `1.` a `5.`, cerrando sin Anexos A/B/C).
   * Ensambla `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` y valida con `gauntlet_gatekeeper.py --target-dir "<COMPANY_DIR>" --target md` hasta obtener `EXIT 0`.
3. **Gráficos (`300 DPI`), Word (`>= 27,000 palabras`) y Pitch Deck (`60 Slides`, sin PDF):**
   * Regenera desde cero los **10 gráficos PNG a 300 DPI** en `charts/` (`chart1` 100% histórico en Módulo 01; `chart8` proyecciones futuras a 5 años en Módulo 11; `chart10` en Módulo 17).
   * Compila desde cero `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` (`>= 27,000 palabras`) con `build_institutional_docx.py --target-dir "<COMPANY_DIR>"` y valida con `--target docx`.
   * Regenera desde cero `[FILE_PREFIX]_PRESENTACION_COMITE_60_SLIDES.pptx` (60 diapositivas 16:9, **sin generar PDF**) y valida con `--target pptx`.
4. **Guion y Podcast a 3 Voces (`.mp3` entre 40 y 70 min, Cobertura Completa M01–M17/M18, eliminando `.wav`):**
   * Redacta desde cero `[FILE_PREFIX]_PODCAST_GUION.md` (`>= 8,000 palabras`, `>= 85 intervenciones`, recorriendo obligatoriamente todo el informe desde el Módulo 01 hasta el Módulo 17 + cierre Módulo 18 sin cortar en módulos intermedios, más los 4 bloques obligatorios: Moat, Calidad de Ingresos, Catalizadores y Riesgos/Red Flags; sin decimales en cifras > 1,000).
   * Ejecuta `build_podcast_kokoro.py --target-dir "<COMPANY_DIR>" --min-seconds 2460 --max-seconds 4020` para generar `[FILE_PREFIX]_PODCAST_COMITE.mp3` (entre 40 y 70 minutos, sintetizando el 100% de los turnos del Módulo 1 al 18) y borrar físicamente el archivo `.wav` temporal.
5. **Verificación Final:**
   * Ejecuta `gauntlet_gatekeeper.py --target-dir "<COMPANY_DIR>" --target all` y no te detengas hasta obtener `EXIT 0`.
```

---

## Caso 2: Generar SOLO el `.docx`, y/o el `.pptx`, y/o el `.mp3` para UNA Carpeta de Empresa

> **Cuándo usarlo:** Cuando la carpeta de la empresa (`COMPANY_DIR`) **ya tiene generado su informe maestro `*_INFORME_COMITE_FINAL.md`** y solo quieres crear o regenerar uno o varios de los entregables derivados (`.docx`, `.pptx` y/o `.mp3`) sin tocar ni reescribir el informe `.md`.
> *(Nota: En el punto 2 del prompt, deja solo las líneas de los archivos que quieras generar: Word, PPT y/o MP3).*

```markdown
Activa el skill `deep-research-gauntlet-loop` en modo selectivo de derivados (`DERIVATIVES-ONLY MODE`) para una única empresa.

### 1. Configuración y Fuente de Verdad
* **Carpeta Objetivo (`COMPANY_DIR`):** `C:\Ruta\A\Tu\Carpeta\<TICKER_EMPRESA>`
* **Regla de Protección del Informe `.md`:** **PROHIBIDO** modificar o regenerar `borrador_parte1..4.md` o `[FILE_PREFIX]_INFORME_COMITE_FINAL.md`. Toma el archivo `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` existente en `COMPANY_DIR` como fuente única de verdad.

### 2. Entregables a Generar / Recrear desde Cero (Sobrescribiendo si existen)
Ejecuta en `COMPANY_DIR` **ÚNICAMENTE** los siguientes entregables marcados:

1. **[SI QUIERES EL WORD `.docx`]**
   * Genera/actualiza los **10 gráficos institucionales a 300 DPI** en `<COMPANY_DIR>\charts\` (`chart1` 100% histórico para Módulo 01; `chart8` proyecciones futuras a 5 años para Módulo 11; `chart10` para Módulo 17).
   * Compila desde cero `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` (`>= 27,000 palabras`) ejecutando:
     `python "<COMPANY_DIR>\build_institutional_docx.py" --target-dir "<COMPANY_DIR>"`
   * Valida con: `python "<COMPANY_DIR>\gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target docx` hasta obtener `EXIT 0`.

2. **[SI QUIERES EL POWERPOINT `.pptx`]**
   * Genera desde cero `[FILE_PREFIX]_PRESENTACION_COMITE_60_SLIDES.pptx` (exactamente 60 diapositivas en formato 16:9, Diapositivas 7 y 8 dedicadas a Modelo de Negocio y Catálogo de Productos, **sin generar archivo `.pdf`**).
   * Valida con: `python "<COMPANY_DIR>\gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target pptx` hasta obtener `EXIT 0`.

3. **[SI QUIERES EL PODCAST `.mp3`]**
   * Redacta directamente con `write_file` el guion `[FILE_PREFIX]_PODCAST_GUION.md` (`>= 8,000 palabras`, `>= 85 turnos`, 3 voces `DIRECTOR:`, `ELENA:`, `MARCOS:`, cubriendo todo el informe más los 4 bloques obligatorios [Moat, Calidad de Ingresos, Catalizadores, Riesgos/Red Flags] y eliminando decimales en números > 1,000).
   * Sintetiza `[FILE_PREFIX]_PODCAST_COMITE.mp3` (`>= 2,400 segundos` / `>= 40 min`, borrando físicamente el `.wav` temporal al terminar) ejecutando:
     `python "<COMPANY_DIR>\build_podcast_kokoro.py" --target-dir "<COMPANY_DIR>" --min-seconds 2460`
   * Valida con: `python "<COMPANY_DIR>\gauntlet_gatekeeper.py" --target-dir "<COMPANY_DIR>" --target podcast` hasta obtener `EXIT 0`.
```

---

## Caso 3: Crear o Regenerar Desde Cero SOLO el Excel Global a partir de un `ROOT_DIR`

> **Cuándo usarlo:** Cuando ya tienes informes generados dentro de las subcarpetas de `ROOT_DIR` (estén todas las empresas terminadas o solo una parte) y quieres **regenerar desde cero únicamente el archivo Excel comparativo** con todas las métricas y datos de `yFinance`, sin tocar los informes ni mover archivos.

```markdown
Ejecuta únicamente la consolidación del Excel global de cartera del skill `deep-research-gauntlet-loop` (`EXCEL-ONLY REBUILD MODE`).

### 1. Parámetros de Ejecución
* **Directorio Raíz (`ROOT_DIR`):** `C:\Ruta\A\Tu\Carpeta_Raiz`
* **Nombre del Archivo Excel de Salida (`EXCEL_NAME`):** `RESUMEN_CARTERA_GLOBAL.xlsx` *(o cámbialo por `TEMP.xlsx` si prefieres otro nombre)*

### 2. Instrucciones Estrictas
1. **Prohibido regenerar informes, presentaciones o podcasts:** No modifiques ningún archivo `.md`, `.docx`, `.pptx` ni `.mp3` dentro de las subcarpetas de las empresas.
2. **Sincronización del Motor y Creación Desde Cero del Excel:**
   * Utiliza el script actualizado `c:\PROJECT\Informes\.agents\skills\deep-research-gauntlet-loop\scripts\build_global_portfolio_summary.py`.
   * Ejecuta:
     `python "c:\PROJECT\Informes\.agents\skills\deep-research-gauntlet-loop\scripts\build_global_portfolio_summary.py" --root-dir "<ROOT_DIR>" --excel-only --excel-name "<EXCEL_NAME>"`
3. **Verificación de Calidad de Datos en el Excel Generado:**
   * Verifica que el archivo `<ROOT_DIR>\<EXCEL_NAME>` se haya creado desde cero incluyendo todas las subcarpetas que ya tengan `*_INFORME_COMITE_FINAL.md`.
   * Comprueba que **no exista columna `Rank`**, que el **Freeze Panes esté en `B2`** (fijando cabecera y primera columna `Compañía`), y que las columnas **`PAIS`**, **`Bolsas`**, **`Ticker`** y **`Divisa`** tengan los valores reales de `yFinance`.
   * Inspecciona todas las filas del Excel generado para confirmar que **ninguna empresa tenga `0.0` en Precio Actual, Precio Objetivo Base (`P.O. Base`), Valor Esperado, Upside %, P/E, EV/EBITDA o Puntuaciones `1-10`**, ni `PENDIENTE` en el Veredicto. Si alguna subcarpeta usa claves JSON distintas, ajústalo y regenera el Excel hasta que el 100% de las filas estén completas.
```
