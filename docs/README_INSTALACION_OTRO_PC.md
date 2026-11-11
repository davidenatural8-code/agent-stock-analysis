# Guía de Instalación y Reutilización en Otro PC — Skill `deep-research-gauntlet-loop`

Este paquete contiene el **Skill completo y autónomo (`deep-research-gauntlet-loop`)** junto con todos los motores en Python (`scripts/`), especificaciones de los 18 módulos (`references/`), dependencias (`requirements.txt`) e instalador automático (`install_on_new_pc.bat` / `.ps1`).

---

## 1. Contenido del Archivo `SKILL_DEEP_RESEARCH_GAUNTLET_LOOP.zip`

```text
deep-research-gauntlet-loop/
├── SKILL.md                                        # Instrucciones maestras del flujo (Fases 0 a 7)
├── README_INSTALACION_OTRO_PC.md                   # Esta guía de instalación y prompts
├── requirements.txt                                # Librerías de Python necesarias
├── install_on_new_pc.bat                           # Instalador en 1 clic para Windows
├── install_on_new_pc.ps1                           # Script PowerShell de instalación automática
├── references/
│   ├── MODULES_01_TO_18_SPECIFICATION.md           # Especificación de los 18 Módulos + Anexos A/B/C
│   └── SUBAGENT_ORCHESTRATION_GUIDE.md             # Guía de oleadas de 8 subagentes y recuperación 429
└── scripts/
    ├── gauntlet_gatekeeper.py                      # Auditor determinista (md, docx, pptx, podcast, all)
    ├── build_podcast_kokoro.py                     # Sintetizador a 3 voces con Kokoro-ONNX (.wav y .mp3)
    ├── build_global_portfolio_summary.py           # Consolidador Excel/MD + copia automática a doc/, mp3/, ppt/
    ├── prepare_company_ocr_and_market.py           # Extractor del 100% de PDFs + datos de mercado en vivo
    ├── web_research_enricher.py                    # Buscador de noticias, consenso y múltiplos de comparables
    └── build_deliverables_reference.py             # Generador de 6 gráficos PNG (300 DPI), Word (.docx) y PPTX/PDF (40 slides)
```

---

## 2. Cómo Instalarlo en Otro PC (Opción A: En 1 Clic — Recomendada)

1. Copia el archivo **`SKILL_DEEP_RESEARCH_GAUNTLET_LOOP.zip`** al nuevo PC y descomprímelo en cualquier carpeta.
2. Haz doble clic sobre **`install_on_new_pc.bat`** (o ejecuta en PowerShell `.\install_on_new_pc.ps1`).
3. El instalador hará automáticamente los 3 pasos:
   - Copiará el skill en la carpeta global de Antigravity del usuario (`C:\Users\<TU_USUARIO>\.gemini\config\skills\deep-research-gauntlet-loop\`), quedando activo para **cualquier proyecto** que abras en ese PC.
   - Instalará todas las librerías de Python (`requirements.txt`).
   - Descargará los modelos de voz de Kokoro-ONNX (`kokoro-v1.0.onnx` y `voices-v1.0.bin`) para que la generación de podcasts funcione desde el primer minuto.

---

## 3. Cómo Instalarlo Manualmente en Otro PC (Opción B)

Si prefieres hacerlo manualmente sin usar el `.bat`:

1. **Copiar la carpeta del Skill:**
   - **Para que esté disponible en TODOS los proyectos del nuevo PC (Global):**
     Copia la carpeta `deep-research-gauntlet-loop` dentro de:
     `C:\Users\<TU_USUARIO>\.gemini\config\skills\deep-research-gauntlet-loop\`
   - **O para un único proyecto específico (Workspace):**
     Copia la carpeta `deep-research-gauntlet-loop` dentro de:
     `<CARPETA_DEL_PROYECTO>\.agents\skills\deep-research-gauntlet-loop\`
2. **Instalar las librerías de Python en el nuevo PC:**
   Abre una terminal en el nuevo PC y ejecuta:
   ```powershell
   pip install -r requirements.txt
   ```
   *(Nota opcional: Si en el nuevo PC deseas exportar automáticamente una copia en `.pdf` de las presentaciones `.pptx` de 40 diapositivas, ten instalado Microsoft PowerPoint o LibreOffice).*

---

## 4. Prompts Listos para Usar en el Nuevo PC

Una vez instalado, abre Antigravity en el nuevo PC y pega cualquiera de estos 3 prompts (cambiando únicamente la ruta `ROOT_DIR` o `COMPANY_DIR` por la carpeta donde tengas tus PDFs):

### Caso 1: Analizar TODAS las carpetas de empresas de un directorio raíz (Podcast estándar `>= 30 min`)

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo y desatendido (`UNATTENDED DEEP-RESEARCH MODE`) sobre el directorio raíz:
ROOT_DIR = "C:\RUTA\A\TUS\CARPETAS_DE_EMPRESAS"

Instrucciones de ejecución:
1. Despliega los motores del skill en `ROOT_DIR\_shared_engine\` y procesa todas las subcarpetas de empresas dentro de `ROOT_DIR` (aplicando SKIP a las que ya pasen `gauntlet_gatekeeper.py --target all` con EXIT 0 y RESUME/NEW a las pendientes, lanzando oleadas paralelas de hasta 8 subagentes).
2. Para cada empresa, extrae el 100% de sus PDFs, realiza búsqueda activa en Internet (`search_web`) y genera:
   - Los 4 borradores redactados directamente (`borrador_parte1..4.md`, prohibido usar plantillas de Python) y el informe maestro `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` (>= 185,000 bytes, >= 22,500 palabras, 18 módulos + Catálogo Exhaustivo 2.1/2.2 + Anexos A, B y C).
   - Los 6 gráficos institucionales a 300 DPI y el Word `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx`.
   - El Pitch Deck `[FILE_PREFIX]_PRESENTACION_COMITE_40_SLIDES.pptx` y `.pdf` (40 slides 16:9).
   - El guion `[FILE_PREFIX]_PODCAST_GUION.md` (>= 5,000 palabras) y el podcast a 3 voces `[FILE_PREFIX]_PODCAST_COMITE.wav` y `.mp3` (>= 30 minutos / 1,800s).
3. Verifica que el 100% de las empresas devuelvan `EXIT 0` en `gauntlet_gatekeeper.py --target all`.
4. Al finalizar todas las empresas, ejecuta `build_global_portfolio_summary.py --root-dir "ROOT_DIR"` para generar `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md`, y copia (sin mover los originales) todos los `.docx`, `.mp3` y `.pptx` en las carpetas consolidadas `doc/`, `mp3/` y `ppt/`.
```

### Caso 2: Analizar TODAS las carpetas de empresas con Podcast Dinámico de `40 a 60 minutos` según contenido y relevancia

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo y desatendido (`UNATTENDED DEEP-RESEARCH MODE`) sobre el directorio raíz:
ROOT_DIR = "C:\RUTA\A\TUS\CARPETAS_DE_EMPRESAS"

Instrucciones de ejecución con REGLA ESPECIAL DE PODCAST DINÁMICO (40 a 60 MINUTOS):
1. Despliega los motores del skill en `ROOT_DIR\_shared_engine\` y procesa todas las subcarpetas de empresas dentro de `ROOT_DIR` en oleadas paralelas de hasta 8 subagentes.
2. Para cada empresa, genera el informe completo de 85–90 páginas (`[FILE_PREFIX]_INFORME_COMITE_FINAL.md` >= 185 KB y >= 22,500 palabras con lectura del 100% de los PDFs y búsqueda web en vivo), el Word institucional (`.docx`) con 6 gráficos a 300 DPI y la presentación de 40 diapositivas (`.pptx` y `.pdf`).
3. DURACIÓN DINÁMICA DEL PODCAST (40 A 60 MINUTOS SEGÚN CONTENIDO Y RELEVANCIA):
   - Evalúa la complejidad contable, el número de segmentos/productos, el tamaño bursátil y la relevancia de la tesis de cada empresa:
     * Relevancia Estándar / Estructura Simple: objetivo de 40 a 45 minutos (`--min-seconds 2460`, guion de 7,000 a 8,000 palabras y 85–100 intervenciones).
     * Relevancia Media-Alta / Multi-Segmento: objetivo de 45 a 52 minutos (`--min-seconds 2850`, guion de 8,000 a 9,200 palabras y 100–115 intervenciones).
     * Relevancia Máxima / Conglomerado Complejo o Tesis Forense Crítica: objetivo de 52 a 60 minutos (`--min-seconds 3300`, guion de 9,200 a 10,800 palabras y 115–135 intervenciones).
   - Redacta directamente `[FILE_PREFIX]_PODCAST_GUION.md` con esa extensión y ejecuta `build_podcast_kokoro.py --target-dir "<COMPANY_DIR>" --min-seconds <SEGUNDOS_OBJETIVO>` para generar el `.wav` y `.mp3` entre 40 y 60 minutos.
   - Exige en `gauntlet_gatekeeper.py` un mínimo de `2,400 segundos` (40.0 minutos) y `>= 7,000 palabras` para `--target podcast`.
4. Al terminar el 100% de las empresas con `EXIT 0`, genera `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md` y copia (sin mover los originales) todos los `.docx`, `.mp3` y `.pptx` en las carpetas consolidadas `doc/`, `mp3/` y `ppt/`.
```

### Caso 3: Analizar SOLO UNA empresa en un directorio específico

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo para analizar ÚNICAMENTE la empresa cuyos PDFs se encuentran en este directorio:
COMPANY_DIR = "C:\RUTA\A\TU\EMPRESA\9988.HK"

Instrucciones de ejecución:
1. Trabaja exclusivamente sobre `COMPANY_DIR` (desplegando en `COMPANY_DIR` los scripts del skill `gauntlet_gatekeeper.py` y `build_podcast_kokoro.py`).
2. Extrae el 100% de las páginas de todos los PDFs dentro de `COMPANY_DIR\extracted_ocr_cache\`, obtén los datos bursátiles en vivo y ejecuta búsqueda activa en Internet (`search_web`) sobre su catálogo completo de productos, noticias 2025–2026, múltiplos y consenso de analistas.
3. Redacta directamente mediante `write_file`/`edit_file` (prohibido usar plantillas en Python) los 4 borradores (`borrador_parte1..4.md`) y consolida `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` (>= 185,000 bytes, >= 22,500 palabras, 18 módulos con Módulo 02 >= 2,400 palabras incluyendo 2.1 Modelo de Negocio y 2.2 Catálogo Exhaustivo de Productos, más Anexos A, B y C).
4. Genera los 6 gráficos PNG a 300 DPI en `charts/`, el documento Word `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` (>= 20,500 palabras) y la presentación `[FILE_PREFIX]_PRESENTACION_COMITE_40_SLIDES.pptx` y `.pdf` (40 diapositivas 16:9).
5. Redacta el guion `[FILE_PREFIX]_PODCAST_GUION.md` (>= 5,000 palabras, >= 65 turnos a 3 voces: DIRECTOR, ELENA y MARCOS) y sintetiza `[FILE_PREFIX]_PODCAST_COMITE.wav` y `.mp3` (>= 30 minutos / 1,800s) con `build_podcast_kokoro.py`.
6. Ejecuta `gauntlet_gatekeeper.py --target-dir "COMPANY_DIR" --target all` hasta obtener `=== GAUNTLET PASS (EXIT 0) ===`, actualiza el Excel comparativo global si existe `ROOT_DIR` y copia (sin mover) el `.docx`, `.mp3` y `.pptx` generados en las carpetas `doc/`, `mp3/` y `ppt/`.
```


---

### Caso 4: Re-ejecutar el flujo pero SOLO para un subconjunto específico de empresas dentro de `ROOT_DIR`

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo sobre el directorio raíz:
ROOT_DIR = "C:\PROJECT\Informes\Reports"

Procesa EXCLUSIVAMENTE esta lista de carpetas de empresas (ignora el resto de carpetas de `ROOT_DIR`):
TARGET_COMPANIES = ["700.HK", "9988.HK", "1810.HK"]

Instrucciones de ejecución:
1. Ejecuta `prepare_company_ocr_and_market.py --root-dir "ROOT_DIR" --tickers 700.HK 9988.HK 1810.HK` para extraer los PDFs y actualizar datos de mercado de esas empresas.
2. Para cada empresa de `TARGET_COMPANIES`, ejecuta el ciclo completo del skill (lectura de PDFs + búsqueda web activa + redacción directa de `borrador_parte1..4.md` + `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` >= 185 KB / >= 22,500 palabras + Word `.docx` con 6 gráficos a 300 DPI + Pitch Deck `.pptx`/`.pdf` de 40 slides + Podcast `.wav`/`.mp3` >= 30 min) hasta obtener `EXIT 0` en `gauntlet_gatekeeper.py --target all`.
3. Al finalizar, ejecuta `build_global_portfolio_summary.py --root-dir "ROOT_DIR"` para actualizar `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md`, y actualiza las copias en las carpetas `doc/`, `mp3/` y `ppt/` (copiar, no mover).
```

---

### Caso 5: Forzar la REGENERACIÓN COMPLETA de los entregables (`.md`, `.docx`, `.pptx`, `.pdf` y `.mp3`) de empresas específicas AUNQUE YA EXISTAN (`FORCE OVERWRITE`)

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo con SOBRESCRITURA FORZADA (`FORCE OVERWRITE`, desactivando la regla `SKIP`) sobre:
ROOT_DIR = "C:\PROJECT\Informes\Reports"
TARGET_COMPANIES = ["700.HK", "9988.HK"]

Instrucciones de ejecución:
1. NO apliques `SKIP` aunque los informes ya existan o pasen el gatekeeper. Fuerza la actualización completa de todas las empresas en `TARGET_COMPANIES`.
2. Si hay nuevos PDFs o quieres refrescar precios en vivo, ejecuta `prepare_company_ocr_and_market.py --root-dir "ROOT_DIR" --tickers 700.HK 9988.HK --force` y realiza búsqueda activa en Internet (`search_web`) con los últimos datos y noticias.
3. Regenera y sobrescribe en cada carpeta de `TARGET_COMPANIES`:
   - Los 4 borradores (`borrador_parte1..4.md` redactados directamente, prohibido usar plantillas de Python) y el informe maestro `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` (>= 185,000 bytes, >= 22,500 palabras).
   - Los 6 gráficos a 300 DPI (`charts/*.png`) y el documento Word `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx`.
   - La presentación de 40 diapositivas `[FILE_PREFIX]_PRESENTACION_COMITE_40_SLIDES.pptx` y `.pdf`.
   - El guion `[FILE_PREFIX]_PODCAST_GUION.md` (>= 5,000 palabras) y el audio `[FILE_PREFIX]_PODCAST_COMITE.wav` y `.mp3` (>= 30 min) ejecutando `build_podcast_kokoro.py --target-dir "<COMPANY_DIR>" --force`.
4. Verifica `EXIT 0` en `gauntlet_gatekeeper.py --target all` para cada empresa regenerada, ejecuta `build_global_portfolio_summary.py --root-dir "ROOT_DIR"` para actualizar `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md`, y sobrescribe las copias en `doc/`, `mp3/` y `ppt/` (copiar, no mover).
```

---

### Caso 6: Forzar la REGENERACIÓN de los entregables (`.md`, `.docx`, `.pptx`, `.pdf` y `.mp3`) de empresas específicas AUNQUE YA EXISTAN, aplicando una lista de CAMBIOS ESPECÍFICOS

```text
Activa y sigue estrictamente el skill `deep-research-gauntlet-loop` en modo 100% autónomo con SOBRESCRITURA FORZADA (`FORCE OVERWRITE`, sin `SKIP`) sobre:
ROOT_DIR = "C:\PROJECT\Informes\Reports"
TARGET_COMPANIES = ["700.HK", "9988.HK"]

Regenera todos los entregables (`.md`, `.docx`, `.pptx`, `.pdf` y `.mp3`) de `TARGET_COMPANIES` aplicando obligatoriamente los siguientes cambios en cascada en todos los formatos:
- Cambio 1: [Describe aquí tu Cambio 1, ej.: Actualizar el WACC al 9.5% y recalcular el DCF, la matriz de sensibilidad y el Precio Objetivo Base en el Módulo 10 y Módulo 15].
- Cambio 2: [Describe aquí tu Cambio 2, ej.: Añadir en el Módulo 02 (sección 2.2) y en la Slide 8 del PPTX la nueva línea de productos lanzada en 2026].
- Cambio N: [Describe aquí tu Cambio N, ej.: Incorporar en el debate del podcast (ELENA vs. MARCOS) una discusión detallada de 5 minutos sobre estos nuevos cambios].

Instrucciones de ejecución en cascada:
1. Modifica/reescribe directamente `borrador_parte1..4.md` en cada empresa de `TARGET_COMPANIES` incorporando `Cambio 1`, `Cambio 2`, ..., `Cambio N` con total coherencia numérica entre módulos, y consolida `[FILE_PREFIX]_INFORME_COMITE_FINAL.md` (>= 185,000 bytes, >= 22,500 palabras). Valida con `gauntlet_gatekeeper.py --target md`.
2. Regenera los 6 gráficos PNG a 300 DPI en `charts/` reflejando los nuevos números y recompila desde el nuevo `.md` el documento Word `[FILE_PREFIX]_INFORME_INSTITUCIONAL_FINAL.docx` y la presentación de 40 diapositivas `[FILE_PREFIX]_PRESENTACION_COMITE_40_SLIDES.pptx` y `.pdf`. Valida con `--target docx` y `--target pptx`.
3. Actualiza directamente el guion `[FILE_PREFIX]_PODCAST_GUION.md` (>= 5,000 palabras) para que `DIRECTOR`, `ELENA` y `MARCOS` debatan explícitamente los cambios aplicados, y re-sintetiza desde cero `[FILE_PREFIX]_PODCAST_COMITE.wav` y `.mp3` (>= 30 min) usando `build_podcast_kokoro.py --target-dir "<COMPANY_DIR>" --force`.
4. Actualiza `extracted_ocr_cache/forensic_metrics.json` y `company_meta.json` con los nuevos KPIs/precios objetivo, verifica `EXIT 0` en `gauntlet_gatekeeper.py --target all`, ejecuta `build_global_portfolio_summary.py --root-dir "ROOT_DIR"` para actualizar `RESUMEN_CARTERA_GLOBAL.xlsx` y `.md`, y copia (sin mover) los nuevos `.docx`, `.mp3` y `.pptx` en las carpetas `doc/`, `mp3/` y `ppt/`.
```
