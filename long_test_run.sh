#!/usr/bin/env bash

# Arg 1 = input file
# Arg 2 = runtime

# Move/link to ./run and chmod +x OR edit PYTHONPATH to actual project root.

export DEBUG=True
export NO_SHOW=True
export PYTHONPATH=..

IN_FILE="$1"
OUT_FILE="${IN_FILE%.*}.out.csv"
LOG_FILE="${IN_FILE%.*}.log"

python -m CarSharing "${IN_FILE}" "${OUT_FILE}" "$2" 42 1 2>&1 | tee "${LOG_FILE}"
