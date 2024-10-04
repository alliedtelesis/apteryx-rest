import apteryx
import json
import pytest
import requests
from conftest import server_uri, server_auth, docroot, set_restconf_headers


def test_restconf_update_string():
    apteryx.set("/test/settings/description", "previously set")
    data = """{"description": "this is a description"}"""
    response = requests.patch("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "this is a description"


def test_restconf_update_missing_string():
    apteryx.set("/test/settings/description", "")
    data = """{"description": "this is a description"}"""
    response = requests.patch("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "this is a description"


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
    response = requests.patch("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 204
    assert apteryx.get("/test/animals/animal/cat/name") == "cat"
    assert apteryx.get("/test/animals/animal/cat/colour") == "purple"
    assert apteryx.get("/test/animals/animal/cat/type") == "1"


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
    response = requests.patch("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
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
    assert apteryx.get("/test/animals/animal/frog/name") is None
    assert apteryx.get("/test/animals/animal/frog/type") is None


def test_restconf_update_existing_list_key():
    data = '{"name" : "fox"}'
    response = requests.patch("{}{}/data/test/animals/animal=cat".format(server_uri, docroot), auth=server_auth, data=data, headers=set_restconf_headers)
    assert response.status_code == 405


def test_restconf_update_existing_list_non_key():
    data = '{"colour" : "pink"}'
    response = requests.patch("{}{}/data/test/animals/animal=cat".format(server_uri, docroot), auth=server_auth, data=data, headers=set_restconf_headers)
    assert response.status_code == 204
