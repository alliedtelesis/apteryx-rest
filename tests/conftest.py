import json
import os
import pytest
import requests
import subprocess
import time


# TEST CONFIGURATION

server_uri = 'http://localhost:8080'
server_auth = None
# server_uri = 'https://192.168.6.2:443'
# server_auth = requests.auth.HTTPBasicAuth('manager', 'friend')
docroot = '/api'

APTERYX = 'LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'
# APTERYX_URL='tcp://192.168.6.2:9999:'
APTERYX_URL = ''

get_restconf_headers = {"Accept": "application/yang-data+json"}
set_restconf_headers = {"Content-Type": "application/yang-data+json"}

# TEST HELPERS

db_default = [
    # Default namespace
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/settings/readonly', '0'),
    ('/test/settings/hidden', 'friend'),
    ('/test/state/counter', '42'),
    ('/test/state/uptime/days', '5'),
    ('/test/state/uptime/hours', '50'),
    ('/test/state/uptime/minutes', '30'),
    ('/test/state/uptime/seconds', '20'),
    ('/test/animals/animal/cat/name', 'cat'),
    ('/test/animals/animal/cat/type', '1'),
    ('/test/animals/animal/dog/name', 'dog'),
    ('/test/animals/animal/dog/colour', 'brown'),
    ('/test/animals/animal/mouse/name', 'mouse'),
    ('/test/animals/animal/mouse/type', '2'),
    ('/test/animals/animal/mouse/colour', 'grey'),
    ('/test/animals/animal/hamster/name', 'hamster'),
    ('/test/animals/animal/hamster/type', '2'),
    ('/test/animals/animal/hamster/food/banana/name', 'banana'),
    ('/test/animals/animal/hamster/food/banana/type', 'fruit'),
    ('/test/animals/animal/hamster/food/nuts/name', 'nuts'),
    ('/test/animals/animal/hamster/food/nuts/type', 'kibble'),
    ('/test/animals/animal/parrot/name', 'parrot'),
    ('/test/animals/animal/parrot/type', '1'),
    ('/test/animals/animal/parrot/colour', 'blue'),
    ('/test/animals/animal/parrot/toys/toy/rings', 'rings'),
    ('/test/animals/animal/parrot/toys/toy/puzzles', 'puzzles'),
    # Default namespace augmented path
    ('/test/settings/volume', '1'),
    # Non-default namespace same path as default
    ('/t2:test/settings/priority', '2'),
    # Non-default namespace augmented path
    ('/t2:test/settings/speed', '2'),
]


def apteryx_set(path, value):
    assert subprocess.check_output('%s -s %s%s "%s"' % (APTERYX, APTERYX_URL, path, value), shell=True).strip().decode('utf-8') != "Failed"


def apteryx_get(path):
    return subprocess.check_output("%s -g %s%s" % (APTERYX, APTERYX_URL, path), shell=True).strip().decode('utf-8')


def apteryx_prune(path):
    assert subprocess.check_output("%s -r %s%s" % (APTERYX, APTERYX_URL, path), shell=True).strip().decode('utf-8') != "Failed"


@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    os.system("%s -r /test" % (APTERYX))
    apteryx_prune("/test")
    apteryx_prune("/t2:test")
    for path, value in db_default:
        apteryx_set(path, value)
    yield
    # After test
    os.system("echo After test")
    apteryx_prune("/test")
    apteryx_prune("/t2:test")
