import json
import requests
from conftest import server_uri, server_auth, docroot, get_restconf_headers


# ietf-yang-library
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
def test_restconf_yang_library_tree():
    response = requests.get("{}{}/data/ietf-yang-library:yang-library".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    tree = response.json()
    contentid = tree['ietf-yang-library:yang-library']['content-id']
    assert contentid is not None
    assert tree == json.loads("""
{
    "ietf-yang-library:yang-library": {
        "content-id": "%s",
        "datastore" : [
            {
                "name" : "ietf-datastores:running",
                "schema" : "common"
            }
        ],
        "module-set": [
            {
                "module": [
                    {
                        "deviation": [
                            "user-example-deviation"
                        ],
                        "feature": [
                            "ether",
                            "fast"
                        ],
                        "name": "example",
                        "namespace": "http://example.com/ns/interfaces",
                        "revision": "2023-04-04"
                    },
                    {
                        "name": "ietf-restconf-monitoring",
                        "namespace": "urn:ietf:params:xml:ns:yang:ietf-restconf-monitoring",
                        "revision": "2017-01-26"
                    },
                    {
                        "name": "ietf-yang-library",
                        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-library",
                        "revision": "2019-01-04"
                    },
                    {
                        "name": "testing",
                        "namespace": "http://test.com/ns/yang/testing",
                        "revision": "2023-01-01"
                    },
                    {
                        "name": "testing-2",
                        "namespace": "http://test.com/ns/yang/testing-2",
                        "revision": "2023-02-01"
                    },
                    {
                        "name": "testing-3",
                        "namespace": "http://test.com/ns/yang/testing-3",
                        "revision": "2023-03-01"
                    },
                    {
                        "name": "testing2-augmented",
                        "namespace": "http://test.com/ns/yang/testing2-augmented",
                        "revision": "2023-02-02"
                    }
                ],
                "name": "common"
            }
        ],
       "schema" : [
            {
                "module-set" : [
                "common"
             ],
            "name" : "common"
            }
       ]
    }
}
""" % (contentid))


def test_restconf_yang_library_data():
    response = requests.get("{}{}/data".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    tree = response.json()
    contentid = tree['ietf-yang-library:yang-library']['content-id']
    assert contentid is not None
    assert tree == json.loads("""
{
    "ietf-yang-library:yang-library": {
        "content-id": "%s",
        "datastore" : [
          {
             "name" : "ietf-datastores:running",
             "schema" : "common"
          }
        ],
        "module-set": [
            {
                "module": [
                    {
                        "deviation": [
                            "user-example-deviation"
                        ],
                        "feature": [
                            "ether",
                            "fast"
                        ],
                        "name": "example",
                        "namespace": "http://example.com/ns/interfaces",
                        "revision": "2023-04-04"
                    },
                    {
                        "name": "ietf-restconf-monitoring",
                        "namespace": "urn:ietf:params:xml:ns:yang:ietf-restconf-monitoring",
                        "revision": "2017-01-26"
                    },
                    {
                        "name": "ietf-yang-library",
                        "namespace": "urn:ietf:params:xml:ns:yang:ietf-yang-library",
                        "revision": "2019-01-04"
                    },
                    {
                        "name": "testing",
                        "namespace": "http://test.com/ns/yang/testing",
                        "revision": "2023-01-01"
                    },
                    {
                        "name": "testing-2",
                        "namespace": "http://test.com/ns/yang/testing-2",
                        "revision": "2023-02-01"
                    },
                    {
                        "name": "testing-3",
                        "namespace": "http://test.com/ns/yang/testing-3",
                        "revision": "2023-03-01"
                    },
                    {
                        "name": "testing2-augmented",
                        "namespace": "http://test.com/ns/yang/testing2-augmented",
                        "revision": "2023-02-02"
                    }
                ],
                "name": "common"
            }
        ],
        "schema" : [
            {
                "module-set" : [
                    "common"
                ],
                "name" : "common"
            }
        ]
    }
}
""" % (contentid))


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
def test_restconf_monitoring_tree():
    response = requests.get("{}{}/data/ietf-restconf-monitoring:restconf-state".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    tree = response.json()
    assert 'ietf-restconf-monitoring:restconf-state' in tree
    assert 'capabilities' in tree['ietf-restconf-monitoring:restconf-state']
    assert 'capability' in tree['ietf-restconf-monitoring:restconf-state']['capabilities']
    assert len(tree['ietf-restconf-monitoring:restconf-state']['capabilities']['capability']) > 0
