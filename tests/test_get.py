import json
import requests
from conftest import server_uri, server_auth, docroot, apteryx_set, get_restconf_headers


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
    apteryx_set("/test/settings/priority", "2")
    response = requests.get("{}{}/data/testing:test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "testing:priority": 2 }')


def test_restconf_get_uint64():
    # /test/settings/volume uint64 range="0..18446744073709551615"
    apteryx_set("/test/settings/volume", "0")
    response = requests.get("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "volume": "0" }')
    apteryx_set("/test/settings/volume", "18446744073709551615")
    response = requests.get("{}{}/data/test/settings/volume".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "volume": "18446744073709551615" }')


def test_restconf_get_int64():
    # /t2:test/settings/speed int64 range="-9223372036854775808..9223372036854775807"
    apteryx_set("/t2:test/settings/speed", "-9223372036854775808")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "-9223372036854775808" }')
    apteryx_set("/t2:test/settings/speed", "0")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "0" }')
    apteryx_set("/t2:test/settings/speed", "9223372036854775807")
    response = requests.get("{}{}/data/testing-2:test/settings/speed".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads('{ "testing2-augmented:speed": "9223372036854775807" }')


def test_restconf_get_string_string():
    apteryx_set("/test/settings/description", "This is a description")
    response = requests.get("{}{}/data/testing:test/settings/description".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "testing:description": "This is a description" }')


def test_restconf_get_string_number():
    apteryx_set("/test/settings/description", "123")
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
    apteryx_set("/test/settings/enable", "false")
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
    apteryx_set("/test/settings/debug", "disable")
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "testing:debug": "disable" }')


def test_restconf_get_node_null():
    apteryx_set("/test/settings/debug", "")
    response = requests.get("{}{}/data/testing:test/settings/debug".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    if len(response.content) != 0:
        print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert (response.status_code == 204 and len(response.content) == 0) or (response.status_code == 200 and response.json() == json.loads('{}'))


def test_restconf_get_node_empty():
    apteryx_set("/test/settings/empty", "empty")
    response = requests.get("{}{}/data/testing:test/settings/empty".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads("""{ "testing:empty": {} }""")


def test_restconf_get_trunk_node_empty():
    apteryx_set("/test/settings/empty", "empty")
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


def test_restconf_get_list_trunk():
    response = requests.get("{}{}/data/testing:test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:animals": {
        "animal": [
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
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
            {"name": "cat", "type": "big"},
            {"name": "dog", "colour": "brown"},
            {"name": "hamster", "type": "little", "food": [
                    {"name": "banana", "type": "fruit"},
                    {"name": "nuts", "type": "kibble"}
                ]
            },
            {"name": "mouse", "colour": "grey", "type": "little"},
            {"name": "parrot", "type": "big", "colour": "blue", "toys": {
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
        {"name": "cat", "type": "big"},
        {"name": "dog", "colour": "brown"},
        {"name": "hamster", "type": "little", "food": [
                {"name": "banana", "type": "fruit"},
                {"name": "nuts", "type": "kibble"}
            ]
        },
        {"name": "mouse", "colour": "grey", "type": "little"},
        {"name": "parrot", "type": "big", "colour": "blue", "toys": {
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
            "type": "big"
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
            "type": "big"
        }
    ]
}
    """)


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


def test_restconf_get_leaf_list_integers():
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/groups/1", "1")
    apteryx_set("/test/settings/users/alfred/groups/5", "5")
    apteryx_set("/test/settings/users/alfred/groups/9", "9")
    response = requests.get("{}{}/data/testing:test/settings/users=alfred/groups".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing:groups": [
        1,
        5,
        9
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
