# Guía de Orquestación Paralela V3.2 Ultra-Lean Hybrid y Recuperación Multi-LLM

Cuando `ROOT_DIR` contiene múltiples carpetas de empresas, el agente principal actúa como **Orquestador Ligero**, manteniendo su contexto `< 60k` tokens (nunca lee borradores ni informes) y coordinando subagentes especializados según [ORCHESTRATION_V2_PHASE_SPLIT.md](./ORCHESTRATION_V2_PHASE_SPLIT.md).

---

## 1. Registro Único del Subagente Ligero (`Palanca #4`)

Al inicio de la sesión, registra una sola vez el perfil `gauntlet_writer` con `define_subagent` (`EnableWriteTools=True`, `EnableSubagentTools=False`, `EnableMCPTools=False`, system prompt de ~350 tokens con reglas `humanamente` y Regla Cero Consola). Esto recorta ~10k tokens de esquemas de plugins/MCPs en cada uno de los `6 × N` redactores. Si `define_subagent` no estuviera disponible, usa `TypeName="self"` como fallback.

---

## 2. Enrutamiento Híbrido de Modelos (`CORE_MODEL` + `LIGHT_MODEL`) y Fallback Multi-LLM (`Palanca #5`)

En Antigravity, `invoke_subagent` admite los selectores `inherit | pro | flash | flash_lite`:
- **`"inherit"`** utiliza siempre el **mismo LLM activo seleccionado en la interfaz de Antigravity** (sea Gemini, Claude Sonnet/Opus, GPT u otro proveedor).
- **Configuración por defecto (0% merma analítica):**
  - `CORE_MODEL = "inherit"` -> `SA-1` (M01–M04 Negocio/Catálogo/Moat), `SA-2` (M05–M08 Forense/NOPLAT), `SA-3` (M09–M11 Valoración DCF/SOTP) y `SA-5` (M16–M18 Debate/Veredicto).
  - `LIGHT_MODEL = "flash"` -> `SA-4` (M12–M15 Técnico/Consenso/Noticias) y `SA-6` (Guion de Podcast desde `brief_ppt_podcast.md`).
- **Overrides directos desde el prompt del usuario:**
  - `"modelos: pro + flash"` -> `CORE_MODEL="pro"`, `LIGHT_MODEL="flash"`
  - `"modelos: inherit + flash_lite"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="flash_lite"`
  - `"modelo_unico: inherit"` -> `CORE_MODEL="inherit"`, `LIGHT_MODEL="inherit"`
  - `"modo: ultra-ahorro"` -> mueve también `SA-1` a `LIGHT_MODEL`.
- **Protocolo de Fallback Automático Multi-LLM (Innegociable):**
  - Si el usuario ejecuta la sesión con un LLM distinto de Gemini o si una llamada `invoke_subagent(..., Model=LIGHT_MODEL)` falla por modelo no disponible, error de proveedor, cuota agotada o entra de inmediato en `state: "errored"`, el orquestador **cambia automáticamente `LIGHT_MODEL = CORE_MODEL` (`"inherit"`)** para esa tarea y para el resto del lote, continuando con el mismo LLM activo sin interrumpir el proceso.

---

## 3. Micro-Packs por Rol (`Palanca #1`), Bandas Objetivo (`Palanca #2`) y Cola Kokoro (`Palanca #3`)

1. **Fase 0 (`--run-phase f0`):** genera `facts_sa1.md` (~32 KB), `facts_sa2.md` (~40 KB), `facts_sa3.md` (~30 KB) y `facts_sa4.md` (~24 KB), todos con la misma cabecera transversal de ~5 KB (`company_meta.json` + `market_data_live.json` + `peers_market_live.json`) para evitar pérdida de contexto cruzado.
2. **Bandas Objetivo (suelo + techo, sin recortar tablas ni catálogo `2.2`):**
   - `SA-1`: `76–92 KB` | `SA-2`: `66–80 KB` | `SA-3`: `52–64 KB` | `SA-4`: `41–52 KB` | `SA-5`: `38–48 KB` -> Maestro: **`273–336 KB` (`31,000–38,000 palabras`)**.
   - `SA-6` (`*_PODCAST_GUION.md`): **`58–70 KB` (`8,600–9,800 palabras`, `90–110 turnos`, ~43–48 min)**.
3. **Protección del TTL de Caché de 5 min:**
   - Durante las oleadas LLM, tras `SA-6` ejecuta únicamente `--run-phase f5-guion` (`0.2s`, incluye autofix oral determinista `P32`).
   - Cuando **terminen todos los subagentes LLM de todas las empresas**, lanza la cola batch de audio:
     ```powershell
     python "<ROOT_DIR>/_shared_engine/gauntlet_gatekeeper.py" --batch-podcast-root "<ROOT_DIR>" --min-seconds 2460
     ```
4. **Recuperación (`send_message`) y Limpieza (`kill`):**
   - Si un subagente queda en `"state": "errored"` por timeout de stream o pico `429`, reanúdalo con `send_message(Recipient="<conversationId>", Message="Continúa desde el paso exacto pendiente.")`; nunca lances duplicados.
   - Ejecuta `manage_subagents(Action="kill", ConversationIds=[...])` en cuanto su archivo/fase quede validado en disco.
