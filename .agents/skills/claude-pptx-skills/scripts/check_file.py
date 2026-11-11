#!/usr/bin/env python3
"""
Lightweight .pptx integrity check (standalone, no external schema files needed).

Checks:
  1. The file is a valid zip archive
  2. Required OOXML parts are present (presentation.xml, content types, etc.)
  3. Every .xml part inside is well-formed XML (catches corruption from bad
     string edits, e.g. unescaped '&' or unclosed tags introduced by a script)
  4. python-pptx can open the file and read every slide's shapes

This is NOT full ISO/IEC 29500 schema validation (that requires bundling the
full OOXML XSD schema set, which is impractical to distribute standalone).
It catches the vast majority of real-world breakage: corrupted zip, malformed
XML from string-replace edits, and structurally unreadable files.

Usage: python check_file.py deck.pptx
"""
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


REQUIRED_PARTS = [
    "[Content_Types].xml",
    "_rels/.rels",
    "ppt/presentation.xml",
]


def check_zip_integrity(path: Path) -> list[str]:
    errors = []
    try:
        with zipfile.ZipFile(path) as z:
            bad_file = z.testzip()
            if bad_file:
                errors.append(f"Corrupt entry in zip: {bad_file}")
            names = set(z.namelist())
            for part in REQUIRED_PARTS:
                if part not in names:
                    errors.append(f"Missing required part: {part}")
    except zipfile.BadZipFile:
        errors.append("File is not a valid zip / .pptx archive")
    return errors


def check_xml_wellformed(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            if name.endswith(".xml") or name.endswith(".rels"):
                try:
                    ET.fromstring(z.read(name))
                except ET.ParseError as e:
                    errors.append(f"Malformed XML in {name}: {e}")
    return errors


def check_python_pptx_can_open(path: Path) -> list[str]:
    errors = []
    try:
        from pptx import Presentation
        prs = Presentation(str(path))
        for i, slide in enumerate(prs.slides):
            _ = list(slide.shapes)  # force-read shape tree
    except Exception as e:
        errors.append(f"python-pptx failed to open/read file: {e}")
    return errors


def main():
    if len(sys.argv) != 2:
        print("Usage: check_file.py deck.pptx", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    all_errors = []
    all_errors += check_zip_integrity(path)
    if not all_errors:  # only bother with deeper checks if the zip itself is sound
        all_errors += check_xml_wellformed(path)
        all_errors += check_python_pptx_can_open(path)

    if all_errors:
        print("Validation FAILED:")
        for e in all_errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("All validations PASSED (zip integrity, required parts, well-formed XML, python-pptx read).")


if __name__ == "__main__":
    main()
