import apteryx
import json
import requests
from conftest import server_uri, server_auth, docroot, get_restconf_headers, rfc3986_reserved


def test_restconf_get_single_node_ns_none():
    response = requests.get("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 1 }')


def test_restconf_get_single_node_ns_aug_none():
    response = requests.get("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "volume": "1" }')


def test_restconf_get_single_node_ns_default():
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:priority": 1 }')


def test_restconf_get_single_node_ns_apteryx():
    response = requests.get("{}{}/data/test3/state/age".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "age": "99" }')


def test_restconf_get_single_node_ns_aug_default():
    response = requests.get("{}{}/data/testing:test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:volume": "1" }')


def test_restconf_get_single_node_ns_other():
    response = requests.get("{}{}/data/testing-2:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing-2:priority": 2 }')


def test_restconf_get_single_node_ns_aug_other():
    response = requests.get("{}{}/data/testing-2:test/settings/testing2-augmented:speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing2-augmented:speed": "2" }')


def test_restconf_get_integer():
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:priority": 1 }')
    apteryx.set("/test/settings/priority", "2")
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "testing:priority": 2 }')


def test_restconf_get_uint64():
    # /test/settings/volume uint64 range="0..18446744073709551615"
    apteryx.set("/test/settings/volume", "0")
    response = requests.get("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "volume": "0" }')
    apteryx.set("/test/settings/volume", "18446744073709551615")
    response = requests.get("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "volume": "18446744073709551615" }')


def test_restconf_get_int64():
    # /t2:test/settings/speed int64 range="-9223372036854775808..9223372036854775807"
    apteryx.set("/t2:test/settings/speed", "-9223372036854775808")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "-9223372036854775808" }')
    apteryx.set("/t2:test/settings/speed", "0")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "0" }')
    apteryx.set("/t2:test/settings/speed", "9223372036854775807")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "9223372036854775807" }')


def test_restconf_get_string_string():
    apteryx.set("/test/settings/description", "This is a description")
    response = requests.get("{}{}/data/testing:test/settings/description".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "testing:description": "This is a description" }')


def test_restconf_get_string_number():
    apteryx.set("/test/settings/description", "123")
    response = requests.get("{}{}/data/testing:test/settings/description".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "testing:description": "123" }')


def test_restconf_get_boolean():
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:enable": true }')
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:enable": false }')


def test_restconf_get_value_string():
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "enable" }')
    apteryx.set("/test/settings/debug", "disable")
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "disable" }')


def test_restconf_get_node_null():
    apteryx.set("/test/settings/debug", "")
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    if len(response.content) != 0:
        print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert (response.status_code == 204 and len(response.content) == 0) or (response.status_code == 200 and response.json() == json.loads('{}'))


def test_restconf_get_node_empty():
    apteryx.set("/test/settings/empty", "empty")
    response = requests.get("{}{}/data/testing:test/settings/empty".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads("""{ "testing:empty": {} }""")


def test_restconf_get_trunk_node_empty():
    apteryx.set("/test/settings/empty", "empty")
    response = requests.get("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json().get('testing:settings').get('empty') == json.loads('{}')


def test_restconf_get_trunk_no_namespace():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": "1"
    }
}
    """)


def test_restconf_get_trunk_namespace():
    response = requests.get("{}{}/data/testing:test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": "1"
    }
}
    """)


def test_restconf_get_trunk_other_namespace():
    response = requests.get("{}{}/data/testing-2:test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing-2:settings": {
        "priority": 2,
        "testing2-augmented:speed": "2"
    }
}
    """)


def test_restconf_get_trunk_ns_apteryx():
    response = requests.get("{}{}/data/test3".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "test3": {
        "state": {
            "age": "99"
        }
    }
}
    """)


def test_restconf_get_list_trunk():
    response = requests.get("{}{}/data/testing:test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animals": {
        "animal": [
            {"name": "cat", "type": "animal-testing-types:big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "animal-testing-types:little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "animal-testing-types:little"},
            {"name": "parrot", "type": "animal-testing-types:big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)


def test_restconf_get_list_trunk_no_namespace():
    response = requests.get("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {"name": "cat", "type": "animal-testing-types:big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "animal-testing-types:little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "animal-testing-types:little"},
            {"name": "parrot", "type": "animal-testing-types:big", "colour": "blue", "toys": {
                "toy": ["puzzles", "rings"]
                }
            }
        ]
    }
}
    """)


def test_restconf_get_list_select_none():
    response = requests.get("{}{}/data/test/animals/animal".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "animal": [
        {"name": "cat", "type": "animal-testing-types:big"},
        {"name": "dog", "colour": "brown"},
        {"name": "hamster", "type": "animal-testing-types:little", "food": [
                {"name": "banana", "type": "fruit"},
                {"name": "nuts", "type": "kibble"}
            ]
        },
        {"name": "mouse", "colour": "grey", "type": "animal-testing-types:little"},
        {"name": "parrot", "type": "animal-testing-types:big", "colour": "blue", "toys": {
            "toy": ["puzzles", "rings"]
            }
        }
    ]
}
    """)


def test_restconf_get_list_select_one_trunk():
    response = requests.get("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_list_select_one_by_path_trunk():
    response = requests.get("{}{}/data/testing:test/animals/animal/cat".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_list_reserved_in_key():
    characters = "-._~!$&()*+;=@,: /"
    escaped = "/"
    apteryx.prune("/test/animals")
    for c in characters:
        key = f"skinny%{ord(c):02X}frog" if (c in escaped) else f"skinny{c}frog"
        apteryx.set(f"/test/animals/animal/{key}/name", f"skinny{c}frog")
    response = requests.get("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    for c in characters:
        assert next((x for x in response.json()['animals']['animal'] if x['name'] == f"skinny{c}frog"), None)


def test_restconf_get_list_select_two_trunk():
    response = requests.get("{}{}/data/testing:test/animals/animal=hamster/food=banana".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:food": [
        {
            "name": "banana",
            "type": "fruit"
        }
    ]
}
    """)


def test_restconf_get_leaf_list_node():
    response = requests.get("{}{}/data/testing:test/animals/animal=parrot/toys/toy".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:toy": [
        "puzzles",
        "rings"
    ]
}
    """)


def test_restconf_get_list_integer_index():
    apteryx.set("/test/settings/rules/1/index", "1")
    apteryx.set("/test/settings/rules/1/name", "name1")
    apteryx.set("/test/settings/rules/99/index", "99")
    apteryx.set("/test/settings/rules/99/name", "name99")
    apteryx.set("/test/settings/rules/9/index", "9")
    apteryx.set("/test/settings/rules/9/name", "name9")
    apteryx.set("/test/settings/rules/10/index", "10")
    apteryx.set("/test/settings/rules/10/name", "name10")
    apteryx.set("/test/settings/rules/5/index", "5")
    apteryx.set("/test/settings/rules/5/name", "name5")
    apteryx.set("/test/settings/rules/33/index", "33")
    apteryx.set("/test/settings/rules/33/name", "name33")
    apteryx.set("/test/settings/rules/3/index", "3")
    apteryx.set("/test/settings/rules/3/name", "name3")
    apteryx.set("/test/settings/rules/111/index", "111")
    apteryx.set("/test/settings/rules/111/name", "name111")
    apteryx.set("/test/settings/rules/2/index", "2")
    apteryx.set("/test/settings/rules/2/name", "name2")
    response = requests.get("{}{}/data/testing:test/settings/rules".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:rules": [
        {
            "index": 1,
            "name": "name1"
        },
        {
            "index": 2,
            "name": "name2"
        },
        {
            "index": 3,
            "name": "name3"
        },
        {
            "index": 5,
            "name": "name5"
        },
        {
            "index": 9,
            "name": "name9"
        },
        {
            "index": 10,
            "name": "name10"
        },
        {
            "index": 33,
            "name": "name33"
        },
        {
            "index": 99,
            "name": "name99"
        },
        {
            "index": 111,
            "name": "name111"
        }
    ]
}
    """)


def test_restconf_get_leaf_list_integers():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/groups/1", "1")
    apteryx.set("/test/settings/users/alfred/groups/99", "99")
    apteryx.set("/test/settings/users/alfred/groups/9", "9")
    apteryx.set("/test/settings/users/alfred/groups/10", "10")
    apteryx.set("/test/settings/users/alfred/groups/5", "5")
    apteryx.set("/test/settings/users/alfred/groups/33", "33")
    apteryx.set("/test/settings/users/alfred/groups/3", "3")
    apteryx.set("/test/settings/users/alfred/groups/111", "111")
    apteryx.set("/test/settings/users/alfred/groups/2", "2")
    response = requests.get("{}{}/data/testing:test/settings/users=alfred/groups".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:groups": [
        1,
        2,
        3,
        5,
        9,
        10,
        33,
        99,
        111
    ]
}
    """)


def test_restconf_get_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "82")
        response = requests.get(f"{server_uri}{docroot}/data/testing:test/settings/users={encoded}", auth=server_auth, headers=get_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200, message
        assert response.headers["Content-Type"] == "application/yang-data+json", message
        assert response.json() == {"testing:users": [{"name": name, "age": 82}]}, message


def test_restconf_get_leaf_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/animals/animal/rabbit/toys/toy/{key}", name)
        response = requests.get(f"{server_uri}{docroot}/data/testing:test/animals/animal=rabbit/toys/toy={encoded}", auth=server_auth, headers=get_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200, message
        assert response.headers["Content-Type"] == "application/yang-data+json", message
        assert response.json() == {"testing:toy": [name]}, message


def test_restconf_get_proxy_value_string():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    response = requests.get("{}{}/data/logical-elements:logical-elements/logical-element/loopy/testing:test/settings/debug".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "enable" }')
    apteryx.set("/test/settings/debug", "disable")
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "disable" }')
    response = requests.get("{}{}/data/logical-elements:logical-elements/logical-element/loopy/testing:test/settings/debug".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "disable" }')


def test_restconf_get_proxy_list_select_one_trunk():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    response = requests.get("{}{}/data/logical-elements:logical-elements/logical-element/loopy/testing:test/animals/animal=cat".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_when_derived_from():
    apteryx.set("/test/animals/animal/cat/n-type", "big")
    response = requests.get("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "n-type": "big",
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_when_condition_true():
    apteryx.set("/test/animals/animal/wombat/name", "wombat")
    apteryx.set("/test/animals/animal/cat/claws", "5")
    response = requests.get("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)

    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "claws": "5",
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_when_condition_false():
    apteryx.set("/test/animals/animal/cat/claws", "5")
    response = requests.get("{}{}/data/testing:test/animals/animal=cat".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)

    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_get_must_condition_true():
    apteryx.set("/test/animals/animal/dog/friend", "ben")
    response = requests.get("{}{}/data/testing:test/animals/animal=dog".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)

    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "colour": "brown",
            "friend": "ben",
            "name": "dog"
        }
    ]
}
    """)


def test_restconf_get_must_condition_false():
    apteryx.set("/test/animals/animal/dog/friend", "ben")
    apteryx.prune("/test/animals/animal/cat")
    response = requests.get("{}{}/data/testing:test/animals/animal=dog".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animal": [
        {
            "colour": "brown",
            "name": "dog"
        }
    ]
}
    """)


# TODO multiple keys
#  /restconf/data/ietf-yang-library:modules-state/module=ietf-interfaces,2014-05-08
#  Missing key values are not allowed, so two consecutive commas are
#   interpreted as a comma, followed by a zero-length string, followed
#   by a comma.  For example, "list1=foo,,baz" would be interpreted as
#   a list named "list1" with three key values, and the second key
#   value is a zero-length string.
#  Note that non-configuration lists are not required to define keys.
#   In this case, a single list instance cannot be accessed.
