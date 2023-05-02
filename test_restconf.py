import json
import os
import pytest
import requests
import subprocess
import time

from lxml import etree

# TEST CONFIGURATION

host='localhost'
port=8080
docroot='/api'

restconf_headers = {"Accept":"application/yang-data+json"}

APTERYX='LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'
APTERYX_URL=''

# TEST HELPERS

db_default = [
    # Default namespace
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/settings/readonly', 'yes'),
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
    ('/t2:test/settings/volume', '2'),
]

def apteryx_set(path, value):
    os.system('%s -s %s "%s"' % (APTERYX, path, value))

def apteryx_get(path):
    return subprocess.check_output("%s -g %s" % (APTERYX, path), shell=True).strip().decode('utf-8')

@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    os.system("%s -r /test" % (APTERYX))
    assert subprocess.check_output("%s -r %s/test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"
    assert subprocess.check_output("%s -r %s/t2:test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"
    for path,value in db_default:
        apteryx_set(path, value)
    yield
    # After test
    os.system("echo After test")
    assert subprocess.check_output("%s -r %s/test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"
    assert subprocess.check_output("%s -r %s/t2:test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"

# API

@pytest.mark.skip(reason="requires target specific http server configuration")
def test_restconf_root_discovery():
    # Accept: application/xrd+xml
    response = requests.get("http://{}:{}/.well-known/host-meta".format(host,port))
    print(response)
    assert response.status_code == 200
    # assert response.headers["Content-Type"] == "application/xrd+xml"
    assert docroot in response

def test_restconf_root_resource():
    response = requests.get("http://{}:{}{}".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:restconf": {
        "data": {},
        "operations": {},
        "yang-library-version": "2016-06-21"
    }
}
""")

def test_restconf_operations_list_empty():
    response = requests.get("http://{}:{}{}/operations".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "operations" : {} }')

def test_restconf_yang_library_version():
    response = requests.get("http://{}:{}{}/yang-library-version".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "yang-library-version" : "2016-06-21" }')

# This is actually useless as it is only second granularity - you should use ETag
def test_restconf_get_timestamp():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != "0"
    # assert response.headers.get("Last-Modified") == time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    assert response.json() == json.loads('{ "enable": true }')

def test_restconf_get_timestamp_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != "0"
    assert response.json() == json.loads('{ "enable": true }')

def test_restconf_get_if_modified_since():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    last_modified = response.headers.get("Last-Modified")
    assert response.json() == json.loads('{ "enable": true }')
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-Modified-Since': last_modified})
    assert response.status_code == 304
    assert len(response.content) == 0
    time.sleep(1)
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-Modified-Since': last_modified})
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != last_modified
    assert response.json() == json.loads('{ "enable": false }')

def test_restconf_get_if_modified_since_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    last_modified = response.headers.get("Last-Modified")
    assert response.json() == json.loads('{ "enable": true }')
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-Modified-Since': last_modified})
    assert response.status_code == 304
    assert len(response.content) == 0
    time.sleep(1)
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-Modified-Since': last_modified})
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != last_modified
    assert response.json() == json.loads('{ "enable": false }')

def test_restconf_get_etag():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": true }')

def test_restconf_get_etag_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": true }')

def test_restconf_get_if_none_match():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    etag = response.headers.get("Etag")
    assert response.json() == json.loads('{ "enable": true }')
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 304
    assert len(response.content) == 0
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Etag") != None and response.headers.get("Etag") != etag
    assert response.json() == json.loads('{ "enable": false }')

def test_restconf_get_if_none_match_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    etag = response.headers.get("Etag")
    assert response.json() == json.loads('{ "enable": true }')
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 304
    assert len(response.content) == 0
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers={**restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Etag") != None and response.headers.get("Etag") != etag
    assert response.json() == json.loads('{ "enable": false }')

# TODO 3.5.3. Any reserved characters MUST be percent-encoded, according to Sections 2.1 and 2.5 of [RFC3986].
# TODO 3.5.4.  Default Handling

# TODO 7.  Error Reporting
#  error-type = transport|rpc|protocol|application
#           | error-tag               | status code      |
#           +-------------------------+------------------+
#           | in-use                  | 409              |
#           | invalid-value           | 400, 404, or 406 |
#           | (request) too-big       | 413              |
#           | (response) too-big      | 400              |
#           | missing-attribute       | 400              |
#           | bad-attribute           | 400              |
#           | unknown-attribute       | 400              |
#           | bad-element             | 400              |
#           | unknown-element         | 400              |
#           | unknown-namespace       | 400              |
#           | access-denied           | 401 or 403       |
#           | lock-denied             | 409              |
#           | resource-denied         | 409              |
#           | rollback-failed         | 500              |
#           | data-exists             | 409              |
#           | data-missing            | 409              |
#           | operation-not-supported | 405 or 501       |
#           | operation-failed        | 412 or 500       |
#           | partial-operation       | 500              |
#           | malformed-message       | 400 

def test_restconf_error_not_found():
    response = requests.get("http://{}:{}{}/data/test/settings/invalid".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "invalid-value",
            "error-message" : "uri path not found"
        }
        ]
    }
}
    """)

def test_restconf_error_hidden_node():
    response = requests.get("http://{}:{}{}/data/test/settings/hidden".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 403
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)

def test_restconf_error_read_only():
    response = requests.post("http://{}:{}{}/data/test/state".format(host,port,docroot), headers=restconf_headers, data="""{"counter": "123"}""")
    assert response.status_code == 403
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)

def test_restconf_error_write_only():
    response = requests.get("http://{}:{}{}/data/test/settings/writeonly".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 403
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)

def test_restconf_error_unknown_namespace():
    response = requests.get("http://{}:{}{}/data/cabbage:test/settings/writeonly".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 400 or response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    if response.status_code == 400:
        assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "unknown-namespace"
            "error-message" : "namespace not found"
        }
        ]
    }
}
    """)
    else:
        assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "invalid-value",
            "error-message" : "uri path not found"
        }
        ]
    }
}
    """)

# 4.  RESTCONF Methods
#   | RESTCONF | NETCONF                                               |
#   +----------+-------------------------------------------------------+
#   | OPTIONS  | none                                                  |
#   | HEAD     | <get-config>, <get>                                   |
#   | GET      | <get-config>, <get>                                   |
#   | POST     | <edit-config> (nc:operation="create")                 |
#   | POST     | invoke an RPC operation                               |
#   | PUT      | <copy-config> (PUT on datastore)                      |
#   | PUT      | <edit-config> (nc:operation="create/replace")         |
#   | PATCH    | <edit-config> (nc:operation depends on PATCH content) |
#   | DELETE   | <edit-config> (nc:operation="delete")   

# OPTIONS

def test_restconf_options():
    response = requests.options("http://{}:{}{}/data/".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    assert response.headers["allow"] == "GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS"
    # assert response.headers["accept-patch"] == "application/yang-data+xml, application/yang-data+json"
    assert response.headers["accept-patch"] == "application/yang-data+json"

# HEAD

def test_restconf_head():
    response = requests.head("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.content == b''

# GET

def test_restconf_get_single_node_ns_none():
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 1 }')

def test_restconf_get_single_node_ns_aug_none():
    response = requests.get("http://{}:{}{}/data/test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "volume": 1 }')

def test_restconf_get_single_node_ns_default():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 1 }')

def test_restconf_get_single_node_ns_aug_default():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "volume": 1 }')

def test_restconf_get_single_node_ns_other():
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 2 }')

@pytest.mark.skip(reason="augmented sub paths not working")
def test_restconf_get_single_node_ns_aug_other():
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "speed": 2 }')

def test_restconf_get_integer():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 1 }')
    apteryx_set("/test/settings/priority", "2")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "priority": 2 }')

def test_restconf_get_boolean():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "enable": true }')
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "enable": false }')

def test_restconf_get_value_string():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/debug".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "debug": "enable" }')
    apteryx_set("/test/settings/debug", "disable")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/debug".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "debug": "disable" }')

def test_restconf_get_node_null():
    apteryx_set("/test/settings/debug", "")
    response = requests.get("http://{}:{}{}/data/testing:test/settings/debug".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{}')

def test_restconf_get_trunk_no_namespace():
    response = requests.get("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": 1
    }
}
    """)

def test_restconf_get_trunk_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": 1
    }
}
    """)

def test_restconf_get_list_trunk():
    response = requests.get("http://{}:{}{}/data/testing:test/animals".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)

def test_restconf_get_list_trunk_no_namespace():
    response = requests.get("http://{}:{}{}/data/test/animals".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)

def test_restconf_get_list_select_one_trunk():
    response = requests.get("http://{}:{}{}/data/testing:test/animals/animal=cat".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "big"
        }
    ]
}
    """)

@pytest.mark.skip(reason="does not work yet")
def test_restconf_get_list_select_one_by_path_trunk():
    response = requests.get("http://{}:{}{}/data/testing:test/animals/animal/cat".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "big"
        }
    ]
}
    """)

def test_restconf_get_list_select_two_trunk():
    response = requests.get("http://{}:{}{}/data/testing:test/animals/animal=hamster/food=banana".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "food": [
        {
            "name": "banana",
            "type": "fruit"
        }
    ]
}
    """)

def test_restconf_get_leaf_list_node():
    response = requests.get("http://{}:{}{}/data/testing:test/animals/animal=parrot/toys/toy".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "toy": [
        "puzzles",
        "rings"
    ]
}
    """)

# TODO multiple keys
#  /restconf/data/ietf-yang-library:modules-state/module=ietf-interfaces,2014-05-08
#  Missing key values are not allowed, so two consecutive commas are
#   interpreted as a comma, followed by a zero-length string, followed
#   by a comma.  For example, "list1=foo,,baz" would be interpreted as
#   a list named "list1" with three key values, and the second key
#   value is a zero-length string.
#  Note that non-configuration lists are not required to define keys.
#   In this case, a single list instance cannot be accessed.

# 4.8 Query Parameters
#    | content       | GET,    | Select config and/or non-config data    |
#    |               | HEAD    | resources                               |
#    | depth         | GET,    | Request limited subtree depth in the    |
#    |               | HEAD    | reply content                           |
#    | fields        | GET,    | Request a subset of the target resource |
#    |               | HEAD    | contents                                |
#    | filter        | GET,    | Boolean notification filter for event   |
#    |               | HEAD    | stream resources                        |
#    | insert        | POST,   | Insertion mode for "ordered-by user"    |
#    |               | PUT     | data resources                          |
#    | point         | POST,   | Insertion point for "ordered-by user"   |
#    |               | PUT     | data resources                          |
#    | start-time    | GET,    | Replay buffer start time for event      |
#    |               | HEAD    | stream resources                        |
#    | stop-time     | GET,    | Replay buffer stop time for event       |
#    |               | HEAD    | stream resources                        |
#    | with-defaults | GET,    | Control the retrieval of default values |
#    |               | HEAD    |

def test_restconf_query_empty():
    response = requests.get("http://{}:{}{}/data/test/state/uptime?".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "hours": 50,
        "minutes": 30,
        "seconds": 20
    }
}
""")

def test_restconf_query_invalid_queries():
    queries = [
        "die",
        "die=",
        "die=now",
        "die=now&fields=enable",
        "fields=enable&die=now",
        # "&",
        "&&,",
        # "fields=;",
        # "fields=;;",
        # "fields=/",
        # "fields=//",
        # "fields=(",
        # "fields=)",
        # "fields=()",
        "content=all&content=all"
    ]
    for query in queries:
        print("Checking " + query)
        response = requests.get("http://{}:{}{}/data/test/settings?{}".format(host,port,docroot,query), headers=restconf_headers)
        assert response.status_code == 400
        assert len(response.content) > 0
        print(json.dumps(response.json(), indent=4, sort_keys=True))
        assert response.headers["Content-Type"] == "application/yang-data+json"
        assert response.json() == json.loads("""
    {
        "ietf-restconf:errors" : {
            "error" : [
            {
                "error-type" : "application",
                "error-tag" : "malformed-message",
                "error-message" : "malformed request syntax"
            }
            ]
        }
    }
        """)

# Query Content

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_content_all():
    response = requests.get("http://{}:{}{}/data/test/settings?content=all".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": 1
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_content_config():
    response = requests.get("http://{}:{}{}/data/test/settings?content=config".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "volume": 1
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_content_nonconfig():
    response = requests.get("http://{}:{}{}/data/test/settings?content=nonconfig".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "readonly": "yes"
    }
}
    """)

# Query Depth

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_unbounded():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=unbounded".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_1():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=1".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_2():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=2".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
        ]
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_3():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=3".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                }
            }
        ]
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_4():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=4".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                "toy": []
                }
            }
        ]
    }
}
    """)

@pytest.mark.skip(reason="not implemented")
def test_restconf_query_depth_5():
    response = requests.get("http://{}:{}{}/data/test/animals?depth=5".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)

# Query Fields

def test_restconf_query_field_one_node():
    response = requests.get("http://{}:{}{}/data/test/state/uptime?fields=hours".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "hours": 50
    }
}
""")

def test_restconf_query_field_two_nodes():
    response = requests.get("http://{}:{}{}/data/test/state/uptime?fields=days;minutes".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "minutes": 30
    }
}
""")

def test_restconf_query_field_three_nodes():
    response = requests.get("http://{}:{}{}/data/test/state/uptime?fields=days;minutes;hours".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "hours": 50,
        "minutes": 30
    }
}
""")

def test_restconf_query_field_one_path():
    response = requests.get("http://{}:{}{}/data/test/state?fields=uptime/days".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5
        }
    }
}
""")

def test_restconf_query_field_two_paths():
    response = requests.get("http://{}:{}{}/data/test/state?fields=uptime/days;uptime/seconds".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "seconds": 20
        }
    }
}
""")

def test_restconf_query_field_three_paths():
    response = requests.get("http://{}:{}{}/data/test/state?fields=uptime/days;uptime/seconds;uptime/hours".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "hours": 50,
            "seconds": 20
        }
    }
}
""")

def test_restconf_query_field_one_path_two_nodes():
    response = requests.get("http://{}:{}{}/data/test/state?fields=uptime(days;seconds)".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "seconds": 20
        }
    }
}
""")

def test_restconf_query_field_two_paths_two_nodes():
    response = requests.get("http://{}:{}{}/data/test/state?fields=uptime(days;seconds);uptime(hours;minutes)".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "hours": 50,
            "minutes": 30,
            "seconds": 20
        }
    }
}
""")

@pytest.mark.skip(reason="does not work yet")
def test_restconf_query_field_list_one_specific_node():
    response = requests.get("http://{}:{}{}/data/test/animals/animal=mouse?fields=type".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [{
        "type": "little"
    }]
}
""")

@pytest.mark.skip(reason="does not work yet")
def test_restconf_query_field_list_two_specific_nodes():
    response = requests.get("http://{}:{}{}/data/test/animals/animal=mouse?fields=name;type".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [{
        "name": "mouse",
        "type": "little"
    }]
}
""")

@pytest.mark.skip(reason="does not work yet")
def test_restconf_query_field_list_all_nodes():
    response = requests.get("http://{}:{}{}/data/test/animals/animal?fields=name".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat"
        },
        {
            "name": "dog"
        },
        {
            "name": "hamster"
        },
        {
            "name": "mouse"
        },
        {
            "name": "parrot"
        }
    ]
}
""")

# GET /restconf/data?fields=ietf-yang-library:modules-state/module(name;revision)
# POST /restconf/data/example-jukebox:jukebox/playlist=Foo-One?insert=first
# POST /restconf/data/example-jukebox:jukebox/playlist=Foo-One?insert=after&point=%2Fexample-jukebox%3Ajukebox%2Fplaylist%3DFoo-One%2Fsong%3D1
# // filter = /event/event-class='fault'
# GET /streams/NETCONF?filter=%2Fevent%2Fevent-class%3D'fault'
# // filter = /event/severity<=4
# GET /streams/NETCONF?filter=%2Fevent%2Fseverity%3C%3D4
# // filter = /linkUp|/linkDown
# GET /streams/SNMP?filter=%2FlinkUp%7C%2FlinkDown
# // filter = /*/reporting-entity/card!='Ethernet0'
# GET /streams/NETCONF?filter=%2F*%2Freporting-entity%2Fcard%21%3D'Ethernet0'
# // filter = /*/email-addr[contains(.,'company.com')]
# GET /streams/critical-syslog?filter=%2F*%2Femail-addr[contains(.%2C'company.com')]
# // Note: The module name is used as the prefix.
# // filter = (/example-mod:event1/name='joe' and
# //           /example-mod:event1/status='online')
# GET /streams/NETCONF?filter=(%2Fexample-mod%3Aevent1%2Fname%3D'joe'%20and%20%2Fexample-mod%3Aevent1%2Fstatus%3D'online')
# // To get notifications from just two modules (e.g., m1 + m2)
# // filter=(/m1:* or /m2:*)
# GET /streams/NETCONF?filter=(%2Fm1%3A*%20or%20%2Fm2%3A*)
# // start-time = 2014-10-25T10:02:00Z
# GET /streams/NETCONF?start-time=2014-10-25T10%3A02%3A00Z
# // start-time = 2014-10-25T10:02:00Z
# // stop-time = 2014-10-25T12:31:00Z
# GET /mystreams/NETCONF?start-time=2014-10-25T10%3A02%3A00Z&stop-time=2014-10-25T12%3A31%3A00Z
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=report-all
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=report-all-tagged
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=trim
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=explicit


# POST - Create the data resource - fail if it already exists

def test_restconf_create_single_node_ns_none():
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": "2"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "2"

def test_restconf_create_single_node_ns_aug_none():
    apteryx_set("/test/settings/volume", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"volume": "2"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "2"

def test_restconf_create_single_node_ns_default():
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": "2"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "2"

def test_restconf_create_single_node_ns_aug_default():
    apteryx_set("/test/settings/volume", "")
    response = requests.post("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"volume": "2"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "2"

def test_restconf_create_single_node_ns_other():
    apteryx_set("/t2:test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/testing-2:test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": "3"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/priority") == "3"

@pytest.mark.skip(reason="namespace change in json data not working")
def test_restconf_create_single_node_ns_aug_other():
    apteryx_set("/t2:test/settings/speed", "")
    response = requests.post("http://{}:{}{}/data/testing-2:test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"testing2-augmented:speed": "3"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/priority") == "3"

def test_restconf_create_string():
    apteryx_set("/test/settings/description", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"description": "this is a description"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/description") == "this is a description"

@pytest.mark.skip(reason="should fail to create and return (CONFLICT)")
def test_restconf_create_existing_string():
    apteryx_set("/test/settings/description", "already set")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"description": "this is a description"}""")
    assert response.status_code == 409
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "data-exists"
            "error-message" : "object already exists"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/description") == "already set"

def test_restconf_create_null():
    apteryx_set("/test/settings/description", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"description": ""}""")
    assert response.status_code == 201
    assert apteryx_get("/test/settings/description") == "Not found"

def test_restconf_create_readonly():
    response = requests.post("http://{}:{}{}/data/test/state".format(host,port,docroot), headers=restconf_headers, data="""{"counter": 123}""")
    assert response.status_code == 403
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/state/counter") == "42"

def test_restconf_create_invalid_path():
    response = requests.post("http://{}:{}{}/data/test/cabbage".format(host,port,docroot), headers=restconf_headers, data="""{"description": "this is a description"}""")
    assert response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "invalid-value",
            "error-message" : "uri path not found"
        }
        ]
    }
}
    """)

def test_restconf_create_enum():
    apteryx_set("/test/settings/debug", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"debug": "disable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    apteryx_set("/test/settings/debug", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"debug": "enable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"

def test_restconf_create_invalid_enum():
    apteryx_set("/test/settings/debug", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "malformed-message",
            "error-message" : "malformed request syntax"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/debug") == "Not found"

def test_restconf_create_hidden():
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"hidden": "cabbage"}""")
    assert response.status_code == 403
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/hidden") == "friend"

def test_restconf_create_out_of_range_integer():
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": 1}""")
    assert response.status_code == 201
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": 0}""")
    assert response.status_code == 400
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": 6}""")
    assert response.status_code == 400
    apteryx_set("/test/settings/priority", "")
    response = requests.post("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"priority": 55}""")
    assert response.status_code == 400
    assert apteryx_get("/test/settings/priority") == "Not found"

def test_restconf_create_list_entry_ok():
    tree = """
{
    "animal" : [
        {
            "name": "frog"
        }
    ] 
}
"""
    response = requests.post("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 201

@pytest.mark.skip(reason="should fail to create return 409(CONFLICT)")
def test_restconf_create_list_entry_exists():
    tree = """
{
    "animal" : [
        {
            "name": "cat",
            "type": "little"
        }
    ] 
}
"""
    response = requests.post("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 409
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "data-exists"
            "error-message" : "object already exists"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/animals/animal/cat/type") == "1"

# PUT - Create or replace the entire data resource
# The entire configuration datastore contents are
# being replaced. Any child nodes not present in the <data> element
# but present in the server will be deleted.

def test_restconf_replace_list_entry_new():
    tree = """
{
    "animal" : [
        {
            "name": "frog",
            "type": "little"
        }
    ] 
}
"""
    response = requests.put("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 204

@pytest.mark.skip(reason="should replace all existing objects")
def test_restconf_replace_list_entry_exists():
    tree = """
{
    "animal" : [
        {
            "name": "cat",
            "colour": "purple"
        }
    ] 
}
"""
    response = requests.put("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 204
    assert apteryx_get("/test/animals/animal/cat/name") == "cat"
    assert apteryx_get("/test/animals/animal/cat/colour") == "purple"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"

def test_restconf_replace_if_not_modified_since():
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    response = requests.put("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers={**restconf_headers, 'If-Unmodified-Since': last_modified}, data="""{"priority": "3"}""")
    assert response.status_code == 412
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed",
            "error-message" : "object modified"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/priority") == "2"

def test_restconf_replace_if_not_modified_since_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    response = requests.put("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers={**restconf_headers, 'If-Unmodified-Since': last_modified}, data="""{"priority": "3"}""")
    assert response.status_code == 412
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed",
            "error-message" : "object modified"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/priority") == "2"

def test_restconf_replace_if_match():
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    etag = response.headers.get("Etag")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    response = requests.put("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers={**restconf_headers, 'If-Match': etag}, data="""{"priority": "3"}""")
    assert response.status_code == 412
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed",
            "error-message" : "object modified"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/priority") == "2"

def test_restconf_replace_if_match_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    etag = response.headers.get("Etag")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    response = requests.put("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers={**restconf_headers, 'If-Match': etag}, data="""{"priority": "3"}""")
    assert response.status_code == 412
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed",
            "error-message" : "object modified"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/priority") == "2"

# PATCH - Create or update a data resource but not create resource instance

def test_restconf_update_string():
    apteryx_set("/test/settings/description", "previously set")
    response = requests.patch("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"description": "this is a description"}""")
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/description") == "this is a description"

def test_restconf_update_missing_string():
    apteryx_set("/test/settings/description", "")
    response = requests.patch("http://{}:{}{}/data/test/settings".format(host,port,docroot), headers=restconf_headers, data="""{"description": "this is a description"}""")
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/description") == "this is a description"

def test_restconf_update_existing_list_entry():
    tree = """
{
    "animal" : [
        {
            "name": "cat",
            "colour": "purple"
        }
    ] 
}
"""
    response = requests.patch("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 204
    assert apteryx_get("/test/animals/animal/cat/name") == "cat"
    assert apteryx_get("/test/animals/animal/cat/colour") == "purple"
    assert apteryx_get("/test/animals/animal/cat/type") == "1"

@pytest.mark.skip(reason="should not create a new list entry and return 404")
def test_restconf_update_missing_list_entry():
    tree = """
{
    "animal" : [
        {
            "name": "frog",
            "type": "little"
        }
    ] 
}
"""
    response = requests.patch("http://{}:{}{}/data/test/animals".format(host,port,docroot), data=tree, headers=restconf_headers)
    assert response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "invalid-value",
            "error-message" : "uri path not found"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/animals/animal/frog/name") == "Not found"
    assert apteryx_get("/test/animals/animal/frog/type") == "Not found"

# DELETE

def test_restconf_delete_single_node_ns_none():
    response = requests.delete("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_single_node_ns_aug_none():
    response = requests.delete("http://{}:{}{}/data/test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_single_node_ns_default():
    response = requests.delete("http://{}:{}{}/data/testing:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_single_node_ns_aug_default():
    response = requests.delete("http://{}:{}{}/data/testing:test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/test/settings/volume".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

@pytest.mark.skip(reason="sch_lookup does not support namespaces")
def test_restconf_delete_single_node_ns_other():
    response = requests.delete("http://{}:{}{}/data/testing-2:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')
    response = requests.get("http://{}:{}{}/data/test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 1 }')

@pytest.mark.skip(reason="augmented sub paths not working")
def test_restconf_delete_single_node_ns_aug_other():
    response = requests.delete("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_trunk_ok():
    response = requests.delete("http://{}:{}{}/data/testing:test/animals".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing:test/animals".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_trunk_denied():
    response = requests.delete("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "protocol",
            "error-tag" : "access-denied"
        }
        ]
    }
}
    """)

def test_restconf_delete_list_entry():
    response = requests.delete("http://{}:{}{}/data/testing:test/animals/animal=cat".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing:test/animals".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "dog",
                "colour": "brown"
            },
            {
                "name": "hamster",
                "food" : [
                   {
                        "name": "banana",
                        "type": "fruit"
                    },
                    {
                        "name": "nuts",
                        "type": "kibble"
                    }
                 ],
                "type": "little"
            },
            {
                "name": "mouse",
                "type": "little",
                "colour": "grey"
            },
            {
                "name": "parrot",
                "type": "big",
                "colour": "blue",
                "toys": {
                    "toy": [
                        "puzzles",
                        "rings"
                    ]
                }
            }
        ]
    }
}
""")

# TODO RPC

# TODO Event Stream resource

# ietf-yang-library Schema Resource
# module: ietf-yang-library
#   +--ro yang-library
#   |  +--ro module-set* [name]
#   |  |  +--ro name                  string
#   |  |  +--ro module* [name]
#   |  |  |  +--ro name         yang:yang-identifier
#   |  |  |  +--ro revision?    revision-identifier
#   |  |  |  +--ro namespace    inet:uri
#   |  |  |  +--ro location*    inet:uri
#   |  |  |  +--ro submodule* [name]
#   |  |  |  |  +--ro name        yang:yang-identifier
#   |  |  |  |  +--ro revision?   revision-identifier
#   |  |  |  |  +--ro location*   inet:uri
#   |  |  |  +--ro feature*     yang:yang-identifier
#   |  |  |  +--ro deviation*   -> ../../module/name
#   |  |  +--ro import-only-module* [name revision]
#   |  |     +--ro name         yang:yang-identifier
#   |  |     +--ro revision     union
#   |  |     +--ro namespace    inet:uri
#   |  |     +--ro location*    inet:uri
#   |  |     +--ro submodule* [name]
#   |  |        +--ro name        yang:yang-identifier
#   |  |        +--ro revision?   revision-identifier
#   |  |        +--ro location*   inet:uri
#   |  +--ro schema* [name]
#   |  |  +--ro name          string
#   |  |  +--ro module-set*   -> ../../module-set/name
#   |  +--ro datastore* [name]
#   |  |  +--ro name      ds:datastore-ref
#   |  |  +--ro schema    -> ../../schema/name
#   |  +--ro content-id    string
#   x--ro modules-state
#      x--ro module-set-id    string
#      x--ro module* [name revision]
#         x--ro name                yang:yang-identifier
#         x--ro revision            union
#         +--ro schema?             inet:uri
#         x--ro namespace           inet:uri
#         x--ro feature*            yang:yang-identifier
#         x--ro deviation* [name revision]
#         |  x--ro name        yang:yang-identifier
#         |  x--ro revision    union
#         x--ro conformance-type    enumeration
#         x--ro submodule* [name revision]
#            x--ro name        yang:yang-identifier
#            x--ro revision    union
#            +--ro schema?     inet:uri
#   notifications:
#     +---n yang-library-update
#     |  +--ro content-id    -> /yang-library/content-id
#     x---n yang-library-change
#        x--ro module-set-id    -> /modules-state/module-set-id
def test_restconf_yang_library_tree():
    response = requests.get("http://{}:{}{}/data/ietf-yang-library:yang-library".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    tree = response.json()
    contentid = tree['yanglib:yang-library']['content-id']
    assert contentid is not None
    assert tree == json.loads("""
{
    "yanglib:yang-library": {
        "content-id": "%s",
        "module-set": [
            {
                "module": [
                    {
                        "name": "ietf-yang-library",
                        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-library",
                        "revision": "2019-01-04"
                    },
                    {
                        "name": "testing",
                        "namespace": "https://github.com/alliedtelesis/apteryx",
                        "revision": "2023-01-01"
                    },
                    {
                        "name": "testing-2",
                        "namespace": "http://test.com/ns/yang/testing-2",
                        "revision": "2023-02-01"
                    }
                ],
                "name": "modules"
            }
        ]
    }
}
""" % (contentid))

# TODO 9.  RESTCONF Monitoring
# module: ietf-restconf-monitoring
#   +--ro restconf-state
#      +--ro capabilities
#      |  +--ro capability*   inet:uri
#      +--ro streams
#         +--ro stream* [name]
#            +--ro name                        string
#            +--ro description?                string
#            +--ro replay-support?             boolean
#            +--ro replay-log-creation-time?   yang:date-and-time
#            +--ro access* [encoding]
#               +--ro encoding  string
#               +--ro location  inet:uri
