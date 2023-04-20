import os
import subprocess
import pytest
import requests
import json
from lxml import etree

# TEST CONFIGURATION

host='localhost'
port=8080
docroot='/api'

restconf_headers = {"Accept":"application/yang-data+json"}

APTERYX='LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'

# TEST HELPERS

db_default = [
    # Default namespace
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
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
    os.system("%s -s %s %s" % (APTERYX, path, value))

def apteryx_get(path):
    return subprocess.check_output("%s -g %s" % (APTERYX, path), shell=True).strip().decode('utf-8')

@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    os.system("%s -r /test" % (APTERYX))
    for path,value in db_default:
        apteryx_set(path, value)
    yield
    # After test
    os.system("echo After test")
    os.system("%s -r /test" % (APTERYX))

# API

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

@pytest.mark.skip(reason="does not work yet")
def test_restconf_get_single_node_ns_aug_other():
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "speed": 2 }')

def test_restconf_get_namespace_invalid():
    response = requests.get("http://{}:{}{}/data/cabbage:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 404
    assert len(response.content) == 0

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

# TODO leaf-list

# TODO multiple keys
#  /restconf/data/example-top:top/list1=key1,key2,key3

@pytest.mark.skip(reason="does not work yet")
def test_restconf_get_timestamp():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != "0"
    assert response.json() == json.loads('{ "enable": true }')

@pytest.mark.skip(reason="does not work yet")
def test_restconf_get_timestamp_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") != None and response.headers.get("Last-Modified") != "0"
    assert response.json() == json.loads('{ "enable": true }')

def test_restconf_get_etag():
    response = requests.get("http://{}:{}{}/data/test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": true }')

@pytest.mark.skip(reason="does not work yet")
def test_restconf_get_etag_namespace():
    response = requests.get("http://{}:{}{}/data/testing:test/settings/enable".format(host,port,docroot), headers=restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": true }')

# TODO query parameters
#    | content       | GET,    | Select config and/or non-config data    |
#    |               | HEAD    | resources                               |
#    |               |         |                                         |
#    | depth         | GET,    | Request limited subtree depth in the    |
#    |               | HEAD    | reply content                           |
#    |               |         |                                         |
#    | fields        | GET,    | Request a subset of the target resource |
#    |               | HEAD    | contents                                |
#    |               |         |                                         |
#    | filter        | GET,    | Boolean notification filter for event   |
#    |               | HEAD    | stream resources                        |
#    |               |         |                                         |
#    | insert        | POST,   | Insertion mode for "ordered-by user"    |
#    |               | PUT     | data resources                          |
#    |               |         |                                         |
#    | point         | POST,   | Insertion point for "ordered-by user"   |
#    |               | PUT     | data resources                          |
#    |               |         |                                         |
#    | start-time    | GET,    | Replay buffer start time for event      |
#    |               | HEAD    | stream resources                        |
#    |               |         |                                         |
#    | stop-time     | GET,    | Replay buffer stop time for event       |
#    |               | HEAD    | stream resources                        |
#    |               |         |                                         |
#    | with-defaults | GET,    | Control the retrieval of default values |
#    |               | HEAD    |

# GET /restconf/data/example-events:events?content=all
# GET /restconf/data/example-events:events?content=config
# GET /restconf/data/example-events:events?content=nonconfig
# GET /restconf/data/example-jukebox:jukebox?depth=unbounded
# GET /restconf/data/example-jukebox:jukebox?depth=1
# GET /restconf/data/example-jukebox:jukebox?depth=3
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
# GET /restconf/data/example:interfaces/interface=eth1?with-defaults=report-all

# HEAD

def test_restconf_head_single_node():
    response = requests.head("http://{}:{}{}/data/testing-2:test/settings/priority".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.content == b''

# TODO POST
# TODO 3.4.1.1.  Timestamp "Last-Modified" header field and "If-Modified-Since" "If-Unmodified-Since"
# TODO 3.4.1.2.  Entity-Tag "ETag" header field and "If-Match" and "If-None-Match"

# TODO PUT

# TODO PATCH

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

@pytest.mark.skip(reason="does not work yet")
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

@pytest.mark.skip(reason="does not work yet")
def test_restconf_delete_single_node_ns_aug_other():
    response = requests.delete("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_restconf_delete_trunk():
    response = requests.delete("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}{}/data/testing:test/settings".format(host,port,docroot), headers=restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

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


# TODO Schema resource
#       GET /restconf/data/ietf-yang-library:modules-state/\
#           module=example-jukebox,2016-08-15/schema HTTP/1.1
#       Host: example.com
#       Accept: application/yang-data+json

#    The server might respond as follows:

#       HTTP/1.1 200 OK
#       Date: Thu, 26 Jan 2017 20:56:30 GMT
#       Server: example-server
#       Content-Type: application/yang-data+json

#       {
#         "ietf-yang-library:schema" :
#          "https://example.com/mymodules/example-jukebox/2016-08-15"
#       }

# TODO Event Stream resource

# TODO errors
    #           | error-tag               | status code      |
    #           +-------------------------+------------------+
    #           | in-use                  | 409              |
    #           |                         |                  |
    #           | invalid-value           | 400, 404, or 406 |
    #           |                         |                  |
    #           | (request) too-big       | 413              |
    #           |                         |                  |
    #           | (response) too-big      | 400              |
    #           |                         |                  |
    #           | missing-attribute       | 400              |
    #           |                         |                  |
    #           | bad-attribute           | 400              |
    #           |                         |                  |
    #           | unknown-attribute       | 400              |
    #           |                         |                  |
    #           | bad-element             | 400              |
    #           |                         |                  |
    #           | unknown-element         | 400              |
    #           |                         |                  |
    #           | unknown-namespace       | 400              |
    #           |                         |                  |
    #           | access-denied           | 401 or 403       |
    #           |                         |                  |
    #           | lock-denied             | 409              |
    #           |                         |                  |
    #           | resource-denied         | 409              |
    #           |                         |                  |
    #           | rollback-failed         | 500              |
    #           |                         |                  |
    #           | data-exists             | 409              |
    #           |                         |                  |
    #           | data-missing            | 409              |
    #           |                         |                  |
    #           | operation-not-supported | 405 or 501       |
    #           |                         |                  |
    #           | operation-failed        | 412 or 500       |
    #           |                         |                  |
    #           | partial-operation       | 500              |
    #           |                         |                  |
    #           | malformed-message       | 400 
    #   HTTP/1.1 409 Conflict
    #   Date: Thu, 26 Jan 2017 20:56:30 GMT
    #   Server: example-server
    #   Content-Type: application/yang-data+json

    #   {
    #     "ietf-restconf:errors" : {
    #       "error" : [
    #         {
    #           "error-type" : "protocol",
    #           "error-tag" : "lock-denied",
    #           "error-message" : "Lock failed; lock already held"
    #         }
    #       ]
    #     }
    #   }