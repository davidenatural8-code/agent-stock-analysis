import os, re

for p in [
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py",
    r"c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py"
]:
    if not os.path.exists(p):
        continue
    with open(p, "r", encoding="utf-8") as f:
        text = f.read()

    target = """    # Eliminar cualquier '## RESUMEN PARTE X' suelto al final de los borradores 1 a 4"""
    
    injection = """    if not re.search(r"(?mi)^#\\s*PERFIL EXTRA[ÍI]DO", text) and re.search(r"##\\s*M[oó]dulo\\s*0?1\\b", text, re.IGNORECASE):
        text = "# PERFIL EXTRAÍDO: Identificación, ticker, ISIN, sector, industria, moneda base\\n\\n### Tabla de control institucional\\n\\n" + text.lstrip("\\n-\\r ")

    # Eliminar cualquier '## RESUMEN PARTE X' suelto al final de los borradores 1 a 4"""

    if target in text and "PERFIL EXTRAÍDO: Identificación" not in text:
        text = text.replace(target, injection, 1)

    with open(p, "w", encoding="utf-8") as f:
        f.write(text)

print("INJECTION COMPLETE")
