#!/usr/bin/env python3
"""
生成测试用的样本文件，包含各种不可见字符，用于验证 charscanner 工具。
运行: python make_test_files.py
"""

import os
from pathlib import Path

SAMPLES_DIR = Path("charscanner_test_samples")
SAMPLES_DIR.mkdir(exist_ok=True)

# ── sample_clean.py: 完全干净的文件 ──────────────────────────────────────
(SAMPLES_DIR / "sample_clean.py").write_text(
    "# Clean file - no issues here\n"
    "def hello(name: str) -> str:\n"
    "    return f'Hello, {name}!'\n",
    encoding="utf-8"
)

# ── sample_zwsp.py: 含零宽空格 ────────────────────────────────────────────
zwsp = "\u200b"
(SAMPLES_DIR / "sample_zwsp.py").write_text(
    f"# This file has a zero-width space\u200b hidden after the hash\n"
    f"def check{zwsp}token(value):\n"
    f"    if value\u200b == 'secret':\n"
    f"        return True\n"
    f"    return False\n",
    encoding="utf-8"
)

# ── sample_mixed.js: 中文注释 + 不可见字符 ────────────────────────────────
bom   = "\ufeff"
rtlo  = "\u202e"
zwj   = "\u200d"
(SAMPLES_DIR / "sample_mixed.js").write_text(
    f"// 这是一个混合示例文件\n"
    f"// 包含中文注释和不可见字符\n"
    f"function greet(name) {{\n"
    f"  // BOM character here: {bom}end\n"
    f"  const msg = 'Hello' + '{zwj}' + name; // ZWJ injected\n"
    f"  return msg;\n"
    f"}}\n",
    encoding="utf-8"
)

# ── sample_trojan.cpp: Trojan-source 风格的双向覆盖字符 ───────────────────
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

print(f"✓ 测试文件已生成到 {SAMPLES_DIR}/ 目录")
print("  sample_clean.py      — 干净文件（无问题）")
print("  sample_zwsp.py       — 含 U+200B 零宽空格")
print("  sample_mixed.js      — 中文注释 + BOM + ZWJ")
print("  sample_trojan.cpp    — 双向文本覆盖（Trojan-source）")
print()
print("运行扫描示例:")
print(f"  python charscanner.py {SAMPLES_DIR}/")
print(f"  python charscanner.py {SAMPLES_DIR}/ --invisible-only")
