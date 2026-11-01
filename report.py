import json
import statistics
import sys
from pathlib import Path


def report(folder):
    out = Path(folder)
    sent = json.loads((out/'send.json').read_text())
    received = json.loads((out/'receive.json').read_text())
    exp = json.loads((out/'experiment.json').read_text())
    control = [json.loads(line) for line in (out/'controller.jsonl').read_text().splitlines()]
    tx = [e for e in sent['events'] if e['type']=='send']
    ack = [e for e in sent['events'] if e['type']=='ack']
    rx = received['events']
    failure = exp['failure']
    # Receiver time minus measured one-way delay reconstructs transmission time.
    after = [e for e in rx if failure is not None and
             e['time']-e['one_way_ms']/1000 >= exp['failure_applied']]
    switch = next((c for c in control if failure is not None and c['detected'] >= failure
                   and c['path'] == ['s1','s3','s4']), None)
    result = dict(mode=exp['mode'], unique_sent=sent['sent_unique'],
                  unique_received=received['unique_received'],
                  acknowledged=sent['acknowledged'],
                  transmissions=len(tx), received_datagrams=len(rx),
                  forward_datagram_loss_percent=100*(len(tx)-len(rx))/len(tx) if tx else None,
                  first_transmission_loss_count=sent['sent_unique']-sum(e['attempt']==1 for e in rx),
                  retransmissions=sum(e['attempt']>1 for e in tx),
                  unrecovered_messages=sent['sent_unique']-received['unique_received'],
                  mean_rtt_ms=statistics.mean(e['rtt_ms'] for e in ack) if ack else None,
                  mean_one_way_latency_ms=statistics.mean(e['one_way_ms'] for e in rx) if rx else None,
                  controller_detection_ms=(switch['detected']-failure)*1000 if switch else None,
                  reroute_completion_ms=(switch['installed']-failure)*1000 if switch else None,
                  first_post_failure_delivery_ms=(min(e['time'] for e in after)-failure)*1000 if after else None)
    (out/'summary.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    return result


if __name__=='__main__': report(sys.argv[1])
