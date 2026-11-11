# Especificación Completa de los 18 Módulos Optimizados en 5 Borradores (`borrador_parte1..5.md`), Catálogo Exhaustivo (`2.1` y `2.2`), Veredicto en 5 Bloques (`Módulo 17`) y Síntesis Integral (`Módulo 18`)

Esta guía detalla la estructura obligatoria de los **5 borradores (`borrador_parte1.md` a `borrador_parte5.md`)**, los conteos mínimos de palabras por módulo (`MODULE_MIN_WORDS`) y las anclas regex verificadas por `gauntlet_gatekeeper.py`.

---

## 1. Pesos Mínimos y Módulos por Borrador (Arquitectura de 5 Partes: 4 Paralelas + 1 de Conclusiones)

> **Regla de Oro de la Arquitectura en 5 Partes:**
> - Los **4 primeros borradores (`borrador_parte1..4.md`)** se ejecutan **en paralelo** (4 subagentes concurrentes `SA-1` a `SA-4`) y cubren desde el **Módulo 01 hasta el Módulo 15**. **Queda prohibido incluir `## RESUMEN PARTE X` al final de los borradores 1 a 4.**
> - Una vez terminados los 4 primeros borradores, se destila automáticamente `m01_m15_digest.md` (`--run-phase f2-digest`) y se lanza el **5º subagente (`SA-5`)** para redactar **`borrador_parte5.md`** (**Módulos 16, 17 y 18**), integrando todas las síntesis ejecutivas de las Partes 1 a 4 dentro del **Módulo 18 (`>= 2,400 palabras`)**.

| Archivo Borrador | Ejecución | Peso Mínimo | Mín. Palabras Módulos | Contenido Obligatorio |
| :--- | :---: | :---: | :---: | :--- |
| **`borrador_parte1.md`** | `SA-1` (Paralelo) | **`>= 72,000 bytes`** | `>= 8,250 pal.` | `# PERFIL EXTRAÍDO` + **Módulos 01 (`>= 1,500`), 02 (`>= 3,400`), 03 (`>= 2,000`) y 04 (`>= 1,350`)** *(sin Resumen Parte 1 al final)* |
| **`borrador_parte2.md`** | `SA-2` (Paralelo) | **`>= 62,000 bytes`** | `>= 7,950 pal.` | **Módulos 05 (`>= 2,800`), 06 (`>= 2,100`), 07 (`>= 1,500`) y 08 (`>= 1,550`)** *(sin Resumen Parte 2 al final)* |
| **`borrador_parte3.md`** | `SA-3` (Paralelo) | **`>= 48,000 bytes`** | `>= 5,650 pal.` | **Módulos 09 (`>= 1,200`), 10 (`>= 2,600`, Secciones A–D) y 11 (`>= 1,850`, Proyecciones 5Y y Riesgos sin `\|`)** *(sin Resumen Parte 3 al final)* |
| **`borrador_parte4.md`** | `SA-4` (Paralelo) | **`>= 38,000 bytes`** | `>= 5,250 pal.` | **Módulos 12 (`>= 1,600`, Catalizadores en prosa sin `\|`), 13 (`>= 1,150`), 14 (`>= 1,050`) y 15 (`>= 1,450`, Noticias 2025–2026 y Monitorización)** *(sin Resumen Parte 4 al final)* |
| **`borrador_parte5.md`** | `SA-5` (Secuencial tras M01–M15) | **`>= 36,000 bytes`** | `>= 5,900 pal.` | **Módulos 16 (`>= 1,650`, Forense + Debate Bull vs. Bear sin `\|`), 17 (`>= 1,850`, Veredicto Ejecutable en 5 Bloques) y 18 (`>= 2,400`, Síntesis Integral de Partes 1 a 4 [`18.1` a `18.4`, 8–10 viñetas cada una] + `18.5` Tear Sheet con 5 puntos numerados)** |
| **`[FILE_PREFIX]_INFORME_COMITE_FINAL.md`** | Ensamblador (`f3-master`) | **`>= 256,000 bytes`** | **`>= 29,250 pal.`** | Concatenación exacta y normalizada de `borrador_parte1..5.md` *(suma mínima por módulos: 33,000 palabras)* |

---

## 2. Mínimo de Palabras por Módulo (`MODULE_MIN_WORDS`) y Ubicación de los 10 Gráficos

`gauntlet_gatekeeper.py` audita individualmente cada uno de los 18 módulos:

- **MÓDULO 01 (`>= 1,500 palabras` | `Gráfico 1`):** Contexto, Historia y Últimos Resultados Auditados (`1.1 Posicionamiento`, `1.2 Cronología e Hitos`, `1.3 Desempeño Histórico en Ciclos y Litigios`, `1.4 Perspectiva Institucional Preliminar`). **Nota:** El Gráfico 1 muestra únicamente la evolución histórica auditada (5 años + último intermedio), sin proyecciones futuras.
- **MÓDULO 02 (`>= 3,400 palabras` | `Gráfico 2`):** Modelo de Negocio (`2.1`), Catálogo Exhaustivo de Productos y Servicios (`2.2` con tabla maestra de mínimo 12 filas de SKUs), Desglose por Segmento y Geografía (`2.3`), Estructura de Ingresos y Backlog (`2.4`), **Puntuación de Calidad de Ingresos (1 a 10): X.X / 10** (`2.5`) y Evaluación del Moat con **Calificación del Moat Global (1 a 10): X.X / 10** y *Pricing Power* (`2.6`).
- **MÓDULO 03 (`>= 2,000 palabras` | `Gráfico 3`):** Inteligencia Sectorial (`3.1 Determinación de TAM, SAM, SOM y CAGR`), `3.2 Vientos de Cola, Regulación y Sensibilidad Macro/Materias Primas/Divisas`, `3.3 Análisis de las 5 Fuerzas de Porter` y `3.4 Mapa Competitivo y Cuota de Mercado frente a Peers Cotizados`.
- **MÓDULO 04 (`>= 1,350 palabras`):** Cultura Corporativa (`4.1 Valores Declarados vs. Reputación Laboral`), `4.2 Cultura de Innovación, Conversión de I+D y Propiedad Intelectual` y `4.3 Perfil ESG Operativo (Ambiental y Social) y Dictamen Cultural`.
- **MÓDULO 05 (`>= 2,800 palabras` | `Gráfico 4`):** Auditoría Forense del Balance y Notas Críticas (`5.1 Serie Multianual de Balance y Solvencia`, `5.2 Calendario de Vencimientos de Deuda y Auditoría Forense de Notas Críticas a los Estados Financieros [Reconocimiento de ingresos, antigüedad de cobros, inventarios, activos/pasivos contractuales, contingencias]`, `5.3 Señales de Alerta Rojas, Ratio de Sloan, Beneish M-Score [8 variables] y Altman Z`, `5.4 Stress Test Cuantificado [-20% Caída de Ingresos]` y `5.5 Puntuación de Salud Forense del Balance (1 a 10): X.X / 10`).
- **MÓDULO 06 (`>= 2,100 palabras` | `Gráfico 5`):** Cuenta de Resultados Histórica, Unit Economics y Flujo de Caja Real (`6.1 Cuenta de Resultados, Ajustes Non-GAAP y Flujos de Caja Históricos [Owner Earnings y FCF ex-SBC]`, `6.2 Evolución de Márgenes, Unit Economics, Apalancamiento Operativo [Costes Fijos vs. Variables], DuPont de 5 Pasos y ROIC vs. WACC`).
- **MÓDULO 07 (`>= 1,500 palabras` | `Gráfico 6`):** KPIs Operativos Sectoriales y Capital Circulante (`7.1 Tabla Histórica de KPIs Operativos y Ciclo de Conversión de Caja [DSO, DIO, DPO, CCC]`, `7.2 Benchmarking Operativo de Eficiencia frente a Competidores Directos` con dictamen `POR ENCIMA / DENTRO / POR DEBAJO`).
- **MÓDULO 08 (`>= 1,550 palabras`):** Directiva, Gobernanza y Asignación de Capital (`8.1 Perfiles Directivos, Gobernanza, Remuneración y Operaciones con Partes Vinculadas`, `8.2 Guidance vs. Ejecución Histórica y Auditoría de M&A`, `8.3 Recompras, Emisiones, Dividendos y ROIC Incremental`).
- **MÓDULO 09 (`>= 1,200 palabras`):** Estructura Accionarial y Smart Money (`9.1 Estructura Accionarial, Free Float y Posicionamiento Institucional [Stock Connect / Fondos]`, `9.2 Transacciones de Insiders y Short Interest`).
- **MÓDULO 10 (`>= 2,600 palabras` | `Gráfico 7`):** Valoración Multi-Método (`10.1 Sección A: WACC, DCF Explícito, Reverse DCF y Matriz 5x5`, `10.2 Sección B: Valoración por Suma de las Partes [SOTP]`, `10.3 Sección C: Múltiplos Comparables vs. Peers e Histórico`, `10.4 Sección D: Escenarios Probabilísticos [Bear / Base / Bull]`).
- **MÓDULO 11 (`>= 1,850 palabras` | `Gráfico 8`):** Potencial de Crecimiento Futuro, Proyecciones a 5 Años y Matriz de Riesgos (`Sección A: Potencial de Crecimiento a Largo Plazo y Modelo de Proyecciones Operativas Futuras a 5 Años` — explicando de dónde salen las proyecciones de ingresos, márgenes y FCF al contrastar el Consenso Sell-Side/Guidance con los Escenarios Bear/Base/Bull del Comité basados en TAM/CAGR y Backlog — y `Sección B: Matriz de Riesgos` en **prosa y viñetas sin `|`**).
- **MÓDULO 12 (`>= 1,600 palabras`):** Catalizadores Futuros (`12.1 Corto Plazo`, `12.2 Medio Plazo`, `12.3 Largo Plazo`, `12.4 Catalizadores Ocultos` y `12.5 Anti-catalizadores / Kill-Switch Events` — **100% prosa y viñetas, CERO caracteres `|`**).
- **MÓDULO 13 (`>= 1,150 palabras` | `Gráfico 9`):** Análisis Técnico Avanzado (`13.1 Estructura de Tendencia, Medias Móviles y Osciladores`, `13.2 Mapa de Soportes y Resistencias y Ejecución en Tramos`).
- **MÓDULO 14 (`>= 1,050 palabras`):** Análisis de Sentimiento de Mercado (`14.1 Consenso Sell-Side vs. Valoración Propia Buyside`, `14.2 Cobertura de Prensa [90 Días] y Sentimiento en Foros`).
- **MÓDULO 15 (`>= 1,450 palabras`):** Noticias Recientes (2025–2026), Hechos Relevantes y Monitorización Trimestral (`15.1 Marco Temporal, Contexto del Precio Reciente y Cronología de Eventos 2025–2026`, `15.2 Matriz de Impacto [Catalizadores Positivos vs. Negativos]`, `15.3 Checklist de Vigencia Trimestral y Trigger Points [Umbrales Verde / Amarillo / Rojo]`).
- **MÓDULO 16 (`>= 1,650 palabras`):** Ajustes Forenses y El Debate del Comité de Inversiones (`16.1 Sección A: Síntesis de Banderas Rojas Forenses y su Penalización Matemática en la Valoración`, `16.2 Sección B: El Debate del Comité de Inversiones [Bull vs. Bear vs. Arbitraje del Presidente]` — **100% prosa y viñetas, CERO caracteres `|`**).
- **MÓDULO 17 (`>= 1,850 palabras` | `Gráfico 10`):** Veredicto Final Ejecutable, Scorecard Institucional y Plan Táctico de Cartera:
  - `17.1 Scorecard Institucional Ponderado (Calificación de los 6 Pilares de 1 a 10)`: Calidad de Ingresos (20%), Moat (20%), Salud Forense y Balance (20%), Directiva y Asignación de Capital (15%), Asimetría de Valoración (15%) y Catalizadores/Timing (10%).
  - `17.2 Anatomía del Retorno Total Esperado (TSR) y TIR Anualizada (IRR)`: Desglose matemático de crecimiento orgánico + expansión de múltiplo + dividendo + recompras netas.
  - `17.3 Factores para Comprar Hoy vs. Factores para Reservar Liquidez`.
  - `17.4 Plan de Ejecución en 3 Tramos, Criterio de Kelly y Gestión del Riesgo (Stop-Loss)`.
  - `17.5 Tabla de Veredicto Ejecutable del Comité` (incluyendo la fila `VEREDICTO GLOBAL`).
- **MÓDULO 18 (`>= 2,400 palabras`):** RESUMEN EJECUTIVO FINAL — Síntesis Integral por Bloques (Partes 1 a 4) y Tear Sheet del Comité:
  - `18.1 Síntesis Ejecutiva de la Parte 1 (Módulos 01 a 04: Negocio, Catálogo, QoE, Moat, Sector y Cultura)`: **8 a 10 viñetas densas** con datos auditados extraídos del Borrador 1.
  - `18.2 Síntesis Ejecutiva de la Parte 2 (Módulos 05 a 08: Balance Forense, Resultados/NOPLAT, KPIs y Directiva)`: **8 a 10 viñetas densas** con datos auditados extraídos del Borrador 2.
  - `18.3 Síntesis Ejecutiva de la Parte 3 (Módulos 09 a 11: Capital, Valoración Multi-Método y Proyecciones 5Y)`: **8 a 10 viñetas densas** con datos auditados extraídos del Borrador 3.
  - `18.4 Síntesis Ejecutiva de la Parte 4 (Módulos 12 a 15: Catalizadores, Análisis Técnico, Sentimiento y Noticias)`: **8 a 10 viñetas densas** con datos auditados extraídos del Borrador 4.
  - `18.5 Tear Sheet Ejecutivo Final del Comité`: **exactamente 5 puntos numerados (`1.` a `5.`)** con la tesis institucional definitiva de inversión.

---

## 3. Requisitos Especiales del Módulo 02 (`>= 2,400 palabras`)

El **Módulo 02 (`## MÓDULO 02: Modelo de Negocio y Catálogo Exhaustivo de Productos y Servicios`)** debe contener obligatoriamente:
1. **`### 2.1 Anatomía Profunda del Modelo de Negocio`**:
   - Arquitectura operativa de principio a fin (I+D, aprovisionamiento, fabricación propia vs. OEM/ODM, logística, canales de distribución B2B/B2C/1P/3P, modelo de fijación de precios, unidad económica, ciclo de cobro/pago y retención).
2. **`### 2.2 Catálogo Exhaustivo de Productos y Servicios`**:
   - **Tabla Maestra en Markdown de mínimo 8 filas** detallando cada línea de producto, marca comercial, SKU/modelo representativo, especificaciones técnicas/comerciales, segmento cliente objetivo, rango de precios / modelo de monetización, peso en ingresos y margen bruto estimado.
   - **Radiografía técnica y comercial línea por línea** de todo el portafolio de productos y servicios de la compañía.

---

## 4. Mapeo Integral de los 18 Módulos a la Nueva Arquitectura en 7 Actos (40 Diapositivas)

Cada diapositiva del Pitch Deck (`*_PRESENTACION_COMITE_40_SLIDES.pptx`) emana directamente de un módulo específico del informe, manteniendo un hilo conductor narrativo ininterrumpido:

1. **ACTO I — Quién es la empresa y qué hace (Diapositivas 1 a 5 | Módulo 01):**
   - Slide 1: Portada ejecutiva y planteamiento de la tesis central.
   - Slide 2: Quién es la compañía, su escala actual y su evolución histórica (`1.1` y `1.2`).
   - Slide 3: Qué problema resuelve y qué lugar ocupa en la cadena de valor (`1.1`).
   - Slide 4: Transformación estratégica reciente: salida de negocios de bajo margen y foco en sus motores principales (`1.2` y `1.3`).
   - Slide 5: Fotografía histórica auditada de los últimos 5 años (100% resultados reales pasados, sin proyecciones) (**`chart1`** | `1.3` y `1.4`).

2. **ACTO II — Cómo lo hace: modelo de negocio, catálogo, sector y ventaja competitiva (Diapositivas 6 a 13 | Módulos 02, 03 y 04):**
   - Slide 6: Estructura de las divisiones de negocio y peso en ingresos (**`chart2`** | `2.3`).
   - Slide 7 (*Ancla obligatoria*): Anatomía del modelo de negocio y unidad económica (`2.1`).
   - Slide 8 (*Ancla obligatoria*): Catálogo exhaustivo de productos y servicios comerciales (`2.2 Parte I`).
   - Slide 9: Catálogo tecnológico: nube, inteligencia artificial, semiconductores y red logística (`2.2 Parte II`).
   - Slide 10: Calidad de los ingresos: recurrencia, retención, concentración y nota de Calidad de Ingresos (`2.4` y `2.5`).
   - Slide 11: El foso competitivo (Moat) y el poder de fijación de precios (Pricing Power) (`2.6`).
   - Slide 12: Tamaño del mercado (TAM/SAM/SOM), vientos de cola y las 5 Fuerzas de Porter (`3.1–3.3`).
   - Slide 13: Mapa competitivo frente a sus rivales cotizados (**`chart3`**) y cultura de innovación/I+D y ESG (`3.4` y `Módulo 04`).

3. **ACTO III — Los números y la calidad financiera: balance, resultados, caja y eficiencia (Diapositivas 14 a 21 | Módulos 05, 06 y 07):**
   - Slide 14: Radiografía del balance multianual: qué activos tiene y cómo se financia (`5.1`).
   - Slide 15: Liquidez real no restringida frente a deuda financiera y caja neta (**`chart4`** | `5.2`).
   - Slide 16: Auditoría forense de las notas contables, Sloan, Beneish, Altman Z'', Stress Test y nota de Salud Forense (`5.2–5.5`).
   - Slide 17: Cuenta de resultados histórica (5 años) y transparencia del puente contable GAAP vs. Non-GAAP (`6.1`).
   - Slide 18: Generación de flujo de caja operativo (OCF), inversión en CapEx y flujo de caja libre real (Owner Earnings / FCF ex-SBC) (`6.1`).
   - Slide 19: Evolución de márgenes, apalancamiento operativo, DuPont y creación de valor ROIC vs. WACC (**`chart5`** | `6.2`).
   - Slide 20: KPIs operativos físicos y cómo el ciclo de conversión de caja negativo financia el negocio gratis (**`chart6`** | `7.1`).
   - Slide 21: Benchmarking de eficiencia operativa frente a sus competidores directos (`7.2`).

4. **ACTO IV — Quién dirige la empresa y cómo asigna el capital (Diapositivas 22 a 24 | Módulos 08 y 09):**
   - Slide 22: Equipo directivo, gobernanza, incentivos y cumplimiento histórico del guidance (`8.1` y `8.2`).
   - Slide 23: Asignación histórica del capital (5 años): CapEx, recompras de acciones, dividendos y ROIC Incremental (`8.3`).
   - Slide 24: Estructura accionarial, movimientos de insiders, flujos institucionales y posiciones cortas (`Módulo 09`).

5. **ACTO V — El futuro del negocio y cuánto vale la acción (Diapositivas 25 a 30 | Módulos 11A y 10):**
   - Slide 25: Motores de crecimiento a largo plazo y de dónde salen las proyecciones del Comité frente al consenso (`Módulo 11 Sección A`).
   - Slide 26: Modelo de proyecciones operativas a 5 años (ingresos, EBITA y cosecha de FCF en escenarios Bear/Base/Bull) (**`chart8`** | `Módulo 11 Sección A`).
   - Slide 27: Valoración por descuento de flujos de caja (DCF), matriz de sensibilidad y qué descuenta el precio actual (Reverse DCF) (`10.1`).
   - Slide 28: Valoración por Suma de las Partes (SOTP): cuánto vale cada división y qué activos nos regala el precio actual (`10.2`).
   - Slide 29: Valoración por múltiplos comparables frente a su historia y frente a sus rivales globales (`10.3`).
   - Slide 30: Triangulación del precio objetivo y escenarios probabilísticos (Campo de Fútbol) (**`chart7`** | `10.4`).

6. **ACTO VI — Qué puede salir mal, qué moverá la acción y el momento de entrada (Diapositivas 31 a 36 | Módulos 11B, 12, 15, 14 y 13):**
   - Slide 31: Riesgos operativos, competitivos y tecnológicos cuantificados y sus mitigantes (`Módulo 11 Sección B - Parte I`).
   - Slide 32: Riesgos macroeconómicos, regulatorios y geopolíticos (`Módulo 11 Sección B - Parte II`).
   - Slide 33: Catalizadores positivos a corto, medio y largo plazo que destaparán el valor (`12.1–12.4`).
   - Slide 34: Eventos Kill-Switch (cuándo abortar la tesis) y cronología de noticias 2025–2026 que explican el descuento actual (`12.5`, `15.1` y `15.2`).
   - Slide 35: Semáforo de monitorización trimestral y sentimiento de mercado (Sell-Side vs. Buyside) (`15.3` y `Módulo 14`).
   - Slide 36: Análisis técnico de los últimos 12 meses, soportes, resistencias y liquidez de ejecución (**`chart9`** | `Módulo 13`).

7. **ACTO VII — El veredicto final: ¿es buena o mala idea de inversión y por qué? (Diapositivas 37 a 40 | Módulos 16, 17 y 18):**
   - Slide 37: Ajustes forenses aplicados y el gran debate del Comité: argumentos Bull frente a argumentos Bear (`16.1` y `16.2`).
   - Slide 38: Por qué es una buena (o mala) idea de inversión: Scorecard de los 6 pilares (**`chart10`**) y anatomía de la rentabilidad esperada (TSR / TIR) (`17.1–17.3`).
   - Slide 39 (*Ancla obligatoria*): Plan táctico ejecutable: peso en cartera, compra en 3 tramos, criterio de Kelly y Stop-Loss duro (`17.4` y `17.5`).
   - Slide 40 (*Ancla obligatoria*): Tear Sheet ejecutivo final con las 5 conclusiones numeradas que resumen toda la historia (`Módulo 18`).

Consulta [PPTX_40_SLIDES_7_ACTS_SPECIFICATION.md](./PPTX_40_SLIDES_7_ACTS_SPECIFICATION.md) para los requerimientos completos de diseño y estructura de cada diapositiva.
