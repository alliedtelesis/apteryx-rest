import json
import requests
import time
from conftest import server_uri, server_auth, docroot, apteryx_set, apteryx_get, apteryx_traverse, get_restconf_headers, set_restconf_headers


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
    response = requests.put("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 204


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
    response = requests.put("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 204
    print(apteryx_traverse("/test/animals/animal/cat"))
    assert apteryx_get("/test/animals/animal/cat") == "Not found"
    assert apteryx_get("/test/animals/animal/cat/name") == "cat"
    assert apteryx_get("/test/animals/animal/cat/colour") == "purple"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"


def test_restconf_replace_if_not_modified_since():
    response = requests.get("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**get_restconf_headers, 'If-Unmodified-Since': last_modified}
    response = requests.put("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"priority": "3"}""")
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
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**get_restconf_headers, 'If-Unmodified-Since': last_modified}
    response = requests.put("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"priority": "3"}""")
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
    response = requests.get("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    etag = response.headers.get("Etag")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    data = """{"priority": "3"}"""
    headers = {**set_restconf_headers, 'If-Match': etag}
    response = requests.put("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data=data)
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
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    etag = response.headers.get("Etag")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**set_restconf_headers, 'If-Match': etag}
    response = requests.put("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"priority": "3"}""")
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
