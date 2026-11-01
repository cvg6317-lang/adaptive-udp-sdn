"""Run a real Mininet diamond with UDP, timed failure and independent controller."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.log import setLogLevel

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--mode', choices=['baseline', 'static', 'adaptive'], default='adaptive')
    args = p.parse_args()
    out = ROOT/'results'/(args.mode+'-'+time.strftime('%Y%m%d-%H%M%S'))
    out.mkdir(parents=True)
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, build=False)
    procs = []
    files = []
    try:
        h1 = net.addHost('h1', ip='10.0.0.1/24', mac='00:00:00:00:00:01')
        h2 = net.addHost('h2', ip='10.0.0.2/24', mac='00:00:00:00:00:02')
        switches = {s: net.addSwitch(s, protocols='OpenFlow13', failMode='secure')
                    for s in ['s1', 's2', 's3', 's4']}
        nodes = dict(switches, h1=h1, h2=h2)
        edges = [('h1','s1'), ('s1','s2'), ('s2','s4'),
                 ('s1','s3'), ('s3','s4'), ('s4','h2')]
        config = dict(ports={s:{} for s in switches}, interfaces={s:{} for s in switches})
        for a,b in edges:
            link = net.addLink(nodes[a], nodes[b], bw=10, delay='5ms')
            for x,y,intf in [(a,b,link.intf1),(b,a,link.intf2)]:
                if x in switches:
                    config['ports'][x][y] = nodes[x].ports[intf]
                    config['interfaces'][x][y] = intf.name
        net.build()
        net.start()
        h1.setARP('10.0.0.2', h2.MAC())
        h2.setARP('10.0.0.1', h1.MAC())
        (out/'topology.json').write_text(json.dumps(config, indent=2))
        log = open(out/'controller-console.log', 'w'); files.append(log)
        ctl = subprocess.Popen([sys.executable, str(ROOT/'controller.py'),
                                '--config', str(out/'topology.json'), '--output', str(out/'controller.jsonl'),
                                '--stop', str(out/'stop')]+(['--static'] if args.mode=='static' else []),
                               stdout=log, stderr=subprocess.STDOUT)
        procs.append(ctl)
        deadline = time.monotonic()+15
        while not (out/'controller.jsonl').exists() or not (out/'controller.jsonl').stat().st_size:
            if ctl.poll() is not None or time.monotonic()>deadline:
                raise RuntimeError('Controller did not initialize; see controller-console.log')
            time.sleep(0.1)
        for host, mode in [(h2,'receive'),(h1,'send')]:
            log = open(out/(mode+'-console.log'), 'w'); files.append(log)
            proc = host.popen([sys.executable, str(ROOT/'udp_app.py'), mode,
                               '--output', str(out/(mode+'.json'))], stdout=log, stderr=subprocess.STDOUT)
            procs.append(proc)
            if mode=='receive': time.sleep(0.3)
        sender = procs[-1]
        time.sleep(4)
        event = dict(mode=args.mode, failure=None)
        if args.mode!='baseline':
            event['failure'] = time.monotonic()
            net.configLinkStatus('s2','s4','down')
            event['failure_applied'] = time.monotonic()
            print('PRIMARY LINK DOWN: s2 -- s4', flush=True)
        (out/'experiment.json').write_text(json.dumps(event, indent=2))
        sender.wait(timeout=25)
        procs[-2].wait(timeout=25)
        if sender.returncode or procs[-2].returncode:
            raise RuntimeError('UDP process failed; inspect console logs')
        (out/'stop').touch()
        ctl.wait(timeout=10)
        subprocess.run([sys.executable, str(ROOT/'report.py'), str(out)], check=True)
        for sw in switches:
            (out/(sw+'-flows.txt')).write_text(subprocess.check_output(
                ['ovs-ofctl','-O','OpenFlow13','dump-flows',sw], text=True))
        print('Results:', out)
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.terminate()
                try: proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    proc.kill(); proc.wait()
        net.stop()
        for f in files: f.close()


if __name__=='__main__':
    setLogLevel('info')
    main()
