# agent-stock-analysis (workspace de Antigravity)

Agente de análisis bursátil institucional que corre **dentro de Antigravity** con tu suscripción. No hace falta ninguna clave de API.

## Puesta en marcha
1. `pip install -r requirements.txt` (y modelos de Kokoro-ONNX según `docs/README_INSTALACION_OTRO_PC.md`).
2. En Antigravity: **File → Open Folder** → `C:\Users\david\Desktop\Momentum\agent-stock-analysis`.
3. En el chat escribe, por ejemplo:
   - `lanza gauntlet en C:\Users\david\Desktop\Momentum\backoffice-stock-analysis\TEST\TEST_5`
   - `lanza gauntlet en <ROOT_DIR> solo para EXPN.L y ZDC.V, sin podcast`

   El skill `gauntlet-run` se activa solo. Para lotes largos (por ejemplo 100 empresas) es mejor anteponer `/goal`.

Ejemplo paso a paso, con variantes y el resultado esperado: [docs/EJEMPLO_EJECUCION_ANTIGRAVITY.md](docs/EJEMPLO_EJECUCION_ANTIGRAVITY.md)

## Contenido
| Ruta | Para qué sirve |
|---|---|
| `AGENTS.md` | Reglas permanentes que se cargan siempre |
| `.agents/skills/gauntlet-run/` | Lanzador corto (sustituye al prompt largo) |
| `.agents/skills/deep-research-gauntlet-loop/` | Pipeline completo: `SKILL.md`, `scripts/` (motor) y `references/` (metodología) |
| `.agents/skills/humanamente/`, `claude-pptx-skills/`, `academic-pptx-skill/` | Skills auxiliares |
| `docs/PROMPTS_OPERATIVOS_GAUNTLET.md` | Prompt operativo completo (por si quieres pegarlo a mano) |

Los datos de las empresas se quedan en su ROOT_DIR, fuera de este workspace.

## Mantener sincronizado
La copia maestra del skill sigue en `C:\PROJECT\Informes\.agents\skills\`. Si la cambias allí, vuelve a copiarla aquí:
```powershell
robocopy C:\PROJECT\Informes\.agents\skills\deep-research-gauntlet-loop .agents\skills\deep-research-gauntlet-loop /E /XD __pycache__
```
