import apteryx
import json
import requests
from conftest import server_uri, server_auth, docroot, get_restconf_headers, set_restconf_headers, rfc3986_reserved


def test_restconf_delete_single_node_ns_none():
    response = requests.delete("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") is None


def test_restconf_delete_single_node_ns_aug_none():
    response = requests.delete("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/volume") is None


def test_restconf_delete_single_node_ns_default():
    response = requests.delete("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") is None


def test_restconf_delete_single_node_ns_aug_default():
    response = requests.delete("{}{}/data/testing:test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/volume") is None


def test_restconf_delete_single_node_ns_other():
    response = requests.delete("{}{}/data/testing-2:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t2:test/settings/volume") is None
    assert apteryx.get("/test/settings/priority") == "1"


def test_restconf_delete_single_node_ns_aug_other():
    response = requests.delete("{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t2:test/settings/speed") is None
    assert apteryx.get("/t2:test/settings/priority") == "2"


def test_restconf_delete_trunk_ns_none():
    response = requests.delete("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    print(apteryx.get_tree("/test/animals"))
    response = requests.get("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')


def test_restconf_delete_trunk_ns_default():
    response = requests.delete("{}{}/data/testing:test/animals".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    response = requests.get("{}{}/data/testing:test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')


def test_restconf_delete_trunk_ns_other():
    response = requests.delete("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t2:test/settings/priority") is None
    assert apteryx.get("/t2:test/settings/speed") is None


def test_restconf_delete_trunk_denied():
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
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


def test_restconf_delete_trunk_hidden():
    # Remove the readonly field so there is nothing illiegal to delete
    apteryx.set("/test/settings/readonly", "")
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") is None
    assert apteryx.get("/test/settings/enable") is None
    assert apteryx.get("/test/settings/priority") is None
    assert apteryx.get("/test/settings/hidden") == "friend"


def test_restconf_delete_trunk_nonschema():
    # Remove the readonly field so there is nothing illiegal to delete
    apteryx.set("/test/settings/readonly", "")
    apteryx.set("/test/settings/vegetable", "cabagge")
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") is None
    assert apteryx.get("/test/settings/enable") is None
    assert apteryx.get("/test/settings/priority") is None
    assert apteryx.get("/test/settings/hidden") == "friend"
    assert apteryx.get("/test/settings/vegetable") == "cabagge"


def test_restconf_delete_trunk_config_only():
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers={**set_restconf_headers, 'X-Config-Only': "on"})
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") is None
    assert apteryx.get("/test/settings/enable") is None
    assert apteryx.get("/test/settings/priority") is None
    assert apteryx.get("/test/settings/readonly") == "0"
    assert apteryx.get("/test/settings/hidden") == "friend"


def test_restconf_delete_list_select_one():
    response = requests.delete("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/name") is None
    assert apteryx.get("/test/animals/animal/cat/type") is None
    assert apteryx.get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx.get('/test/animals/animal/dog/colour') == 'brown'


def test_restconf_delete_list_select_by_path_one():
    response = requests.delete("{}{}/data/testing:test/animals/animal/cat".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/name") is None
    assert apteryx.get("/test/animals/animal/cat/type") is None
    assert apteryx.get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx.get('/test/animals/animal/dog/colour') == 'brown'


def test_restconf_delete_list_select_two():
    response = requests.delete("{}{}/data/testing:test/animals/animal=hamster/food=banana".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/hamster/food/banana/name") is None
    assert apteryx.get("/test/animals/animal/hamster/food/banana/type") is None
    assert apteryx.get('/test/animals/animal/hamster/food/nuts/name') == 'nuts'
    assert apteryx.get('/test/animals/animal/hamster/food/nuts/type') == 'kibble'


def test_restconf_delete_list_by_path_select_two():
    response = requests.delete("{}{}/data/testing:test/animals/animal/hamster/food/banana".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/hamster/food/banana/name") is None
    assert apteryx.get("/test/animals/animal/hamster/food/banana/type") is None
    assert apteryx.get('/test/animals/animal/hamster/food/nuts/name') == 'nuts'
    assert apteryx.get('/test/animals/animal/hamster/food/nuts/type') == 'kibble'


def test_restconf_delete_list_by_path_select_list_leaf():
    response = requests.delete("{}{}/data/testing:test/animals/animal/parrot/toys/toy/puzzles".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/parrot/toys/toy/puzzles") is None
    assert apteryx.get("/test/animals/animal/parrot/toys/toy/rings") == 'rings'


def test_restconf_delete_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "73")
        response = requests.delete(f"{server_uri}{docroot}/data/testing:test/settings/users={encoded}", headers=set_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 204, message
        assert len(response.content) == 0, message
        assert not apteryx.search("/test/settings/users/"), message


def test_restconf_delete_leaf_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/animals/animal/rabbit/toys/toy/{key}", name)
        response = requests.delete(f"{server_uri}{docroot}/data/testing:test/animals/animal=rabbit/toys/toy={encoded}", auth=server_auth, headers=set_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 204, message
        assert len(response.content) == 0, message
        assert not apteryx.search("/test/animals/animal/rabbit/toys/toy/"), message


def test_restconf_delete_sublist_readonly_leaf():
    apteryx.set("/test/settings/users/fred/name", "fred")
    apteryx.set("/test/settings/users/fred/active", "true")
    response = requests.delete(f"{server_uri}{docroot}/data/test/settings/users/fred", auth=server_auth, headers=set_restconf_headers)
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/name") == "fred"
    assert apteryx.get("/test/settings/users/fred/active") == "true"
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


def test_restconf_delete_sublist_config_only_readonly_leaf():
    apteryx.set("/test/settings/users/fred/name", "fred")
    apteryx.set("/test/settings/users/fred/active", "true")
    response = requests.delete(f"{server_uri}{docroot}/data/test/settings/users/fred", auth=server_auth, headers={**set_restconf_headers, 'X-Config-Only': "on"})
    assert response.status_code == 204
    assert len(response.content) == 0
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/name") is None
    assert apteryx.get("/test/settings/users/fred/active") == "true"


def test_restconf_delete_proxy_list_select_one():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    response = requests.delete("{}{}/data/logical-elements:logical-elements/logical-element/loopy/testing:test/animals/animal=dog".format(server_uri, docroot),
                               auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/name") == 'cat'
    assert apteryx.get('/test/animals/animal/dog/name') is None
    assert apteryx.get('/test/animals/animal/dog/colour') is None


def test_restconf_delete_proxy_list_select_one_read_only():
    apteryx.set("/logical-elements/logical-element-ro/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element-ro/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element-ro/loopy/*", "tcp://127.0.0.1:9999")
    response = requests.delete("{}{}/data/logical-elements:logical-elements/logical-element-ro/loopy/testing:test/animals/animal=dog".format(server_uri, docroot),
                               auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 404
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-message": "uri path not found",
            "error-type" : "application",
            "error-tag" : "invalid-value"
        }
        ]
    }
}
    """)
