# Informe de Auditoría de Tokens y Coste por Modelo (Deep-Research Gauntlet-Loop)

**Generado:** 2026-11-06 18:15  
**Entorno Auditado:** Ejecución `TEST_2` (`002371.SZ` — NAURA Technology Group) en Antigravity (`V2 Phase-Split`) vs. Ejecución Histórica Monolítica (`V1` en `.dsh`).

---

## 1. Aclaración Crítica: Por qué salían 311M en el registro histórico vs. los 21,7M reales de `TEST_2`

1. **De dónde salían los 311,7M del reporte anterior:**
   El archivo `token_usage_registry.jsonl` conservaba acumulados los **1.034 pasos** de las sesiones previas ejecutadas en *DeepSeek Harness* (`.dsh/sessions`) bajo el modo **monolítico V1**. En un LLM, cada paso de agente reenvía todo el historial previo de la conversación (que se sirve desde *prompt-cache*). Cuando un único agente monolítico alcanza 450.000 tokens de contexto y ejecuta 650 pasos seguidos, la suma de lecturas de caché es $650 \times 450.000 \approx 292\text{M}$ de tokens de *cache-read*.
2. **Consumo REAL medido en esta ejecución (`TEST_2` / `002371.SZ`) con Arquitectura V2 (Fase-Split):**
   Al dividir el trabajo en subagentes efímeros con contexto aislado (`ORQUESTADOR` + `SA-1` + `SA-2` + `SA-5`), el consumo real medido en los `transcript_full.jsonl` de esta ejecución ha caído más de un **93%**:

| Sesión / Agente (`TEST_2` - `002371.SZ`) | ID Conversación | Pasos LLM | Tokens INPUT Fresco | Tokens CACHE-READ (Contexto Acum.) | Tokens OUTPUT Generados |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Orquestador Principal** | `05f44ec7` | 163 | 82.797 | 11.100.273 | 34.913 |
| **SA-1 (Borradores Parte 1 y 2 — Mód. 01-08)** | `e72ba7c0` | 68 | 28.750 | 3.394.825 | 52.999 |
| **SA-2 (Borradores Parte 3 y 4 — Mód. 09-18)** | `464e6a61` | 68 | 22.559 | 4.026.769 | 99.526 |
| **SA-5 (Guion de Podcast + Kokoro + QA)** | `f1c7cc3d` | 83 | 27.611 | 3.172.442 | 28.843 |
| **TOTAL REAL `TEST_2` (1 Empresa Completa V2)** | **4 sesiones** | **382** | **161.717 (0,16 M)** | **21.694.309 (21,69 M)** | **216.281 (0,22 M)** |
| *Comparativa Modo Monolítico Anterior (V1)* | *Histórico `.dsh`* | *1.034* | *3.463.371 (3,46 M)* | *308.242.236 (308,24 M)* | *705.467 (0,71 M)* |
| **Ahorro Logrado en `TEST_2` (V2 vs. V1)** | — | **-63,1%** | **-95,3%** | **-93,0%** | **-69,3%** |

---

## 2. Estimación de Coste Real por Empresa (`TEST_2` V2: 0,16M In / 21,7M Cache / 0,22M Out)

Aplicando el consumo real de `002371.SZ` (**161.717 tokens input fresco + 21.694.309 tokens cache-read + 216.281 tokens output**) a los distintos modelos del mercado:

| Modelo Candidato | USD/M Input | USD/M Cache | USD/M Output | Coste Input | Coste Caché | Coste Output | **TOTAL 1 Empresa (USD)** | **TOTAL 1 Empresa (EUR)** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **DeepSeek V4.1 Flash (valle)** | $0,15 | $0,003 | $0,60 | $0,02 | $0,07 | $0,13 | **$0,22 USD** | **0,20 €** |
| **GPT-6 Luna (OpenAI)** | $0,10 | $0,010 | $0,50 | $0,02 | $0,22 | $0,11 | **$0,34 USD** | **0,31 €** |
| **DeepSeek V4.1 Flash (pico)** | $0,30 | $0,006 | $1,20 | $0,05 | $0,13 | $0,26 | **$0,44 USD** | **0,40 €** |
| **MiniMax M3.1 Flash** | $0,15 | $0,015 | $0,60 | $0,02 | $0,33 | $0,13 | **$0,48 USD** | **0,44 €** |
| **Gemini 2.5 / 3.8 Flash (Google)** | $0,15 | $0,0375 | $0,60 | $0,02 | $0,81 | $0,13 | **$0,97 USD** | **0,89 €** |
| **GPT-4o Mini (OpenAI)** | $0,15 | $0,075 | $0,60 | $0,02 | $1,63 | $0,13 | **$1,78 USD** | **1,64 €** |
| **GLM-5.3 Flash** | $0,37 | $0,075 | $1,25 | $0,06 | $1,63 | $0,27 | **$1,96 USD** | **1,80 €** |
| **Qwen 2.5 72B Instruct** | $0,35 | $0,080 | $1,40 | $0,06 | $1,74 | $0,30 | **$2,10 USD** | **1,93 €** |
| **Claude 3.5 Haiku (Anthropic)** | $0,80 | $0,080 | $4,00 | $0,13 | $1,74 | $0,87 | **$2,73 USD** | **2,51 €** |
| **Claude 3.5 / 5.5 Sonnet** | $2,00 | $0,100 | $10,00 | $0,32 | $2,17 | $2,16 | **$4,66 USD** | **4,29 €** |
| **Gemini 2.5 / 3.8 Pro (Google)** | $1,25 | $0,3125 | $5,00 | $0,20 | $6,78 | $1,08 | **$8,06 USD** | **7,42 €** |
| **Claude 3.7 Sonnet (Anthropic)** | $3,00 | $0,300 | $15,00 | $0,49 | $6,51 | $3,24 | **$10,24 USD** | **9,42 €** |
| **GPT-4o (OpenAI)** | $2,50 | $1,250 | $10,00 | $0,40 | $27,12 | $2,16 | **$29,68 USD** | **27,31 €** |

---

## 3. Cómo Reducir Todavía Más el Consumo: De 21,7M a ~4,5M de Contexto Total (Plan V3 Ultra-Lean)

Aunque los **161k tokens de input fresco** y **216k de output** ya son prácticamente el mínimo físico (porque el informe final de 42.000 palabras + guion de 8.800 palabras + lecturas base ya suman ~150k tokens de texto puro), los **21,7M de tokens de caché acumulada** se deben exclusivamente al **número de pasos (382 pasos)**: cada vez que el agente ejecuta un comando pequeño en consola, re-envía su contexto acumulado a la caché.

Aplicando estas **5 medidas quirúrgicas**, podemos bajar de **382 pasos a ~45 pasos totales** y reducir el contexto acumulado de **21,7M a ~4,5M tokens por empresa** (reduciendo otro **80%** el coste sin tocar una sola palabra de calidad):

### 1. Pre-extracción contable determinista en Fase 0 (Baja el Orquestador de 163 pasos / 11,1M a 12 pasos / 0,6M)
* **Qué ocurrió:** El Orquestador gastó ~100 pasos ejecutando micro-scripts `python -c` para buscar tablas en chino dentro de los JSON de OCR, depurar encabezados y comprobar anclas.
* **Solución:** Incorporar en `build_company_financial_model.py` un extractor determinista de las tablas contables (ingresos, beneficio neto, CFO, activos, patrimonio, auditor) y un pre-validador automático que normalice las anclas de `borrador_parte1..4.md` en Python puro antes de llamar al Gatekeeper.

### 2. Pre-empaquetado de consultas (`company_facts_pack.md`) antes de lanzar SA-1 y SA-2 (Baja SA-1 y SA-2 de 136 pasos / 7,4M a 16 pasos / 1,8M)
* **Qué ocurrió:** SA-1 y SA-2 hicieron ~68 pasos cada uno porque ejecutaron múltiples consultas a `gauntlet_memory_wiki.py` y verificaciones parciales mientras ya tenían medio borrador en su ventana de contexto.
* **Solución:** Que el script determinista de Fase 0 ejecute de golpe las 10 consultas clave de `gauntlet_memory_wiki.py` y guarde un único archivo `company_facts_pack.md` (~15 KB). Así SA-1 y SA-2 lo leen en el paso 1 y redactan sus borradores de principio a fin sin hacer búsquedas intermedias.

### 3. Escritura en 1 solo bloque por borrador + Autofix determinista inmediato
* **Qué ocurrió:** Redactar cada borrador en 2 bloques (`Overwrite` + `Append`) y luego corregir gerundios o titulares a mano duplica los turnos donde el borrador entero viaja en el contexto.
* **Solución:** Escribir cada `borrador_parteN.md` en 1 sola llamada `write_file` y aplicar `python humanamente_gate.py --fix` determinista (0 tokens LLM).

### 4. Script único encadenado para la Fase 2.3 (Derivados Visuales, Word y PPTX en 1 solo paso LLM)
* **Qué ocurrió:** Lanzar por separado `generate_10_charts.py`, `build_institutional_docx.py`, `build_slides_deck_json.py`, `build_institutional_pptx.py` y sus respectivos gatekeepers consume 8-10 turnos de agente.
* **Solución:** Ejecutar los 4 compiladores deterministas en un único comando encadenado de consola (1 solo paso LLM = 0 re-lecturas de contexto).

### 5. SA-5 (Podcast) directo desde `brief_ppt_podcast.md` en 4 pasos (Baja SA-5 de 83 pasos / 3,17M a 5 pasos / 0,35M)
* **Solución:** SA-5 lee únicamente `brief_ppt_podcast.md` (19 KB), escribe el guion en 1-2 llamadas `write_file`, y lanza en un único comando final `humanamente_gate.py --fix && build_podcast_kokoro.py && gauntlet_gatekeeper.py --target podcast`.

### Proyección de Coste con el Plan V3 Ultra-Lean (~4,5M Cache / 120k In / 210k Out):
* **DeepSeek V4.1 Flash:** **$0,16 USD (0,15 €)** por empresa.
* **Gemini 2.5 / 3.8 Flash:** **$0,31 USD (0,29 €)** por empresa.
* **Claude 3.5 Haiku:** **$1,30 USD (1,20 €)** por empresa.
* **Claude 3.5 Sonnet:** **$2,75 USD (2,53 €)** por empresa.
