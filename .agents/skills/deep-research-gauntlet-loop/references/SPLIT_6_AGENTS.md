# Reparto en 7 subagentes (V3.8.1) — cuando SA-4 o SA-5 se desbordan

> **Cuándo se aplica.** Si en la ejecución anterior algún subagente superó **1,8k tokens de output por KB entregado** o hizo **más de 45 pasos**, esa parte se trocea. Medición que motiva la regla (CAML.L, 2026-11-10):
>
> | Agente | Pasos | Output | Output/KB |
> | :--- | ---: | ---: | ---: |
> | SA-3 (M09–M11) | 30 | 61.360 | 1,02k |
> | SA-4 (M12–M15) | 99 | 114.188 | 2,28k |
> | SA-5 (M16–M18) | 79 | 95.334 | 2,12k |
>
> El patrón no es la reescritura (el centinela la bloquea) sino la **fragmentación**: 22 de los 99 pasos de SA-4 produjeron menos de 150 tokens de salida.

## 1. Reparto

| Agente | Módulos | Fichero | Banda |
| :--- | :--- | :--- | ---: |
| SA-1 | M01–M04 | `borrador_parte1.md` | 76–92 KB |
| SA-2 | M05–M08 | `borrador_parte2.md` | 66–80 KB |
| SA-3 | M09–M11 | `borrador_parte3.md` | 52–64 KB |
| SA-4a | M12 | `borrador_parte4a.md` | 22–28 KB |
| SA-4b | M13–M15 | `borrador_parte4b.md` | 20–26 KB |
| SA-5a | M16–M17 | `borrador_parte5a.md` | 24–30 KB |
| SA-5b | M18 | `borrador_parte5b.md` | 18–24 KB |

Solo se trocean las partes que se desbordaron; SA-1, SA-2 y SA-3 se dejan enteros mientras su ratio sea ≤ 1,8k.

## 2. Orden de ejecución

1. Oleada A (paralela, 4 agentes): SA-1, SA-2, SA-3 y SA-4a.
2. Oleada B (paralela, 3 agentes): SA-4b, SA-5a y SA-5b.
3. **Fusión determinista, 0 tokens**, antes de `f3-master`:
   ```powershell
   python "<ROOT_DIR>/_shared_engine/merge_split_parts.py" --target-dir "<COMPANY_DIR>"
   ```
4. `f3-master` → `f4-derivatives` → SA-6 → `f5-guion` → cola Kokoro.

`merge_split_parts.py` concatena en orden `a` → `b` → `c` y escribe el fichero canónico que espera el ensamblador.

## 3. Encabezados obligatorios por trozo

- SA-4a: `## Módulo 12 — Catalizadores Futuros y Eventos Kill-Switch` con `### 12.1` … `### 12.5`. Prosa sin `|`.
- SA-4b: `## Módulo 13` (13.1–13.2), `## Módulo 14` (14.1–14.2), `## Módulo 15` (15.1–15.3).
- SA-5a: `## Módulo 16` (16.1–16.2, 16.2 en prosa sin `|`), `## Módulo 17` (17.1–17.5, con `VEREDICTO GLOBAL`).
- SA-5b: `## Módulo 18` (18.1–18.5), cerrando con exactamente 5 puntos numerados.

## 4. Presupuesto por agente

- **Máximo de llamadas de escritura** = techo de la banda dividido entre 18 KB, redondeado al alza (una parte de 26 KB: 2 escrituras; una de 45 KB: 3).
- **Prohibido** releer el borrador propio, ejecutar comandos de verificación o hacer micro-ediciones. Cada llamada reenvía el contexto completo.
- **Corte del orquestador**: si un agente supera el doble de escrituras previstas más seis pasos, se le pide cerrar el trozo en curso y el resto se lanza como agente nuevo.

## 5. Esqueleto de prompt (idéntico para los siete)

```
Eres <SA-X> del pipeline Deep-Research Gauntlet-Loop (V3.8.1).
EMPRESA: <nombre> (<ticker>). DIRECTORIO: <COMPANY_DIR>
PASO 1: lee completo `facts_sa<N>.md` (o `m01_m15_digest.md` para SA-5a/SA-5b). ÚNICA fuente.
PASO 2: escribe `<fichero>` con la estructura EXACTA de la sección 0 del pack: <lista de encabezados>.
EXTENSIÓN: <banda>. Mínimos por módulo: <mínimos>.
ESCRITURA: `write` con `<!--CONT-->`; después `edit` con old_string `<!--CONT-->` y new_string
`<fragmento>\n<!--CONT-->`, aportando >= 12.000 bytes por llamada; última llamada vacía.
PROHIBIDO volver a usar `write`, releer el borrador o verificarlo con comandos.
Máximo de llamadas de escritura: <N>.
Responde EXACTAMENTE: PASS | <ticker> | <fichero> | <bytes> bytes
```

## 6. Verificación tras la oleada

- `merge_split_parts.py` informa del tamaño de cada parte fusionada; el maestro debe seguir quedando en 273–336 KB.
- El check de anclas de `f3-master` es el que confirma que la fusión no rompió ninguna subsección.
- Guardar la medición de tokens de la ejecución (`token_gauntlet_profiler.py --report`) para comparar contra la referencia de 606.399 tokens de output.
