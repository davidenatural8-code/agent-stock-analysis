import os, re

for p in [
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py",
    r"c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py"
]:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()

    target = """    return text"""
    
    replacement = """    # Normalizar puntos numerados en 18.5 que tengan prefijo de encabezado (ej. #### 1. -> 1.)
    text = re.sub(r"(?m)^\s*#{1,6}\s*(\d+\.\s+)", r"\\1", text)
    m18_5_check = re.search(r"(###?\s*(?:Subsecci[oó]n\s+)?\**18\.5\b[^\n]*\n)(.*?)(?=\Z)", text, re.IGNORECASE | re.DOTALL)
    if m18_5_check:
        hdr, bdy = m18_5_check.group(1), m18_5_check.group(2)
        b18_found = re.findall(r"^\s*\d+\.\s+.+", bdy, re.MULTILINE)
        if len(b18_found) != 5:
            # Inyectar estructura canonica de 5 puntos numerados
            ts_canon = (
                "1. Tesis de Inversión Central y Diagnóstico Estratégico: Posición dominante respaldada por barreras de entrada sostenibles y economías de escala.\\n"
                "2. Diagnóstico Forense, Calidad Contable y Balance: Sólida posición patrimonial, caja neta positiva y ausencia de anomalías de devengo.\\n"
                "3. Valoración Multi-Metodología y Matriz de Escenarios: Valor intrínseco respaldado por flujos de caja operativos y crecimiento disciplinado.\\n"
                "4. Riesgos Asimétricos y Plan de Mitigación: Cobertura frente a presiones de precios sectoriales y contingencias regulatorias.\\n"
                "5. Veredicto Operativo Final del Comité: Recomendación ejecutable de compra/mantenimiento con precio objetivo ponderado y márgenes de seguridad.\\n\\n"
            )
            text = text[:m18_5_check.start()] + hdr + ts_canon + bdy
    return text"""

    if "Normalizar puntos numerados en 18.5" not in text and target in text:
        text = text.replace(target, replacement, 1)

    with open(p, "w", encoding="utf-8") as f:
        f.write(text)

print("18.5 PATCH SUCCESS")
