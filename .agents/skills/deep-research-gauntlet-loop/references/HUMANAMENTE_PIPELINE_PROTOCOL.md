# Protocolo Obligatorio `humanamente` en el Pipeline `deep-research-gauntlet-loop`

Este documento traduce e integra de forma vinculante el skill **`vicentealvarezasencio/humanamente`** (`SKILL.md` completo: *Alma y Personalidad*, Patrones `P01` a `P33`, §6 *Banco de tics del español-IA* y *Motor de 3 Pasadas con Rúbrica >= 42/60*) en los **tres entregables escritos** del pipeline:
1. **Informe Maestro y sus 4 Borradores (`borrador_parte1..4.md` y `*_INFORME_COMITE_FINAL.md`)** -> *Y por herencia directa, el Word `.docx`.*
2. **Presentación Ejecutiva de 40 Diapositivas (`slides_deck.json` / `generate_pptx.py` -> `*_PRESENTACION_COMITE_40_SLIDES.pptx`)**
3. **Guion de Podcast a 3 Voces (`*_PODCAST_GUION.md`)**

> **REGLA DE BLOQUEO DETERMINISTA:** `gauntlet_gatekeeper.py` invoca automáticamente [`scripts/humanamente_gate.py`](../scripts/humanamente_gate.py) en `--target md`, `--target docx`, `--target pptx`, `--target podcast` y `--target all`. Si cualquiera de los tres textos incumple las reglas de `humanamente` o carece de la certificación del Motor de 3 Pasadas (`gauntlet_logs/humanamente_audit.json` con puntuación `>= 42/60`), el gatekeeper devuelve **`FAIL (EXIT 1)`**.

---

## 1. Calibración de Voz por Entregable (`humanamente` §Modos y §Alma)

| Entregable | Registro `humanamente` | Cómo debe sonar (Voz Humana Real) |
| :--- | :--- | :--- |
| **Informe `.md` (y `.docx`)** | **Técnico / Analista Senior Buyside** | Directo, sobrio, incisivo y sin adornos promocionales. Aplica la **regla 70/30** (70% castellano llano y verbos directos como *es, tiene, gana, pierde, cobra, paga*; 30% terminología contable/financiera exacta). **Burstiness real (`P32`):** alterna frases cortas y secas de 4 a 10 palabras (*«La caja manda.»*, *«Ahí está la trampa contable.»*, *«El margen aguantó.»*) con oraciones analíticas de 20 a 32 palabras. Prohibidos los párrafos de frases maratonianas de 55–80 palabras encadenadas con comas y gerundios. |
| **Pitch Deck `.pptx` (40 slides)** | **Corporativo Ejecutivo / Comité** | **Action Titles en *sentence case* español (`P17`):** solo lleva mayúscula la primera palabra y los nombres propios o siglas (*«Descuento del 30% en P/E frente a Agnico Eagle pese a mayor ROIC»*, **NUNCA** *«Descuento Injustificado del -30% Pese a Márgenes Superiores»*). Viñetas limpias en oración natural, sin abrir cada punto con `**Término:** definición` (`P16`). |
| **Guion Podcast `*_PODCAST_GUION.md`** | **Hablado con Alma y Personalidad** | Conversación real de sala de comité entre tres personas con criterio propio (`DIRECTOR`, `ELENA`, `MARCOS`). Frases orales breves (`media < 25 palabras`, abundancia de réplicas de 4–12 palabras), marcadores discursivos naturales (*«ahora bien»*, *«eso sí»*, *«fíjate en este dato»*, *«la verdad es que aquí dudo»*), matices honestos y **cero peloteo robótico (`P23`)**: prohibido decir *«¡Excelente observación, Elena!»* o *«Tienes toda la razón, Marcos»*. |

---

## 2. Reglas Estrictas `P01–P33` Auditadas por `humanamente_gate.py`

1. **`P17` — Prohibido el *Title Case* anglosajón en titulares (`.md` y `.pptx`):**
   - **Mal (IA inglesa):** `### 2.1 Anatomía Profunda del Modelo de Negocio y Mecánica Operativa`
   - **Bien (Castellano nativo):** `### 2.1 Anatomía profunda del modelo de negocio y mecánica operativa`
   - **Mal (Slide PPTX):** `Fortaleza Patrimonial Inexpugnable al 30 de Septiembre de 2026`
   - **Bien (Slide PPTX):** `Fortaleza patrimonial al 30 de septiembre de 2026 con caja neta récord` *(recuerda: los meses en español van siempre en minúscula).*
2. **`P14` — Prohibido sobreusar la raya inglesa con espacios (` — ` o ` -- `):**
   - No uses ` — ` como sustituto perezoso de comas, dos puntos o paréntesis. Usa `:`, `,`, `.` o paréntesis `(…)`. Si haces un inciso literario legítimo en español, la raya va pegada a las palabras interiores (`—así, sin espacio interior—`), nunca a lo anglosajón (` — `).
3. **`P19` y `P18` — Comillas latinas `« »` y cero emojis:**
   - Prohibidas las comillas curvas inglesas (`“ ”`). Usa siempre comillas angulares latinas `« »` (o rectas `"` solo dentro de código/tablas técnicas). Cero emojis en texto, titulares o diapositivas.
4. **`P03` y `P22` — Prohibidos los racimos de gerundios de consecuencia tras coma:**
   - **Mal (IA):** *«La empresa amortizó el préstamo sindicado, reduciendo los costes financieros e impulsando el flujo de caja libre, situando la caja neta en máximos.»*
   - **Bien (Humano):** *«La empresa amortizó el préstamo sindicado en febrero. Los intereses cayeron a la mitad y la caja neta cerró el trimestre en máximos.»*
5. **`P09` — Prohibido el paralelismo negativo mecánico:**
   - Elimina construcciones del tipo *«No solo X, sino también Y»* o *«No se trata solo de X, sino de Y»*. Di lo que es directamente.
6. **`P01`, `P04`, `P07`, `P08`, `P13`, `P24`, `P26`, `P27`, `P28` — Cero inflación, muletillas, cópula recargada ni cierres de manual:**
   - **Prohibido en racimo:** *cabe destacar, cabe señalar, es importante señalar, se puede observar que, pone de manifiesto, pone de relieve, juega un papel fundamental/crucial, marca un antes y un después, se erige como, constituye un testimonio, un sinfín de, una miríada de, un abanico de, en el panorama actual, sin lugar a dudas, en conclusión, en definitiva, en última instancia, en primer lugar… en segundo lugar…, profundizar, adentrarse, fomentar, potenciar, subrayar, recalcar, holístico, sinérgico, disruptivo, vanguardista, en aras de, de la mano de.*
   - En vez de *«se erige como el líder»* o *«cuenta con cuatro plantas»*, escribe *«es el líder»* y *«tiene cuatro plantas»* (`P08`).
7. **`P15` y `P16` — Contención en negritas y listas:**
   - No satures los párrafos con frases enteras en negrita (`< 16%` del texto narrativo).
   - No conviertas todas las viñetas del informe ni del PPTX en listas mecánicas `- **Concepto:** explicación` (`P16`). Reserva los campos estructurados únicamente para donde el gatekeeper técnico los exige (p. ej. fichas de catalizadores del Módulo 12).
8. **`P32` y `P33` — *Burstiness* obligatorio y cero conectores repetitivos:**
   - La media de longitud de frase en prosa narrativa debe mantenerse **por debajo de 34 palabras** (`< 28` en podcast), con **al menos un 7%–10% de frases cortas (`3 a 12 palabras`)** que rompan la cadencia metronómica.
   - No abras párrafo tras párrafo con *«Además,»*, *«Asimismo,»*, *«No obstante,»* o *«Por consiguiente,»* (`P33`). Empieza directamente con el sujeto o el dato.

---

## 3. Ejecución Obligatoria del Motor de 3 Pasadas en el Pipeline

En cada uno de los 3 puntos de control (`md`, `pptx`, `podcast`), ejecuta sin saltarte ningún paso:

### Punto de Control A — Borradores `borrador_parte1..4.md` e Informe `.md` (Fase 3)
1. **Pasada 1 (Redacción calibrada):** Escribe cada `borrador_parteX.md` aplicando desde el primer párrafo *sentence case* (`P17`), comillas `« »` (`P19`), frases variadas con *burstiness* (`P32`) y verbos activos sin gerundios de cola (`P03/P22`).
2. **Pasada 2 (Autointerrogación + Auditoría determinista por borrador):** Nada más guardar cada `borrador_parteX.md`, pregúntate *«¿Qué sigue sonando a IA aquí?»* y ejecuta:
   ```powershell
   python "<COMPANY_DIR>/humanamente_gate.py" --file "<COMPANY_DIR>/borrador_parte1.md" --mode md-draft
   ```
   *(Repite para `borrador_parte2.md`, `borrador_parte3.md` y `borrador_parte4.md`).*
3. **Pasada 3 (Reescritura final y Certificación 6D >= 42/60):** Corrige con `edit_file` todos los tics detectados en cada borrador, ensambla `[FILE_PREFIX]_INFORME_COMITE_FINAL.md`, puntúa honestamente las 6 dimensiones (`Claridad, Ritmo, Confianza, Autenticidad, Densidad, Alma`, umbral `>= 42/60`) y registra el certificado:
   ```powershell
   python "<COMPANY_DIR>/humanamente_gate.py" --target-dir "<COMPANY_DIR>" --record-audit md --scores "8,8,8,8,8,7" --tics "P03,P07,P14,P17,P32" --notes "Resumen concreto de los tics eliminados en los 4 borradores"
   ```

### Punto de Control B — Contenido de las 40 Diapositivas `.pptx` (Fase 5)
1. **Pasada 1:** Redacta los `Action Titles` en *sentence case* español (`P17`) y las viñetas como afirmaciones directas con cifras, sin `**Encabezado:**` (`P16`) ni ` — ` (`P14`).
2. **Pasada 2 y 3:** Compila con `build_institutional_pptx.py`, ejecuta `humanamente_gate.py --file "<PPTX>" --mode pptx`, pule cualquier diapositiva marcada y registra la certificación `pptx` (`--record-audit pptx --scores "..." --tics "..."`).

### Punto de Control C — Guion de Podcast `*_PODCAST_GUION.md` (Fase 6, ANTES del TTS)
1. **Pasada 1:** Escribe el diálogo entre `DIRECTOR`, `ELENA` y `MARCOS` con ritmo oral real (frases cortas mezcladas con explicaciones claras, dudas honestas, cero tono sicofántico `P23`, cero decimales en cifras > 1,000).
2. **Pasada 2 y 3 (ANTES de lanzar `build_podcast_kokoro.py`):** Audita el guion en 0.2 segundos con:
   ```powershell
   python "<COMPANY_DIR>/humanamente_gate.py" --file "<COMPANY_DIR>/<FILE_PREFIX>_PODCAST_GUION.md" --mode podcast
   ```
   Reescribe cualquier réplica larga o robótica hasta obtener `HUMANAMENTE PASS (EXIT 0)`, registra la certificación `podcast` (`--record-audit podcast`) y **solo entonces** sintetiza el audio `.mp3` con `build_podcast_kokoro.py`.
