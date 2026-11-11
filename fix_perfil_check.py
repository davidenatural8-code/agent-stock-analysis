paths = [
    r"c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py",
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py"
]

old_check = '''    if not re.search(r"(?mi)^#\\s*PERFIL EXTRA[ÍI]DO", text) and re.search(r"##\\s*M[oó]dulo\\s*0?1\\b", text, re.IGNORECASE):
        text = "# PERFIL EXTRAÍDO: Identificación, ticker, ISIN, sector, industria, moneda base\\n\\n### Tabla de control institucional\\n\\n" + text.lstrip("\\n-\\r ")'''

new_check = '''    if not re.search(r"(?mi)^#\\s*PERFIL EXTRA[ÍI]DO", text):
        if re.search(r"(?mi)^#+\\s*M[oó]dulo\\s*0?1\\b", text) or re.search(r"(?mi)^###?\\s+Tabla de control institucional", text):
            text = "# PERFIL EXTRAÍDO: Identificación, ticker, ISIN, sector, industria, moneda base\\n\\n" + text.lstrip("\\n-\\r ")'''

for p in paths:
    with open(p, "r", encoding="utf-8") as f:
        content = f.read()
    if old_check in content:
        content = content.replace(old_check, new_check)
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        print("Fixed PERFIL EXTRAIDO check in:", p)
    else:
        print("Target not found in:", p)
