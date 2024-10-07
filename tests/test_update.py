import apteryx
import json
import pytest
import requests
from conftest import server_uri, server_auth, docroot, set_restconf_headers, rfc3986_reserved


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


def test_restconf_update_list_non_key_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        apteryx.prune("/test/settings/users")
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "33")
        data = json.dumps({"age": 74})
        response = requests.patch(f"{server_uri}{docroot}/data/test/settings/users={encoded}", auth=server_auth, data=data, headers=set_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 204, message
        assert len(response.content) == 0, message
        print(apteryx.get_tree("/test/settings/users"))
        assert apteryx.get(f"/test/settings/users/{key}/age") == "74", message
