#!/usr/bin/env python3
"""Guard: apply --hermes-home <empty dir> must not change the live ~/.hermes tree."""
from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

LIVE = (Path.home() / ".hermes").expanduser()
ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "scripts" / "baseline.py"

WATCH = [
    LIVE / "config.yaml",
    LIVE / ".env",
    LIVE / "SOUL.md",
    LIVE / "profiles" / "side" / "config.yaml",
    LIVE / "profiles" / "side" / ".env",
    LIVE / "hermes-agent" / "plugins" / "web" / "anysearch" / "provider.py",
    LIVE / "hermes-agent" / "hermes_cli" / "commands.py",
    LIVE / "hermes-agent" / "agent" / "display.py",
]


def digest(path: Path) -> str:
    if not path.is_file():
        return "MISSING"
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    before = {str(p): digest(p) for p in WATCH}
    scratch = Path(tempfile.mkdtemp(prefix="hts-iso-"))
    env = {**os.environ, "HERMES_HOME": str(scratch), "HERMES_TW_ISOLATED": "1"}
    r = subprocess.run(
        [sys.executable, str(BASELINE), "apply", "--hermes-home", str(scratch), "--yes"],
        capture_output=True,
        text=True,
        timeout=180,
        env=env,
    )
    after = {str(p): digest(p) for p in WATCH}
    changed = [p for p in before if before[p] != after[p]]
    print(r.stdout[-2000:] if r.stdout else "")
    if r.stderr:
        print(r.stderr[-1000:], file=sys.stderr)
    if changed:
        print("FAIL: live files changed:", *changed, sep="\n  ")
        return 1
    print(f"OK: live ~/.hermes unchanged; scratch={scratch} apply_code={r.returncode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
