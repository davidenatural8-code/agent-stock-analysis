import re

for p in [
    r"C:\Users\david\Desktop\Momentum\FLASH_TO_PROCESS\_Cartera_1\_shared_engine\gauntlet_gatekeeper.py",
    r"c:\Users\david\Desktop\Momentum\agent-stock-analysis\.agents\skills\deep-research-gauntlet-loop\scripts\gauntlet_gatekeeper.py"
]:
    with open(p, "r", encoding="latin1") as f:
        lines = f.readlines()
    start_idx = None
    for i, l in enumerate(lines):
        if "Normalizar puntos numerados en 18.5" in l:
            start_idx = i
            break
    if start_idx is not None:
        end_idx = None
        for j in range(start_idx, min(len(lines), start_idx + 25)):
            if "return text" in lines[j]:
                end_idx = j
                break
        if end_idx is not None:
            new_lines = [
                "    # Normalizar puntos numerados en 18.5 que tengan prefijo de encabezado (ej. #### 1. -> 1.)\n",
                "    text = re.sub(r'(?m)^\\s*#{1,6}\\s*(\\d+\\.\\s+)', r'\\1', text)\n",
                "    return text\n"
            ]
            lines = lines[:start_idx] + new_lines + lines[end_idx+1:]
            with open(p, "w", encoding="latin1") as f:
                f.writelines(lines)
            print("FIXED", p)
