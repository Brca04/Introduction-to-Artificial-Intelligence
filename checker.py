import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import os
import unicodedata

# ── Cyrillic homoglyphs that visually mimic Latin characters ───────────────
# These are the dangerous substitutions: they look identical but differ in
# Unicode codepoint, which can hide malicious intent in source code.
HOMOGLYPH_MAP = {
    '\u0430': 'a',   # Cyrillic 'а' looks like Latin 'a'
    '\u0435': 'e',   # Cyrillic 'е' looks like Latin 'e'
    '\u0456': 'i',   # Cyrillic 'і' looks like Latin 'i'
    '\u043e': 'o',   # Cyrillic 'о' looks like Latin 'o'
    '\u0441': 'c',   # Cyrillic 'с' looks like Latin 'c'
    '\u0440': 'p',   # Cyrillic 'р' looks like Latin 'p'
    '\u0443': 'y',   # Cyrillic 'у' looks like Latin 'y'
    '\u0445': 'x',   # Cyrillic 'х' looks like Latin 'x'
    '\u042c': 'b',   # Cyrillic 'Ь' can resemble 'b'
}

CYRILLIC_HOMOGLYPHS = set(HOMOGLYPH_MAP.keys())


def _find_comment_start(line):
    """Find the index of '#' that begins a real comment (not inside a string)."""
    in_str = None
    escape = False
    for i, ch in enumerate(line):
        if escape:
            escape = False
            continue
        if ch == '\\' and in_str:
            escape = True
            continue
        if ch in ('"', "'") and not in_str:
            in_str = ch
        elif ch == in_str:
            in_str = None
        elif ch == '#' and not in_str:
            return i
    return None


def scan_for_cyrillic(filepath):
    """
    Scan a Python file for ANY Cyrillic homoglyphs — in code or comments.
    Returns a structured report. A clean file = PASS.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()

    lines = source.splitlines()
    issues = []

    for idx, line in enumerate(lines, start=1):
        for col, ch in enumerate(line):
            if ch in CYRILLIC_HOMOGLYPHS:
                latin_equiv = HOMOGLYPH_MAP[ch]
                codepoint = f'U+{ord(ch):04X}'
                # Determine if it's in a comment or in code
                comment_start = _find_comment_start(line)
                location = "comment" if (comment_start is not None and col > comment_start) else "code"
                issues.append({
                    'line': idx,
                    'col': col + 1,
                    'char': ch,
                    'codepoint': codepoint,
                    'looks_like': latin_equiv,
                    'location': location,
                    'context': line.strip(),
                })

    # Also do a broader sweep: any character in Cyrillic Unicode block
    for idx, line in enumerate(lines, start=1):
        for col, ch in enumerate(line):
            if ch not in CYRILLIC_HOMOGLYPHS and '\u0400' <= ch <= '\u04FF':
                codepoint = f'U+{ord(ch):04X}'
                name = unicodedata.name(ch, 'UNKNOWN')
                comment_start = _find_comment_start(line)
                location = "comment" if (comment_start is not None and col > comment_start) else "code"
                issues.append({
                    'line': idx,
                    'col': col + 1,
                    'char': ch,
                    'codepoint': codepoint,
                    'looks_like': f'(Cyrillic: {name})',
                    'location': location,
                    'context': line.strip(),
                })

    return {
        'filepath': filepath,
        'total_lines': len(lines),
        'pass': len(issues) == 0,
        'issues': issues,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Tkinter GUI
# ═══════════════════════════════════════════════════════════════════════════

class CheckerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cyrillic Homoglyph Injection Detector")
        self.geometry("960x680")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)
        self._build_ui()

    def _build_ui(self):
        # ── Top frame ───────────────────────────────────────────────────
        top = tk.Frame(self, bg="#1e1e2e", pady=10, padx=10)
        top.pack(fill=tk.X)

        tk.Label(
            top, text="Cyrillic Homoglyph Detector",
            font=("Segoe UI", 18, "bold"), fg="#cdd6f4", bg="#1e1e2e"
        ).pack(anchor=tk.W)

        tk.Label(
            top,
            text="Detects hidden Cyrillic characters disguised as Latin in .py files",
            font=("Segoe UI", 10), fg="#a6adc8", bg="#1e1e2e"
        ).pack(anchor=tk.W, pady=(0, 8))

        btn_frame = tk.Frame(top, bg="#1e1e2e")
        btn_frame.pack(fill=tk.X)

        self.path_var = tk.StringVar(value="No file selected")
        tk.Label(
            btn_frame, textvariable=self.path_var, font=("Consolas", 10),
            fg="#a6adc8", bg="#313244", relief=tk.FLAT, padx=8, pady=4
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        tk.Button(
            btn_frame, text="Browse\u2026", command=self._browse,
            font=("Segoe UI", 10, "bold"), bg="#89b4fa", fg="#1e1e2e",
            activebackground="#74c7ec", relief=tk.FLAT, padx=14, pady=4, cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(
            btn_frame, text="\u25b6  Scan File", command=self._run_check,
            font=("Segoe UI", 10, "bold"), bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2d5", relief=tk.FLAT, padx=14, pady=4, cursor="hand2"
        ).pack(side=tk.LEFT)

        # ── Status bar ──────────────────────────────────────────────────
        self.status_var = tk.StringVar(value="Ready \u2014 select a .py file to scan")
        self.status_label = tk.Label(
            self, textvariable=self.status_var, font=("Segoe UI", 11, "bold"),
            fg="#a6adc8", bg="#1e1e2e", pady=4
        )
        self.status_label.pack(fill=tk.X, padx=10)

        # ── Results area ────────────────────────────────────────────────
        self.output = scrolledtext.ScrolledText(
            self, wrap=tk.WORD, font=("Consolas", 10),
            bg="#181825", fg="#cdd6f4", insertbackground="#cdd6f4",
            relief=tk.FLAT, padx=10, pady=10, state=tk.DISABLED
        )
        self.output.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.output.tag_configure("header", foreground="#89b4fa", font=("Consolas", 11, "bold"))
        self.output.tag_configure("pass", foreground="#a6e3a1", font=("Consolas", 12, "bold"))
        self.output.tag_configure("fail", foreground="#f38ba8", font=("Consolas", 12, "bold"))
        self.output.tag_configure("warn", foreground="#fab387")
        self.output.tag_configure("info", foreground="#a6adc8")
        self.output.tag_configure("line_ref", foreground="#f9e2af")
        self.output.tag_configure("detail", foreground="#cdd6f4")

    # ── Actions ─────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select a Python file to scan",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")],
        )
        if path:
            self.path_var.set(path)

    def _run_check(self):
        filepath = self.path_var.get()
        if not filepath or filepath == "No file selected":
            messagebox.showwarning("No file", "Please select a .py file first.")
            return
        if not os.path.isfile(filepath):
            messagebox.showerror("Error", f"File not found:\n{filepath}")
            return

        try:
            report = scan_for_cyrillic(filepath)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to scan file:\n{exc}")
            return

        self._display_report(report)

    def _display_report(self, report):
        out = self.output
        out.configure(state=tk.NORMAL)
        out.delete("1.0", tk.END)

        out.insert(tk.END, "\u2550" * 70 + "\n", "header")
        out.insert(tk.END, "  CYRILLIC HOMOGLYPH SCAN REPORT\n", "header")
        out.insert(tk.END, "\u2550" * 70 + "\n\n", "header")

        out.insert(tk.END, f"  File:   {report['filepath']}\n", "info")
        out.insert(tk.END, f"  Lines:  {report['total_lines']}\n\n", "info")

        if report['pass']:
            # ── CLEAN: no Cyrillic found ────────────────────────────────
            out.insert(tk.END, "  \u2705  CLEAN \u2014 No Cyrillic homoglyphs detected\n\n", "pass")
            out.insert(tk.END, "  This file contains no hidden Cyrillic character\n", "info")
            out.insert(tk.END, "  substitutions. It is safe from this class of\n", "info")
            out.insert(tk.END, "  homoglyph injection.\n\n", "info")
            self.status_var.set("\u2705 CLEAN \u2014 no Cyrillic homoglyphs found")
            self.status_label.configure(fg="#a6e3a1")
        else:
            # ── INFECTED: Cyrillic found ────────────────────────────────
            n = len(report['issues'])
            out.insert(tk.END, f"  \u26a0\ufe0f  ALERT \u2014 {n} Cyrillic homoglyph(s) detected!\n\n", "fail")
            self.status_var.set(f"\u26a0\ufe0f ALERT \u2014 {n} hidden Cyrillic character(s) found")
            self.status_label.configure(fg="#f38ba8")

            # Group by location (code vs comment)
            in_code = [i for i in report['issues'] if i['location'] == 'code']
            in_comments = [i for i in report['issues'] if i['location'] == 'comment']

            if in_code:
                out.insert(tk.END, "\u2500" * 60 + "\n", "info")
                out.insert(tk.END, f"  \u26d4 Cyrillic in CODE ({len(in_code)}) \u2014 HIGH RISK\n", "fail")
                out.insert(tk.END, "\u2500" * 60 + "\n", "info")
                for iss in in_code:
                    out.insert(tk.END, f"  Line {iss['line']:>4}, Col {iss['col']:>3}: ", "line_ref")
                    out.insert(
                        tk.END,
                        f"'{iss['char']}' ({iss['codepoint']}) looks like Latin '{iss['looks_like']}'\n",
                        "detail",
                    )
                out.insert(tk.END, "\n")

            if in_comments:
                out.insert(tk.END, "\u2500" * 60 + "\n", "info")
                out.insert(tk.END, f"  \u26a0  Cyrillic in COMMENTS ({len(in_comments)})\n", "warn")
                out.insert(tk.END, "\u2500" * 60 + "\n", "info")
                for iss in in_comments:
                    out.insert(tk.END, f"  Line {iss['line']:>4}, Col {iss['col']:>3}: ", "line_ref")
                    out.insert(
                        tk.END,
                        f"'{iss['char']}' ({iss['codepoint']}) looks like Latin '{iss['looks_like']}'\n",
                        "detail",
                    )
                out.insert(tk.END, "\n")

        # ── Legend ──────────────────────────────────────────────────────
        out.insert(tk.END, "\u2500" * 60 + "\n", "info")
        out.insert(tk.END, "  What this checks:\n", "header")
        out.insert(tk.END, "  Scans for Cyrillic Unicode chars that are visually\n", "info")
        out.insert(tk.END, "  identical to Latin letters (homoglyphs). These are\n", "info")
        out.insert(tk.END, "  used in prompt-injection attacks to hide proof that\n", "info")
        out.insert(tk.END, "  code was AI-generated or tampered with.\n", "info")
        out.insert(tk.END, "\u2500" * 60 + "\n", "info")

        out.configure(state=tk.DISABLED)


if __name__ == "__main__":
    app = CheckerApp()
    app.mainloop()
