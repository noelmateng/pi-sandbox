"""Fixed OpenRouter chat endpoint. Never a general HTTP/CONNECT proxy."""
import http.client
import http.server
import json
import os
import socket
import socketserver
import ssl

MODEL = 'deepseek/deepseek-v4.1-flash-1017'
HOST = 'openrouter.ai'
SOCKET = '/run/gateway/api.sock'
KEY_PATH = '/run/secrets/openrouter_key'


class ProxiedHTTPS(http.client.HTTPSConnection):
    def connect(self):
        # Even the credential gateway has no network interface. All inference
        # egress passes through the same audited Smokescreen proxy.
        self.set_tunnel(HOST, 443)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect('/run/egress/proxy.sock')
        self._tunnel()
        self.sock = ssl.create_default_context().wrap_socket(self.sock, server_hostname=HOST)


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log request bodies, credentials, or prompts.

    def reject(self, status, message):
        body = json.dumps({'error': {'message': message}}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == '/health':
            self.reject(200, 'gateway ready')
        else:
            self.reject(403, 'Only chat completions are allowed')

    def do_POST(self):
        self.response_started = False
        connection = None
        if self.path != '/api/v1/chat/completions':
            return self.reject(403, 'Only chat completions are allowed')
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 32 * 1024 * 1024:
                return self.reject(413, 'Invalid request size')
            payload = json.loads(self.rfile.read(size))
            if payload.get('model') != MODEL:
                return self.reject(403, 'Only the configured DeepSeek model is allowed')
            # External URLs could cause provider-side fetching. Accept inline
            # image data only, and reject routing/plugins supplied by the agent.
            for message in payload.get('messages', []):
                content = message.get('content')
                if isinstance(content, list):
                    for part in content:
                        if part.get('type') == 'image_url' and not part.get('image_url', {}).get('url', '').startswith('data:'):
                            return self.reject(403, 'Use inline image data')
            for field in ('plugins', 'provider', 'models', 'route', 'transforms', 'web_search_options'):
                payload.pop(field, None)
            with open(KEY_PATH) as source:
                key = source.read().strip()
            if not key:
                return self.reject(503, 'Run ./pi-sandbox auth on the host first')
            connection = ProxiedHTTPS(HOST, timeout=300)
            connection.request('POST', '/api/v1/chat/completions', json.dumps(payload).encode(), {
                'Authorization': 'Bearer ' + key,
                'Content-Type': 'application/json',
                'Accept': 'text/event-stream' if payload.get('stream') else 'application/json',
            })
            response = connection.getresponse()
            # Do not follow redirects or expose arbitrary upstream headers.
            if 300 <= response.status < 400:
                connection.close()
                return self.reject(502, 'Upstream redirects are disabled')
            self.send_response(response.status)
            self.send_header('Content-Type', response.getheader('Content-Type', 'application/json'))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.response_started = True
            while block := response.read1(65536):
                self.wfile.write(block)
                self.wfile.flush()
            connection.close()
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            if not self.response_started:
                try:
                    self.reject(502, 'Model request failed; check gateway connectivity and your key')
                except OSError:
                    pass
        finally:
            if connection is not None:
                connection.close()


class Server(socketserver.ThreadingMixIn, socketserver.UnixStreamServer):
    daemon_threads = True


if os.path.exists(SOCKET):
    os.unlink(SOCKET)
with Server(SOCKET, Handler) as server:
    os.chmod(SOCKET, 0o666)
    server.serve_forever()
