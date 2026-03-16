#!/usr/bin/env python3
"""
charscanner — scan source files for non-ASCII and invisible characters
Usage: python charscanner.py [path] [options]
"""

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator

# ── ANSI colors ────────────────────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    MAGENTA= "\033[95m"
    WHITE  = "\033[97m"
    GRAY   = "\033[90m"

def no_color(text: str) -> str:
    """Strip ANSI color codes (used for file output)."""
    return re.sub(r"\033\[[0-9;]*m", "", text)

# ── Invisible / special character lookup table ─────────────────────────────
INVISIBLE_CHARS: dict[str, str] = {
    "\u200b": "ZERO WIDTH SPACE",
    "\u200c": "ZERO WIDTH NON-JOINER",
    "\u200d": "ZERO WIDTH JOINER",
    "\u200e": "LEFT-TO-RIGHT MARK",
    "\u200f": "RIGHT-TO-LEFT MARK",
    "\u202a": "LEFT-TO-RIGHT EMBEDDING",
    "\u202b": "RIGHT-TO-LEFT EMBEDDING",
    "\u202c": "POP DIRECTIONAL FORMATTING",
    "\u202d": "LEFT-TO-RIGHT OVERRIDE",
    "\u202e": "RIGHT-TO-LEFT OVERRIDE",
    "\u2060": "WORD JOINER",
    "\u2061": "FUNCTION APPLICATION",
    "\u2062": "INVISIBLE TIMES",
    "\u2063": "INVISIBLE SEPARATOR",
    "\u2064": "INVISIBLE PLUS",
    "\ufeff": "ZERO WIDTH NO-BREAK SPACE (BOM)",
    "\u00ad": "SOFT HYPHEN",
    "\u034f": "COMBINING GRAPHEME JOINER",
    "\u115f": "HANGUL CHOSEONG FILLER",
    "\u1160": "HANGUL JUNGSEONG FILLER",
    "\u17b4": "KHMER VOWEL INHERENT AQ",
    "\u17b5": "KHMER VOWEL INHERENT AA",
    "\u180e": "MONGOLIAN VOWEL SEPARATOR",
    "\u3164": "HANGUL FILLER",
    "\ufe00": "VARIATION SELECTOR-1",
    "\u00a0": "NO-BREAK SPACE",
    "\u2002": "EN SPACE",
    "\u2003": "EM SPACE",
    "\u2004": "THREE-PER-EM SPACE",
    "\u2005": "FOUR-PER-EM SPACE",
    "\u2006": "SIX-PER-EM SPACE",
    "\u2007": "FIGURE SPACE",
    "\u2008": "PUNCTUATION SPACE",
    "\u2009": "THIN SPACE",
    "\u200a": "HAIR SPACE",
    "\u205f": "MEDIUM MATHEMATICAL SPACE",
    "\u3000": "IDEOGRAPHIC SPACE",
}

# Regex matching all non-ASCII characters
RE_NON_ASCII = re.compile(r"[^\x00-\x7f]")

# Supported file extensions
DEFAULT_EXTENSIONS = {".py", ".js", ".cpp", ".ts", ".jsx", ".tsx", ".c", ".h", ".java"}

# ── Data structures ─────────────────────────────────────────────────────────
@dataclass
class Hit:
    line_no: int
    col_no: int
    char: str
    codepoint: str
    name: str
    line_preview: str
    is_invisible: bool

@dataclass
class FileResult:
    path: Path
    hits: list[Hit] = field(default_factory=list)
    error: str | None = None

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    @property
    def invisible_count(self) -> int:
        return sum(1 for h in self.hits if h.is_invisible)

# ── Core scan logic ─────────────────────────────────────────────────────────
def char_name(ch: str) -> tuple[str, bool]:
    """Return (character name, is_invisible)."""
    if ch in INVISIBLE_CHARS:
        return INVISIBLE_CHARS[ch], True
    try:
        import unicodedata
        return unicodedata.name(ch, f"U+{ord(ch):04X}"), False
    except Exception:
        return f"U+{ord(ch):04X}", False

def scan_line(line: str, line_no: int) -> list[Hit]:
    hits: list[Hit] = []
    for m in RE_NON_ASCII.finditer(line):
        ch = m.group()
        col = m.start() + 1
        name, is_invisible = char_name(ch)
        preview = line.rstrip("\n")
        if len(preview) > 120:
            start = max(0, col - 40)
            preview = ("…" if start > 0 else "") + preview[start:start+120] + "…"
        hits.append(Hit(
            line_no=line_no,
            col_no=col,
            char=ch,
            codepoint=f"U+{ord(ch):04X}",
            name=name,
            line_preview=preview,
            is_invisible=is_invisible,
        ))
    return hits

def scan_file(path: Path, invisible_only: bool = False) -> FileResult:
    result = FileResult(path=path)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line_no, line in enumerate(f, start=1):
                for hit in scan_line(line, line_no):
                    if invisible_only and not hit.is_invisible:
                        continue
                    result.hits.append(hit)
    except Exception as e:
        result.error = str(e)
    return result

def iter_files(
    root: Path,
    extensions: set[str],
    recursive: bool = True,
) -> Generator[Path, None, None]:
    if root.is_file():
        if root.suffix in extensions:
            yield root
        return
    pattern = "**/*" if recursive else "*"
    for p in root.glob(pattern):
        if p.is_file() and p.suffix in extensions:
            yield p

# ── Output rendering ────────────────────────────────────────────────────────
def severity_color(hit: Hit) -> str:
    if hit.is_invisible:
        return C.RED
    return C.YELLOW

def render_hit(hit: Hit, use_color: bool = True) -> str:
    cc = C if use_color else type("NoC", (), {k: "" for k in vars(C)})()
    tag = f"{cc.RED}[INVISIBLE]{cc.RESET}" if hit.is_invisible else f"{cc.YELLOW}[NON-ASCII]{cc.RESET}"
    loc = f"{cc.CYAN}line {hit.line_no:>4}{cc.RESET}  {cc.DIM}col {hit.col_no:>3}{cc.RESET}"
    cp  = f"{cc.MAGENTA}{hit.codepoint}{cc.RESET}"
    nm  = f"{cc.WHITE}{hit.name}{cc.RESET}"
    # Mark the offending character in the preview
    preview = hit.line_preview.replace(
        hit.char,
        f"{cc.RED}◆{cc.RESET}",
        1,
    )
    return f"  {loc}  {tag}  {cp}  {nm}\n  {cc.GRAY}│{cc.RESET} {preview}"

def render_file_header(result: FileResult, use_color: bool = True) -> str:
    cc = C if use_color else type("NoC", (), {k: "" for k in vars(C)})()
    badge = (
        f"{cc.RED}{result.hit_count} issue{'s' if result.hit_count != 1 else ''}{cc.RESET}"
        if result.hit_count else f"{cc.GREEN}clean{cc.RESET}"
    )
    return f"\n{cc.BOLD}{cc.WHITE}{result.path}{cc.RESET}  {badge}"

def render_summary(results: list[FileResult], use_color: bool = True) -> str:
    cc = C if use_color else type("NoC", (), {k: "" for k in vars(C)})()
    total_files   = len(results)
    dirty_files   = sum(1 for r in results if r.hit_count)
    total_hits    = sum(r.hit_count for r in results)
    invisible     = sum(r.invisible_count for r in results)
    error_files   = sum(1 for r in results if r.error)

    lines = [
        f"\n{cc.BOLD}{'─'*60}{cc.RESET}",
        f"{cc.BOLD}Scan complete{cc.RESET}",
        f"  Files scanned:     {cc.CYAN}{total_files}{cc.RESET}",
        f"  Files with issues: {cc.RED if dirty_files else cc.GREEN}{dirty_files}{cc.RESET}",
        f"  Total hits:        {cc.RED if total_hits else cc.GREEN}{total_hits}{cc.RESET}",
        f"  Invisible chars:   {cc.RED if invisible else cc.GREEN}{invisible}{cc.RESET}",
    ]
    if error_files:
        lines.append(f"  Read errors:       {cc.RED}{error_files}{cc.RESET}")
    lines.append(f"{cc.BOLD}{'─'*60}{cc.RESET}")
    return "\n".join(lines)

# ── CLI ─────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="charscanner",
        description="Scan source files for non-ASCII and invisible characters (e.g. U+200B Zero Width Space)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python charscanner.py .                      # scan current directory
  python charscanner.py src/                   # scan the src directory
  python charscanner.py main.py                # scan a single file
  python charscanner.py . --invisible-only     # report invisible chars only
  python charscanner.py . --ext .py .ts        # scan only .py and .ts files
  python charscanner.py . --no-recursive       # do not recurse subdirectories
  python charscanner.py . --no-color           # plain text output
  python charscanner.py . -o report.txt        # write results to a file
  python charscanner.py . --fail-on-found      # exit non-zero if issues found
        """,
    )
    p.add_argument("path", nargs="?", default=".",
                   help="directory or file to scan (default: current directory)")
    p.add_argument("--ext", nargs="+", default=None, metavar="EXT",
                   help="file extensions to scan (default: .py .js .cpp .ts ...)")
    p.add_argument("--invisible-only", action="store_true",
                   help="report only invisible characters (skip regular non-ASCII such as CJK)")
    p.add_argument("--no-recursive", action="store_true",
                   help="do not recurse into subdirectories")
    p.add_argument("--no-color", action="store_true",
                   help="disable ANSI color output")
    p.add_argument("-o", "--output", metavar="FILE",
                   help="also write results to this file (still prints to terminal)")
    p.add_argument("--fail-on-found", action="store_true",
                   help="exit with code 1 if any issues are found (for CI)")
    p.add_argument("--quiet", "-q", action="store_true",
                   help="show summary only, suppress per-hit details")
    p.add_argument("--show-clean", action="store_true",
                   help="also list files with no issues")
    return p

def main() -> int:
    parser = build_parser()
    args   = parser.parse_args()

    use_color  = not args.no_color and sys.stdout.isatty()
    root       = Path(args.path)
    extensions = set(args.ext) if args.ext else DEFAULT_EXTENSIONS
    recursive  = not args.no_recursive

    if not root.exists():
        print(f"Error: path does not exist → {root}", file=sys.stderr)
        return 2

    # ── Scan ──────────────────────────────────────────────────────────────
    results: list[FileResult] = []
    files = list(iter_files(root, extensions, recursive))

    if not files:
        print("No matching files found.")
        return 0

    cc = C if use_color else type("NoC", (), {k: "" for k in vars(C)})()
    print(f"{cc.DIM}Scanning {len(files)} file{'s' if len(files) != 1 else ''}…{cc.RESET}")

    for fp in files:
        r = scan_file(fp, invisible_only=args.invisible_only)
        results.append(r)

    # ── Render ────────────────────────────────────────────────────────────
    output_lines: list[str] = []

    for r in results:
        if r.error:
            output_lines.append(f"\n{cc.RED}✗ Read error: {r.path} — {r.error}{cc.RESET}")
            continue
        if not r.hit_count and not args.show_clean:
            continue
        output_lines.append(render_file_header(r, use_color))
        if not args.quiet:
            for hit in r.hits:
                output_lines.append(render_hit(hit, use_color))

    output_lines.append(render_summary(results, use_color))

    full_output = "\n".join(output_lines)
    print(full_output)

    if args.output:
        clean = no_color(full_output)
        Path(args.output).write_text(clean, encoding="utf-8")
        print(f"\n{cc.GREEN}Report written → {args.output}{cc.RESET}")

    total_hits = sum(r.hit_count for r in results)
    if args.fail_on_found and total_hits > 0:
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
