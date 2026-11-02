"""
Sanad ML Experiment Tracker
Logs all runs (hyperparameters, dataset versions, commit hashes, hardware specs, duration, and metrics)
to a reproducible local ledger (ml/eval/experiments.jsonl) with optional MLflow interoperability.
"""

import os
import sys
import json
import time
import socket
import platform
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

EXPERIMENTS_LOG_PATH = Path("ml/eval/experiments.jsonl")

def get_git_commit_hash() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unversioned-local-commit"

def get_system_hardware_info() -> Dict[str, Any]:
    info = {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "processor": os.environ.get("PROCESSOR_IDENTIFIER", platform.processor()),
        "logical_cpus": os.cpu_count() or 1,
        "python_version": sys.version.split()[0],
    }
    return info

class ExperimentRun:
    def __init__(self, run_name: str, config: Dict[str, Any], data_version: str = "v1.0.0"):
        self.run_name = run_name
        self.config = config
        self.data_version = data_version
        self.start_time = time.time()
        self.run_id = f"{run_name}_{int(self.start_time)}"
        self.metrics: Dict[str, float] = {}
        self.artifacts: Dict[str, str] = {}
        self.status = "RUNNING"
        self.commit_hash = get_git_commit_hash()
        self.hardware = get_system_hardware_info()

    def log_metric(self, name: str, value: float):
        self.metrics[name] = float(value)

    def log_metrics(self, metrics: Dict[str, float]):
        for k, v in metrics.items():
            self.log_metric(k, v)

    def log_artifact(self, name: str, path: str):
        self.artifacts[name] = str(path)

    def finish(self, status: str = "COMPLETED"):
        self.status = status
        duration = round(time.time() - self.start_time, 2)
        record = {
            "run_id": self.run_id,
            "run_name": self.run_name,
            "status": self.status,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
            "duration_seconds": duration,
            "commit_hash": self.commit_hash,
            "data_version": self.data_version,
            "hardware": self.hardware,
            "config": self.config,
            "metrics": self.metrics,
            "artifacts": self.artifacts,
        }
        EXPERIMENTS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(EXPERIMENTS_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
        return record
