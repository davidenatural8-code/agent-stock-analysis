#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""merge_split_parts.py — Fusiona borradores troceados en los ficheros canónicos.

Uso:
    python merge_split_parts.py --target-dir <COMPANY_DIR>

Convención de nombres (V3.8.1):
    borrador_parte1a.md + borrador_parte1b.md -> borrador_parte1.md
    borrador_parte2a.md + borrador_parte2b.md -> borrador_parte2.md
    borrador_parte3a.md + borrador_parte3b.md -> borrador_parte3.md
    borrador_parte4a.md + borrador_parte4b.md -> borrador_parte4.md
    borrador_parte5a.md + borrador_parte5b.md -> borrador_parte5.md

Solo actúa si existen los trozos; si no hay trozos, deja el fichero canónico intacto.
Es determinista y no consume tokens: se ejecuta entre la oleada de subagentes y `f3-master`.
"""
from __future__ import annotations

import argparse
import os
import sys

SUFFIXES = ("a", "b", "c")


def merge_parts(target_dir: str) -> int:
    merged = 0
    for n in (1, 2, 3, 4, 5):
        chunks = []
        for suf in SUFFIXES:
            p = os.path.join(target_dir, f"borrador_parte{n}{suf}.md")
            if os.path.exists(p) and os.path.getsize(p) > 0:
                chunks.append(p)
        if not chunks:
            continue
        out_path = os.path.join(target_dir, f"borrador_parte{n}.md")
        content = []
        for p in chunks:
            with open(p, "r", encoding="utf-8") as f:
                content.append(f.read().rstrip() + "\n")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))
        size = os.path.getsize(out_path)
        print(f"[merge] borrador_parte{n}.md <- {len(chunks)} trozos ({size:,} bytes)")
        merged += 1
    if merged == 0:
        print("[merge] sin trozos que fusionar; nada que hacer")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target-dir", required=True)
    args = ap.parse_args()
    if not os.path.isdir(args.target_dir):
        print(f"[merge] no existe el directorio: {args.target_dir}", file=sys.stderr)
        return 1
    return merge_parts(args.target_dir)


if __name__ == "__main__":
    raise SystemExit(main())
