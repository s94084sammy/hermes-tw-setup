#!/usr/bin/env python3
"""Wrapper: implementation lives in scripts/generate.py."""
from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).resolve().parent / "scripts" / "generate.py"), run_name="__main__")
