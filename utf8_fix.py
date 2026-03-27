"""
utf8_fix.py — Corrige encoding UTF-8 no terminal Windows.

Importe este módulo ANTES de qualquer output no terminal.
"""

import sys
import os

if sys.platform == "win32":
    # Força o terminal Windows a usar UTF-8
    os.system("chcp 65001 > nul 2>&1")
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    # Garante que PYTHONUTF8 esteja ativo
    os.environ["PYTHONUTF8"] = "1"
