#!/usr/bin/env python3
"""Minify linkedin_capture.js into a javascript: bookmarklet href file."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = Path(__file__).resolve().parent / "linkedin_capture.js"
OUTPUT = ROOT / "public" / "tools" / "bookmarklet.href"


def minify_js(source: str) -> str:
    # Drop block comments and line comments (bookmarklet has no strings with //)
    source = re.sub(r"/\*[\s\S]*?\*/", "", source)
    source = re.sub(r"//.*?$", "", source, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", source).strip()


def main() -> int:
    raw = SOURCE.read_text(encoding="utf-8")
    compact = minify_js(raw)
    href = f"javascript:{compact}"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(href, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({len(href)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
