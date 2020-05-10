#!/bin/bash
set -euo pipefail

if [[ "${VIRTUAL_ENV:-}" == "" ]]
then
    echo "⚠️  Running outside of a virtual environment."
fi

PYTHON_PACKAGES=(covid_graphs covid_web)

for PYTHON_PACKAGE in "${PYTHON_PACKAGES[@]}"
do
   echo "☞  Running on ${PYTHON_PACKAGE}"
   echo "Formatting imports (isort)"
   isort --apply --recursive $PYTHON_PACKAGE
   
   echo "Formatting code (black)"
   black $PYTHON_PACKAGE
done
