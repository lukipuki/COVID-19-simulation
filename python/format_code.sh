#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

PYTHON_PACKAGES=(covid_graphs covid_web)

echo "Formatting imports (isort)"
isort --apply --recursive "${PYTHON_PACKAGES[@]}"

echo "Formatting code (black)"
black "${PYTHON_PACKAGES[@]}"
