#!/usr/bin/env python3
"""
Sanad ML CLI Dispatcher / Cross-Platform Makefile Alternative
Supports Windows, Linux, and macOS without requiring GNU make installed.
"""

import sys
import subprocess
import os

COMMANDS = {
    "data-fetch": "ml.src.data.fetch",
    "data-build": "ml.src.data.build_sanad_cert",
    "data-check": "ml.src.data.check_data",
    "train-ocr": "ml.src.train.train_ocr",
    "train-extract": "ml.src.train.train_extract",
    "train-tamper": "ml.src.train.train_tamper",
    "train-fusion": "ml.src.train.train_fusion",
    "eval": "ml.src.eval.run_eval",
    "report": "ml.src.eval.generate_report",
}

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print("Sanad ML CLI Dispatcher:")
        for cmd, mod in COMMANDS.items():
            print(f"  python ml/run.py {cmd:<15} -> python -m {mod}")
        sys.exit(0)

    target = sys.argv[1]
    if target not in COMMANDS:
        print(f"Unknown target: '{target}'. Available: {', '.join(COMMANDS.keys())}")
        sys.exit(1)

    module = COMMANDS[target]
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    cmd = [sys.executable, "-m", module] + sys.argv[2:]
    res = subprocess.run(cmd, env=env)
    sys.exit(res.returncode)

if __name__ == "__main__":
    main()
