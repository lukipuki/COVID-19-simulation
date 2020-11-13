#!/bin/bash
set -euo pipefail

rm -rf .venv
python3.7 -m venv --system-site-packages .venv

source .venv/bin/activate
pip install -r dev_requirements.txt
pip install -e covid_graphs
pip install -e covid_web

set +o nounset
deactivate
set -o nounset

echo -e "\n✅  Success, virtualenv created! Activate it by running:\n\tsource .venv/bin/activate"
