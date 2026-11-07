# Contributing

Keep changes focused and explain the behavior they change. This project targets
local Docker Desktop on macOS; describe your host platform and Docker version
when reporting reproducible bugs. Redact hostnames, addresses and identifiers
from logs when appropriate. Never attach API keys or workspace contents.

## Development

The host utilities use built-in Node.js modules. The gateway uses the Python
standard library. There are no host npm or pip dependencies to install.

```sh
bash -n pi-sandbox start.sh
for script in ./*.cjs; do node --check "$script"; done
python3 - <<'PY'
import ast
from pathlib import Path
for path in [Path('gateway.py'), *Path('config').glob('*.py')]:
    ast.parse(path.read_text(), filename=str(path))
PY
docker compose config --quiet
./pi-sandbox build
./pi-sandbox check
./pi-sandbox requests
./pi-sandbox stop
```

Run `./pi-sandbox check` after changes to networking, mounts, credentials,
container permissions or startup. It creates runtime directories and an empty
key file when needed, without overwriting an existing key. It performs real
public HTTP/HTTPS requests and attempts blocked private connections. Tests
require internet access but no paid model calls. Host Python is optional for
the syntax check; runtime Python is included in the Docker image.

Changes that affect the HTTP proxy should also verify native Node fetch, npm,
and HTTPS Git from `./pi-sandbox shell`, then inspect the audit log. Model
changes should verify a real response using your own key and budget; report
clearly when inference was not tested.

## Preserve these boundaries

- Pi and the credential gateway keep `network_mode: none`.
- Only Smokescreen receives an external network interface.
- The real model key is mounted only into the credential gateway.
- Agent processes cannot mount or edit durable audit files.
- No host Docker socket, home directory, SSH agent or published port is added.
- Public proxy access cannot bypass private-address or host-network checks.
- An audit write failure stops the proxy.

Document any deliberate change to these properties and its security impact.
Do not weaken isolation just to make a failing tool work.

## Repository hygiene

Keep secrets, logs, runtime host-network snapshots, exports, `.env` files and
Python caches out of commits. Review `git diff --cached` before committing.
Use your own anonymized examples rather than captured real traffic.

For dependency updates, pin the new version or image digest, review upstream
changes, rebuild both images and run the isolation checks. Update dependency
notices if the licenses or distribution method change.
