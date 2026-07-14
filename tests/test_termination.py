import os
import signal
import subprocess
import tempfile
import time

import pytest

from conftest import docroot
from fcgi import fcgi_get

BUILD = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".build"))
FCGI_SOCK_PATH = os.path.join(tempfile.gettempdir(), "apteryx-rest-termination-test.sock")


def terminate(proc):
    """SIGTERM apteryx-rest and check it exits promptly and cleanly"""
    proc.send_signal(signal.SIGTERM)
    try:
        returncode = proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        pytest.fail("apteryx-rest did not exit after SIGTERM")
    assert returncode == 0, "apteryx-rest did not exit cleanly (exit code %d)" % returncode


@pytest.fixture
def apteryx_rest_instance():
    # A private apteryx-rest instance so the tests can observe its exit code
    if os.path.exists(FCGI_SOCK_PATH):
        os.unlink(FCGI_SOCK_PATH)
    proc = subprocess.Popen([os.path.join(BUILD, "..", "apteryx-rest"),
                             "-m", os.path.join(BUILD, "etc/restconf/"), "-s", FCGI_SOCK_PATH],
                            cwd=BUILD, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(50):
            if os.path.exists(FCGI_SOCK_PATH):
                break
            time.sleep(0.1)
        else:
            pytest.fail("apteryx-rest did not create socket %s" % FCGI_SOCK_PATH)
        yield proc
    finally:
        if proc.poll() is None:
            proc.kill()
        proc.wait()
        if os.path.exists(FCGI_SOCK_PATH):
            os.unlink(FCGI_SOCK_PATH)


def test_termination_with_get_requests_active(apteryx_rest_instance):
    # Termination must not crash while workers are still inside apteryx calls
    # (abort on assert(rpc) after apteryx_shutdown). Pause apteryxd so the
    # workers are reliably still inside those calls at shutdown.
    proc = apteryx_rest_instance
    result = subprocess.run(["pidof", "apteryxd"], capture_output=True, text=True)
    pids = [int(pid) for pid in result.stdout.split()]
    assert pids, "could not find a running apteryxd"
    requests = []
    try:
        for pid in pids:
            os.kill(pid, signal.SIGSTOP)
        for _ in range(10):
            requests.append(fcgi_get(FCGI_SOCK_PATH, docroot, "/test/settings", "application/json"))
        time.sleep(0.1)
        terminate(proc)
    finally:
        for pid in pids:
            os.kill(pid, signal.SIGCONT)
        for sock in requests:
            sock.close()


def test_termination_with_streams_connected(apteryx_rest_instance):
    # Termination must not hang waiting for workers blocked in event streams
    proc = apteryx_rest_instance
    streams = []
    for _ in range(10):
        sock = fcgi_get(FCGI_SOCK_PATH, docroot, "/test/settings/priority", "text/event-stream")
        sock.settimeout(10)
        data = b""
        while b"\r\n\r\n" not in data:
            data += sock.recv(4096)
        assert b"Status: 200" in data
        streams.append(sock)
    try:
        terminate(proc)
    finally:
        for sock in streams:
            sock.close()
