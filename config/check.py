import http.client
import json
import os
import socket
import subprocess


def check(condition, message):
    print(('PASS ' if condition else 'FAIL ') + message, flush=True)
    if not condition:
        raise SystemExit(1)


check(os.getuid() == 1000, 'Pi runs as an unprivileged user')
active = [name for _, name in socket.if_nameindex()
          if int(open('/sys/class/net/' + name + '/flags').read(), 16) & 1]
check(active == ['lo'], 'Only loopback is active; no LAN, internet, or Docker network interface')
check(len(open('/proc/net/route').read().splitlines()) == 1, 'No IPv4 routes exist')
check(not os.path.exists('/var/run/docker.sock'), 'No Docker control socket')
check(not os.path.exists('/run/secrets/openrouter_key'), 'Real API key is absent from Pi')
check(not any(name.endswith('_API_KEY') for name in os.environ), 'No API keys in Pi environment')
for path in ['/root/host-test', '/etc/pi-sandbox-write-test']:
    try:
        with open(path, 'w') as output:
            output.write('test')
    except OSError:
        print('PASS Root filesystem write blocked: ' + path)
    else:
        raise SystemExit('FAIL root filesystem writable')
for path in ['/workspace/.sandbox-check', '/home/node/.sandbox-check']:
    with open(path, 'w') as output:
        output.write('test')
    os.unlink(path)
print('PASS Workspace and Pi home are writable Docker volumes')
for address in ['1.1.1.1', '192.168.1.1', '10.0.0.1', '169.254.169.254']:
    try:
        with socket.create_connection((address, 443), timeout=1):
            raise SystemExit('FAIL reachable destination: ' + address)
    except OSError:
        print('PASS Direct network connection blocked: ' + address)
for method, path, payload, expected in [
    ('GET', '/health', None, 200),
    ('GET', '/api/v1/key', None, 403),
    ('POST', '/api/v1/chat/completions', json.dumps({'model': 'unapproved'}), 403),
    ('CONNECT', '192.168.1.1:443', None, 403),
]:
    conn = http.client.HTTPConnection('127.0.0.1', 8080, timeout=5)
    conn.request(method, path, payload)
    reply = conn.getresponse()
    check(reply.status == expected, f'Gateway {method} {path}: {reply.status}')
    reply.read()
    conn.close()
subprocess.run(['pi', '--offline', '--no-extensions', '--no-mcp', '--list-models', 'deepseek-v4.1-flash-1017'], check=True)

# An explicit proxy is the sole outbound transport. Check both HTTP and HTTPS
# target validation, including private IPs reached through a DNS name.
for target in ['127.0.0.1:80', '10.0.0.1:443', '172.16.0.1:443',
               '192.168.1.1:443', '169.254.169.254:80', '100.64.0.1:443',
               '[::1]:443', '[fd00::1]:443', '[fe80::1]:443',
               '[::ffff:127.0.0.1]:443', 'host.docker.internal:80',
               'localhost:80']:
    conn = http.client.HTTPConnection('127.0.0.1', 3128, timeout=20)
    conn.request('CONNECT', target)
    reply = conn.getresponse()
    check(reply.status == 407, f'Smokescreen denies {target}: HTTP {reply.status}')
    reply.read()
    conn.close()

for url in ['http://example.com', 'https://example.com']:
    result = subprocess.run(['curl', '--fail', '--silent', '--show-error',
                             '--max-time', '30', url], capture_output=True)
    check(result.returncode == 0 and b'Example Domain' in result.stdout,
          'Public internet works through proxy: ' + url +
          (': ' + result.stderr.decode() if result.returncode else ''))

result = subprocess.run(['curl', '--silent', '--show-error', '--max-time', '5',
                         '--noproxy', '*', 'https://example.com'], capture_output=True)
check(result.returncode != 0, 'Clearing proxy use cannot bypass isolation')
check(not os.path.exists('/audit/egress.jsonl'), 'Pi cannot access or edit durable audit logs')
