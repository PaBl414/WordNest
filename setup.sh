#!/usr/bin/env sh
set -eu
cd "$(dirname "$0")"
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd frontend
if [ -f package-lock.json ]; then npm ci; else npm install; fi
npm run build
printf '\nGotowe. Uruchom: .venv/bin/python start.py\n'
