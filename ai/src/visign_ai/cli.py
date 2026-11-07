# ai/src/visign_ai/cli.py
"""Cau hinh output cho CLI tren Windows va UTF-8."""

import sys


def make_console_output_safe() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")
