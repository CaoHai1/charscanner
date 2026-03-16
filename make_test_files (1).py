#!/usr/bin/env python3
"""
Generate sample test files containing various invisible characters
to verify charscanner behaviour.
Run: python make_test_files.py
"""

import os
from pathlib import Path

SAMPLES_DIR = Path("charscanner_test_samples")
SAMPLES_DIR.mkdir(exist_ok=True)

# ── sample_clean.py: completely clean file ────────────────────────────────
(SAMPLES_DIR / "sample_clean.py").write_text(
    "# Clean file - no issues here\n"
    "def hello(name: str) -> str:\n"
    "    return f'Hello, {name}!'\n",
    encoding="utf-8"
)

# ── sample_zwsp.py: contains Zero Width Space (U+200B) ───────────────────
zwsp = "\u200b"
(SAMPLES_DIR / "sample_zwsp.py").write_text(
    f"# This file has a zero-width space\u200b hidden after the hash\n"
    f"def check{zwsp}token(value):\n"
    f"    if value\u200b == 'secret':\n"
    f"        return True\n"
    f"    return False\n",
    encoding="utf-8"
)

# ── sample_mixed.js: regular non-ASCII comments + invisible characters ────
bom   = "\ufeff"
rtlo  = "\u202e"
zwj   = "\u200d"
(SAMPLES_DIR / "sample_mixed.js").write_text(
    f"// This is a mixed example file\n"
    f"// Contains regular non-ASCII text and invisible characters\n"
    f"function greet(name) {{\n"
    f"  // BOM character here: {bom}end\n"
    f"  const msg = 'Hello' + '{zwj}' + name; // ZWJ injected\n"
    f"  return msg;\n"
    f"}}\n",
    encoding="utf-8"
)

# ── sample_trojan.cpp: bidirectional override (Trojan-source style) ───────
(SAMPLES_DIR / "sample_trojan.cpp").write_text(
    "// Trojan-source demo\n"
    "#include <iostream>\n"
    "bool isAdmin(std::string role) {\n"
    "    // Check if role is \u202e\"admin\"\u202c\n"
    "    return role == \"user\";\n"
    "}\n"
    "int main() {\n"
    "    std::cout << isAdmin(\"admin\") << std::endl;\n"
    "    return 0;\n"
    "}\n",
    encoding="utf-8"
)

print(f"✓ Test files generated in {SAMPLES_DIR}/")
print("  sample_clean.py      — clean file (no issues)")
print("  sample_zwsp.py       — contains U+200B Zero Width Space")
print("  sample_mixed.js      — non-ASCII text + BOM + ZWJ")
print("  sample_trojan.cpp    — bidirectional text override (Trojan-source)")
print()
print("Run a scan:")
print(f"  python charscanner.py {SAMPLES_DIR}/")
print(f"  python charscanner.py {SAMPLES_DIR}/ --invisible-only")
