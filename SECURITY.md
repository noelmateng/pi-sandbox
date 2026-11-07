# Security policy

## Scope and support

This is an experimental local sandbox, not a formally audited security product.
Only the current `main` branch is maintained. Validate isolation on your host
before using it with untrusted repositories or generated code.

## Intended protection

The complete Pi process and its tools run as an unprivileged user in a Linux
container with a read-only root filesystem. Pi and the model credential gateway
have no external network interface. Unix sockets connect them to a separate
Smokescreen service, which checks destination addresses and records traffic.
Private and special-use ranges and a startup snapshot of the host's connected
networks are denied. The real API key and durable audit logs are outside Pi.

The host administrator, Docker daemon/VM, images, Smokescreen, credential
gateway and audit writer are trusted. Anyone controlling Docker or the host
can change the policy, read credentials or alter logs. The credential file is
plaintext beneath an owner-only directory. Desktop bind-mount behavior is part
of the supported environment; native Linux permissions are not validated.

## Limits

- Container or kernel vulnerabilities may defeat isolation.
- Public internet destinations are allowed. Workspace data can be uploaded to
  them, and the model receives prompts and tool results. Public tunnels into
  local systems need separate deny rules.
- Localhost inside Pi's container remains available for its own services.
- Host network rules are a startup snapshot. Rerun the launcher after changing
  networks or VPNs. Public destinations reached over an unusual route, tunnel
  or public-addressed VPN network may need extra deny ranges.
- HTTP CONNECT supports opaque public TCP tunnels. This is not application
  protocol inspection or data-loss prevention.
- HTTPS bodies, paths and individual requests inside a reused tunnel are not
  logged. Logs are connection metadata, not a full packet capture.
- Logs rotate; old events are deleted after the retention limit. Log records
  are not cryptographically signed or protected from a host administrator.
- Pi can alter or delete its own workspace and sessions, consume disk, and
  make billable requests. Memory/CPU/process limits do not provide disk quotas.
- A bind-mounted project folder would be writable by Pi. The default uses
  Docker volumes and explicit copies.
- Image builds need network access outside the runtime proxy policy. Only run
  builds from source you trust; build-time traffic is not in the runtime audit.

## Reporting vulnerabilities

Do not post working isolation escapes, credentials, private host information
or unredacted logs in public issues. If the hosted repository offers GitHub
private vulnerability reporting, use its Security tab to report privately.
Otherwise arrange a private channel with the repository owner before sharing
sensitive details. This repository does not configure a reporting address or
promise a response timeline.

Include affected revisions, host/Docker versions, a minimal reproduction,
expected boundary, actual behavior and a redacted log excerpt. Stop the
sandbox if you suspect a bypass. Revoke exposed provider keys through the
provider and preserve logs privately for investigation.
