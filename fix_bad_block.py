with open(r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py", "r", encoding="utf-8", errors="ignore") as f:
    text = f.read()

bad_block = """    # Normalizar puntos numerados en 18.5 que tengan prefijo de encabezado (ej. #### 1. -> 1.)
    text = re.sub(r"(?m)^\s*#{1,6}\s*(\d+\.\s+)", r"\\1", text)
    m18_5_check = re.search(r"(###?\s*(?:Subsecci[o]n\s+)?\**18\.5 [^
]*
)(.*?)(?=\Z)", text, re.IGNORECASE | re.DOTALL)
    if m18_5_check:
        hdr, bdy = m18_5_check.group(1), m18_5_check.group(2)
        b18_found = re.findall(r"^\s*\d+\.\s+.+", bdy, re.MULTILINE)
        if len(b18_found) != 5:
            # Inyectar estructura canonica de 5 puntos numerados
            ts_canon = (
                "1. Tesis de Inversin Central y Diagnstico Estratgico: Posicin dominante respaldada por barreras de entrada sostenibles y economas de escala.\\n"
                "2. Diagnstico Forense, Calidad Contable y Balance: Slida posicin patrimonial, caja neta positiva y ausencia de anomalas de devengo.\\n"
                "3. Valoracin Multi-Metodologa y Matriz de Escenarios: Valor intrnseco respaldado por flujos de caja operativos y crecimiento disciplinado.\\n"
                "4. Riesgos Asimtricos y Plan de Mitigacin: Cobertura frente a presiones de precios sectoriales y contingencias regulatorias.\\n"
                "5. Veredicto Operativo Final del Comit: Recomendacin ejecutable de compra/mantenimiento con precio objetivo ponderado y mrgenes de seguridad.\\n\\n"
            )
            text = text[:m18_5_check.start()] + hdr + ts_canon + bdy
    return text"""

good_block = """    text = re.sub(r"(?m)^\s*#{1,6}\s*(\d+\.\s+)", r"\\1", text)
    return text"""

for p in [
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py",
    r"c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py"
]:
    with open(p, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    content = content.replace(bad_block, good_block)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

print("CLEANED")
