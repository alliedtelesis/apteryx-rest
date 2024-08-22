import json
import requests
from conftest import server_uri, server_auth, docroot, apteryx_set, apteryx_get, apteryx_traverse, get_restconf_headers, set_restconf_headers, apteryx_proxy


def test_restconf_delete_single_node_ns_none():
    response = requests.delete("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "Not found"


def test_restconf_delete_single_node_ns_aug_none():
    response = requests.delete("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "Not found"


def test_restconf_delete_single_node_ns_default():
    response = requests.delete("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "Not found"


def test_restconf_delete_single_node_ns_aug_default():
    response = requests.delete("{}{}/data/testing:test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "Not found"


def test_restconf_delete_single_node_ns_other():
    response = requests.delete("{}{}/data/testing-2:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/volume") == "Not found"
    assert apteryx_get("/test/settings/priority") == "1"


def test_restconf_delete_single_node_ns_aug_other():
    response = requests.delete("{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/speed") == "Not found"
    assert apteryx_get("/t2:test/settings/priority") == "2"


def test_restconf_delete_trunk_ns_none():
    response = requests.delete("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    print(apteryx_traverse("/test/animals"))
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
    assert apteryx_get("/t2:test/settings/priority") == "Not found"
    assert apteryx_get("/t2:test/settings/speed") == "Not found"


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
    apteryx_set("/test/settings/readonly", "")
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "Not found"
    assert apteryx_get("/test/settings/enable") == "Not found"
    assert apteryx_get("/test/settings/priority") == "Not found"
    assert apteryx_get("/test/settings/hidden") == "friend"


def test_restconf_delete_trunk_nonschema():
    # Remove the readonly field so there is nothing illiegal to delete
    apteryx_set("/test/settings/readonly", "")
    apteryx_set("/test/settings/vegetable", "cabagge")
    response = requests.delete("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "Not found"
    assert apteryx_get("/test/settings/enable") == "Not found"
    assert apteryx_get("/test/settings/priority") == "Not found"
    assert apteryx_get("/test/settings/hidden") == "friend"
    assert apteryx_get("/test/settings/vegetable") == "cabagge"


def test_restconf_delete_list_select_one():
    response = requests.delete("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/cat/name") == "Not found"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"
    assert apteryx_get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx_get('/test/animals/animal/dog/colour') == 'brown'


def test_restconf_delete_list_select_by_path_one():
    response = requests.delete("{}{}/data/testing:test/animals/animal/cat".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/cat/name") == "Not found"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"
    assert apteryx_get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx_get('/test/animals/animal/dog/colour') == 'brown'


def test_restconf_delete_list_select_two():
    response = requests.delete("{}{}/data/testing:test/animals/animal=hamster/food=banana".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/hamster/food/banana/name") == "Not found"
    assert apteryx_get("/test/animals/animal/hamster/food/banana/type") == "Not found"
    assert apteryx_get('/test/animals/animal/hamster/food/nuts/name') == 'nuts'
    assert apteryx_get('/test/animals/animal/hamster/food/nuts/type') == 'kibble'


def test_restconf_delete_list_by_path_select_two():
    response = requests.delete("{}{}/data/testing:test/animals/animal/hamster/food/banana".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/hamster/food/banana/name") == "Not found"
    assert apteryx_get("/test/animals/animal/hamster/food/banana/type") == "Not found"
    assert apteryx_get('/test/animals/animal/hamster/food/nuts/name') == 'nuts'
    assert apteryx_get('/test/animals/animal/hamster/food/nuts/type') == 'kibble'


def test_restconf_delete_list_by_path_select_list_leaf():
    response = requests.delete("{}{}/data/testing:test/animals/animal/parrot/toys/toy/puzzles".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/parrot/toys/toy/puzzles") == "Not found"
    assert apteryx_get("/test/animals/animal/parrot/toys/toy/rings") == 'rings'


def test_restconf_delete_proxy_list_select_one():
    apteryx_set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx_set("/logical-elements/logical-element/loop/root", "root")
    apteryx_set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx_proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    response = requests.delete("{}{}/data/logical-elements:logical-elements/logical-element/loopy/testing:test/animals/animal=dog".format(server_uri, docroot),
                               auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/cat/name") == 'cat'
    assert apteryx_get('/test/animals/animal/dog/name') == "Not found"
    assert apteryx_get('/test/animals/animal/dog/colour') == "Not found"


def test_restconf_delete_proxy_list_select_one_read_only():
    apteryx_set("/logical-elements/logical-element-ro/loop/name", "loopy")
    apteryx_set("/logical-elements/logical-element-ro/loop/root", "root")
    apteryx_set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx_proxy("/logical-elements/logical-element-ro/loopy/*", "tcp://127.0.0.1:9999")
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
