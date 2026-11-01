# Adaptive Communication Network with Failure Recovery

Project 30 - SDN and UDP socket programming

## Objective

Maintain UDP application delivery when the active network path fails, using a
centralized SDN control application to reroute traffic and application-level
retransmissions to recover missing messages.

## Implementation

The recorded reference experiment was run in an Ubuntu 26.04 VirtualBox VM with
Mininet 2.3.0, Open vSwitch 3.7.1 and Python 3.14.4. This is the environment
reported by the supplied experiment logs; it is not a claim about the student's
Ubuntu 25.04 VM. Re-run the experiments on the submission VM and update this
environment description with the actual version output. Two hosts communicate across a four-switch diamond. Both alternative
paths have four links between hosts, with 10 Mbps bandwidth and 5 ms delay per
link. The primary switch path is s1--s2--s4; the backup is s1--s3--s4.

udp_app.py uses UDP sockets to send 600 numbered messages at 20 ms intervals.
The receiver acknowledges datagrams and records each sequence only once as a
delivered message. The sender retries pending messages after 250 ms and has a
finite deadline for unrecoverable failures.

controller.py is a separate local control process. It receives the configured
topology and port map, polls OVS link state, selects an available path and uses
ovs-ofctl to install explicit OpenFlow 1.3 rules in both directions. Static ARP
entries and explicit outputs prevent broadcast loops. This implementation uses
OVS management tools; it does not depend on Ryu or ONOS.

experiment.py starts the network and applications, then disables s2--s4 after
four seconds. The control process independently detects the failure. The
experiment does not command the controller to select the backup route.

## Experiments and actual results

Tests were executed in the Ubuntu VM on 1 November 2026. Each row is one run.

| Scenario | Unique sent | Unique received | Unrecovered | Retransmissions | Mean RTT |
|---|---:|---:|---:|---:|---:|
| Baseline, no failure | 600 | 600 | 0 | 0 | 49.285 ms |
| Failure, fixed route | 600 | 197 | 403 | 18,740 | 48.059 ms |
| Failure, adaptive route | 600 | 600 | 0 | 15 | 45.316 ms |

In the adaptive run, detection took 95.747 ms, rule installation completed
262.600 ms after failure started, and the first message transmitted after the
failure operation arrived at 271.935 ms. Thirteen original datagrams were lost;
application retries recovered all messages. Forward loss over all datagram
attempts, including retries, was 2.276%. Mean delivered-datagram one-way latency
was 22.573 ms.

Controller events show the path changing from s1--s2--s4 to s1--s3--s4.
Captured flow rules show h1 traffic leaving s1 on port 3 and reverse traffic
leaving s4 on port 2, matching the backup topology. Packet counters are nonzero.

## Interpretation

The baseline confirms ordinary UDP delivery. The fixed-route test demonstrates
that retransmission alone cannot overcome a permanently broken route. Adaptive
routing restores connectivity; retransmission then recovers messages lost during
the transition. All 600 unique messages were ultimately delivered in that run.

The lower adaptive mean RTT is run-to-run variation, not evidence that a failure
improves latency. RTT and latency averages include delivered packets only.

## Demonstration

Open a terminal in the installed VM:

```bash
cd ~/project30
bash run-demo.sh
```

The program creates the diamond network, sends UDP messages, prints the primary
link failure, and displays the measured summary. Raw logs are retained under
results/. To repeat the comparison, run the three commands in README.md and then
run `python3 compare.py`.

## Limitations

The topology is configured rather than discovered using LLDP. Link state is
polled; controller execution and polling add detection delay. Rule changes are
sequential and can temporarily lose packets. UDP retries have a finite deadline.
The test covers a primary inter-switch link failure, not host failures, controller
failures, or simultaneous loss of both routes. One-way timing relies on Mininet
hosts sharing one kernel clock. Multiple repetitions are needed for statistical
performance conclusions.

## References

- Mininet walkthrough: https://mininet.org/walkthrough/
- OVS OpenFlow tools: https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html

## Reproduction note for submission

The ZIP's `results/` folder contains the supplied reference run logs. These are
useful for understanding expected output, but students must rerun baseline,
static and adaptive modes on their own configured VM. Replace the environment
description and results table with those newly generated measurements if they
differ. Do not claim the supplied reference run was performed on Ubuntu 25.04.
