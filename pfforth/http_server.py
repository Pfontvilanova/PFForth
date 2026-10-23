"""Small, polling HTTP/1.x socket layer for Forth applications.

No routes or HTML live here. Each poll performs bounded, nonblocking socket
work; the Forth caller decides when and how to respond to each request.
One request is accepted per connection, which is closed after the response.
"""

from http import HTTPStatus
import queue
import socket
import time


MAX_HEADERS = 8192
MAX_BODY = 65536
MAX_CLIENTS = 16
CLIENT_TIMEOUT = 15
CHUNK = 4096


class HTTPRequest:
    def __init__(self, server, sock, method, path, headers, body):
        self.server = server
        self.sock = sock
        self.method = method
        self.path = path
        self.headers = headers
        self.body = body
        self.responded = False


class _Connection:
    def __init__(self, sock):
        self.sock = sock
        self.buffer = bytearray()
        self.header_end = None
        self.body_length = 0
        self.request = None
        self.output = b""
        self.sent = 0
        self.updated = time.monotonic()


class HTTPServer:
    def __init__(self, host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((host, port))
            self.sock.listen(16)
            self.sock.setblocking(False)
        except Exception:
            self.sock.close()
            raise
        self.port = self.sock.getsockname()[1]
        self.clients = {}
        self.requests = queue.Queue()
        self.closed = False

    def _close_client(self, conn):
        self.clients.pop(conn.sock, None)
        try:
            conn.sock.close()
        except OSError:
            pass

    def stop(self):
        if self.closed:
            return
        self.closed = True
        self.sock.close()
        for conn in list(self.clients.values()):
            self._close_client(conn)
        while not self.requests.empty():
            self.requests.get_nowait()

    def _send(self, conn):
        try:
            if conn.sent < len(conn.output):
                n = conn.sock.send(conn.output[conn.sent:])
                if n == 0:
                    self._close_client(conn)
                    return
                conn.sent += n
                conn.updated = time.monotonic()
            if conn.sent == len(conn.output):
                self._close_client(conn)
        except (BlockingIOError, InterruptedError):
            pass
        except (BrokenPipeError, ConnectionResetError, OSError):
            # Browsers can cancel speculative requests at any time.
            self._close_client(conn)

    def _error(self, conn, status):
        reason = HTTPStatus(status).phrase
        body = (str(status) + " " + reason + "\n").encode("ascii")
        conn.output = self._frame(status, "text/plain; charset=utf-8", body)
        conn.sent = 0
        self._send(conn)

    @staticmethod
    def _frame(status, content_type, body, head=False):
        if not 100 <= status <= 599:
            raise ValueError("invalid HTTP status")
        if "\r" in content_type or "\n" in content_type:
            raise ValueError("invalid Content-Type")
        try:
            reason = HTTPStatus(status).phrase
        except ValueError:
            reason = "Unknown"
        if status in (204, 304) or 100 <= status < 200:
            body = b""
        header = (
            "HTTP/1.1 {} {}\r\n"
            "Content-Type: {}\r\n"
            "Content-Length: {}\r\n"
            "Connection: close\r\n\r\n"
        ).format(status, reason, content_type, len(body)).encode("ascii")
        return header if head else header + body

    def _parse(self, conn):
        buf = conn.buffer
        if conn.header_end is None:
            end = buf.find(b"\r\n\r\n")
            if end < 0:
                if len(buf) > MAX_HEADERS:
                    self._error(conn, 431)
                return
            conn.header_end = end + 4
            if conn.header_end > MAX_HEADERS:
                self._error(conn, 431)
                return
            try:
                lines = bytes(buf[:end]).decode("iso-8859-1").split("\r\n")
                parts = lines[0].split(" ")
                if len(parts) != 3 or parts[2] not in ("HTTP/1.0", "HTTP/1.1"):
                    raise ValueError("bad request line")
                method, path, _version = parts
                if not method.isalpha() or not method.isascii() or not path.startswith("/"):
                    raise ValueError("bad method or path")
                headers = {}
                for line in lines[1:]:
                    name, sep, value = line.partition(":")
                    if not sep or not name.strip() or name != name.strip():
                        raise ValueError("bad header")
                    name = name.lower()
                    if name in headers and name in ("content-length", "transfer-encoding"):
                        raise ValueError("duplicate framing header")
                    headers[name] = value.strip()
                if "transfer-encoding" in headers:
                    raise ValueError("unsupported transfer encoding")
                length = headers.get("content-length", "0")
                if not length.isascii() or not length.isdigit():
                    raise ValueError("bad content length")
                conn.body_length = int(length)
                if conn.body_length > MAX_BODY:
                    self._error(conn, 413)
                    return
                conn._method = method
                conn._path = path
                conn._headers = headers
            except (ValueError, UnicodeError):
                self._error(conn, 400)
                return
        length = len(buf) - conn.header_end
        if length >= conn.body_length:
            body = bytes(buf[conn.header_end:conn.header_end + conn.body_length])
            conn.request = HTTPRequest(self, conn.sock, conn._method,
                                       conn._path, conn._headers, body)
            self.requests.put(conn.request)

    def poll(self):
        if self.closed:
            raise RuntimeError("HTTP server is stopped")
        while len(self.clients) < MAX_CLIENTS:
            try:
                sock, _addr = self.sock.accept()
            except (BlockingIOError, InterruptedError):
                break
            sock.setblocking(False)
            self.clients[sock] = _Connection(sock)
        now = time.monotonic()
        for conn in list(self.clients.values()):
            if now - conn.updated > CLIENT_TIMEOUT:
                if conn.request is None and not conn.output:
                    self._error(conn, 408)
                else:
                    self._close_client(conn)
                continue
            if conn.output:
                self._send(conn)
                continue
            if conn.request is not None:
                # Notice client disconnects while Forth prepares a response.
                try:
                    data = conn.sock.recv(1, socket.MSG_PEEK)
                    if data == b"":
                        self._close_client(conn)
                except (BlockingIOError, InterruptedError):
                    pass
                except (ConnectionResetError, OSError):
                    self._close_client(conn)
                continue
            try:
                data = conn.sock.recv(CHUNK)
                if not data:
                    self._close_client(conn)
                    continue
                conn.buffer.extend(data)
                conn.updated = now
                self._parse(conn)
            except (BlockingIOError, InterruptedError):
                pass
            except (ConnectionResetError, OSError):
                self._close_client(conn)
        while not self.requests.empty():
            req = self.requests.get_nowait()
            if req.sock in self.clients:
                return req
        return None

    def respond(self, req, status, content_type, body):
        if req.server is not self or self.closed:
            raise ValueError("request does not belong to this open server")
        if req.responded:
            raise ValueError("request already answered")
        conn = self.clients.get(req.sock)
        if conn is None or conn.request is not req:
            raise ValueError("request connection has closed")
        if isinstance(body, str):
            body = body.encode("utf-8")
        if not isinstance(body, bytes):
            raise TypeError("response body must be a string or bytes")
        conn.output = self._frame(int(status), str(content_type), body,
                                  head=req.method == "HEAD")
        req.responded = True
        self._send(conn)


class ForthHTTP:
    """Forth-facing, application-neutral HTTP socket vocabulary."""

    def _register_http_words(self):
        self.words["http-start"] = self._http_start
        self.words["http-port"] = self._http_port
        self.words["http-receive"] = self._http_receive
        self.words["http-method"] = self._http_method
        self.words["http-path"] = self._http_path
        self.words["http-body"] = self._http_body
        self.words["http-header"] = self._http_header
        self.words["http-respond"] = self._http_respond
        self.words["http-stop"] = self._http_stop

    def _http_start(self):
        port = int(self.stack[-1])
        host = str(self.stack[-2])
        server = HTTPServer(host, port)
        del self.stack[-2:]
        self.stack.append(server)

    def _http_port(self):
        self.stack.append(self.stack.pop().port)

    def _http_receive(self):
        self.stack.append(self.stack.pop().poll() or 0)

    def _http_method(self):
        self.stack.append(self.stack.pop().method)

    def _http_path(self):
        self.stack.append(self.stack.pop().path)

    def _http_body(self):
        self.stack.append(self.stack.pop().body.decode("utf-8"))

    def _http_header(self):
        name = str(self.stack.pop()).lower()
        request = self.stack.pop()
        self.stack.append(request.headers.get(name, ""))

    def _http_respond(self):
        request, status, content_type, body = self.stack[-4:]
        request.server.respond(request, status, content_type, body)
        del self.stack[-4:]

    def _http_stop(self):
        self.stack.pop().stop()