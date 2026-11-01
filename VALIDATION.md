# Validation status

Completed on the Windows host:

- Python syntax compilation for all project scripts.
- Forwarding-rule test for the primary and backup routes, checking two directed
  rules per active switch, correct sender egress and no broadcast/flood actions.
- Real localhost UDP sender/receiver test through a UDP relay that deliberately
  dropped six first transmissions out of 30 messages. All 30 unique messages
  arrived and were acknowledged after retransmission.

Completed in the Ubuntu VM (1 November 2026):

- Mininet 2.3.0, Open vSwitch 3.7.1 and Python 3.14.4 installed.
- `mn --switch ovsbr --test pingall`: 0% dropped, 2/2 received.
- Controller forwarding-rule unit test passed in Ubuntu.
- Baseline: all 600 messages received, no retransmissions or packet loss.
- Static failure: 197 of 600 messages received; 403 unrecovered.
- Adaptive failure: all 600 messages received and acknowledged; zero unrecovered.
  13 original transmissions were lost, with 15 retransmissions overall.
- Controller detected the failed path in 95.747 ms and completed rerouting in
  262.600 ms. First post-failure delivery occurred after 271.935 ms.
- Controller events confirm s1--s2--s4 changed to s1--s3--s4; captured OpenFlow
  rules and packet counters confirm forwarding through the backup ports.
- Raw logs and summaries are saved in results/, with comparison.md.

The Mininet results are one real run per scenario. They establish working behavior
for this configured link failure, not statistical performance guarantees or
recovery from every possible network failure.

## Added usability features (not yet executed in the user's VM)

- `interactive_demo.py`: interactive Mininet CLI demonstration; user can manually
  bring the primary link down/up while UDP traffic runs.
- `run-all.sh`: sequential baseline/static/adaptive experiment runner.
- `plot_results.py`: generates charts from real summary.json files.
These additions require execution and validation on the student's Ubuntu VM.
