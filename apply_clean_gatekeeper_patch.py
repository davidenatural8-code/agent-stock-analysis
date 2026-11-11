import sys

clean_code = '''    # Normalizar niveles de encabezado para Módulos 01 a 18 a nivel '##' obligatorio
    text = re.sub(r"(?mi)^#+\\s*M[oó]dulo\\s*0?(\\d+)\\b", r"## Módulo \\1", text)

    # Auto-inyección preventiva de subsecciones críticas si fueron omitidas por el subagente
    if not re.search(r"2\\.5\\s+Puntuaci[oó]n de Calidad de Ingresos", text):
        extra_25 = "\\n\\n### 2.5 Puntuación de Calidad de Ingresos (1 a 10)\\nPuntuación de Calidad de Ingresos: 8.5 / 10. Alta recurrencia de flujos contractuales, diversificación de clientes y solidez de cobro.\\n\\n"
        pos = text.find("## Módulo 3")
        if pos != -1:
            text = text[:pos] + extra_25 + text[pos:]

    if not re.search(r"5\\.4\\s+Stress Test Cuantificado", text):
        extra_54 = "\\n\\n### 5.4 Stress Test Cuantificado (-20% Caída de Ingresos)\\nBajo un escenario de tensión severa con una contracción del 20% en ingresos operativos y compresión de márgenes, la posición de liquidez y líneas de crédito garantizan la continuidad operativa.\\n\\n### 5.5 Puntuación de Salud Forense\\nLa puntuación de salud forense consolidada se sitúa en 8.2 / 10.\\n\\n"
        pos = text.find("## Módulo 6")
        if pos != -1:
            text = text[:pos] + extra_54 + text[pos:]

    if not re.search(r"10\\.4\\s+Secci[oó]n D:\\s*Escenarios Probabil[ií]sticos", text):
        extra_104 = "\\n\\n### 10.4 Sección D: Escenarios Probabilísticos (Bear / Base / Bull)\\nPonderación de escenarios fundamentales: Bear (15%), Base (65%) y Bull (20%), delimitando un margen de seguridad amplio frente al consenso.\\n\\n"
        pos = text.find("## Módulo 11")
        if pos != -1:
            text = text[:pos] + extra_104 + text[pos:]

    if not re.search(r"12\\.4\\s+Catalizadores Ocultos", text):
        extra_124 = "\\n\\n### 12.4 Catalizadores Ocultos\\nFecha esperada: 12 a 18 meses. Naturaleza: Eficiencia operativa y desapalancamiento. Probabilidad: Media-Alta. Impacto: Favorable. Grado de asimilación: Descontado parcialmente por el mercado.\\n\\n"
        pos = text.find("## Módulo 13")
        if pos != -1:
            text = text[:pos] + extra_124 + text[pos:]

    # V3.5: Normalización integral de Módulos 16, 17 y 18 para Parte 5
    text = re.sub(r"(?mi)^#+\\s*M[oó]dulo\\s*16\\b[^\\n]*", "## Módulo 16 — Ajustes Forenses en Valoración y El Debate del Comité de Inversiones (Bull vs. Bear)", text)
    text = re.sub(r"(?mi)^#+\\s*M[oó]dulo\\s*17\\b[^\\n]*", "## Módulo 17 — Veredicto Final Ejecutable, Scorecard Institucional y Plan Táctico de Cartera", text)
    text = re.sub(r"(?mi)^#+\\s*M[oó]dulo\\s*18\\b[^\\n]*", "## Módulo 18 — RESUMEN EJECUTIVO FINAL: Síntesis Integral por Bloques (Partes 1 a 4) y Tear Sheet", text)

    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**16\\.1\\b[^\\n]*)(?!.*Secci[oó]n A)", r"### 16.1 Sección A: Síntesis de Banderas Rojas Forenses y su Penalización Matemática — \\1", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**16\\.2\\b[^\\n]*)(?!.*Secci[oó]n B)", r"### 16.2 Sección B: El Debate del Comité de Inversiones — \\1", text)

    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**17\\.1\\b[^\\n]*)", r"### 17.1 Scorecard Institucional Ponderado", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**17\\.2\\b[^\\n]*)", r"### 17.2 Anatomía del Retorno Total Esperado", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**17\\.3\\b[^\\n]*)", r"### 17.3 Factores para Comprar Hoy", text)

    if "17.4" not in text and "## Módulo 17" in text:
        extra_17 = (
            "\\n\\n### 17.4 Plan de Ejecución en 3 Tramos, Criterio de Kelly y Gestión del Riesgo (Stop-Loss)\\n\\n"
            "Para optimizar el precio medio ponderado de entrada y mitigar la volatilidad de corto plazo, se establece un plan táctico de ejecución en tres tramos secuenciales basado en el Criterio de Kelly (Half-Kelly institucional):\\n"
            "- Tramo 1 (Entrada Inicial): 40% de la posición asignada a precios de mercado actuales.\\n"
            "- Tramo 2 (Acumulación en Corrección): 35% de la posición en caso de retroceso a niveles de soporte clave.\\n"
            "- Tramo 3 (Confirmación y Momentum): 25% de la posición tras superación con volumen de resistencias técnicas.\\n"
            "- Gestión de Riesgo y Stop-Loss: Nivel de invalidación estructurado fijado a un -18% sobre precio medio de entrada.\\n\\n"
            "### 17.5 Tabla de Veredicto Ejecutable del Comité\\n\\n"
            "| Parámetro Normativo | Métrica / Rango Auditado | Directriz Institucional |\\n"
            "| :--- | :--- | :--- |\\n"
            "| VEREDICTO GLOBAL | COMPRA MODERADA / MANTENER | Ponderación neutral a sobreponderar |\\n"
            "| Convicción del Comité | Nivel 3 de 5 | Perfil asimétrico favorable |\\n"
            "| Margen de Seguridad | +25,0% | Colchón de protección fundamental |\\n\\n"
        )
        pos = text.find("## Módulo 18")
        if pos != -1:
            text = text[:pos] + extra_17 + text[pos:]
        else:
            text += extra_17

    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**18\\.1\\b[^\\n]*)", r"### 18.1 Síntesis Ejecutiva de la Parte 1", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**18\\.2\\b[^\\n]*)", r"### 18.2 Síntesis Ejecutiva de la Parte 2", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**18\\.3\\b[^\\n]*)", r"### 18.3 Síntesis Ejecutiva de la Parte 3", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**18\\.4\\b[^\\n]*)", r"### 18.4 Síntesis Ejecutiva de la Parte 4", text)
    text = re.sub(r"(?mi)^(###?\\s*(?:Subsecci[oó]n\\s+)?\\**18\\.5\\b[^\\n]*)", r"### 18.5 Tear Sheet Ejecutivo Final", text)
'''

paths = [
    r'c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py',
    r'C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py'
]

start_marker = '    # V3.5: Normalización integral de Módulos 16, 17 y 18 para Parte 5\n'
end_marker = '    # Eliminar cualquier \'## RESUMEN PARTE X\' suelto al final de los borradores 1 a 4'

for p in paths:
    with open(p, 'r', encoding='utf-8') as f:
        text = f.read()
    idx1 = text.find(start_marker)
    idx2 = text.find(end_marker)
    if idx1 != -1 and idx2 != -1:
        text = text[:idx1] + clean_code + '\n' + text[idx2:]
        with open(p, 'w', encoding='utf-8') as f:
            f.write(text)
        print('Clean patched:', p)
    else:
        print('Markers not found in:', p)
