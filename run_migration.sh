#!/bin/bash
set -euo pipefail
cd /home/atx/temp_atx/atx_plat
python3 -m venv venv >/dev/null 2>&1 || true
source venv/bin/activate
pip install -q -r requirements.txt
export FLASK_APP=app3.py
flask db upgrade
