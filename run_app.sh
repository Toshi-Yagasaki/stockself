#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

export HOME="$PWD/.streamlit-home"
export STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
export STREAMLIT_SERVER_HEADLESS=true

mkdir -p "$HOME"

if [ -x ".venv/bin/python3" ]; then
    exec .venv/bin/python3 -m streamlit run app.py
fi

exec python3 -m streamlit run app.py
