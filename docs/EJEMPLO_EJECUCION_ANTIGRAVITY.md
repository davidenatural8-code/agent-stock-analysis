# Ejemplo de ejecución en Antigravity

## 0. Preparar los datos (fuera del workspace)

```
C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\TEST\TEST_5\
├── EXPN.L\      ← PDFs: informes anuales, intermedios y trimestrales
├── ZDC.V\
└── QES.SI\
```

Cada subcarpeta se llama como el ticker de yFinance y contiene solo los PDFs de esa empresa.

## 1. Abrir el workspace

Antigravity → **File → Open Folder** → `C:\Users\david\Desktop\Momentum\agent-stock-analysis`

## 2. Escribir en el chat (elige una opción)

**A. Lote completo (lo más habitual):**
```
lanza gauntlet en C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\TEST\TEST_5
```

**B. Solo algunas empresas y sin podcast (prueba rápida o barata):**
```
lanza gauntlet en C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\TEST\TEST_5 solo para EXPN.L y ZDC.V, sin podcast
```

**C. Lote grande, desatendido toda la noche:**
```
/goal lanza gauntlet en C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\TEST\TEST_100 y no pares hasta que todas las empresas den EXIT 0 en el gatekeeper
```

**D. Reanudar un lote cortado:** repite exactamente el mismo mensaje. Las empresas que ya están en EXIT 0 se saltan y las demás continúan desde lo que haya en disco.

**E. Consultar el estado sin procesar nada:**
```
pasa el gatekeeper --target all a todas las empresas de C:\...\TEST_5 y dime cuáles faltan
```

**F. Cambiar el número de subagentes en paralelo (por defecto 4):**
```
lanza gauntlet en C:\...\TEST_5 con 8 subagentes en paralelo
```
```
/goal lanza gauntlet en C:\...\TEST_100 con 12 subagentes en paralelo y no pares hasta que todas den EXIT 0
```
El agente mantiene siempre N subagentes activos: cuando uno termina, lanza la siguiente empresa de la cola. El OCR también sube sus procesos hasta N, con el número de núcleos de la CPU como tope.

| Paralelo | Cuándo usarlo | A tener en cuenta |
|---|---|---|
| 4 (defecto) | Lotes de hasta 10 empresas | El más estable con los límites de cuota |
| 8 | 10 a 40 empresas | Más avisos de cuota (429); el agente reanuda solo |
| 12 | Lotes nocturnos de 40 a 100 empresas con `/goal` | Mucha CPU/RAM en OCR y Kokoro; reanudaciones frecuentes |

Por encima de 12 no se recomienda: la cuota de la suscripción se reparte entre todos los subagentes y el tiempo total no mejora.

## 3. Qué verás mientras corre

1. `[SKIP] / [TODO]` por empresa (triaje con el gatekeeper).
2. OCR en paralelo de todas las empresas pendientes, sin gastar tokens.
3. Un subagente por empresa en el panel lateral (por ejemplo "Analyst - ZDC.V"). Cada uno hace la búsqueda web, escribe los 4 borradores, valida el informe maestro (`md` EXIT 0) y genera gráficos, Word, PPTX de 60 slides y podcast.
4. Si un subagente se corta por cuota, el agente principal lo reanuda solo, sin duplicarlo.
5. Al final aparecen el Excel global y el informe de tokens.

## 4. Resultado esperado

```
TEST_5\
├── EXPN.L\  EXPERIAN_PLC_EXPN.L_INFORME_COMITE_FINAL.md
│            EXPERIAN_PLC_EXPN.L_INFORME_INSTITUCIONAL_FINAL.docx
│            EXPERIAN_PLC_EXPN.L_PRESENTACION_COMITE_60_SLIDES.pptx
│            EXPERIAN_PLC_EXPN.L_PODCAST_COMITE.mp3
│            charts\chart1..10.png
├── doc\  mp3\  ppt\           ← copias consolidadas
├── RESUMEN_CARTERA_GLOBAL.xlsx / .md
└── (informe de tokens exportado por token_gauntlet_profiler.py)
```

Mensaje final del agente (ejemplo):

| Empresa | Gatekeeper | Palabras md / docx | Slides | MP3 |
|---|---|---|---|---|
| EXPN.L | EXIT 0 | 30.120 / 27.876 | 60 | 42 min |
| ZDC.V | EXIT 0 | 29.810 / 27.420 | 60 | 41 min |

Le sigue el análisis de consumo de tokens por fase y por empresa, con las optimizaciones propuestas.

## 5. Peticiones habituales después

- `regenera solo el PPTX de ZDC.V` → solo vuelve a ejecutar `build_slides_deck_json.py` + `build_institutional_pptx.py`.
- `rehaz el módulo 10 de EXPN.L con el precio de hoy` → edita el borrador, reensambla el informe y vuelve a pasar el gatekeeper.
- `actualiza el Excel global` → `build_global_portfolio_summary.py --root-dir ...`.
