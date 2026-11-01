#!/usr/bin/env python3
"""Interactive Mininet demo: manually fail/restore primary link while UDP runs."""
import json, subprocess, sys, time
from pathlib import Path
from mininet.net import Mininet
from mininet.node import OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel

ROOT = Path(__file__).resolve().parent

def main():
    net = Mininet(controller=None, switch=OVSSwitch, link=TCLink, build=False)
    procs, logs = [], []
    work = Path("/tmp/project30-manual")
    work.mkdir(exist_ok=True)
    stop = work / "stop"
    if stop.exists(): stop.unlink()
    try:
        h1 = net.addHost("h1", ip="10.0.0.1/24", mac="00:00:00:00:00:01")
        h2 = net.addHost("h2", ip="10.0.0.2/24", mac="00:00:00:00:00:02")
        sw = {n: net.addSwitch(n, protocols="OpenFlow13", failMode="secure")
              for n in ("s1","s2","s3","s4")}
        nodes = dict(sw, h1=h1, h2=h2)
        edges = [("h1","s1"),("s1","s2"),("s2","s4"),
                 ("s1","s3"),("s3","s4"),("s4","h2")]
        cfg = {"ports":{n:{} for n in sw}, "interfaces":{n:{} for n in sw}}
        for a,b in edges:
            link=net.addLink(nodes[a],nodes[b],bw=10,delay="5ms")
            for x,y,intf in ((a,b,link.intf1),(b,a,link.intf2)):
                if x in sw:
                    cfg["ports"][x][y]=nodes[x].ports[intf]
                    cfg["interfaces"][x][y]=intf.name
        net.build(); net.start()
        h1.setARP("10.0.0.2",h2.MAC()); h2.setARP("10.0.0.1",h1.MAC())
        config=work/"topology.json"; config.write_text(json.dumps(cfg))
        ctl_log=open(work/"controller.log","w"); logs.append(ctl_log)
        ctl=subprocess.Popen([sys.executable,str(ROOT/"controller.py"),
            "--config",str(config),"--output",str(work/"controller.jsonl"),
            "--stop",str(stop)],stdout=ctl_log,stderr=subprocess.STDOUT)
        procs.append(ctl)
        deadline=time.time()+12
        while not (work/"controller.jsonl").exists() or not (work/"controller.jsonl").stat().st_size:
            if ctl.poll() is not None or time.time()>deadline:
                raise RuntimeError("Controller did not initialize; see /tmp/project30-manual/controller.log")
            time.sleep(.1)
        rxlog=open(work/"receiver.log","w"); logs.append(rxlog)
        rx=h2.popen([sys.executable,str(ROOT/"udp_app.py"),"receive",
            "--output",str(work/"manual-receive.json"),"--duration","90"],
            stdout=rxlog,stderr=subprocess.STDOUT)
        procs.append(rx)
        print("\nManual simulation is ready.")
        print("At mininet> start traffic:")
        print(f"  h1 python3 {ROOT}/udp_app.py send --output {work}/manual-send.json --count 600 --interval 0.02")
        print("Then fail primary path: link s2 s4 down")
        print("Observe controller route change to s1-s3-s4 in /tmp/project30-manual/controller.jsonl")
        print("Restore primary path: link s2 s4 up")
        CLI(net)
    finally:
        stop.touch()
        for p in procs:
            if p.poll() is None:
                p.terminate()
                try: p.wait(timeout=3)
                except subprocess.TimeoutExpired: p.kill(); p.wait()
        net.stop()
        for f in logs: f.close()

if __name__=="__main__":
    setLogLevel("info")
    main()
