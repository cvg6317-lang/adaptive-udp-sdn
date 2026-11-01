"""UDP selective-repeat sender and duplicate-safe acknowledging receiver."""
import argparse
import json
import socket
import time
from pathlib import Path


def save(path, value):
    Path(path).write_text(json.dumps(value, indent=2))


def receive(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    sock.settimeout(0.2)
    seen = set()
    events = []
    deadline = time.monotonic() + args.duration
    while time.monotonic() < deadline:
        try:
            data, peer = sock.recvfrom(4096)
        except socket.timeout:
            continue
        try:
            msg = json.loads(data)
            seq = int(msg['seq'])
        except (ValueError, KeyError, TypeError):
            continue
        now = time.monotonic()
        events.append(dict(time=now, seq=seq, attempt=msg['attempt'],
                           duplicate=seq in seen,
                           one_way_ms=(now-msg['sent'])*1000))
        seen.add(seq)
        sock.sendto(json.dumps(dict(seq=seq, sent=msg['sent'],
                                   attempt=msg['attempt'])).encode(), peer)
    sock.close()
    save(args.output, dict(unique_received=len(seen), events=events))


def send(args):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.connect((args.host, args.port))
    sock.settimeout(0.005)
    pending = {}
    events = []
    acked = set()
    first_acks = set()
    start = time.monotonic()
    next_send = start
    seq = 0
    deadline = start + args.count*args.interval + args.grace
    while time.monotonic() < deadline and len(acked) < args.count:
        now = time.monotonic()
        if seq < args.count and now >= next_send:
            pending[seq] = dict(last=0, attempts=0)
            seq += 1
            next_send += args.interval
        for number, state in list(pending.items()):
            if now-state['last'] >= args.timeout:
                state['attempts'] += 1
                state['last'] = now
                msg = dict(seq=number, sent=now, attempt=state['attempts'])
                sock.send(json.dumps(msg).encode())
                events.append(dict(type='send', time=now, seq=number,
                                   attempt=state['attempts']))
        try:
            reply = json.loads(sock.recv(4096))
        except (socket.timeout, ConnectionRefusedError):
            continue
        now = time.monotonic()
        number = reply['seq']
        if number not in acked:
            acked.add(number)
            pending.pop(number, None)
            if reply['attempt'] == 1:
                first_acks.add(number)
            events.append(dict(type='ack', time=now, seq=number,
                               attempt=reply['attempt'],
                               rtt_ms=(now-reply['sent'])*1000))
    sock.close()
    save(args.output, dict(requested=args.count, sent_unique=seq,
                          acknowledged=len(acked), first_attempt_acked=len(first_acks),
                          unrecovered=sorted(set(range(args.count))-acked), events=events))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['send', 'receive'])
    p.add_argument('--host', default='10.0.0.2')
    p.add_argument('--port', type=int, default=9000)
    p.add_argument('--count', type=int, default=600)
    p.add_argument('--interval', type=float, default=0.02)
    p.add_argument('--timeout', type=float, default=0.25)
    p.add_argument('--grace', type=float, default=8)
    p.add_argument('--duration', type=float, default=23)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    (send if a.mode == 'send' else receive)(a)
