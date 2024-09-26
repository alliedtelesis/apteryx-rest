import json
import requests
import time
import re
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
    response = requests.put("{}{}/data/test/animals/animal".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
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
    response = requests.put("{}{}/data/test/animals/animal".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 204
    print(apteryx_traverse("/test/animals/animal/cat"))
    assert apteryx_get("/test/animals/animal/cat") == "Not found"
    assert apteryx_get("/test/animals/animal/cat/name") == "cat"
    assert apteryx_get("/test/animals/animal/cat/colour") == "purple"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"


def test_restconf_replace_if_not_modified_since():
    """
    Using last modified from get will fail when we modify the variable and try a put with If-Unmodified-Since.
    """
    response = requests.get("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**get_restconf_headers, 'If-Unmodified-Since': last_modified}
    response = requests.put("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"priority": "3"}""")
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


def test_restconf_replace_if_not_modified_since_2():
    """
    Using last modified adjusted one second past the time from the get will work with PUT and If-Unmodified-Since.
    This test was added because original code used != instead of > to check timestamps, so we need a time that is
    not equal.
    """
    response = requests.get("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "priority": 1 }')
    last_modified = response.headers.get("Last-Modified")

    # Adjust last_modified one second into the future. If we run this test at 23:59:59 it's an automatic pass.
    xxx = re.match("^(.*)([0-9][0-9]):([0-9][0-9]):([0-9][0-9])(.*)$", last_modified)
    sec = int(xxx.group(4))
    minu = int(xxx.group(3))
    hour = int(xxx.group(2))
    sec += 1
    if sec == 60:
        minu += 1
        sec = 0
        if minu == 60:
            hour += 1
            minu = 0
            if hour == 24:
                return
    time.sleep(1.1)
    last_modified = f"{xxx.group(1)}{hour:02}:{minu:02}:{sec:02}{xxx.group(5)}"
    headers = {**get_restconf_headers, 'If-Unmodified-Since': last_modified}
    response = requests.put("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"priority": 3}""")
    assert response.status_code == 204
    assert apteryx_get("/test/settings/priority") == "3"


def test_restconf_replace_if_not_modified_since_namespace():
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "testing:priority": 1 }')
    last_modified = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**get_restconf_headers, 'If-Unmodified-Since': last_modified}
    response = requests.put("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"testing:priority": "3"}""")
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
    assert response.status_code == 200 and len(response.content) > 0 and response.json() == json.loads('{ "testing:priority": 1 }')
    etag = response.headers.get("Etag")
    time.sleep(1)
    apteryx_set("/test/settings/priority", "2")
    headers = {**set_restconf_headers, 'If-Match': etag}
    response = requests.put("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=headers, data="""{"testing:priority": "3"}""")
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


def test_restconf_replace_existing_list_key():
    data = '{"name" : "fox"}'
    response = requests.put("{}{}/data/test/animals/animal=cat/name".format(server_uri, docroot), auth=server_auth, data=data, headers=set_restconf_headers)
    assert response.status_code == 405


def test_restconf_replace_existing_list_non_key():
    data = '{"colour" : "pink"}'
    response = requests.put("{}{}/data/test/animals/animal=cat/colour".format(server_uri, docroot), auth=server_auth, data=data, headers=set_restconf_headers)
    assert response.status_code == 204
