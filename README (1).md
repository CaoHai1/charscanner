# charscanner 🔍

> Scan source files for hidden non-ASCII and invisible characters (e.g. `U+200B` Zero Width Space)

---

## Why does this exist?

Invisible characters — like Zero Width Space (`U+200B`) and Right-to-Left Override (`U+202E`) — are commonly injected into source code maliciously, creating vulnerabilities that are invisible to the human eye but detectable by compilers and interpreters. This is known as a [Trojan-Source](https://trojansource.codes/) attack.

This tool uses **plain regex matching** — fast, zero dependencies, zero false positives.

---

## File structure

```
charscanner/
├── charscanner.py      # Main script (the CLI tool)
├── make_test_files.py  # Generates sample test files
└── README.md
```

---

## Quick start

### Requirements

- Python **3.10+** — no third-party libraries needed, standard library only

### Installation (optional — register as a global command)

```bash
# Option 1: run directly (recommended)
python charscanner.py .

# Option 2: make executable (macOS / Linux)
chmod +x charscanner.py
./charscanner.py .

# Option 3: install as a global command
pip install --editable .   # requires setup.py / pyproject.toml
```

---

## Usage

```
python charscanner.py [path] [options]
```

### Options

| Option | Description |
|---|---|
| `path` | Directory or file to scan (default: current directory) |
| `--ext .py .ts` | File extensions to scan (default: .py .js .cpp .ts .jsx .tsx .c .h .java) |
| `--invisible-only` | Report only invisible characters; skip regular non-ASCII like CJK comments |
| `--no-recursive` | Do not recurse into subdirectories |
| `--no-color` | Disable ANSI colors (useful when piping to a file) |
| `-o report.txt` | Also write results to a file |
| `--fail-on-found` | Exit with code `1` if any issues are found (for CI/CD) |
| `-q / --quiet` | Show summary only, suppress per-hit details |
| `--show-clean` | Also list files with no issues |

### Examples

```bash
# Scan the current directory (all supported extensions)
python charscanner.py .

# Scan only .py files, report invisible characters only
python charscanner.py src/ --ext .py --invisible-only

# Scan a single file
python charscanner.py main.py

# Write a plain-text report
python charscanner.py . --no-color -o report.txt

# Use in CI — fail the build if issues are found
python charscanner.py . --invisible-only --fail-on-found
```

---

## Sample output

```
Scanning 4 files…

charscanner_test_samples/sample_zwsp.py  3 issues
  line    1  col  35  [INVISIBLE]  U+200B  ZERO WIDTH SPACE
  │ # This file has a zero-width space◆ hidden after the hash
  line    2  col  10  [INVISIBLE]  U+200B  ZERO WIDTH SPACE
  │ def check◆token(value):
  line    3  col  13  [INVISIBLE]  U+200B  ZERO WIDTH SPACE
  │     if value◆ == 'secret':

charscanner_test_samples/sample_trojan.cpp  2 issues
  line    4  col  25  [INVISIBLE]  U+202E  RIGHT-TO-LEFT OVERRIDE
  │     // Check if role is ◆"admin"
  line    4  col  33  [INVISIBLE]  U+202C  POP DIRECTIONAL FORMATTING
  │     // Check if role is ◆"admin"◆

────────────────────────────────────────────────────────────
Scan complete
  Files scanned:     4
  Files with issues: 2
  Total hits:        5
  Invisible chars:   5
────────────────────────────────────────────────────────────
```

---

## Detected invisible characters (partial list)

| Codepoint | Name | Risk |
|---|---|---|
| `U+200B` | ZERO WIDTH SPACE | High |
| `U+200C/D` | ZERO WIDTH NON-JOINER / JOINER | High |
| `U+202E` | RIGHT-TO-LEFT OVERRIDE | Critical (Trojan-Source) |
| `U+202A–D` | Bidirectional embedding/override series | Critical |
| `U+FEFF` | BOM / ZERO WIDTH NO-BREAK SPACE | Medium |
| `U+00AD` | SOFT HYPHEN | Medium |
| `U+2060` | WORD JOINER | Medium |
| `U+00A0` | NO-BREAK SPACE | Low |
| `U+2003` etc. | EM / EN / THIN SPACE variants | Low |

---

## CI/CD integration (GitHub Actions example)

```yaml
- name: Scan for invisible characters
  run: |
    python charscanner.py . \
      --invisible-only \
      --fail-on-found \
      --no-color \
      -o invisible_chars_report.txt
```

---

## Design principles

- **Zero dependencies** — standard library only
- **Regex-based** — one pattern `[^\x00-\x7f]` covers all non-ASCII characters
- **Fast** — handles tens of thousands of files in seconds
- **CI-composable** — exit code design works cleanly in build pipelines
