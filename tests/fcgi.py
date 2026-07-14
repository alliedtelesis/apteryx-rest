# Minimal FastCGI client for talking directly to apteryx-rest
import socket
import struct

FCGI_BEGIN_REQUEST = 1
FCGI_PARAMS = 4
FCGI_STDIN = 5
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
