#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

echo "Formatting imports (isort)"
isort covid_graphs/ --apply --recursive

echo "Formatting code (black)"
black covid_graphs/
