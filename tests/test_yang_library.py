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
                    },
                    {
                        "name": "testing2-augmented",
                        "namespace": "http://test.com/ns/yang/testing2-augmented",
                        "revision": "2023-02-02"
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
