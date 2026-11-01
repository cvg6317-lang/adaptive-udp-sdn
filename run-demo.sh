#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
sudo python3 experiment.py --mode adaptive
