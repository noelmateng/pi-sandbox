// Snapshot this Mac's directly attached networks, including public IPv6 LANs.
// Smokescreen must reject those in addition to its standard non-public ranges.
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const directory = path.join(__dirname, 'runtime');
for (const name of ['logs', 'secrets', 'runtime']) {
  const target = path.join(__dirname, name);
  fs.mkdirSync(target, {recursive: true, mode: 0o700});
  fs.chmodSync(target, 0o700);
}
// Allow isolation checks before authentication without ever replacing a key.
try {
  fs.closeSync(fs.openSync(path.join(__dirname, 'secrets', 'openrouter-key'), 'ax', 0o644));
} catch (error) {
  if (error.code !== 'EEXIST') throw error;
}
const ranges = [...new Set(Object.values(os.networkInterfaces()).flat()
  .map(address => address.cidr).filter(Boolean))].sort();
if (!ranges.length) throw new Error('Cannot discover host network ranges; refusing to start');
fs.writeFileSync(path.join(directory, 'host-deny-ranges.json'), JSON.stringify(ranges) + '\n', {mode: 0o644});
process.stdout.write(crypto.createHash('sha256').update(JSON.stringify(ranges)).digest('hex'));
