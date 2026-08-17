# Minimal FastCGI client for talking directly to apteryx-rest
import socket
import struct

FCGI_BEGIN_REQUEST = 1
FCGI_END_REQUEST = 3
FCGI_PARAMS = 4
FCGI_STDIN = 5
FCGI_STDOUT = 6
FCGI_RESPONDER = 1


def fcgi_record(rtype, content):
    return struct.pack("!BBHHBB", 1, rtype, 1, len(content), 0, 0) + content


def fcgi_param(name, value):
    name = name.encode("utf-8")
    value = value.encode("utf-8")
    data = b""
    for length in (len(name), len(value)):
        if length < 128:
            data += struct.pack("!B", length)
        else:
            data += struct.pack("!I", length | 0x80000000)
    return data + name + value


def fcgi_get(sock_path, docroot, path, accept):
    """Send a FastCGI GET request and return the connected socket"""
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(sock_path)
    params = (fcgi_param("REQUEST_METHOD", "GET") +
              fcgi_param("REQUEST_URI", docroot + path) +
              fcgi_param("DOCUMENT_ROOT", docroot) +
              fcgi_param("HTTP_ACCEPT", accept))
    sock.sendall(fcgi_record(FCGI_BEGIN_REQUEST, struct.pack("!HB5x", FCGI_RESPONDER, 0)) +
                 fcgi_record(FCGI_PARAMS, params) +
                 fcgi_record(FCGI_PARAMS, b"") +
                 fcgi_record(FCGI_STDIN, b""))
    return sock


def _recv_exactly(sock, n):
    """Read up to n bytes; a short read means the peer closed early."""
    buf = b""
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf


def _parse_status(stdout):
    """Pull the CGI 'Status:' code out of the response headers (default 200)."""
    head = stdout.decode("latin-1", "replace").split("\r\n\r\n", 1)[0]
    for line in head.split("\r\n"):
        if line.lower().startswith("status:"):
            token = line.split(":", 1)[1].strip().split()
            if token and token[0].isdigit():
                return int(token[0])
    return 200 if stdout else None


def fcgi_request(sock_path, method, docroot, path, body=b"",
                 content_type="application/yang-data+json",
                 accept="application/yang-data+json",
                 content_length=None, timeout=10, request_uri=None):
    """Perform a single FastCGI request directly against apteryx-rest and return
    a ``(status, body)`` tuple, where ``body`` is the decoded response body with
    the CGI headers stripped.

    ``content_length`` overrides the CONTENT_LENGTH param independently of the
    bytes actually placed on STDIN, so a caller can forge a mismatched or
    malformed value. This is deliberate: a front-end web server normalises
    Content-Length before proxying, so speaking FastCGI directly is the only way
    to exercise apteryx-rest's own CONTENT_LENGTH validation. ``request_uri``
    overrides the REQUEST_URI param (default ``docroot + path``) so a caller can
    forge a raw path such as one whose first segment is "..". ``status`` is None
    if the connection dropped without a CGI response."""
    if isinstance(body, str):
        body = body.encode("utf-8")
    if content_length is None:
        content_length = str(len(body))
    if request_uri is None:
        request_uri = docroot + path
    params = (fcgi_param("REQUEST_METHOD", method) +
              fcgi_param("REQUEST_URI", request_uri) +
              fcgi_param("DOCUMENT_ROOT", docroot) +
              fcgi_param("CONTENT_TYPE", content_type) +
              fcgi_param("HTTP_ACCEPT", accept) +
              fcgi_param("CONTENT_LENGTH", content_length))
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.connect(sock_path)
    stdout = b""
    try:
        sock.sendall(fcgi_record(FCGI_BEGIN_REQUEST, struct.pack("!HB5x", FCGI_RESPONDER, 0)) +
                     fcgi_record(FCGI_PARAMS, params) +
                     fcgi_record(FCGI_PARAMS, b"") +
                     fcgi_record(FCGI_STDIN, body) +
                     fcgi_record(FCGI_STDIN, b""))
        while True:
            header = _recv_exactly(sock, 8)
            if len(header) < 8:
                break
            _, rtype, _, clen, plen, _ = struct.unpack("!BBHHBB", header)
            content = _recv_exactly(sock, clen + plen)[:clen]
            if rtype == FCGI_STDOUT:
                stdout += content
            elif rtype == FCGI_END_REQUEST:
                break
    finally:
        sock.close()
    _, _, raw_body = stdout.partition(b"\r\n\r\n")
    return _parse_status(stdout), raw_body.decode("latin-1", "replace")
