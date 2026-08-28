#!/usr/bin/env python3
"""List command image references outside the three normalized sections."""

from __future__ import annotations

import re
from pathlib import Path

from audit_and_crop_command_images import command_docs
from build_parameter_image_contact_sheets import section_references


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    image_pattern = re.compile(r"!\[[^\]]*\]\((?:\./)?(images/[^)#]+)")
    total = classified = 0
    for document in command_docs(root):
        text = document.read_text(encoding="utf-8")
        refs = image_pattern.findall(text)
        known = []
        for section in ("parameter", "usage", "effect"):
            known.extend(section_references(text, section))
        total += len(refs)
        classified += len(known)
        for ref in refs:
            if ref not in known:
                print(f"{document.relative_to(root).as_posix()},{ref}")
    print(f"total={total} classified={classified} unclassified={total-classified}")


if __name__ == "__main__":
    main()
