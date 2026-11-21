import apteryx
import struct
from conftest import docroot
from fcgi import fcgi_request, fcgi_get, _recv_exactly, FCGI_STDOUT, FCGI_END_REQUEST

# A list key value in the request path that holds an unencoded reserved
# character. The text after the character is long so that any copy of it
# that apteryx-rest (or apteryx-xml under it) fails to free is easy to see.
# Run the daemon under valgrind (TEST_WRAPPER in run.sh) to check for loss.
# The assertions check the status, which shows that the path was parsed.
# apteryx-xml cuts a path element at the '=', so these requests act on the
# list entry "fred". Some statuses record that current behaviour: POST
# expects 409 because "fred" exists, and PUT, PATCH and DELETE change or
# remove the data of "fred".
#
# The requests go straight to the FastCGI socket: a front-end web server may
# reject a request line this long.
KEY_TAIL = "x" * 10000


def _add_fred():
    apteryx.set("/test/settings/users/fred/name", "fred")
    apteryx.set("/test/settings/users/fred/age", "31")


def test_key_with_equals_get(fcgi_sock):
    _add_fred()
    for _ in range(10):
        status, _body = fcgi_request(fcgi_sock, "GET", docroot,
                                     "/data/test/settings/users/fred=" + KEY_TAIL + "/name")
        assert status == 200


def test_key_with_equals_delete(fcgi_sock):
    for _ in range(10):
        _add_fred()
        status, _body = fcgi_request(fcgi_sock, "DELETE", docroot,
                                     "/data/test/settings/users/fred=" + KEY_TAIL + "/age")
        assert status == 204


def test_key_with_bracket_get(fcgi_sock):
    _add_fred()
    for _ in range(10):
        status, _body = fcgi_request(fcgi_sock, "GET", docroot,
                                     "/data/test/settings/users/fred[" + KEY_TAIL + "/name")
        assert status == 200


def test_key_plain_get(fcgi_sock):
    _add_fred()
    for _ in range(10):
        status, body = fcgi_request(fcgi_sock, "GET", docroot,
                                    "/data/test/settings/users/fred/name")
        assert status == 200
        assert "fred" in body


def test_key_with_equals_put(fcgi_sock):
    for _ in range(10):
        _add_fred()
        status, _body = fcgi_request(fcgi_sock, "PUT", docroot,
                                     "/data/test/settings/users/fred=" + KEY_TAIL + "/age",
                                     body='{"age": 32}')
        assert status == 204


def test_key_with_equals_patch(fcgi_sock):
    for _ in range(10):
        _add_fred()
        status, _body = fcgi_request(fcgi_sock, "PATCH", docroot,
                                     "/data/test/settings/users/fred=" + KEY_TAIL,
                                     body='{"age": 33}')
        assert status == 204


def test_key_with_equals_post(fcgi_sock):
    for _ in range(10):
        _add_fred()
        status, _body = fcgi_request(fcgi_sock, "POST", docroot,
                                     "/data/test/settings/users/fred=" + KEY_TAIL,
                                     body='{"age": 34}')
        # "fred" exists already
        assert status == 409


def _watch_once(sock_path, path):
    """Open a watch (event stream), read up to the end of the response
    headers, then close the connection. Return the CGI status line."""
    sock = fcgi_get(sock_path, docroot, path, "text/event-stream")
    sock.settimeout(30)
    stdout = b""
    try:
        while b"\r\n\r\n" not in stdout:
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
    return stdout.split(b"\r\n", 1)[0]


def test_key_with_equals_watch(fcgi_sock):
    # An event stream request is not RESTCONF, so the path has no "/data".
    # The status is sent before the path is parsed, so it shows only that the
    # watch was accepted; valgrind shows whether the parse lost memory.
    _add_fred()
    for _ in range(10):
        status = _watch_once(fcgi_sock, "/test/settings/users/fred=" + KEY_TAIL + "/name")
        assert status == b"Status: 200"


def test_key_with_equals_delete_read_only_proxy(fcgi_sock):
    # The element after a read-only proxy fails as not writable.
    # rest_api_delete() returns 404 for any path that does not parse, so the
    # status does not show which error; the apteryx-xml unit test
    # test_path_reserved_chars_not_writable checks for SCH_E_NOTWRITABLE.
    for _ in range(10):
        status, _body = fcgi_request(fcgi_sock, "DELETE", docroot,
                                     "/data/logical-elements:logical-elements/logical-element-ro/loopy/testing:test="
                                     + KEY_TAIL + "/animals/animal=dog")
        assert status == 404
