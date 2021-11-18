import os
import subprocess
import pytest
import requests
import json
from lxml import etree

# TEST CONFIGURATION

host='localhost'
port=8080

APTERYX='LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'

# TEST HELPERS

db_default = [
    ('/test/settings/debug', 'enable'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/state/counter', '42'),
    ('/test/animals/animal/cat/name', 'cat'),
    ('/test/animals/animal/cat/type', 'big'),
    ('/test/animals/animal/dog/name', 'dog'),
    ('/test/animals/animal/dog/colour', 'brown'),
    ('/test/animals/animal/mouse/name', 'mouse'),
    ('/test/animals/animal/mouse/type', 'little'),
    ('/test/animals/animal/mouse/colour', 'grey'),
]

def apteryx_set(path, value):
    os.system("%s -s %s %s" % (APTERYX, path, value))

def apteryx_get(path):
    return subprocess.check_output("%s -g %s" % (APTERYX, path), shell=True).strip().decode('utf-8')

@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    os.system("%s -r /test" % (APTERYX))
    for path,value in db_default:
        apteryx_set(path, value)
    yield
    # After test
    os.system("echo After test")
    os.system("%s -r /test" % (APTERYX))

# API

def test_api_xml():
    response = requests.get("http://{}:{}/api.xml".format(host,port))
    xml = etree.fromstring(response.content)
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "txt/xml"

# GET

def test_basic_get_single_node():
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads('{ "debug": "enable" }')

def test_basic_get_node_null():
    os.system("%s -s %s %s" % (APTERYX, "/test/settings/debug", ""))
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads('{}')

def test_basic_get_tree_strings():
    response = requests.get("http://{}:{}/api/test/settings".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": "true",
        "debug": "enable",
        "priority": "1"
    }
}
""")

def test_basic_get_tree_json_types():
    response = requests.get("http://{}:{}/api/test/settings".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": true,
        "debug": "enable",
        "priority": 1
    }
}
""")

def test_basic_get_list_object():
    response = requests.get("http://{}:{}/api/test/animals/animal".format(host,port), headers={"X-JSON-Types":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animal": {
        "cat": {"name": "cat", "type": "big"},
        "dog": {"name": "dog", "colour": "brown"},
        "mouse": {"name": "mouse", "colour": "grey", "type": "little"}
    }
}
""")

def test_basic_get_list_array():
    response = requests.get("http://{}:{}/api/test/animals/animal".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animal": [
        {"name": "cat", "type": "big"},
        {"name": "dog", "colour": "brown"},
        {"name": "mouse", "colour": "grey", "type": "little"}
    ]
}
""")

def test_basic_get_etag_exists():
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.headers.get("ETag") != None
    assert response.json() == json.loads('{ "debug": "enable" }')

def test_basic_get_etag_changes():
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.headers.get("ETag") != None
    assert response.json() == json.loads('{ "debug": "enable" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert tag1 == response.headers.get("ETag")
    os.system("%s -s %s %s" % (APTERYX, "/test/settings/debug", "disable"))
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "debug": "disable" }')
    assert tag1 != response.headers.get("ETag")

def test_basic_get_etag_not_modified():
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.headers.get("ETag") != None
    assert response.json() == json.loads('{ "debug": "enable" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port), headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0

def test_basic_get_not_found():
    response = requests.get("http://{}:{}/api/test/settings/invalid".format(host,port))
    assert response.status_code == 404
    assert len(response.content) == 0

def test_basic_get_forbidden():
    response = requests.get("http://{}:{}/api/test/settings/readonly".format(host,port))
    assert response.status_code == 403
    assert len(response.content) == 0

def test_basic_get_hidden():
    response = requests.get("http://{}:{}/api/test/settings/secret".format(host,port))
    assert response.status_code == 403
    assert len(response.content) == 0

# SET

def test_basic_set_single_node():
    response = requests.post("http://{}:{}/api/test/settings".format(host,port), data="""{"debug": "disable"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "debug": "disable" }')

def test_basic_set_node_null():
    response = requests.post("http://{}:{}/api/test/settings".format(host,port), data="""{"debug": ""}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port))
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_basic_set_invalid_path():
    response = requests.post("http://{}:{}/api/test/cabbage".format(host,port), data="""{"debug": "enable"}""")
    assert response.status_code == 404
    assert len(response.content) == 0
    assert apteryx_get("/test/cabbage/debug") == ""

def test_basic_set_invalid_value():
    response = requests.post("http://{}:{}/api/test/settings".format(host,port), data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "enable"

def test_basic_set_hidden():
    response = requests.post("http://{}:{}/api/test/settings".format(host,port), data="""{"secret": "cabbage"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/secret") == "friend"

def test_basic_set_tree_static():
    tree = """
{
    "settings": {
        "enable": false,
        "debug": "disable",
        "priority": 99
    }
}
"""
    response = requests.post("http://{}:{}/api/test".format(host,port), data=tree)
    assert response.status_code == 200
    response = requests.get("http://{}:{}/api/test/settings".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == tree

def test_basic_set_tree_null_value():
    tree = """
{
    "settings": {
        "enable": false,
        "debug": "",
        "priority": 99
    }
}
"""
    response = requests.post("http://{}:{}/api/test".format(host,port), data=tree)
    assert response.status_code == 200
    response = requests.get("http://{}:{}/api/test/settings".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": false,
        "priority": 99
    }
}
""")

def test_basic_set_tree_list_full_strings():
    tree = """
{
    "animals": { 
        "animal": {
            "frog": {
                "name": "frog",
                "type": "little"
            }
        }
    }
}
"""
    response = requests.post("http://{}:{}/api/test".format(host,port), data=tree)
    assert response.status_code == 200
    response = requests.get("http://{}:{}/api/test/animals".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": {
            "cat": {
                "name": "cat",
                "type": "big"
            },
            "dog": {
                "name": "dog",
                "colour": "brown"
            },
            "frog": {
                "name": "frog",
                "type": "little"
            },
            "mouse": {
                "name": "mouse",
                "type": "little",
                "colour": "grey"
            }
        }
    }
}
""")

def test_basic_set_tree_list_single_strings():
    tree = """
{
    "name": "frog",
    "type": "little"
}
"""
    response = requests.post("http://{}:{}/api/test/animals/animal/frog".format(host,port), data=tree)
    assert response.status_code == 200
    response = requests.get("http://{}:{}/api/test/animals/animal/frog".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "frog": {
        "name": "frog",
        "type": "little"
    }
}
""")

def test_basic_set_tree_list_full_arrays():
    tree = """
{
    "animals": { 
        "animal": [
            {
                "name": "frog",
                "type": "little"
            },
        ]
    }
}
"""
    response = requests.post("http://{}:{}/api/test".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"}, data=tree)
    assert response.status_code == 200
    response = requests.get("http://{}:{}/api/test/animals".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "big"
            },
            {
                "name": "dog",
                "colour": "brown"
            },
            {
                "name": "frog",
                "type": "little"
            },
            {
                "name": "mouse",
                "type": "little",
                "colour": "grey"
            },
        ]
    }
}
""")

# DELETE

def test_basic_delete_single_node():
    response = requests.delete("http://{}:{}/api/test/settings/debug".format(host,port))
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}/api/test/settings/debug".format(host,port))
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_basic_delete_trunk():
    response = requests.delete("http://{}:{}/api/test/settings".format(host,port))
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}/api/test/settings".format(host,port))
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_basic_delete_list_entry():
    response = requests.delete("http://{}:{}/api/test/animals/animal/cat".format(host,port))
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("http://{}:{}/api/test/animals".format(host,port), headers={"X-JSON-Types":"on","X-JSON-Array":"on"})
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "dog",
                "colour": "brown"
            },
            {
                "name": "mouse",
                "type": "little",
                "colour": "grey"
            }
        ]
    }
}
""")

# SEARCH 

def test_basic_search_node():
    response = requests.get("http://{}:{}/api/test/settings/enable/".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "enable": []
}
""")

def test_basic_search_trunk():
    response = requests.get("http://{}:{}/api/test/settings/".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "settings": [
        "enable",
        "debug",
        "priority"
    ]
}
""")

def test_basic_search_list():
    response = requests.get("http://{}:{}/api/test/animals/animal/".format(host,port))
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang.data+json"
    assert response.json() == json.loads("""
{
    "animal": [
        "cat",
        "dog",
        "mouse"
    ]
}
""")

# STREAMS
