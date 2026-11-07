#!/bin/bash
set -euo pipefail
mkdir -p /home/node/.pi/agent
cp /opt/pi-config/models.json /opt/pi-config/settings.json /home/node/.pi/agent/
node /opt/sandbox/relay.cjs &
relay_pid=$!
trap 'kill "$relay_pid" 2>/dev/null || true; exit 0' TERM INT
wait "$relay_pid"
