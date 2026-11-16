#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="${REVIEWER_PYTHON:-${ROOT}/.venv/bin/python}"
"${PYTHON}" "${ROOT}/analyze.py"
"${PYTHON}" "${ROOT}/validate.py"
