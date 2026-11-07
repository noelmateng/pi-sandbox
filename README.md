# Pi + DeepSeek sandbox with audited internet access

Pi 1.5.0 uses OpenRouter model `deepseek/deepseek-v4.1-flash-1017`.
Your existing host Pi configuration is untouched.

## Requirements

Tested on Apple Silicon macOS with Docker Desktop. Install Node.js 20 or later
on the host, Docker Desktop with Docker Compose v2 or later (`--wait` support),
and Git. Allow Docker enough memory for Pi (4 GiB limit) plus the two gateways.
Native Linux and Windows setups have not been validated; bind-mount ownership
and host-network discovery may need changes. Use a local Docker context.

An OpenRouter account/key is needed for model responses. Network isolation
checks do not need a key and do not make paid model calls.

## Start from a fresh clone

Keep Docker Desktop running. In a Mac terminal:

```sh
# From the cloned repository directory:
./pi-sandbox build
./pi-sandbox auth
./pi-sandbox check
./pi-sandbox run
```

`auth` prompts for an [OpenRouter API key](https://openrouter.ai/settings/keys)
without echoing it. Use a key with a spending limit; do not paste it into chat.
The key stays in the owner-only `secrets/` directory and is supplied only to the
model gateway. Pi receives a dummy key. Secrets and logs are excluded from Git
and from the image build context. Model prompts and tool outputs are sent to
OpenRouter and its chosen provider, consuming API credits.

## Network policy

```text
Pi tools -> 127.0.0.1:3128 -> Unix socket -> Stripe Smokescreen -> public internet
Pi model -> local gateway -> Unix socket -> Stripe Smokescreen -> OpenRouter
```

Pi and the model gateway both use `network_mode: none`. They have no external
network interface, routes, or direct DNS access. Changing environment variables
cannot create a bypass. Proxy-aware clients receive HTTP_PROXY, HTTPS_PROXY,
ALL_PROXY (and lowercase equivalents); Node receives NODE_USE_ENV_PROXY=1.

Only the separate Smokescreen container has an external network interface.
It validates resolved destination addresses before connecting. Default IP
safety checks plus explicit deny ranges reject private, loopback, link-local,
metadata, CGNAT, multicast, reserved/documentation addresses and IPv6 transition
ranges. IPv4-mapped private IPv6 addresses are checked as IPv4. Docker host
aliases resolving to private addresses are denied too. DNS resolution and the
actual connection are handled by Smokescreen, avoiding a client-side DNS check
followed by an unchecked second lookup.

Startup also blocks every network directly attached to your Mac, including
public IPv6 LAN prefixes. Run the launcher again after changing Wi-Fi or VPN
connections to refresh this snapshot; changed ranges recreate the proxy.

Public HTTP and HTTPS work, including HTTPS Git repositories, npm, and pip.
Tools that ignore proxy settings fail closed. Raw SSH, UDP, arbitrary direct
sockets, mDNS, and discovery of LAN devices do not work. SSH Git remotes should
use HTTPS instead. Loopback services started *inside Pi's own sandbox* remain
reachable; that loopback is separate from your Mac's loopback.

Public destinations are broadly allowed. This prevents access to private
network addresses; it does not prevent sending workspace data to public sites.
A service exposed through a public tunnel or public address is still a public
destination. Such services need an additional explicit deny rule if relevant.

## Track traffic

```sh
./pi-sandbox requests  # destination summary: allowed/blocked decisions and bytes
./pi-sandbox logs      # follow JSON audit events; Ctrl+C ends the viewer
```

Durable logs live on your Mac at `~/pi-sandbox/logs/egress.jsonl`. They survive
container stops and removal. Rotation retains the active file and nine backups,
about 100 MiB total. Pi has no mount for this directory and cannot edit these
logs. Only the dedicated egress service writes them. The proxy exits if audit
logging fails, so new traffic cannot silently continue without logging.

Smokescreen records timestamps, destination hostname/port, allow/deny decision
and reason, and a connection ID. Connection-close events add the resolved IP,
connection duration, bytes transferred and errors. HTTPS logs describe CONNECT
tunnels: encrypted URL paths, headers, bodies, and individual requests inside a
reused tunnel are not visible. There is no TLS interception or custom root CA.
The summary counts proxy decisions/tunnels rather than individual HTTPS requests.
Log files can contain destination hostnames or IPs that are sensitive to you.

## Sandbox controls

- Pi runs as UID 1000 in Docker Desktop's Linux VM with all capabilities dropped
  and no-new-privileges enabled.
- Root filesystems are read-only. Pi can write its Docker workspace/home volumes
  and temporary directory. No Mac project/home folder, SSH agent, host Pi auth,
  or Docker control socket is mounted into Pi.
- Pi is limited to 2 CPUs, 4 GiB RAM and 256 processes. Egress and model gateway
  have separate smaller limits. No ports are published on your Mac.
- Host extensions, skills and MCP integrations are not loaded.
- Smokescreen is built from Stripe's pinned v0.1.0 Go module. Node and Go base
  images are pinned by digest. The egress container receives no API key.

Docker provides practical isolation, not an absolute guarantee against runtime
or kernel vulnerabilities. Pi can delete or change its own workspace and make
billable model requests. Workspace Docker volumes have no per-volume disk quota.

## Commands

```sh
./pi-sandbox run -p 'Write a hello-world Python program in /workspace'
./pi-sandbox run --continue
./pi-sandbox shell     # shell inside Pi's container
./pi-sandbox check     # real public requests plus private/bypass denial checks
./pi-sandbox status
./pi-sandbox stop      # keep workspace, sessions and audit files
./pi-sandbox build     # rebuild Pi first, then Smokescreen
```

## Copy files explicitly

The workspace persists in a Docker volume. To copy a project into the running
sandbox, use a Mac terminal:

```sh
cd ~/pi-sandbox
agent_id=$(docker compose ps -q pi)
docker cp /absolute/path/to/project "$agent_id:/workspace/project"
docker compose exec -u 0 pi chown -R 1000:1000 /workspace/project
```

Copy only what you intend to share with public internet services and the model
provider. This is an independent copy of the original. To retrieve results:

```sh
mkdir -p ~/pi-sandbox/exports
agent_id=$(docker compose ps -q pi)
docker cp "$agent_id:/workspace/project" ~/pi-sandbox/exports/project-result
```

Use a new export folder and review generated files before running them on your
Mac. A dedicated project bind mount is also possible, but would give Pi write
access to that host folder. Never mount your entire home or the Docker socket.

## Lifecycle

`./pi-sandbox stop` removes this project's containers and network but preserves
workspace/session volumes and the host audit directory. Rebuilding or restarting
uses the same volumes. To permanently delete workspace and sessions (destructive):

```sh
cd ~/pi-sandbox
docker compose down --volumes
```

The host key and audit files remain until you remove them. Revoke an unused key
in OpenRouter. Do not delete audit files while the proxy is running.

## Troubleshooting

- If images are missing, run `./pi-sandbox build` first. It builds the Pi base
  before the Smokescreen image; direct `docker compose build` is not the
  supported build entry point.
- A `407` response for a private destination is an expected policy rejection.
- If a public tool request fails, check `./pi-sandbox requests` and verify the
  client supports HTTP proxy environment variables. Direct connections fail.
- After switching networks or VPNs, rerun the launcher to update host deny rules.
  If the new network is still reachable unexpectedly, stop the sandbox and
  investigate before continuing.
- A `503` asking for authentication means the model gateway has no key. Run
  `./pi-sandbox auth`. Check your OpenRouter balance for provider errors.
- Docker's legacy builder can print a deprecation notice. The build command
  uses an isolated anonymous client configuration to avoid blocking on macOS
  Keychain helpers. Private registries and remote TLS contexts are unsupported.

## Project information

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and verification,
[SECURITY.md](SECURITY.md) for the threat model and reporting guidance, and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for upstream dependencies.
Project-authored code is available under the [MIT License](LICENSE).
This project is independent of Stripe, Pi, OpenRouter, and DeepSeek.
