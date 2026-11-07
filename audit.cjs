const fs = require('node:fs');
const path = require('node:path');
const base = path.join(__dirname, 'logs', 'egress.jsonl');
const rows = new Map();
for (const file of [...Array.from({length:9}, (_,i) => `${base}.${9-i}`), base]) {
  if (!fs.existsSync(file)) continue;
  for (const line of fs.readFileSync(file, 'utf8').split('\n')) {
    if (!line.trim()) continue;
    let event;
    try { event = JSON.parse(line); } catch { continue; }
    if (!event.requested_host) continue;
    const row = rows.get(event.requested_host) || {
      destination: event.requested_host, allowed: 0, blocked: 0, received: 0, sent: 0,
    };
    if (event.msg === 'CANONICAL-PROXY-DECISION') {
      if (event.allow) row.allowed++; else row.blocked++;
    }
    if (event.msg === 'CANONICAL-PROXY-CN-CLOSE') {
      row.received += event.bytes_in || 0;
      row.sent += event.bytes_out || 0;
    }
    rows.set(event.requested_host, row);
  }
}
if (!rows.size) console.log('No recorded proxy traffic yet.');
else console.table([...rows.values()].sort((a,b) => a.destination.localeCompare(b.destination)));
console.log('Counts are proxy decisions / HTTPS tunnels, not individual requests inside encrypted HTTPS connections.');
