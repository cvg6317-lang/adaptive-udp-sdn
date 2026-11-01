"""Local SDN control process: poll OVS link status and install OpenFlow rules.

Topology and port map are supplied by the experiment, not discovered via LLDP.
No NORMAL/flood actions are used, so the diamond cannot create a broadcast loop.
"""
import json
import subprocess
import time
from pathlib import Path


def command(*args):
    return subprocess.check_output(args, text=True, timeout=5).strip()


def up(interface):
    # Both administrative and carrier state are checked independently.
    return (command('ovs-vsctl', 'get', 'Interface', interface, 'admin_state') == 'up'
            and command('ovs-vsctl', 'get', 'Interface', interface, 'link_state') == 'up')


def install(path, ports):
    for switch in ('s1', 's2', 's3', 's4'):
        command('ovs-ofctl', '-O', 'OpenFlow13', 'del-flows', switch)
    # Configure transit switches first; ingress is switched last.
    for switch in path[1:-1] + [path[-1], path[0]]:
        for src, dst, route in [('10.0.0.1', '10.0.0.2', path),
                                ('10.0.0.2', '10.0.0.1', list(reversed(path)))]:
            i = route.index(switch)
            neighbor = route[i+1] if i+1 < len(route) else ('h2' if dst.endswith('.2') else 'h1')
            output = ports[switch][neighbor]
            command('ovs-ofctl', '-O', 'OpenFlow13', 'add-flow', switch,
                    f'priority=100,ip,nw_src={src},nw_dst={dst},actions=output:{output}')


def run(config, output, stop, adaptive=True, poll=0.1):
    data = json.loads(Path(config).read_text())
    routes = [['s1', 's2', 's4'], ['s1', 's3', 's4']]
    current = None
    with open(output, 'w', buffering=1) as log:
        while not Path(stop).exists():
            available = []
            for route in routes:
                available.append(all(up(data['interfaces'][a][b]) and
                                     up(data['interfaces'][b][a])
                                     for a, b in zip(route, route[1:])))
            chosen = next((r for r, ok in zip(routes, available) if ok), None)
            if current is None or adaptive:
                if chosen != current:
                    detected = time.monotonic()
                    if chosen is not None:
                        install(chosen, data['ports'])
                    else:
                        for sw in data['ports']:
                            command('ovs-ofctl', '-O', 'OpenFlow13', 'del-flows', sw)
                    current = chosen
                    log.write(json.dumps(dict(detected=detected, installed=time.monotonic(),
                                              path=chosen, available=available))+'\n')
            time.sleep(poll)


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--config', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--stop', required=True)
    p.add_argument('--static', action='store_true')
    a = p.parse_args()
    run(a.config, a.output, a.stop, not a.static)
