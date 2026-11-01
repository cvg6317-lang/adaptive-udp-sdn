#!/usr/bin/env python3
"""Plot actual metrics from the latest completed baseline/static/adaptive runs."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
MODES = ["baseline", "static", "adaptive"]
LABELS = ["Baseline", "Static failure", "Adaptive recovery"]

def latest(mode):
    files = sorted((ROOT / "results").glob(mode + "-*/summary.json"))
    if not files:
        raise SystemExit(f"Missing completed {mode} result. Run experiment.py --mode {mode} first.")
    return json.loads(files[-1].read_text())

def main():
    data = [latest(m) for m in MODES]
    out = ROOT / "results" / "graphs"
    out.mkdir(parents=True, exist_ok=True)
    charts = [
        ("unique_received", "Unique UDP messages received", "Messages", "delivery.png"),
        ("unrecovered_messages", "Unrecovered UDP messages", "Messages", "unrecovered.png"),
        ("forward_datagram_loss_percent", "Forward datagram loss", "Loss (%)", "packet_loss.png"),
        ("mean_rtt_ms", "Mean acknowledged UDP RTT", "RTT (ms)", "rtt.png"),
    ]
    for key, title, ylabel, filename in charts:
        vals = [d.get(key) for d in data]
        if all(v is None for v in vals):
            continue
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar(LABELS, [0 if v is None else v for v in vals])
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(axis="x", rotation=10)
        fig.tight_layout()
        fig.savefig(out / filename, dpi=160)
        plt.close(fig)
    # Recovery timings are only meaningful for the adaptive run.
    adaptive = data[2]
    keys = [("controller_detection_ms", "Detection"),
            ("reroute_completion_ms", "Rule installation"),
            ("first_post_failure_delivery_ms", "First post-failure delivery")]
    present = [(label, adaptive.get(key)) for key, label in keys if adaptive.get(key) is not None]
    if present:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.bar([x[0] for x in present], [x[1] for x in present])
        ax.set_title("Adaptive recovery timeline")
        ax.set_ylabel("Time from failure start (ms)")
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(axis="x", rotation=10)
        fig.tight_layout()
        fig.savefig(out / "recovery_timeline.png", dpi=160)
        plt.close(fig)
    print(f"Charts written to {out}")

if __name__ == "__main__":
    main()
