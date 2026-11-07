// This process has no network interface except loopback. It relays HTTP over
// a Unix socket to the separate, fixed-destination model gateway.
const http = require('node:http');
const net = require('node:net');
// Transparent HTTP proxy transport; policy is enforced by Smokescreen outside
// this container. A process ignoring the proxy still has no network route.
net.createServer(client => {
  const remote = net.connect('/run/egress/proxy.sock');
  client.on('error', () => remote.destroy());
  remote.on('error', () => client.destroy());
  client.on('close', () => remote.destroy());
  remote.on('close', () => client.destroy());
  client.pipe(remote).pipe(client);
}).listen(3128, '127.0.0.1');
http.createServer((req, res) => {
  const upstream = http.request({socketPath:'/run/gateway/api.sock',
    path:req.url, method:req.method, headers:req.headers}, incoming => {
    res.writeHead(incoming.statusCode, incoming.headers);
    incoming.pipe(res);
  });
  upstream.on('error', () => { if (!res.headersSent) res.writeHead(502); res.end('Model gateway unavailable'); });
  req.on('aborted', () => upstream.destroy());
  req.pipe(upstream);
}).on('connect', (_req, socket) => {
  socket.end('HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\nConnection: close\r\n\r\n');
}).listen(8080, '127.0.0.1');
