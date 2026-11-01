#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname "$0")"
for mode in baseline static adaptive; do
  echo "===== Running $mode scenario ====="
  sudo python3 experiment.py --mode "$mode"
done
python3 compare.py
python3 plot_results.py
echo "Finished. See results/comparison.md and results/graphs/."
