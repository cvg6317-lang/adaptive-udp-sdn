"""Generate a comparison report from the latest real run of each scenario."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    runs = {}
    for mode in ['baseline', 'static', 'adaptive']:
        matches = sorted((ROOT/'results').glob(mode+'-*/summary.json'))
        if not matches:
            raise SystemExit('Missing completed scenario: '+mode)
        runs[mode] = json.loads(matches[-1].read_text())
    rows = [('# Project 30 experiment results\n\n'
             'Generated from actual summary.json files in the latest completed '
             'baseline, static and adaptive runs.\n\n'),
            '| Measurement | Baseline | Static failure | Adaptive recovery |\n',
            '|---|---:|---:|---:|\n']
    metrics = [('Unique messages sent', 'unique_sent'),
               ('Unique messages received', 'unique_received'),
               ('Unrecovered messages', 'unrecovered_messages'),
               ('Forward datagram loss (%)', 'forward_datagram_loss_percent'),
               ('Retransmissions', 'retransmissions'),
               ('Mean RTT (ms)', 'mean_rtt_ms'),
               ('Mean one-way latency (ms)', 'mean_one_way_latency_ms'),
               ('Failure detection (ms)', 'controller_detection_ms'),
               ('Reroute completion (ms)', 'reroute_completion_ms'),
               ('First post-failure delivery (ms)', 'first_post_failure_delivery_ms')]
    for label, key in metrics:
        values = [runs[m][key] for m in runs]
        cells = ['N/A' if v is None else f'{v:.3f}' if isinstance(v,float) else str(v)
                 for v in values]
        rows.append('| '+label+' | '+' | '.join(cells)+' |\n')
    rows.append('\nN/A means no applicable event or no recovery was observed. '
                'See README.md for metric definitions and timing limitations. '
                'These are individual runs; repeat them before making statistical claims.\n')
    output = ROOT/'results'/'comparison.md'
    output.write_text(''.join(rows))
    print(output)


if __name__=='__main__': main()
