import pytest
import requests
import json
from lxml import etree
from conftest import server_uri, server_auth, docroot, apteryx_set, apteryx_get


# TEST CONFIGURATION
# docroot = '/api'
search_etag = True
json_types = True
APTERYX_URL = ''


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
    assert xml.findall('.//*[@mode="h"]') == []
    assert xml.findall('.//*[@mode="hr"]') == []
    assert xml.findall('.//*[@mode="rh"]') == []
    assert xml.findall('.//*[@mode="wh"]') == []
    assert xml.findall('.//*[@mode="hw"]') == []


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
    apteryx_set("/test/settings/enable", "false")
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
    apteryx_set("/test/settings/enable", "false")
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
    apteryx_set("/test/settings/debug", "0")
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
    apteryx_set("/test/settings/debug", "0")
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "disable" }')


def test_restapi_get_node_null():
    apteryx_set("/test/settings/debug", "")
    response = requests.get("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{}')


def test_restapi_get_node_empty():
    apteryx_set("/test/settings/empty", "empty")
    response = requests.get("{}{}/test/settings/empty".format(server_uri, docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{}')


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
        "volume": 1
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
    apteryx_set("/test/animals/animal/cat:ty/name", "cat:ty")
    apteryx_set("/test/animals/animal/cat:ty/type", "1")
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
    apteryx_set("/t2:test/settings/users/fre:dy/name", "fre:dy")
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
    apteryx_set("/test/settings/enable", "false")
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
    apteryx_set("/test/settings/enable", "")
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
    apteryx_set("/test/settings/debug", "")
    apteryx_set("/test/settings/enable", "")
    apteryx_set("/test/settings/priority", "")
    apteryx_set("/test/settings/readonly", "")
    apteryx_set("/test/settings/volume", "")
    response = requests.get("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')


# FLAGS_JSON_FORMAT_ROOT=off
def test_restapi_get_drop_root_string():
    apteryx_set("/test/settings/description", "This is a description")
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
    assert apteryx_get("/test/settings/description") == "This is a description"


def test_restapi_set_nonjson_string_quoted():
    response = requests.post("{}{}/test/settings/description".format(server_uri, docroot), verify=False, auth=server_auth, data='"This is a description"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/description") == "This is a description"


def test_restapi_set_nonjson_number_unquoted():
    response = requests.post("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, data='5')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "5"


def test_restapi_set_nonjson_number_quoted():
    response = requests.post("{}{}/test/settings/priority".format(server_uri, docroot), verify=False, auth=server_auth, data='"5"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "5"


def test_restapi_set_nonjson_value_unquoted():
    response = requests.post("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, data="disable")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"


def test_restapi_set_nonjson_value_quoted():
    response = requests.post("{}{}/test/settings/debug".format(server_uri, docroot), verify=False, auth=server_auth, data='"disable"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"


def test_restapi_set_nonjson_writeonly():
    response = requests.post("{}{}/test/settings/writeonly".format(server_uri, docroot), verify=False, auth=server_auth, data='"123"')
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/writeonly") == "123"


def test_restapi_set_nonjson_readonly():
    response = requests.post("{}{}/test/state/counter".format(server_uri, docroot), verify=False, auth=server_auth, data='"123"')
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/state/counter") == "42"


def test_restapi_set_single_node():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "5"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "5"


def test_restapi_set_explicit_content_type():
    headers = {"Content-Type": "application/json"}
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "5"}""", headers=headers)
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "5"


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_set_value_name():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "disable"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "enable"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"


def test_restapi_set_value_value():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "0"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "1"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"


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
    assert apteryx_get("/test/cabbage/debug") == "Not found"


def test_restapi_set_invalid_enum_value():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"


def test_restapi_set_readonly():
    response = requests.post("{}{}/test/state".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"counter": "123"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/state/counter") == "42"


def test_restapi_set_writeonly():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"writeonly": "123"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/writeonly") == "123"


def test_restapi_set_hidden():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"hidden": "cabbage"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/hidden") == "friend"


def test_restapi_set_out_of_range_integer_string():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "1"}""")
    assert response.status_code == 200 or response.status_code == 201
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "0"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "6"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"priority": "55"}""")
    assert response.status_code == 400
    assert apteryx_get("/test/settings/priority") == "1"


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
    assert apteryx_get("/test/settings/priority") == "1"


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
    assert apteryx_get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": "true"}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx_get("/test/settings/enable") == "true"


@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_restapi_set_true_false_boolean():
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": false}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx_get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri, docroot), verify=False, auth=server_auth, data="""{"enable": true}""")
    assert response.status_code == 200 or response.status_code == 201
    assert apteryx_get("/test/settings/enable") == "true"


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
    assert apteryx_get("/test/settings/readonly") == "0"
    assert apteryx_get("/test/settings/hidden") == "friend"


def test_restapi_delete_list_entry():
    response = requests.delete("{}{}/test/animals/animal/cat".format(server_uri, docroot), verify=False, auth=server_auth)
    assert response.status_code == 200 or response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/test/animals/animal/cat/name") == "Not found"
    assert apteryx_get("/test/animals/animal/cat/type") == "Not found"
    assert apteryx_get('/test/animals/animal/dog/name') == 'dog'
    assert apteryx_get('/test/animals/animal/dog/colour') == 'brown'


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
    apteryx_set("/test/settings/debug", "")
    apteryx_set("/test/settings/enable", "")
    apteryx_set("/test/settings/priority", "")
    apteryx_set("/test/settings/readonly", "")
    apteryx_set("/test/settings/volume", "")
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


def test_restapi_stream_event_node():
    url = "{}{}/test/settings/priority".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    apteryx_set("/test/settings/priority", "2")
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"priority": 2}':
            break


def test_restapi_stream_json_node():
    url = "{}{}/test/settings/priority".format(server_uri, docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    apteryx_set("/test/settings/priority", "2")
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
        # "fields=;",
        # "fields=;",
        # "fields=;;",
        # "fields=/",
        # "fields=//",
        # "fields=(",
        # "fields=)",
        # "fields=()",
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
