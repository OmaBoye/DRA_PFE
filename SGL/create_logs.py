# create_logs.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / 'logs'

LOGS_DIR.mkdir(exist_ok=True)
(LOGS_DIR / 'analysis.log').touch()
(LOGS_DIR / 'debug.log').touch()

print(f"Created log files in {LOGS_DIR}")