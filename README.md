# Project 30: Adaptive Communication Network with Failure Recovery

Run inside an Ubuntu VM. Physical switches are unnecessary: **`experiment.py` is the
network simulation**. It creates a real Mininet emulation (Linux network namespaces,
virtual Ethernet links and Open vSwitch datapaths), not just a diagram or a mocked
network. `run-demo.sh` runs the adaptive failure scenario automatically. There is
also a manual interactive demo (`interactive_demo.py`) where you can issue link
failure/recovery commands at the Mininet CLI.

Installation and all three experiments have been verified in the Ubuntu VM.
See PROJECT_REPORT.md for the explanation, VALIDATION.md for checks, and
results/comparison.md for the actual measured comparison. Run the failure-recovery
demo with `bash run-demo.sh` from this folder.

## Install and run

From this folder in Ubuntu:

```bash
bash install.sh
sudo python3 experiment.py --mode baseline
sudo python3 experiment.py --mode static
sudo python3 experiment.py --mode adaptive
sudo python3 interactive_demo.py
python3 compare.py
python3 plot_results.py
```

Do not run simultaneous experiments or use this while another Mininet network is
active. After an interrupted run, `sudo mn -c` removes residual Mininet resources.

## Network

```
           s2
          /  \
h1 ---- s1    s4 ---- h2
          \  /
           s3
```

Two hosts, four OpenFlow 1.3 switches, two alternative paths, 10 Mbps links and
5 ms delay per link. Static ARP entries avoid broadcast loops. h1 sends 600
numbered UDP messages to h2, one every 20 ms. The receiver acknowledges every
datagram and delivers each sequence only once. Pending messages retry after
250 ms; the sender stops after a finite grace period if a route never recovers.

## Independent SDN control process

controller.py receives the known topology/port map, polls OVS administrative and
carrier status at roughly 100 ms plus command execution time, chooses an available
path, and programs OpenFlow forwarding rules through ovs-ofctl. It is a local
centralized SDN control application, not a Ryu/ONOS remote-controller framework.
Ask your instructor if a particular controller framework is mandatory. This
prototype monitors links in its configured topology; it does not use LLDP for
arbitrary topology discovery. Rules use explicit outputs and never flood the loop.

At four seconds the experiment disables s2--s4. The control process independently
detects the change; the experiment never instructs it to reroute. Rule updates
are sequential, not atomic, so a short interruption is expected.

## Comparison experiments

- baseline: no link failure; establishes normal delay and delivery.
- static: link fails; controller retains the original rules, showing the failure
  without adaptive routing. Application retries eventually time out.
- adaptive: same failure; controller chooses s1--s3--s4 and retransmission recovers
  lost messages. Repeat each scenario to account for timing variation.

## Evidence and metrics

Each run creates a timestamped results folder with raw sender/receiver JSON,
controller route events, topology, failure timestamps, switch flow dumps and
summary.json. No measurements are fabricated or prefilled.

- Forward datagram loss includes original packets and retransmissions; reverse
  ACK loss is separate from this metric.
- First-transmission loss counts original datagrams absent at the receiver.
- Unrecovered messages counts unique messages still absent after all retries.
- RTT measures an acknowledged attempt; it is not one-way latency.
- One-way latency uses the shared monotonic clock of Mininet namespaces on the
  same kernel. This measurement method cannot be used unchanged across machines.
- Detection and rule-install times are relative to the start of the failure
  operation. Delivery recovery is the first arrival sent after failure completes;
  it includes scheduling, packet pacing and propagation, not just controller time.
- Latency averages cover delivered datagrams; they exclude undelivered packets.

## Demonstration and submission

Explain the topology, run the three experiments, show the primary link-down
message, inspect controller.jsonl for the backup path, and compare summary.json.
Submit source code, setup commands, topology diagram, real logs, results table
and a report explaining UDP recovery, SDN rerouting, and limitations. The supplied
assignment does not specify a submission template.

References: https://mininet.org/walkthrough/ and
https://www.openvswitch.org/support/dist-docs/ovs-ofctl.8.html

## Visual results

After all three scenarios have completed, run `python3 plot_results.py`.
It reads the actual latest `summary.json` files and writes PNG charts under
`results/graphs/`. It does not invent or prepopulate measurement values.

## Interactive simulation

`interactive_demo.py` creates the same Mininet diamond and starts the independent
controller plus UDP receiver. At the Mininet prompt, start a sender with:

```text
mininet> h1 python3 /absolute/path/to/project30/udp_app.py send --output /tmp/manual-send.json --count 600 --interval 0.02
```

While it runs, type `link s2 s4 down` to fail the primary route. The controller
should detect the unavailable link and switch to s1-s3-s4. Restore it with
`link s2 s4 up`. The receiver logs to `/tmp/manual-receive.json`. Exit with
`exit`; the script stops background processes and Mininet.
