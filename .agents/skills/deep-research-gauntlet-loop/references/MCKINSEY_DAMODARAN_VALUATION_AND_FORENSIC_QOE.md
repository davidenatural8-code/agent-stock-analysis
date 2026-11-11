# Marco Maestro Unificado de Evaluación Financiera, Calidad de Ingresos (QoE), Auditoría Forense del Balance y Valoración Intrínseca (McKinsey 7.ª Ed. + Aswath Damodaran 4.ª Ed.)

Este documento fusiona en un **único motor metodológico sin conflictos** los tres marcos de referencia institucionales:
1. **`evaluacion-empresa-mckinsey`**: Auditoría forense del balance, *Quality of Earnings* (QoE), reorganización contable analítica y puente de valoración.
2. **`valoracion-mckinsey`** (*Valuation: Measuring and Managing the Value of Companies*, 7.ª Ed. — Koller, Goedhart & Wessels): Reorganización en $\text{NOPLAT}$ y $\text{Capital Invertido}$, descomposición del árbol $\text{ROIC}$, $\text{Economic Profit (EVA)}$, fórmula *Key Value Driver* para el Valor Continuo ($\text{CV}$), jerarquía de múltiplos ($\text{EV/EBITA}$) y *Reverse DCF*.
3. **`damodaran-valuation`** (*Investment Valuation*, 4.ª Ed. — Aswath Damodaran): *Bottom-Up Beta*, Prima de Riesgo País ($\text{CRP}$ ponderada por exposición $\lambda$), Rating Sintético de Deuda, capitalización de $\text{I+D}$ y arrendamientos, vínculo fundamental $\text{Crecimiento} = \text{Tasa de Reinversión} \times \text{ROIC}$, Test de las **3P** (*Narrativa vs. Números: Posible, Plausible, Probable*), control de múltiplos por su **Variable Compañera** y valoración de situaciones especiales (financieras, cíclicas, opciones reales).

---

## 1. Reorganización Analítica de Estados Financieros (Estándar McKinsey + Ajustes Damodaran)

Los estados contables GAAP/IFRS están diseñados para acreedores y autoridades fiscales, no para medir la creación de valor económico. **En los Módulos 05 y 06 es obligatorio reorganizar el Balance y la Cuenta de Resultados** bajo estas reglas:

### 1.1 Reorganización del Balance: Fondo de Maniobra Operativo ($\text{OWC}$) y Capital Invertido ($\text{IC}$)
1. **Fondo de Maniobra Operativo ($\text{Operating Working Capital — OWC}$):**
   $$\text{OWC} = \text{Activos Corrientes Operativos} - \text{Pasivos Corrientes Operativos}$$
   * **Activos Corrientes Operativos:** Cuentas por cobrar comerciales $+$ Inventarios $+$ Gastos anticipados $+$ Caja operativa estrictamente necesaria (fijada en el **$1.5\% \text{ al } 2.0\%$ de los ingresos anuales**).
   * **Exclusión Crítica (Activos No Operativos):** Toda la caja, depósitos y valores negociables que superen el $2.0\%$ de las ventas se clasifican como **Caja Excedente No Operativa** (se suman al final en el puente de $\text{EV}$ a $\text{Equity}$, nunca dentro del $\text{OWC}$).
   * **Pasivos Corrientes Operativos:** Cuentas por pagar comerciales $+$ Gastos devengados $+$ Ingresos diferidos operativos $+$ Impuestos corrientes operativos. (*Se excluyen estrictamente la deuda financiera a corto plazo, porción corriente de deuda LP y dividendos por pagar*).
2. **Capital Invertido Operativo ($\text{Invested Capital — IC}$):**
   $$\text{Capital Invertido (sin Goodwill)} = \text{OWC} + \text{PP\&E Neto} + \text{Intangibles Operativos Netos} + \text{Activos por Derecho de Uso (Leases IFRS 16)} + \text{Activo de I+D Capitalizado}$$
   $$\text{Capital Invertido Total (con Goodwill)} = \text{Capital Invertido (sin Goodwill)} + \text{Fondo de Comercio (Goodwill Acumulado e Intangibles de M\&A)}$$
   * **Regla Dual de McKinsey:**
     * Calcula siempre el **$\text{ROIC sin Goodwill}$** (y con $\text{I+D}$ capitalizado en empresas tecnológicas/farma/industriales intensivas en $\text{I+D}$, amortizando linealmente en $3\text{--}5\text{ años}$) para medir la **competitividad microeconómica intrínseca** y el Moat operativo.
     * Calcula siempre el **$\text{ROIC con Goodwill}$** para auditar si la directiva ha creado o destruido valor al pagar primas en adquisiciones ($\text{M\&A}$).
3. **Identidad Fundamental de Control del Balance:**
   $$\text{Capital Invertido Total} + \text{Activos No Operativos} = \text{Financiación Total (Deuda Financiera + Pasivos Leases + Déficit Pensiones + Minoritarios + Patrimonio Neto)}$$

### 1.2 Reorganización de la Cuenta de Resultados: $\text{EBITA}$, Impuestos Operativos y $\text{NOPLAT}$
El **$\text{NOPLAT}$** (*Net Operating Profit Less Adjusted Taxes*) mide el beneficio operativo después de impuestos como si la empresa estuviera financiada al $100\%$ con capital propio:
1. **$\text{EBITA Operativo Normalizado}$:**
   $$\text{EBITA} = \text{Ingresos} - \text{COGS} - \text{SG\&A (incluyendo SBC como gasto real)} - \text{Depreciación Operativa} + \text{Interés Implícito de Leases (si no está en gasto financiero)} + (\text{Gasto I+D Actual} - \text{Amortización Activo I+D})$$
   * Excluye ingresos/gastos financieros, resultados de asociadas y partidas extraordinarias verdaderamente puntuales (pero **no excluyas** costes de reestructuración que se repiten cada año).
2. **Impuestos Operativos (Eliminación del Escudo Fiscal de la Deuda):**
   $$\text{Impuestos Operativos} = \text{Impuestos Contables Reportados} + (\text{Gasto Financiero Neto} \times t_{\text{marginal}}) - \text{Impuestos sobre Partidas No Operativas}$$
3. **$\text{NOPLAT}$ y Flujo de Caja Libre ($\text{FCF}$ / $\text{FCFF}$):**
   $$\text{NOPLAT} = \text{EBITA} - \text{Impuestos Operativos}$$
   $$\text{Inversión Neta ($\text{Net Investment}$)} = (\text{CapEx} - \text{Depreciación}) + \Delta \text{OWC} + \text{Inversión Neta en I+D/Leases}$$
   $$\text{Tasa de Reinversión ($\text{IR}$)} = \frac{\text{Inversión Neta}}{\text{NOPLAT}} \quad \Longrightarrow \quad \text{FCF} = \text{NOPLAT} - \text{Inversión Neta} = \text{NOPLAT} \times (1 - \text{IR})$$

---

## 2. Rúbrica Cuantitativa de Calidad de los Ingresos y Beneficios — QoE (`Módulo 02.5` y `Módulo 06`, Escala `1.0 a 10.0`)

Para calcular la **`Puntuación de Calidad de Ingresos (1 a 10): X.X / 10`** exigida en el **Módulo 02 (`2.5`)** y en el Excel global de cartera, audita obligatoriamente estos **5 bloques ponderados sobre 10.0 puntos** (Metodología QoE de McKinsey + Damodaran):

| Bloque de Auditoría QoE (Calidad de Ingresos y Beneficios) | Peso Máximo | Criterios Cuantitativos y Umbrales Forenses |
| :--- | :---: | :--- |
| **1. Crecimiento Orgánico Puro vs. M&A, Recurrencia y Visibilidad** | **`2.5 pts`** | Proporción de ingresos recurrentes/suscripción/mantenimiento o respaldados por *Backlog* firme; aislamiento del crecimiento orgánico (volumen $\times$ precio en perímetro constante) frente a adquisiciones («roll-ups»); baja concentración en el Top 5 de clientes ($< 30\%$). |
| **2. Integridad del Reconocimiento de Ingresos ($\text{DSO}$ y $\text{DSRI}$)** | **`2.0 pts`** | Convergencia entre crecimiento de ventas y cuentas por cobrar ($\text{DSRI} \approx 1.00$). Penalizar si los días de cobro ($\text{DSO}$) crecen $> 15\%$ más rápido que las ventas o si aumentan los *unbilled receivables* / activos del contrato (alerta de *channel stuffing* o relajación crediticia). |
| **3. Ratio de Conversión de Caja McKinsey ($\text{CFO}/\text{NI}$ y $\text{FCF}/\text{NOPLAT}$)** | **`2.5 pts`** | En un negocio sano, $\text{CFO} / \text{Beneficio Neto}$ debe situarse entre el **$80\%$ y el $120\%$** y $\text{FCF} / \text{NOPLAT} > 70\%$ a lo largo del ciclo. **Alarma Roja:** Beneficio contable subiendo con $\text{CFO}$ plano o cayendo durante $\ge 2$ años consecutivos. |
| **4. Análisis de Devengos Contables Netos de Sloan (*Sloan Accruals*)** | **`1.5 pts`** | $\text{Ratio de Sloan} = \frac{(\Delta \text{Activos Op.} - \Delta \text{Caja}) - (\Delta \text{Pasivos Op.} - \Delta \text{Deuda CP}) - \text{D\&A}}{\text{Activos Totales Medios}}$. Zona óptima: **$-10\%$ a $+5\%$**. Si supera **$+10\%$**, alerta roja de reversión inminente de márgenes. |
| **5. Limpieza del «Adjusted EBITDA», $\text{SBC}$ y Partidas «No Recurrentes»** | **`1.5 pts`** | El *Stock-Based Compensation* ($\text{SBC}$) se deduce íntegramente como coste laboral real ($\text{FCF ex-SBC}$). Penalizar si la empresa presenta gastos de «reestructuración», «integración» o «litigios» todos los años para inflar su EBITDA ajustado. |
| **Puntuación de Calidad de Ingresos (1 a 10)** | **`10.0 pts`** | **Resultado obligatorio en formato: `Puntuación de Calidad de Ingresos (1 a 10): X.X / 10`** |

---

## 3. Rúbrica Cuantitativa de Salud Forense del Balance (`Módulo 05.5`, Escala `1.0 a 10.0`)

Para calcular la **`Puntuación de Salud Forense del Balance (1 a 10): X.X / 10`** exigida en el **Módulo 05 (`5.5`)** y en el Excel global de cartera, audita obligatoriamente estos **5 bloques ponderados sobre 10.0 puntos**:

| Bloque de Auditoría Forense del Balance (McKinsey + Damodaran) | Peso Máximo | Criterios Cuantitativos y Umbrales Forenses |
| :--- | :---: | :--- |
| **1. Solvencia Real, Caja Excedente No Restringida y Cobertura** | **`2.0 pts`** | Separación entre caja operativa ($1.5\%\text{--}2.0\%$ de ventas), caja restringida/pignorada y **Caja Excedente Libre Real**; ratio $\text{Deuda Neta Total (incl. Leases y Pensiones)} / \text{EBITDA} < 2.0\text{x}$ (o Caja Neta positiva) y cobertura de intereses $\text{EBITA} / \text{Intereses} > 5.0\text{x}$. |
| **2. Calidad de Activos (*Asset Bloat*), Goodwill, $\text{DIO}$ y Depreciación** | **`2.0 pts`** | Ratio $\text{Goodwill} / \text{Fondos Propios} < 40\%$ (si supera $40\%\text{--}50\%$ con $\text{ROIC con Goodwill} \approx \text{WACC}$, alto riesgo de *impairment*); $\text{DIO}$ (días de inventario) controlado sin obsolescencia oculta; vida útil contable realista ($\text{CapEx Mantenimiento} \approx \text{Depreciación}$). |
| **3. Ausencia de *Window Dressing*, Confirming Encubierto y Deuda Oculta** | **`2.0 pts`** | Auditoría de las Notas a los EE.FF.: ausencia de retraso artificial de pagos a cierre de año, reclasificación de *Supply Chain Finance / Reverse Factoring* bancario como deuda financiera, cuantificación de compromisos irrevocables *Take-or-Pay*, garantías a asociadas/JVs y déficit neto de pensiones ($\text{PBO} - \text{Activos del Plan}$). |
| **4. Modelos Forenses Multivariantes (Beneish M-Score y Altman Z)** | **`2.0 pts`** | **Beneish M-Score (8 variables: DSRI, GMI, AQI, SGI, DEPI, SGAI, LVGI, TATA) $< -1.78$** descartando manipulación contable, y **Altman Z / Z''-Score** en Zona Segura ($> 2.99$ manufactura o $> 2.60$ servicios/emergentes). |
| **5. Supervivencia en el Stress Test Cuantificado ($-20\%$ Ingresos)** | **`2.0 pts`** | Ante un choque simultáneo de $-20\%$ en ingresos, $-300\text{ bps}$ en margen $\text{EBITA}$ y $+15\text{ días}$ en $\text{DSO}$, la compañía mantiene liquidez suficiente para cubrir todos los vencimientos de deuda a 24 meses sin violar *covenants* ni diluir al accionista. |
| **Puntuación de Salud Forense del Balance (1 a 10)** | **`10.0 pts`** | **Resultado obligatorio en formato: `Puntuación de Salud Forense del Balance (1 a 10): X.X / 10` + Dictamen (`TRAYECTORIA EN MEJORA / EN DETERIORO / LISTA DE VIGILANCIA`)** |

---

## 4. Árbol de Descomposición del $\text{ROIC}$ y Creación de Valor ($\text{EVA}$) — `Módulo 06.2`

1. **Descomposición Fundamental de McKinsey:**
   $$\text{ROIC} = \frac{\text{NOPLAT}}{\text{Capital Invertido}} = \underbrace{\left(\frac{\text{NOPLAT}}{\text{Ingresos}}\right)}_{\text{Margen NOPLAT (Pricing Power)}} \times \underbrace{\left(\frac{\text{Ingresos}}{\text{Capital Invertido}}\right)}_{\text{Rotación del Capital (Eficiencia)}}$$
   * **Tablas obligatorias:** Reporta siempre el **$\text{ROIC sin Goodwill}$** (eficiencia operativa pura) y el **$\text{ROIC con Goodwill}$** (retorno tras adquisiciones), junto con el **Beneficio Económico Anual ($\text{Economic Profit / EVA}$)**:
     $$\text{EVA} = \text{Capital Invertido} \times (\text{ROIC} - \text{WACC}) = \text{NOPLAT} - (\text{Capital Invertido} \times \text{WACC})$$
2. **Vínculo Fundamental de Crecimiento, Reinversión y Valor (McKinsey & Damodaran):**
   $$g_{\text{operativo}} = \text{Tasa de Reinversión (IR)} \times \text{RONIC}$$
   * **Regla de Conservación del Valor:** Crecer cuando $\text{RONIC} > \text{WACC}$ acelera exponencialmente el valor; crecer cuando $\text{RONIC} = \text{WACC}$ es neutro para el valor; crecer cuando $\text{RONIC} < \text{WACC}$ destruye valor para el accionista.

---

## 5. Motor de Valoración Intrínseca y Relativa (Síntesis McKinsey + Damodaran) — `Módulo 10` y `Módulo 11`

### 5.1 Coste de Capital ($\text{WACC}$) con *Bottom-Up Beta*, Prima de Riesgo País ($\lambda$) y Rating Sintético
1. **Consistencia Monetaria (Regla de Damodaran):** La tasa libre de riesgo ($R_f$), la inflación implícita y los flujos de caja ($\text{FCF}$) deben estar expresados en la **misma moneda**. Si el bono soberano local tiene riesgo de impago, resta el *Default Spread* soberano para obtener el $R_f$ libre de riesgo real.
2. **Beta Bottom-Up Desapalancada y Reapalancada (McKinsey + Damodaran):**
   * Prohibido usar la Beta de regresión simple de un único ticker si presenta ruido estadístico. Calcula la **Beta del Activo ($\beta_U$) Bottom-Up** a partir de la mediana de los comparables cotizados (ponderada por divisiones si es un conglomerado) y reapaláncala con Hamada a valores de mercado:
     $$\beta_L = \beta_U \times \left[ 1 + (1 - t_{\text{marginal}}) \left(\frac{D_{\text{mercado (incl. Leases)}}}{E_{\text{mercado}}}\right) \right]$$
3. **Coste del Equity ($K_e$) con Exposición Real a Riesgo País ($\lambda$):**
   $$K_e = R_f + \beta_L \times \text{ERP}_{\text{Mercado Maduro (4.5\%–5.5\%)}} + \lambda \times \text{Country Risk Premium (CRP)}$$
   Donde $\lambda$ mide la proporción real de ingresos y activos productivos expuestos al país emergente.
4. **Coste de la Deuda ($K_d$) mediante YTM o Rating Sintético de Damodaran:**
   * Si no existe deuda cotizada líquida, estima el **Rating Sintético** a partir del ratio de cobertura de intereses ($\text{EBITA} / \text{Gasto Financiero}$), asigna su *Default Spread* correspondiente y calcula $K_d \text{ post-tax} = (R_f + \text{Spread}) \times (1 - t_{\text{marginal}})$.

### 5.2 Modelo Enterprise DCF, Fórmula *Key Value Driver* para el Valor Continuo ($\text{CV}$) y Test de las 3P
1. **Vínculo de Proyecciones Futuras (`Módulo 11`) con Reinversión:** Toda proyección de crecimiento de ingresos a 5–10 años debe ir acompañada del capital incremental necesario medido por el ratio **$\text{Ventas} / \text{Capital Invertido}$ (*Sales-to-Capital Ratio*)** o $\text{IR} = g / \text{RONIC}$, y superar el **Test de las 3P de Damodaran** (*¿Es Posible, Plausible y Probable?*).
2. **Valor Continuo ($\text{Continuing Value — CV}$) mediante la Ecuación *Key Value Driver* de McKinsey:**
   $$\text{CV}_N = \frac{\text{NOPLAT}_{N+1} \times \left(1 - \frac{g_{\text{terminal}}}{\text{RONIC}_{\text{terminal}}}\right)}{\text{WACC} - g_{\text{terminal}}}$$
   * **Restricción macroeconómica inquebrantable:** $g_{\text{terminal}}$ **nunca** puede superar el crecimiento nominal del PIB a largo plazo ni la tasa libre de riesgo ($2.0\%\text{--}3.5\%$).
   * **Convergencia de $\text{RONIC}_{\text{terminal}}$:** En empresas con Moat $< 7.5/10$, fija $\text{RONIC}_{\text{terminal}} = \text{WACC}$ (o un *fade* gradual hacia $\text{WACC}$). Solo en empresas con **Wide Moat ($\ge 7.5/10$)** se permite mantener un spread positivo acotado ($\text{RONIC}_{\text{terminal}} > \text{WACC}$), deduciendo siempre la reinversión perpetua obligatoria $\text{IR}_{\text{terminal}} = g_{\text{terminal}} / \text{RONIC}_{\text{terminal}}$.

### 5.3 Puente Institucional de 10 Pasos de Enterprise Value ($\text{EV}$) a Valor Intrínseco por Acción
En el **Módulo 10 (`10.1`)** y en el **Módulo 16 (`16.1 Ajustes Forenses`)**, el paso de $\text{Enterprise Value}$ a $\text{Equity Value}$ debe detallar explícitamente estos **10 escalones**:
1. $(+)$ **Valor Actual de los $\text{FCF}$ Explícitos** $+$ **Valor Actual del Valor Continuo ($\text{CV}$)** $=$ **$\text{Enterprise Value Operativo}$**
2. $(+)$ **Caja y Equivalentes Excedentes No Restringidos** (descontando el $1.5\%\text{--}2.0\%$ de caja operativa y cualquier caja pignorada/restringida)
3. $(+)$ **Valor de Mercado/Intrínseco de Asociadas No Consolidadas, JVs y Activos Fiscales ($\text{NOLs}$)**
4. $(-)$ **Deuda Financiera Bruta Total (Corto + Largo Plazo a valor de mercado)**
5. $(-)$ **Pasivos por Arrendamiento Capitalizados (Leases IFRS 16 / ASC 842)**
6. $(-)$ **Déficit Neto de Planes de Pensiones y Jubilación post-impuestos** ($\text{Déficit} \times (1 - t_{\text{marginal}})$)
7. $(-)$ **Deuda Oculta Reclasificada** (*Reverse Factoring / Confirming* bancario excedente y compromisos *Take-or-Pay* onerosos detectados en el Módulo 05)
8. $(-)$ **Provisiones por Litigios, Reestructuraciones, Contingencias Fiscales y Pasivos Ambientales**
9. $(-)$ **Intereses Minoritarios (Participaciones No Dominantes valoradas a múltiplo de mercado, no a valor contable)** y Acciones Preferentes
10. $(-)$ **Valor Razonable del *Option Overhang* / $\text{RSUs}$ Directivas Pendientes de Dilución**
$$\Longrightarrow \quad \text{Valor Intrínseco por Acción} = \frac{\text{Equity Value Ajustado}}{\text{Acciones Ordinarias Totalmente Diluidas}}$$

### 5.4 Valoración por Múltiplos: Jerarquía de McKinsey + Control por Variable Compañera de Damodaran (`Módulo 10.3`)
Queda prohibido aplicar medias simples de múltiplos sectoriales sin controlar por sus determinantes fundamentales:
1. **Test de Consistencia (Damodaran):** Numerador y denominador deben tener la misma naturaleza ($\text{EV}$ con métricas pre-deuda como $\text{EBITA/EBITDA/Ventas}$; $\text{Precio}$ con métricas post-deuda como $\text{BPA}$ o $\text{Valor Contable}$).
2. **Jerarquía de Múltiplos (McKinsey):** Prioriza siempre **$\text{EV/EBITA Forward Normalizado}$** sobre $\text{EV/EBITDA}$ (que ignora diferencias en intensidad de $\text{CapEx}$ y vida útil de activos) y sobre $\text{P/E}$ (distorsionado por apalancamiento y partidas no operativas).
3. **Control por Variable Compañera (*Companion Variable* de Damodaran):**
   * **$\text{EV/EBITA}$ y $\text{EV/EBITDA}$** $\longrightarrow$ Controlar por **$\text{ROIC}$ y crecimiento $g$** (evaluar dónde se sitúa la empresa en la regresión $\text{EV/EBITA}$ vs. $\text{ROIC}$ de sus comparables).
   * **$\text{P/E}$** $\longrightarrow$ Controlar por **crecimiento esperado de BPA ($g$), $\text{ROE}$ (payout $1 - g/\text{ROE}$) y riesgo ($K_e$)**.
   * **$\text{P/BV}$** $\longrightarrow$ Controlar por la **Matriz de Desajuste $\text{P/BV}$ vs. $(\text{ROE} - K_e)$** (bajo $\text{P/BV}$ con alto $\text{ROE} > K_e$ señala infravaloración).
   * **$\text{EV/Ventas}$** $\longrightarrow$ Controlar por **Margen $\text{NOPLAT}$ / Margen Operativo After-Tax**.

### 5.5 Reglas para Situaciones Especiales (Damodaran Cap. 21–30 y McKinsey Cap. 35–39)
* **Bancos, Aseguradoras y Servicios Financieros:** Prohibido usar $\text{EV/EBITDA}$ o $\text{Enterprise DCF}$. Valora directamente el **Equity** mediante **Modelo de Retorno Excedentario (*Excess Return Model*: $\text{Capital Contable} + \text{PV de } (\text{ROE} - K_e) \times \text{Capital}$)**, **$\text{FCFE}$ ajustado por capital regulatorio ($\text{CET1 / Tier 1}$)** y **Matriz $\text{P/BV}$ vs. $\text{ROE}$**.
* **Compañías Cíclicas y de Materias Primas:** Prohibido extrapolar márgenes de pico o valle de ciclo. Normaliza el $\text{NOPLAT}$ aplicando el **margen operativo o $\text{ROIC}$ medio de mitad de ciclo (*Mid-Cycle*)** sobre los ingresos actuales.
* **Opciones Reales y Activos Contingentes:** En empresas con reservas mineras/energéticas no desarrolladas, *pipelines* biotecnológicos en fases clínicas o plataformas digitales con opcionalidad de expansión, cuantifica la **Opción Real (Expandir, Retrasar o Abandonar)** de forma separada en el SOTP (`Módulo 10.2`), sin duplicar flujos ya incluidos en el DCF base.
