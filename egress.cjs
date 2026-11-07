// Trusted transport and durable audit logging for Stripe Smokescreen.
const fs = require('node:fs');
const net = require('node:net');
const {spawn} = require('node:child_process');
const path = '/audit/egress.jsonl';
const socketPath = '/run/egress/proxy.sock';
const hostRanges = JSON.parse(fs.readFileSync('/etc/sandbox/host-deny-ranges.json', 'utf8'));
if (!Array.isArray(hostRanges) || !hostRanges.length) throw new Error('Host deny ranges are required');
const limit = 10 * 1024 * 1024;
let fd, length;
function openLog() {
  fd = fs.openSync(path, 'a', 0o600);
  length = fs.fstatSync(fd).size;
}
function record(line) {
  let entry;
  try { entry = JSON.parse(line); }
  catch { entry = {time: new Date().toISOString(), msg: line, source: 'smokescreen'}; }
  const output = JSON.stringify(entry) + '\n';
  if (length + Buffer.byteLength(output) > limit) {
    fs.closeSync(fd);
    for (let i = 9; i >= 1; --i) {
      const source = i === 1 ? path : `${path}.${i - 1}`;
      if (fs.existsSync(source)) fs.renameSync(source, `${path}.${i}`);
    }
    openLog();
  }
  fs.writeSync(fd, output);
  fs.fdatasyncSync(fd);
  length += Buffer.byteLength(output);
  process.stdout.write(output);
}
openLog(); // Fail closed if the durable audit destination is not writable.
const child = spawn('/usr/local/bin/smokescreen', [
  '--listen-ip=127.0.0.1', '--listen-port=4750',
  '--timeout=15s', '--stats-socket-dir=/tmp',
  ...hostRanges.map(range => `--deny-range=${range}`),
  // Explicit defense in depth, including IPv4-embedding and translation ranges.
  ...['0.0.0.0/8', '10.0.0.0/8', '100.64.0.0/10', '127.0.0.0/8',
      '169.254.0.0/16', '172.16.0.0/12', '192.0.0.0/24', '192.168.0.0/16',
      '192.0.2.0/24', '198.18.0.0/15', '198.51.100.0/24', '203.0.113.0/24',
      '224.0.0.0/4', '240.0.0.0/4', '::/96',
      '64:ff9b::/96', '64:ff9b:1::/48', '100::/64', '2001::/23',
      '2001:db8::/32', '2002::/16', 'fc00::/7', 'fe80::/10', 'ff00::/8']
    .map(range => `--deny-range=${range}`),
], {stdio: ['ignore', 'pipe', 'pipe']});
for (const stream of [child.stdout, child.stderr]) {
  let pending = '';
  stream.setEncoding('utf8');
  stream.on('data', chunk => {
    pending += chunk;
    let end;
    while ((end = pending.indexOf('\n')) !== -1) {
      record(pending.slice(0, end)); pending = pending.slice(end + 1);
    }
  });
  stream.on('end', () => { if (pending) record(pending); });
}
child.on('error', error => { record(JSON.stringify({msg: error.message})); process.exit(1); });
child.on('exit', code => process.exit(code || 0));
for (const signal of ['SIGTERM', 'SIGINT']) process.on(signal, () => child.kill(signal));
process.on('exit', () => child.kill('SIGKILL'));
if (fs.existsSync(socketPath)) fs.unlinkSync(socketPath);
net.createServer(client => {
  const remote = net.connect(4750, '127.0.0.1');
  client.on('error', () => remote.destroy());
  remote.on('error', () => client.destroy());
  client.on('close', () => remote.destroy());
  remote.on('close', () => client.destroy());
  client.pipe(remote).pipe(client);
}).listen(socketPath, () => fs.chmodSync(socketPath, 0o666));
