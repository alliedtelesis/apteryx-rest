import json
import requests
from conftest import server_uri, server_auth, docroot, apteryx_set, apteryx_get, set_restconf_headers


def test_restconf_create_single_node_ns_none():
    apteryx_set("/test/settings/priority", "")
    data = """{"priority": "2"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "2"


def test_restconf_create_single_node_ns_aug_none():
    apteryx_set("/test/settings/volume", "")
    data = """{"volume": "2"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "2"


def test_restconf_create_single_node_ns_default():
    apteryx_set("/test/settings/priority", "")
    data = """{"priority": "2"}"""
    response = requests.post("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "2"


def test_restconf_create_single_node_ns_aug_default():
    apteryx_set("/test/settings/volume", "")
    data = """{"volume": "2"}"""
    response = requests.post("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/volume") == "2"


def test_restconf_create_single_node_ns_other():
    apteryx_set("/t2:test/settings/priority", "")
    data = """{"priority": "3"}"""
    response = requests.post("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/priority") == "3"


def test_restconf_create_single_node_ns_aug_other():
    apteryx_set("/t2:test/settings/speed", "")
    data = """{"testing2-augmented:speed": "3"}"""
    response = requests.post("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/t2:test/settings/speed") == "3"


def test_restconf_create_string():
    apteryx_set("/test/settings/description", "")
    data = """{"description": "this is a description"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/description") == "this is a description"


def test_restconf_create_existing_string():
    apteryx_set("/test/settings/description", "already set")
    data = """{"description": "this is a description"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
            "error-tag" : "data-exists",
            "error-message" : "object already exists"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/settings/description") == "already set"


def test_restconf_create_null():
    apteryx_set("/test/settings/description", "")
    data = """{"description": ""}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert apteryx_get("/test/settings/description") == "Not found"


def test_restconf_create_readonly():
    data = """{"counter": 123}"""
    response = requests.post("{}{}/data/test/state".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
    data = """{"description": "this is a description"}"""
    response = requests.post("{}{}/data/test/cabbage".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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


def test_restconf_create_invalid_leaf():
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"cabbage": "this is cabbage"}""")
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


def test_restconf_create_invalid_json():
    apteryx_set("/test/settings/description", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"description":""")
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


def test_restconf_create_enum():
    apteryx_set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "disable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    apteryx_set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "enable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"


def test_restconf_create_invalid_enum():
    apteryx_set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "cabbage"}""")
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
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"hidden": "cabbage"}""")
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
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"priority": 1}""")
    assert response.status_code == 201
    apteryx_set("/test/settings/priority", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"priority": 0}""")
    assert response.status_code == 400
    apteryx_set("/test/settings/priority", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"priority": 6}""")
    assert response.status_code == 400
    apteryx_set("/test/settings/priority", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"priority": 55}""")
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
    response = requests.post("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 201


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
    response = requests.post("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
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
            "error-tag" : "data-exists",
            "error-message" : "object already exists"
        }
        ]
    }
}
    """)
    assert apteryx_get("/test/animals/animal/cat/type") == "1"
