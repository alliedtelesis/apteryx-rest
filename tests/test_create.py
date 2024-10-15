import apteryx
import json
import requests
from conftest import server_uri, server_auth, docroot, set_restconf_headers, rfc3986_reserved


def test_restconf_create_single_node_ns_none():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": "2"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "2"


def test_restconf_create_single_node_ns_aug_none():
    apteryx.set("/test/settings/volume", "")
    data = """{"volume": "2"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/volume") == "2"


def test_restconf_create_single_node_ns_default():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": "2"}"""
    response = requests.post("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "2"


def test_restconf_create_single_node_ns_aug_default():
    apteryx.set("/test/settings/volume", "")
    data = """{"volume": "2"}"""
    response = requests.post("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/volume") == "2"


def test_restconf_create_single_node_ns_other():
    apteryx.set("/t2:test/settings/priority", "")
    data = """{"priority": "3"}"""
    response = requests.post("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/t2:test/settings/priority") == "3"


def test_restconf_create_single_node_ns_aug_other():
    apteryx.set("/t2:test/settings/speed", "")
    data = """{"testing2-augmented:speed": "3"}"""
    response = requests.post("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/t2:test/settings/speed") == "3"


def test_restconf_create_string():
    apteryx.set("/test/settings/description", "")
    data = """{"description": "this is a description"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "this is a description"


def test_restconf_create_existing_string():
    apteryx.set("/test/settings/description", "already set")
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
    assert apteryx.get("/test/settings/description") == "already set"


def test_restconf_create_null():
    apteryx.set("/test/settings/description", "")
    data = """{"description": ""}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert apteryx.get("/test/settings/description") is None


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
    assert apteryx.get("/test/state/counter") == "42"


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
    apteryx.set("/test/settings/description", "")
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
    apteryx.set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "disable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "0"
    apteryx.set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "enable"}""")
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "1"


def test_restconf_create_invalid_enum():
    apteryx.set("/test/settings/debug", "")
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors": {
        "error": [
            {
                "error-message": "Invalid input parameter",
                "error-tag": "invalid-value",
                "error-type": "application"
            }
        ]
    }
}
    """)
    assert apteryx.get("/test/settings/debug") is None


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
    assert apteryx.get("/test/settings/hidden") == "friend"


def test_restconf_create_out_of_range_integer():
    # /test/settings/priority range="-5..-1|1..5|99"
    tests = [
        ("""{"priority": -9223372036854775808}""", 400),
        ("""{"priority": -55}""", 400),
        ("""{"priority": -6}""", 400),
        ("""{"priority": -5}""", 201),
        ("""{"priority": -1}""", 201),
        ("""{"priority": 0}""", 400),
        ("""{"priority": -1}""", 201),
        ("""{"priority": 5}""", 201),
        ("""{"priority": 6}""", 400),
        ("""{"priority": 55}""", 400),
        ("""{"priority": 99}""", 201),
        ("""{"priority": 18446744073709551615}""", 400)
    ]
    for data, rc in tests:
        apteryx.set("/test/settings/priority", "")
        response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
        assert response.status_code == rc


def test_restconf_create_out_of_range_uint64():
    # /test/settings/volume uint64 range="0..18446744073709551615"
    tests = [
        ("""{"volume": "-1"}""", 400),
        ("""{"volume": "0"}""", 201),
        ("""{"volume": "18446744073709551615"}""", 201),
        ("""{"volume": "28446744073709551615"}""", 400)
    ]
    for data, rc in tests:
        apteryx.set("/test/settings/volume", "")
        response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
        assert response.status_code == rc


def test_restconf_create_out_of_range_int64():
    # /t2:test/settings/speed int64 range="-9223372036854775808..9223372036854775807"
    tests = [
        ("""{"speed": "-18446744073709551615"}""", 400),
        ("""{"speed": "-9223372036854775808"}""", 201),
        ("""{"speed": "0"}""", 201),
        ("""{"speed": "9223372036854775807"}""", 201),
        ("""{"speed": "18446744073709551615"}""", 400)
    ]
    for data, rc in tests:
        apteryx.set("/t2:test/settings/speed", "")
        response = requests.post("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
        assert response.status_code == rc


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
    print(apteryx.get_tree("/test/animals/animal/frog"))
    assert apteryx.get("/test/animals/animal/frog/name") == "frog"


def test_restconf_create_list_leaf_string_ok():
    tree = """
{
    "toy": [
        "ball",
        "mouse"
    ]
}
"""
    response = requests.post("{}{}/data/test/animals/animal=cat/toys".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 201
    print(apteryx.get_tree("/test/animals/animal/cat"))
    assert apteryx.get("/test/animals/animal/cat/toys/toy/ball") == "ball"
    assert apteryx.get("/test/animals/animal/cat/toys/toy/mouse") == "mouse"


def test_restconf_create_list_with_key_with_reserved_characters():
    for c in rfc3986_reserved:
        apteryx.prune("/test/settings/users")
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        data = json.dumps({"users": [{"name": name, "age": 74}]})
        response = requests.post(f"{server_uri}{docroot}/data/test/settings", auth=server_auth, data=data, headers=set_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 201, message
        assert len(response.content) == 0, message
        print(apteryx.get_tree("/test/settings/users"))
        assert apteryx.get(f"/test/settings/users/{key}/name") == name, message
        assert apteryx.get(f"/test/settings/users/{key}/age") == "74", message


def test_restconf_create_leaf_list_with_key_with_reserved_characters():
    for c in rfc3986_reserved:
        apteryx.prune("/test/animals/animal")
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        data = json.dumps({"toy": [name]})
        response = requests.post(f"{server_uri}{docroot}/data/test/animals/animal=cat/toys", auth=server_auth, data=data, headers=set_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 201, message
        assert len(response.content) == 0, message
        print(apteryx.get_tree("/test/animals/animal/cat/toys/toy"))
        assert apteryx.get(f"/test/animals/animal/cat/toys/toy/{key}") == name, message


def test_restconf_create_list_leaf_integer_ok():
    tree = """
{
    "groups": [
        1,
        5
    ]
}
"""
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.post("{}{}/data/test/settings/users=fred".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 201
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/groups/1") == "1"
    assert apteryx.get("/test/settings/users/fred/groups/5") == "5"


def test_restconf_create_list_leaf_integer_invalid():
    tree = """
{
    "groups": [
        "cat",
        5
    ]
}
"""
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.post("{}{}/data/test/settings/users=fred".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 400
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors": {
        "error": [
            {
                "error-message": "Invalid input parameter",
                "error-tag": "invalid-value",
                "error-type": "application"
            }
        ]
    }
}
    """)
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/groups/cat") != "cat"
    assert apteryx.get("/test/settings/users/fred/groups/5") != "5"


def test_restconf_create_list_leaf_integer_invalid_path():
    tree = """
{
    "groups": [
        "cat"
    ]
}
"""
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.post("{}{}/data/test/settings/users=fred/groups".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 405
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors": {
        "error": [
            {
                "error-message": "requested operation is not supported",
                "error-tag": "operation-not-supported",
                "error-type": "application"
            }
        ]
    }
}
    """)
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/groups/cat") != "cat"


def test_restconf_create_complex_ok():
    tree = """
{
    "users" : [
        {
            "name": "fred",
            "age": 99,
            "groups": [
                1,
                5
            ]
        }
    ]
}
"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, data=tree, headers=set_restconf_headers)
    assert response.status_code == 201
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users/fred/name") == "fred"
    assert apteryx.get("/test/settings/users/fred/age") == "99"
    assert apteryx.get("/test/settings/users/fred/groups/1") == "1"
    assert apteryx.get("/test/settings/users/fred/groups/5") == "5"


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
    assert apteryx.get("/test/animals/animal/cat/type") == "1"


def test_restconf_create_proxy_string():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    apteryx.set("/test/settings/description", "")
    data = """{"description": "this is a description via a proxy"}"""
    response = requests.post("{}{}/data/logical-elements:logical-elements/logical-element/loopy/test/settings".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "this is a description via a proxy"


def test_restconf_create_proxy_string_read_only():
    apteryx.set("/logical-elements/logical-element-ro/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element-ro/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element-ro/loopy/*", "tcp://127.0.0.1:9999")
    apteryx.set("/test/settings/description", "")
    data = """{"description": "this is a description via a proxy"}"""
    response = requests.post("{}{}/data/logical-elements:logical-elements-ro/logical-element/loopy/test/settings".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
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


def test_restconf_create_if_feature_false():
    data = """{"days": "1"}"""
    response = requests.post("{}{}/data/test/settings/magictime".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
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


def test_restconf_create_if_feature_true():
    data = """{"days": "1"}"""
    response = requests.post("{}{}/data/test/settings/testtime".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/testtime/days") == "1"


def test_restconf_create_when_condition_true():
    tree = """
{
    "house": [
        "kennel"
    ]
}
"""
    response = requests.post("{}{}/data/test/animals/animal/dog/houses".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=tree)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/dog/houses/house/kennel") == "kennel"


def test_restconf_create_when_condition_false():
    tree = """
{
    "house": [
        "cattery"
    ]
}
"""
    response = requests.post("{}{}/data/test/animals/animal/cat/houses".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=tree)
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


def test_restconf_when_condition_true():
    apteryx.set("/test/animals/animal/wombat/name", "wombat")
    data = """{"claws": "5"}"""
    response = requests.post("{}{}/data/test/animals/animal/cat".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/claws") == "5"


def test_restconf_when_condition_false():
    data = """{"claws": "5"}"""
    response = requests.post("{}{}/data/test/animals/animal/cat".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
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


def test_restconf_when_condition_translate_true():
    tree = """
{
    "cage": [
        "box"
    ]
}
"""
    response = requests.post("{}{}/data/test/animals/animal/cat/cages".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=tree)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/cages/cage/box") == "box"


def test_restconf_when_condition_translate_false():
    tree = """
{
    "cage": [
        "box"
    ]
}
"""
    response = requests.post("{}{}/data/test/animals/animal/mouse/cages".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=tree)
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


def test_restconf_must_condition_true():
    data = """{"friend": "ben"}"""
    response = requests.post("{}{}/data/test/animals/animal/dog".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/dog/friend") == "ben"


def test_restconf_must_condition_false():
    apteryx.prune("/test/animals/animal/cat")
    data = """{"friend": "ben"}"""
    response = requests.post("{}{}/data/test/animals/animal/dog".format(server_uri, docroot),
                             auth=server_auth, headers=set_restconf_headers, data=data)
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
