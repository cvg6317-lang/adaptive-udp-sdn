#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update
sudo apt-get install -y mininet openvswitch-switch python3 python3-matplotlib
sudo systemctl start openvswitch-switch
sudo mn --switch ovsbr --test pingall
