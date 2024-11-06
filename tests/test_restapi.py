import apteryx
import pytest
import requests
import json
import time
from lxml import etree
from conftest import server_uri, server_auth, docroot, rfc3986_reserved


# TEST CONFIGURATION
# docroot = '/api'
search_etag = True
json_types = True
apteryx.URL = ''


# TEST HELPERS
if json_types:
    json_headers = {"X-JSON-Types": "on", "X-JSON-Array": "on"}
else:
    json_headers = {"X-JSON-Array": "on"}


# API


def test_restapi_api_xml():
    response = requests.get("{}{}.xml".format(server_uri, docroot), verify=False, auth=server_auth)
    xml = etree.fromstring(response.content)
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/xml"
    assert int(response.headers["Content-Length"]) == len(response.content)
    assert xml.findall('.//*[@mode="h"]') == []
    assert xml.findall('.//*[@mode="hr"]') == []
    assert xml.findall('.//*[@mode="rh"]') == []
    assert xml.findall('.//*[@mode="wh"]') == []
    assert xml.findall('.//*[@mode="hw"]') == []
    assert xml.findall('.//{*}WATCH') == []
    assert xml.findall('.//{*}PROVIDE') == []
    assert xml.findall('.//{*}INDEX') == []
    assert xml.findall('.//{*}REFRESH') == []


def test_restapi_ns_api_xml():
    response = requests.get("{}{}.xml".format(server_uri, docroot), verify=False, auth=server_auth)
    xml = etree.fromstring(response.content)
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/xml"
    print(xml.findall('.//{*}NODE'))
    ns_default = [e.attrib['name'] for e in xml.findall('.//{*}NODE')]
    print(ns_default)
    for node in ['yang-library', 'modules-state', 'test', 't2:test', 'settings', 'debug', 'enable', 'priority', 'writeonly', 'speed', 'priority']:
        assert node in ns_default


def test_restapi_get_single_node():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": "1" }')


def test_restapi_get_explicit_accept():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, headers={"Accept": "application/json"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": "1" }')


def test_restapi_get_integer_string():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": "1" }')


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_get_integer_integer():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": 1 }')


def test_restapi_get_boolean_string():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": "true" }')
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": "false" }')


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_get_boolean_boolean():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": true }')
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": false }')


def test_restapi_get_enum_value():
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "1" }')
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "0" }')


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_get_enum_name():
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "enable" }')
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "disable" }')


def test_restapi_get_node_null():
    apteryx.set("/test/settings/debug", "")
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{}')


def test_restapi_get_node_empty():
    apteryx.set("/test/settings/empty", "empty")
    response = requests.get("{}{}/test/settings/empty".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "empty": {} }')


def test_restapi_get_trunk_node_empty():
    apteryx.set("/test/settings/empty", "empty")
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json().get('settings').get('empty') == json.loads('{}')


def test_restapi_get_tree_strings():
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "1",
        "enable": "true",
        "priority": "1",
        "readonly": "0",
        "volume": "1"
    }
}
""")


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_get_tree_json_types():
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": true,
        "debug": "enable",
        "priority": 1,
        "readonly": "yes",
        "volume": "1"
    }
}
""")


def test_restapi_get_tree_root():
    response = requests.get("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "test": {
        "animals": {
            "animal": {
                "cat": {
                    "name": "cat",
                    "type": "1"
                },
                "dog": {
                    "colour": "brown",
                    "name": "dog"
                },
                "hamster": {
                    "food": {
                        "banana": {
                            "name": "banana",
                            "type": "fruit"
                        },
                        "nuts": {
                            "name": "nuts",
                            "type": "kibble"
                        }
                    },
                    "name": "hamster",
                    "type": "2"
                },
                "mouse": {
                    "colour": "grey",
                    "name": "mouse",
                    "type": "2"
                },
                "parrot": {
                    "colour": "blue",
                    "name": "parrot",
                    "toys": {
                        "toy": {
                            "puzzles": "puzzles",
                            "rings": "rings"
                        }
                    },
                    "type": "1"
                }
            }
        },
        "settings": {
            "debug": "1",
            "enable": "true",
            "priority": "1",
            "readonly": "0",
            "volume": "1"
        },
        "state": {
            "counter": "42",
            "uptime": {
                "days": "5",
                "hours": "50",
                "minutes": "30",
                "seconds": "20"
            }
        }
    }
}
""")


def test_restapi_get_list_object_strings():
    response = requests.get("{}{}/test/animals/animal".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": {
        "cat": {"name": "cat", "type": "1"},
        "dog": {"name": "dog", "colour": "brown"},
        "hamster": {"name": "hamster", "type": "2", "food": {
            "nuts": {"name": "nuts", "type": "kibble"},
            "banana": {"name": "banana", "type": "fruit"}
            }
        },
        "mouse": {"name": "mouse", "colour": "grey", "type": "2"},
        "parrot": {"name": "parrot", "type": "1", "colour": "blue", "toys": {
            "toy": {"rings": "rings", "puzzles": "puzzles"}
            }
        }
    }
}
""")


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_get_list_object_types():
    response = requests.get("{}{}/test/animals/animal".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Types": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": {
        "cat": {"name": "cat", "type": "big"},
        "dog": {"name": "dog", "colour": "brown"},
        "hamster": {"name": "hamster", "type": "little", "food": {
            "banana": {"name": "banana", "type": "fruit"},
            "nuts": {"name": "nuts", "type": "kibble"}
            }
        },
        "mouse": {"name": "mouse", "colour": "grey", "type": "little"},
        "parrot": {"name": "parrot", "type": "big", "colour": "blue", "toys": {
            "toy": {"rings": "rings", "puzzles": "puzzles"}
            }
        }
    }
}
""")


def test_restapi_get_list_array():
    response = requests.get("{}{}/test/animals/animal".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Array": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": [
        {"name": "cat", "type": "1"},
        {"name": "dog", "colour": "brown"},
        {"name": "hamster", "type": "2", "food": [
                {"name": "banana", "type": "fruit"},
                {"name": "nuts", "type": "kibble"}
            ]
        },
        {"name": "mouse", "colour": "grey", "type": "2"},
        {"name": "parrot", "type": "1", "colour": "blue", "toys": {
            "toy": ["puzzles", "rings"]
            }
        }
    ]
}
""")


def test_restapi_get_list_select_one_strings():
    response = requests.get("{}{}/test/animals/animal/cat".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "cat": {
        "name": "cat",
        "type": "1"
    }
}
""")


def test_restapi_get_list_select_one_with_colon():
    apteryx.set("/test/animals/animal/cat:ty/name", "cat:ty")
    apteryx.set("/test/animals/animal/cat:ty/type", "1")
    response = requests.get("{}{}/test/animals/animal/cat:ty".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "cat:ty": {
        "name": "cat:ty",
        "type": "1"
    }
}
""")


def test_restapi_get_list_select_one_ns_with_colon():
    apteryx.set("/t2:test/settings/users/fre:dy/name", "fre:dy")
    response = requests.get("{}{}/t2:test/settings/users/fre:dy".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "fre:dy": {
        "name": "fre:dy"
    }
}
""")


def test_restapi_get_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "82")
        response = requests.get(f"{server_uri}{docroot}/test/settings/users/{encoded}", verify=False, auth=server_auth)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200, message
        assert response.headers["Content-Type"] == "application/json", message
        assert response.json() == {key: {"name": name, "age": "82"}}, message


def test_restapi_get_leaf_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/animals/animal/rabbit/toys/toy/{key}", name)
        response = requests.get(f"{server_uri}{docroot}/test/animals/animal/rabbit/toys/toy/{encoded}", verify=False, auth=server_auth)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200, message
        assert response.headers["Content-Type"] == "application/json", message
        assert response.json() == {key: name}, message


def test_restapi_get_list_select_one_array():
    response = requests.get("{}{}/test/animals/animal/cat".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Array": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
[
    {
        "name": "cat",
        "type": "1"
    }
]
""")


def test_restapi_get_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*/name".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "cat": {
        "name": "cat"
    },
    "dog": {
        "name": "dog"
    },
    "hamster": {
        "name": "hamster"
    },
    "mouse": {
        "name": "mouse"
    },
    "parrot": {
        "name": "parrot"
    }
}
""")


def test_restapi_get_two_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*/food/*/name".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "hamster": {
        "food": {
            "banana": {
                "name": "banana"
            },
            "nuts": {
                "name": "nuts"
            }
        }
    }
}
""")


def test_restapi_get_etag_exists():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": "true" }')


def test_restapi_get_etag_changes():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") is not None
    assert response.json() == json.loads('{ "enable": "true" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert tag1 == response.headers.get("ETag")
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "enable": "false" }')
    assert tag1 != response.headers.get("ETag")


def test_restapi_get_etag_not_modified():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") is not None
    assert response.json() == json.loads('{ "enable": "true" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0


def test_restapi_get_etag_zero():
    apteryx.set("/test/settings/enable", "")
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") == "0"
    assert response.json() == json.loads('{}')


def test_restapi_get_not_found():
    response = requests.get("{}{}/test/settings/invalid".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 404
    assert len(response.content) == 0


def test_restapi_get_forbidden():
    response = requests.get("{}{}/test/settings/writeonly".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_get_hidden_node():
    response = requests.get("{}{}/test/settings/hidden".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_get_hidden_tree():
    apteryx.set("/test/settings/debug", "")
    apteryx.set("/test/settings/enable", "")
    apteryx.set("/test/settings/priority", "")
    apteryx.set("/test/settings/readonly", "")
    apteryx.set("/test/settings/volume", "")
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')


# FLAGS_JSON_FORMAT_ROOT=off
def test_restapi_get_drop_root_string():
    apteryx.set("/test/settings/description", "This is a description")
    response = requests.get("{}{}/test/settings/description".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"This is a description"')


# FLAGS_JSON_FORMAT_ROOT=off
def test_restapi_get_drop_root_writeonly():
    response = requests.get("{}{}/test/settings/writeonly".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    assert response.status_code == 403


# FLAGS_JSON_FORMAT_ROOT=off
def test_restapi_get_drop_root_hidden():
    response = requests.get("{}{}/test/settings/hidden".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    assert response.status_code == 403


def test_restapi_get_drop_root_integer_string():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"1"')


def test_restapi_get_drop_root_integer_json():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off", "X-JSON-Types": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('1')


def test_restapi_get_drop_root_boolean_string():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"true"')


def test_restapi_get_drop_root_boolean_json():
    response = requests.get("{}{}/test/settings/enable".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off", "X-JSON-Types": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('true')


def test_restapi_get_drop_root_enum_string():
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"1"')


def test_restapi_get_drop_root_enum_json():
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off", "X-JSON-Types": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"enable"')


# FLAGS_JSON_FORMAT_MULTI=on
def test_restapi_get_multi():
    response = requests.get("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Multi": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('[ { "priority": "1" } ]')


def test_restapi_set_nonjson_string_unquoted():
    response = requests.post("{}{}/test/settings/description".format(server_uri, docroot), verify=False, auth=server_auth, data="This is a description")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "This is a description"


def test_restapi_set_nonjson_string_quoted():
    response = requests.post("{}{}/test/settings/description".format(server_uri, docroot), verify=False, auth=server_auth, data='"This is a description"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/description") == "This is a description"


def test_restapi_set_nonjson_number_unquoted():
    response = requests.post("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, data='5')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "5"


def test_restapi_set_nonjson_number_quoted():
    response = requests.post("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, data='"5"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "5"


def test_restapi_set_nonjson_value_unquoted():
    response = requests.post("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, data="disable")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "0"


def test_restapi_set_nonjson_value_quoted():
    response = requests.post("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, data='"disable"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "0"


def test_restapi_set_nonjson_writeonly():
    response = requests.post("{}{}/test/settings/writeonly".format(server_uri, docroot), verify=False, auth=server_auth, data='"123"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/writeonly") == "123"


def test_restapi_set_nonjson_readonly():
    response = requests.post("{}{}/test/state/counter".format(server_uri, docroot), verify=False, auth=server_auth, data='"123"')
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx.get("/test/state/counter") == "42"


def test_restapi_set_single_node():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "5"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "5"


def test_restapi_set_explicit_content_type():
    headers = {"Content-Type": "application/json"}
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "5"}""", headers=headers)
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "5"


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_set_value_name():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "disable"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "enable"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "1"


def test_restapi_set_value_value():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "0"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "1"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "1"


def test_restapi_set_node_null():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": ""}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 201
    assert response.json() == json.loads('{}')


def test_restapi_set_invalid_path():
    response = requests.post("{}{}/test/cabbage".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "enable"}""")
    assert response.status_code == 404
    assert len(response.content) == 0
    assert apteryx.get("/test/cabbage/debug") is None


def test_restapi_set_invalid_enum_value():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/debug") == "1"


def test_restapi_set_readonly():
    response = requests.post("{}{}/test/state".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"counter": "123"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx.get("/test/state/counter") == "42"


def test_restapi_set_writeonly():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"writeonly": "123"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/writeonly") == "123"


def test_restapi_set_hidden():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"hidden": "cabbage"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/hidden") == "friend"


def test_restapi_set_out_of_range_integer_string():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "1"}""")
    assert response.status_code == 200 or response.status_code == 201
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "0"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "6"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "55"}""")
    assert response.status_code == 400
    assert apteryx.get("/test/settings/priority") == "1"


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_set_out_of_range_integer_integer():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": 1}""")
    assert response.status_code == 200 or response.status_code == 201
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": 0}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": 6}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": 55}""")
    assert response.status_code == 400
    assert apteryx.get("/test/settings/priority") == "1"


def test_restapi_set_tree_static():
    tree = """
{
    "settings": {
        "enable": "false",
        "debug": "0",
        "priority": "5",
        "volume": "1"
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": "false",
        "debug": "0",
        "priority": "5",
        "readonly": "0",
        "volume": "1"
    }
}
""")


def test_restapi_set_tree_null_value():
    tree = """
{
    "settings": {
        "enable": "false",
        "debug": "",
        "priority": "5"
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": "false",
        "priority": "5",
        "readonly": "0",
        "volume": "1"
    }
}
""")


def test_restapi_set_tree_list_full_strings():
    tree = """
{
    "animals": {
        "animal": {
            "frog": {
                "name": "frog",
                "type": "1",
                "food": {
                    "cricket": {
                        "name": "cricket",
                        "type": "insect"
                    },
                    "snail": {
                        "name": "snail",
                        "type": "insect"
                    }
                }
            },
            "turtle": {
                "name": "turtle",
                "type": "2",
                "toys": {
                    "toy": {
                        "basketball": "basketball",
                        "stones": "stones"
                    }
                }
            }
        }
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/animals".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": {
            "cat": {
                "name": "cat",
                "type": "1"
            },
            "dog": {
                "name": "dog",
                "colour": "brown"
            },
            "hamster": {
                "name": "hamster",
                "food" : {
                    "nuts": {
                        "name": "nuts",
                        "type": "kibble"
                    },
                    "banana" : {
                        "name": "banana",
                        "type": "fruit"
                    }
                },
                "type": "2"
            },
            "frog": {
                "name": "frog",
                "type": "1",
                "food": {
                    "cricket": {
                        "name": "cricket",
                        "type": "insect"
                    },
                    "snail": {
                        "name": "snail",
                        "type": "insect"
                    }
                }
            },
            "mouse": {
                "name": "mouse",
                "type": "2",
                "colour": "grey"
            },
            "parrot": {
                "name": "parrot",
                "type": "1",
                "colour": "blue",
                "toys": {
                    "toy": {
                        "rings": "rings",
                        "puzzles": "puzzles"
                    }
                }
            },
            "turtle": {
                "name": "turtle",
                "type": "2",
                "toys": {
                    "toy": {
                        "basketball": "basketball",
                        "stones": "stones"
                    }
                }
            }
        }
    }
}
""")


def test_restapi_set_tree_list_single_strings():
    tree = """
{
    "name": "frog",
    "type": "2"
}
"""
    response = requests.post("{}{}/test/animals/animal/frog".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/animals/animal/frog".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "frog": {
        "name": "frog",
        "type": "2"
    }
}
""")


def test_restapi_set_tree_list_key_colon():
    tree = """
{
    "name": "frog:y",
    "type": "2"
}
"""
    response = requests.post("{}{}/test/animals/animal/frog:y".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/animals/animal/frog:y".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "frog:y": {
        "name": "frog:y",
        "type": "2"
    }
}
""")


def test_restapi_set_tree_list_key_ns_colon():
    tree = """
{
    "name": "fre:dy"
}
"""
    response = requests.post("{}{}/t2:test/settings/users/fre:dy".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/t2:test/settings/users/fre:dy".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "fre:dy": {
        "name": "fre:dy"
    }
}
""")


def test_restapi_set_leaf_list_string():
    response = requests.post("{}{}/test/animals/animal/cat/toys/toy/ball".format(server_uri, docroot), verify=False, auth=server_auth, data="ball")
    assert response.status_code == 201
    assert apteryx.get("/test/animals/animal/cat/toys/toy/ball") == "ball"


def test_restapi_set_leaf_list_integer():
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.post("{}{}/test/settings/users/fred/groups/1".format(server_uri, docroot), verify=False, auth=server_auth, data="1")
    assert response.status_code == 201
    assert apteryx.get("/test/settings/users/fred/groups/1") == "1"


def test_restapi_set_leaf_list_invalid():
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.post("{}{}/test/settings/users/fred/groups/1".format(server_uri, docroot), verify=False, auth=server_auth, data="cat")
    assert response.status_code == 400


def test_restapi_set_leaf_list_array():
    data = """
{
    "toy": [
        "ball",
        "mouse"
    ]
}
    """
    response = requests.post("{}{}/test/animals/animal/cat/toys".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Array": "on"}, data=data)
    assert response.status_code == 201
    assert apteryx.get("/test/animals/animal/cat/toys/toy/ball") == "ball"
    assert apteryx.get("/test/animals/animal/cat/toys/toy/mouse") == "mouse"


def test_restapi_set_tree_list_full_arrays():
    tree = """
{
    "animals": {
        "animal": [
            {
                "name": "frog",
                "type": "2",
                "food": [
                    {
                        "name": "cricket",
                        "type": "insect"
                    },
                    {
                        "name": "snail",
                        "type": "insect"
                    }
                ]
            },
            {
                "name": "turtle",
                "type": "2",
                "toys": {
                    "toy": [
                        "basketball",
                        "stones"
                    ]
                }
            }

        ]
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers, data=tree)
    assert response.status_code == 200 or response.status_code == 201
    response = requests.get("{}{}/test/animals".format(server_uri, docroot), verify=False, auth=server_auth, headers={"X-JSON-Array": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200 or response.status_code == 201
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "1"
            },
            {
                "name": "dog",
                "colour": "brown"
            },
            {
                "name": "frog",
                "type": "2",
                "food": [
                    {
                        "name": "cricket",
                        "type": "insect"
                    },
                    {
                        "name": "snail",
                        "type": "insect"
                    }
                ]
            },
            {
                "name": "hamster",
                "food": [
                    {
                        "name": "banana",
                        "type": "fruit"
                    },
                    {
                        "name": "nuts",
                        "type": "kibble"
                    }
                ],
                "type": "2"
            },
            {
                "name": "mouse",
                "type": "2",
                "colour": "grey"
            },
            {
                "name": "parrot",
                "type": "1",
                "colour": "blue",
                "toys": {
                    "toy": [
                        "puzzles",
                        "rings"
                    ]
                }
            },
            {
                "name": "turtle",
                "type": "2",
                "toys": {
                    "toy": [
                        "basketball",
                        "stones"
                    ]
                }
            }
        ]
    }
}
""")


def test_restapi_set_true_false_string():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": "false"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx.get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": "true"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx.get("/test/settings/enable") == "true"


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_set_true_false_boolean():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": false}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx.get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": true}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx.get("/test/settings/enable") == "true"


def test_restapi_set_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        apteryx.prune("/test/settings/users")
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        data = json.dumps({"name": name, "age": 74})
        response = requests.post(f"{server_uri}{docroot}/test/settings/users/{encoded}", verify=False, auth=server_auth, data=data)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200 or response.status_code == 204 or response.status_code == 201, message
        assert len(response.content) == 0, message
        print(apteryx.get_tree("/test/settings/users"))
        assert apteryx.get(f"/test/settings/users/{key}/name") == name, message
        assert apteryx.get(f"/test/settings/users/{key}/age") == "74", message


def test_restapi_set_leaf_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        apteryx.prune("/test/animals/animal")
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        data = json.dumps(name)
        response = requests.post(f"{server_uri}{docroot}/test/animals/animal/cat/toys/toy/{encoded}", verify=False, auth=server_auth, data=data)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 201, message
        assert len(response.content) == 0, message
        print(apteryx.get_tree("/test/animals/animal/cat/toys/toy"))
        assert apteryx.get(f"/test/animals/animal/cat/toys/toy/{key}") == name, message


def test_restapi_set_tree_list_with_keys_with_slash():
    apteryx.prune("/test/animals/animal")
    c = '/'
    name = f"skinny{c}frog"
    encoded = f"skinny%{ord(c):02X}frog"
    key = name if c != '/' else encoded
    data = """
{
    "animals": {
        "animal": {
            """ + '"' + encoded + '"' + """: {
                "name": """ + '"' + name + '"' + """
            }
        }
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, data=data)
    message = f"Failed to process reserved character '{name}'"
    assert response.status_code == 201, message
    assert len(response.content) == 0, message
    print(apteryx.get_tree("/test/animals"))
    assert apteryx.get(f"/test/animals/animal/{key}/name") == name, message


def test_restapi_set_tree_leaf_list_with_keys_with_slash():
    apteryx.prune("/test/animals/animal")
    c = '/'
    name = f"skinny{c}frog"
    encoded = f"skinny%{ord(c):02X}frog"
    key = name if c != '/' else encoded
    data = """
{
    "animals": {
        "animal": {
            "cat": {
                "toys": {
                    "toy": {
                        """ + '"' + encoded + '"' + """: """ + '"' + name + '"' + """
                    }
                }
            }
        }
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri, docroot), verify=False, auth=server_auth, data=data)
    message = f"Failed to process reserved character '{name}'"
    assert response.status_code == 201, message
    assert len(response.content) == 0, message
    print(apteryx.get_tree("/test/animals"))
    assert apteryx.get(f"/test/animals/animal/cat/toys/toy/{key}") == name, message


def test_restapi_delete_not_found():
    response = requests.delete("{}{}/test/settings/invalid".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_delete_read_only_node():
    response = requests.delete("{}{}/test/state/counter".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_delete_read_only_trunk():
    response = requests.delete("{}{}/test/state".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_delete_hidden_node():
    response = requests.delete("{}{}/test/settings/hidden".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_delete_unset():
    response = requests.delete("{}{}/test/settings/description".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0


def test_restapi_delete_single_node():
    response = requests.delete("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')


def test_restapi_delete_trunk():
    response = requests.delete("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert apteryx.get("/test/settings/readonly") == "0"
    assert apteryx.get("/test/settings/hidden") == "friend"


def test_restapi_delete_list_entry():
    response = requests.delete("{}{}/test/animals/animal/cat".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/animals/animal/cat/name") is None
    assert apteryx.get("/test/animals/animal/cat/type") is None
    assert apteryx.get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx.get('/test/animals/animal/dog/colour') == 'brown'


def test_restapi_delete_list_entry_with_sublist():
    apteryx.set("/test/settings/users/fred/name", "fred")
    apteryx.set("/test/settings/users/fred/groups/admin", "admin")
    apteryx.set("/test/settings/users/fred/groups/software", "software")
    apteryx.set("/test/settings/users/fred/age", "99")
    response = requests.delete("{}{}/test/settings/users/fred".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    print(apteryx.get_tree("/test/settings/users"))
    assert not apteryx.search("/test/settings/users/")


def test_restapi_delete_list_entry_with_empty_sublist():
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.delete("{}{}/test/settings/users/fred".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    print(apteryx.get_tree("/test/settings/users"))
    assert not apteryx.search("/test/settings/users/")


def test_restapi_delete_list_entry_with_sublist_readonly_leaf():
    apteryx.set("/test/settings/users/fred/name", "fred")
    apteryx.set("/test/settings/users/fred/active", "true")
    response = requests.delete(f"{server_uri}{docroot}/test/settings/users/fred", verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    print(apteryx.get_tree("/test/settings/users"))
    assert apteryx.get("/test/settings/users") is None
    assert apteryx.get("/test/settings/users/fred/name") is None
    assert apteryx.get("/test/settings/users/fred/active") == "true"


def test_restapi_delete_trunk_with_list_containing_readonly_leaf():
    apteryx.set("/test/settings/hidden", "")
    apteryx.set("/test/settings/readonly", "")
    apteryx.set("/test/settings/users/fred/active", "true")
    apteryx.set("/test/settings/users/barney/active", "true")
    apteryx.set("/test/settings/users/wilma/active", "true")
    response = requests.delete(f"{server_uri}{docroot}/test/settings", verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/users/fred/active") == "true"
    assert apteryx.get("/test/settings/users/barney/active") == "true"
    assert apteryx.get("/test/settings/users/wilma/active") == "true"
    apteryx.set("/test/settings/users/fred/active", "")
    apteryx.set("/test/settings/users/barney/active", "")
    apteryx.set("/test/settings/users/wilma/active", "")
    print(apteryx.get_tree("/test/settings"))
    # This checks for a bug where there are no leaves in users/fred to delete
    # but we accidently left fred in the tree. Hence it looks like a set of
    # /test/settings/users = fred to apteryx
    assert apteryx.get("/test/settings/users") is None
    assert not apteryx.search("/test/settings/users/")


def test_restapi_delete_trunk_with_readonly_leaflist():
    apteryx.set("/test/state/romembers/fred", "fred")
    apteryx.set("/test/state/romembers/barney", "barney")
    apteryx.set("/test/state/romembers/wilma", "wilma")
    response = requests.delete(f"{server_uri}{docroot}/test/state", verify=False, auth=server_auth)
    assert response.status_code == 404  # Nothing to delete
    assert len(response.content) == 0
    assert apteryx.get("/test/state/romembers/fred") == "fred"
    assert apteryx.get("/test/state/romembers/barney") == "barney"
    assert apteryx.get("/test/state/romembers/wilma") == "wilma"


def test_restapi_delete_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "73")
        response = requests.delete(f"{server_uri}{docroot}/test/settings/users/{encoded}", verify=False, auth=server_auth)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200 or response.status_code == 204, message
        assert len(response.content) == 0, message
        assert not apteryx.search("/test/settings/users/"), message


def test_restapi_delete_leaf_list_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"red{c}ball"
        encoded = f"red%{ord(c):02X}ball"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/animals/animal/rabbit/toys/toy/{key}", name)
        response = requests.delete(f"{server_uri}{docroot}/test/animals/animal/rabbit/toys/toy/{encoded}", verify=False, auth=server_auth)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 204, message
        assert len(response.content) == 0, message
        assert not apteryx.search("/test/animals/animal/rabbit/toys/toy/"), message


def test_restapi_search_node():
    response = requests.get("{}{}/test/settings/enable/".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "enable": []
}
""")


def test_restapi_search_empty():
    apteryx.set("/test/settings/debug", "")
    apteryx.set("/test/settings/enable", "")
    apteryx.set("/test/settings/priority", "")
    apteryx.set("/test/settings/readonly", "")
    apteryx.set("/test/settings/volume", "")
    response = requests.get("{}{}/test/settings/".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": []
}
""")


def test_restapi_search_not_found():
    response = requests.get("{}{}/test/settings/invalid/".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 404
    assert len(response.content) == 0


def test_restapi_search_forbidden():
    response = requests.get("{}{}/test/settings/writeonly/".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_search_hidden_node():
    response = requests.get("{}{}/test/settings/hidden/".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0


def test_restapi_search_trunk():
    response = requests.get("{}{}/test/settings/".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": [
        "debug",
        "enable",
        "priority",
        "readonly",
        "volume"
    ]
}
""")


def test_restapi_search_list():
    response = requests.get("{}{}/test/animals/animal/".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": [
        "cat",
        "dog",
        "hamster",
        "mouse",
        "parrot"
    ]
}
""")


@pytest.mark.skipif(not search_etag, reason="do not support ETAG on search")
def test_restapi_search_etag_not_modified():
    response = requests.get("{}{}/test/animals/animal/".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") is not None
    assert response.headers.get("ETag") != "0"
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/animals/animal/".format(server_uri, docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0


def test_restapi_stream_event_no_initial_value():
    apteryx.set("/test/settings/priority", "")
    url = "{}{}/test/settings/priority".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    apteryx.set("/test/settings/priority", "1")
    for line in response.iter_lines(decode_unicode=True):
        if line == 'data: {"priority": 1}':
            event = True
            break
    response.close()
    time.sleep(1)
    assert event is True, "Did not receive an event for the change in data"
    # assert not apteryx.find("/apteryx/watchers/*", "/test/settings/priority")


def test_restapi_stream_event_node():
    apteryx.set("/test/settings/priority", "1")
    url = "{}{}/test/settings/priority".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    apteryx.set("/test/settings/priority", "2")
    initial = update = False
    for line in response.iter_lines(decode_unicode=True):
        if line == 'data: {"priority": 1}':
            initial = True
        elif line == 'data: {"priority": 2}':
            update = True
            break
    response.close()
    time.sleep(1)
    assert initial is True, "Did not receive the event for initial data"
    assert update is True, "Did not receive an event for the change in data"
    # assert not apteryx.find("/apteryx/watchers/*", "/test/settings/priority")


def test_restapi_stream_json_node():
    url = "{}{}/test/settings/priority".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    apteryx.set("/test/settings/priority", "2")
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"priority": 2}'):
            break


def test_restapi_stream_event_tree():
    url = "{}{}/test/settings".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    tree = """{"priority": "2", "enable": "false"}"""
    requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"settings": {"enable": false, "priority": 2}}':
            break


def test_restapi_stream_json_tree():
    url = "{}{}/test/settings".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    tree = """{"priority": "2", "enable": "false"}"""
    requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"settings": {"enable": false, "priority": 2}}'):
            break


def test_restapi_stream_event_list():
    url = "{}{}/test/animals".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    tree = """{"name": "frog","type": "2"}"""
    requests.post("{}{}/test/animals/animal/frog".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"animals": {"animal": [{"name": "frog", "type": "little"}]}}':
            break


def test_restapi_stream_json_list():
    url = "{}{}/test/animals".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    tree = """{"name": "frog","type": "2"}"""
    requests.post("{}{}/test/animals/animal/frog".format(server_uri, docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"animals": {"animal": [{"name": "frog", "type": "little"}]}}'):
            break


def test_restapi_query_empty():
    response = requests.get("{}{}/test/state/uptime?".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": "5",
        "hours": "50",
        "minutes": "30",
        "seconds": "20"
    }
}
""")


def test_restapi_query_invalid_queries():
    queries = [
        "die",
        "die=",
        "die=now",
        "die=now&fields=counter",
        "fields=counter&die=now",
        # "&",
        "&&,",
        "fields=;",
        "fields=;;",
        # "fields=/",
        # "fields=//",
        "fields=(",
        "fields=)",
        "fields=()",
        "fields=(node;node1)(node2;node3)",
    ]
    for query in queries:
        print("Checking " + query)
        response = requests.get("{}{}/test/state?{}".format(server_uri, docroot, query), verify=False, auth=server_auth)
        assert response.status_code == 400
        assert len(response.content) == 0


def test_restapi_query_field_empty():
    response = requests.get("{}{}/test/state/uptime?fields=".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 400
    assert len(response.content) == 0


def test_restapi_query_field_one_node():
    response = requests.get("{}{}/test/state/uptime?fields=hours".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "uptime": {
        "hours": "50"
    }
}
""")


def test_restapi_query_field_two_nodes():
    response = requests.get("{}{}/test/state/uptime?fields=days;minutes".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": "5",
        "minutes": "30"
    }
}
""")


def test_restapi_query_field_three_nodes():
    response = requests.get("{}{}/test/state/uptime?fields=days;minutes;hours".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": "5",
        "hours": "50",
        "minutes": "30"
    }
}
""")


def test_restapi_query_field_one_path():
    response = requests.get("{}{}/test/state?fields=uptime/days".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": "5"
        }
    }
}
""")


def test_restapi_query_field_two_paths():
    response = requests.get("{}{}/test/state?fields=uptime/days;uptime/seconds".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": "5",
            "seconds": "20"
        }
    }
}
""")


def test_restapi_query_field_three_paths():
    response = requests.get("{}{}/test/state?fields=uptime/days;uptime/seconds;uptime/hours".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": "5",
            "hours": "50",
            "seconds": "20"
        }
    }
}
""")


def test_restapi_query_field_one_path_two_nodes():
    response = requests.get("{}{}/test/state?fields=uptime(days;seconds)".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": "5",
            "seconds": "20"
        }
    }
}
""")


def test_restapi_query_field_two_paths_two_nodes():
    response = requests.get("{}{}/test/state?fields=uptime(days;seconds);uptime(hours;minutes)".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": "5",
            "hours": "50",
            "minutes": "30",
            "seconds": "20"
        }
    }
}
""")


def test_restapi_query_field_list_one_specific_node():
    response = requests.get("{}{}/test/animals/animal/mouse?fields=type".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "mouse": {
        "type": "2"
    }
}
""")


def test_restapi_query_field_list_two_specific_nodes():
    response = requests.get("{}{}/test/animals/animal/mouse?fields=name;type".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "mouse": {
        "name": "mouse",
        "type": "2"
    }
}
""")


def test_restapi_query_field_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*?fields=name".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "cat": {
        "name": "cat"
    },
    "dog": {
        "name": "dog"
    },
    "hamster": {
        "name": "hamster"
    },
    "mouse": {
        "name": "mouse"
    },
    "parrot": {
        "name": "parrot"
    }
}
""")


def test_restapi_query_field_two_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*/food/*?fields=name".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "hamster": {
        "food": {
            "banana": {
                "name": "banana"
            },
            "nuts": {
                "name": "nuts"
            }
        }
    }
}
""")


def test_restapi_query_field_etag_not_modified():
    response = requests.get("{}{}/test/settings?fields=priority".format(server_uri, docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads("""
{
    "settings": {
        "priority": "1"
    }
}
""")
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings?fields=priority".format(server_uri, docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0


_animals_all_name = """
{
    "animals": {
        "animal": {
            "cat": {
                "name": "cat"
            },
            "dog": {
                "name": "dog"
            },
            "hamster": {
                "name": "hamster"
            },
            "mouse": {
                "name": "mouse"
            },
            "parrot": {
                "name": "parrot"
            }
        }
    }
}
"""
_animal_all_name = """
{
    "animal": {
        "cat": {
            "name": "cat"
        },
        "dog": {
            "name": "dog"
        },
        "hamster": {
            "name": "hamster"
        },
        "mouse": {
            "name": "mouse"
        },
        "parrot": {
            "name": "parrot"
        }
    }
}
"""
_animals_mouse_name = """
{
    "animals": {
        "animal": {
            "mouse": {
                "name": "mouse"
            }
        }
    }
}
"""


def test_restapi_query_field_wild_index_1():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal(*/name)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_all_name)


def test_restapi_query_field_wild_index_2():
    response = requests.get(f"{server_uri}{docroot}/test/animals/animal?fields=*/name", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animal_all_name)


def test_restapi_query_field_specific_index_1():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal/mouse(name)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_mouse_name)


def test_restapi_query_field_specific_index_2():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal(mouse/name)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_mouse_name)


@pytest.mark.skip(reason="Needs a fix to query result to json conversion")
def test_restapi_query_field_mixed_index_1():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal(mouse/name;*/type)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": {
            "cat": {
                "type": "1"
            },
            "hamster": {
                "type": "2"
            },
            "mouse": {
                "name": "mouse"
            },
            "parrot": {
                "type": "1"
            }
        }
    }
}
    """)


@pytest.mark.skip(reason="Needs a fix to query result to json conversion")
def test_restapi_query_field_mixed_index_2():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal(mouse/name;type)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": {
            "cat": {
                "type": "1"
            },
            "hamster": {
                "type": "2"
            },
            "mouse": {
                "name": "mouse"
            },
            "parrot": {
                "type": "1"
            }
        }
    }
}
    """)


def test_restapi_query_field_no_index_1():
    response = requests.get(f"{server_uri}{docroot}/test/animals?fields=animal(name)", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_all_name)


def test_restapi_query_field_no_index_2():
    response = requests.get(f"{server_uri}{docroot}/test/animals/animal?fields=name", verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animal_all_name)


def test_restapi_rpc_native():
    apteryx.set("/t4:test/state/age", "100")
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_root_namespace():
    headers = {"X-JSON-Types": "on", "X-JSON-Array": "on", "X-JSON-Namespace": "on"}
    apteryx.set("/t4:test/state/age", "100")
    response = requests.post("{}{}/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_namespace():
    headers = {"X-JSON-Types": "on", "X-JSON-Array": "on", "X-JSON-Namespace": "on"}
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 204
    assert len(response.content) == 0


def test_restapi_rpc_empty_input():
    apteryx.set("/t4:test/state/age", "100")
    data = ""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_with_input():
    data = """{ "delay": 55 }"""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") == "55"


def test_restapi_rpc_with_input_invalid():
    data = """{ "delay": "cabbage" }"""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_with_simple_input_integer():
    data = """55"""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") == "55"


def test_restapi_rpc_with_simple_input_quoted():
    data = '"55"'
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") == "55"


def test_restapi_rpc_with_simple_input_invalid():
    data = """cabbage"""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_with_simple_input_integer_outofrange():
    data = """-1"""
    response = requests.post("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/age") is None


def test_restapi_rpc_alternate_operation():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.get("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "delay": 5 }""")


def test_restapi_rpc_invalid_operation():
    data = """{ "delay": 55 }"""
    response = requests.put("{}{}/t4:test/state/reset".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 405
    assert len(response.content) == 0


def test_restapi_rpc_with_output_string():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.post("{}{}/t4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "last-reset": "5" }""")


def test_restapi_rpc_with_output_integer():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.post("{}{}/t4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "last-reset": 5 }""")


def test_restapi_rpc_with_output_no_root_string():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.post("{}{}/t4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"5"')


def test_restapi_rpc_with_output_no_root_json():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.post("{}{}/t4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth, headers={"X-JSON-Types": "on", "X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("5")


def test_restapi_rpc_with_output_list():
    apteryx.set("/t4:test/state/history/1", "5")
    apteryx.set("/t4:test/state/history/2", "55")
    response = requests.post("{}{}/t4:test/state/get-reset-history".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "history": [ 5, 55 ] }""")


def test_restapi_rpc_with_output_multiple():
    apteryx.set("/t4:test/state/age", "5")
    apteryx.set("/t4:test/state/history/1", "5")
    apteryx.set("/t4:test/state/history/2", "55")
    response = requests.post("{}{}/t4:test/state/get-reset-history".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "last-reset": 5, "history": [ 5, 55 ] }""")


def test_restapi_rpc_with_output_list_empty():
    response = requests.post("{}{}/t4:test/state/get-reset-history".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "history": [] }""")


def test_restapi_rpc_get_with_output():
    apteryx.set("/t4:test/state/age", "5")
    response = requests.get("{}{}/t4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "last-reset": "5" }""")


def test_restapi_rpc_wildcard_no_input():
    response = requests.post("{}{}/t4:test/state/users/fred/set-age".format(server_uri, docroot), auth=server_auth)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/users/fred/age") is None


def test_restapi_rpc_wildcard_with_input():
    data = """{ "age": 74 }"""
    response = requests.post("{}{}/t4:test/state/users/fred/set-age".format(server_uri, docroot), auth=server_auth, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/users/fred/age") == "74"


def test_restapi_rpc_list_get():
    apteryx.set("/t4:test/state/users/fred/name", "fred")
    apteryx.set("/t4:test/state/users/fred/age", "24")
    response = requests.get("{}{}/t4:test/state/users".format(server_uri, docroot), auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{ "users": [{ "name": "fred", "age": 24 }]}""")


def test_restapi_rpc_list_create_entry():
    data = """{ "name": "fred", "age": 74 }"""
    response = requests.post("{}{}/t4:test/state/users".format(server_uri, docroot), verify=False, auth=server_auth, data=data)
    assert response.status_code == 200 or response.status_code == 204 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/users/fred/name") == "fred"
    assert apteryx.get("/t4:test/state/users/fred/age") == "74"


def test_restapi_rpc_list_modify_entry():
    apteryx.set("/t4:test/state/users/fred/name", "fred")
    apteryx.set("/t4:test/state/users/fred/age", "56")
    data = """{ "age": 33 }"""
    response = requests.put("{}{}/t4:test/state/users/fred".format(server_uri, docroot), verify=False, auth=server_auth, data=data)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/users/fred/name") == "fred"
    assert apteryx.get("/t4:test/state/users/fred/age") == "33"


def test_restapi_rpc_list_delete_entry():
    apteryx.set("/t4:test/state/users/fred/name", "fred")
    apteryx.set("/t4:test/state/users/fred/age", "73")
    response = requests.delete("{}{}/t4:test/state/users/fred".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    assert apteryx.get("/t4:test/state/users/fred/name") is None
    assert apteryx.get("/t4:test/state/users/fred/age") is None


def test_restapi_rpc_get_rpcs():
    headers = {"X-JSON-Types": "on", "X-JSON-Array": "on", "X-JSON-Namespace": "on"}
    response = requests.get("{}{}/operations/testing-4:get-rpcs".format(server_uri, docroot), auth=server_auth, headers=headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "paths": [
        { "methods": ["POST"], "path": "/operations/t4:reboot" },
        { "methods": ["GET", "POST"], "path": "/operations/t4:get-reboot-info" },
        { "methods": ["GET", "POST"], "path": "/operations/t4:get-rpcs" },
        { "methods": ["GET", "POST"], "path": "/t4:test/state/reset" },
        { "methods": ["GET", "POST"], "path": "/t4:test/state/get-last-reset-time" },
        { "methods": ["GET", "POST"], "path": "/t4:test/state/get-reset-history" },
        { "methods": ["GET", "POST"], "path": "/t4:test/state/users" },
        { "methods": ["PUT", "DELETE"], "path": "/t4:test/state/users/*" },
        { "methods": ["POST"], "path": "/t4:test/state/users/*/set-age" }
    ]
}
""")
