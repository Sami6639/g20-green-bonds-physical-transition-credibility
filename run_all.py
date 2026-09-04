from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SCRIPTS = [
    ROOT / "code" / "00_preflight.py",
    ROOT / "code" / "01_build_panel.py",
    ROOT / "code" / "02_analyze.py",
    ROOT / "code" / "03_verify.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"Running {script.name}", flush=True)
        subprocess.run([sys.executable, str(script)], cwd=ROOT, check=True)
    print("REPRODUCIBILITY PIPELINE PASS", flush=True)


if __name__ == "__main__":
    main()
