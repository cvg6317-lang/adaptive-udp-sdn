# Project 30 experiment results

Generated from actual summary.json files in the latest completed baseline, static and adaptive runs.

| Measurement | Baseline | Static failure | Adaptive recovery |
|---|---:|---:|---:|
| Unique messages sent | 600 | 600 | 600 |
| Unique messages received | 600 | 197 | 600 |
| Unrecovered messages | 0 | 403 | 0 |
| Forward datagram loss (%) | 0.000 | 98.981 | 2.276 |
| Retransmissions | 0 | 18740 | 15 |
| Mean RTT (ms) | 49.285 | 48.059 | 45.316 |
| Mean one-way latency (ms) | 24.650 | 24.146 | 22.573 |
| Failure detection (ms) | N/A | N/A | 95.747 |
| Reroute completion (ms) | N/A | N/A | 262.600 |
| First post-failure delivery (ms) | N/A | N/A | 271.935 |

N/A means no applicable event or no recovery was observed. See README.md for metric definitions and timing limitations. These are individual runs; repeat them before making statistical claims.
