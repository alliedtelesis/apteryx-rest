import os
import subprocess
import pytest
import requests
import warnings
import json
from lxml import etree

# TEST CONFIGURATION
docroot = '/api'
search_etag = True
json_types = True
APTERYX_URL=''
server_uri = 'http://localhost:8080'
server_auth = None
# apteryx -s /apteryx/sockets/test tcp://0.0.0.0:9999
# APTERYX_URL='tcp://192.168.6.2:9999:'
# server_uri = 'https://192.168.6.2:443'
# server_auth = requests.auth.HTTPBasicAuth('manager', 'friend')

# TEST HELPERS
if json_types:
    json_headers = {"X-JSON-Types":"on", "X-JSON-Array":"on"}
else:
    json_headers = {"X-JSON-Array":"on"}

APTERYX='LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'

db_default = [
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/settings/hidden', 'friend'),
    ('/test/state/counter', '42'),
    ('/test/state/uptime/days', '5'),
    ('/test/state/uptime/hours', '50'),
    ('/test/state/uptime/minutes', '30'),
    ('/test/state/uptime/seconds', '20'),
    ('/test/animals/animal/cat/name', 'cat'),
    ('/test/animals/animal/cat/type', '1'),
    ('/test/animals/animal/dog/name', 'dog'),
    ('/test/animals/animal/dog/colour', 'brown'),
    ('/test/animals/animal/mouse/name', 'mouse'),
    ('/test/animals/animal/mouse/type', '2'),
    ('/test/animals/animal/mouse/colour', 'grey'),
]

def apteryx_set(path, value):
    assert subprocess.check_output("%s -s %s%s %s" % (APTERYX, APTERYX_URL, path, value), shell=True).strip().decode('utf-8') != "Failed"

def apteryx_get(path):
    return subprocess.check_output("%s -g %s%s" % (APTERYX, APTERYX_URL, path), shell=True).strip().decode('utf-8')

@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    warnings.filterwarnings('ignore', message='Unverified HTTPS request')
    os.system("echo Before test")
    assert subprocess.check_output("%s -r %s/test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"
    for path,value in db_default:
        apteryx_set(path, value)
    yield
    # After test
    os.system("echo After test")
    assert subprocess.check_output("%s -r %s/test" % (APTERYX, APTERYX_URL), shell=True).strip().decode('utf-8') != "Failed"

# API

def test_rest_api_xml():
    response = requests.get("{}{}.xml".format(server_uri,docroot), verify=False, auth=server_auth)
    xml = etree.fromstring(response.content)
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/xml"

# GET

def test_rest_get_single_node():
    response = requests.get("{}{}/test/settings/priority".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": "1" }')

def test_rest_get_integer_string():
    response = requests.get("{}{}/test/settings/priority".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": "1" }')

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_get_integer_integer():
    response = requests.get("{}{}/test/settings/priority".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "priority": 1 }')

def test_rest_get_boolean_string():
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": "true" }')
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": "false" }')

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_get_boolean_boolean():
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": true }')
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "enable": false }')

def test_rest_get_enum_value():
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "1" }')
    apteryx_set("/test/settings/debug", "0")
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "0" }')

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_get_enum_name():
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "enable" }')
    apteryx_set("/test/settings/debug", "0")
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{ "debug": "disable" }')

def test_rest_get_node_null():
    apteryx_set("/test/settings/debug", "")
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('{}')

def test_rest_get_tree_strings():
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": "true",
        "debug": "1",
        "priority": "1"
    }
}
""")

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_get_tree_json_types():
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": true,
        "debug": "enable",
        "priority": 1
    }
}
""")

def test_rest_get_list_object_strings():
    response = requests.get("{}{}/test/animals/animal".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": {
        "cat": {"name": "cat", "type": "1"},
        "dog": {"name": "dog", "colour": "brown"},
        "mouse": {"name": "mouse", "colour": "grey", "type": "2"}
    }
}
""")

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_get_list_object_types():
    response = requests.get("{}{}/test/animals/animal".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Types":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": {
        "cat": {"name": "cat", "type": "big"},
        "dog": {"name": "dog", "colour": "brown"},
        "mouse": {"name": "mouse", "colour": "grey", "type": "little"}
    }
}
""")

def test_rest_get_list_array():
    response = requests.get("{}{}/test/animals/animal".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": [
        {"name": "cat", "type": "1"},
        {"name": "dog", "colour": "brown"},
        {"name": "mouse", "colour": "grey", "type": "2"}
    ]
}
""")

def test_rest_get_list_select_one_strings():
    response = requests.get("{}{}/test/animals/animal/cat".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_get_list_select_one_array():
    response = requests.get("{}{}/test/animals/animal/cat".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": [
        { "name": "cat", "type": "1" }
    ]
}
""")

def test_rest_get_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*/name".format(server_uri,docroot), verify=False, auth=server_auth)
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
    "mouse": {
        "name": "mouse"
    }
}
""")

def test_rest_get_etag_exists():
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": "true" }')

def test_rest_get_etag_changes():
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") != None
    assert response.json() == json.loads('{ "enable": "true" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert tag1 == response.headers.get("ETag")
    apteryx_set("/test/settings/enable", "false")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.json() == json.loads('{ "enable": "false" }')
    assert tag1 != response.headers.get("ETag")

def test_rest_get_etag_not_modified():
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") != None
    assert response.json() == json.loads('{ "enable": "true" }')
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0

def test_rest_get_etag_zero():
    apteryx_set("/test/settings/enable", "")
    response = requests.get("{}{}/test/settings/enable".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") != None and response.headers.get("ETag") == "0"
    assert response.json() == json.loads('{}')

def test_rest_get_not_found():
    response = requests.get("{}{}/test/settings/invalid".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 404
    assert len(response.content) == 0

def test_rest_get_forbidden():
    response = requests.get("{}{}/test/settings/writeonly".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0

def test_rest_get_hidden_node():
    response = requests.get("{}{}/test/settings/hidden".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 403 or response.status_code == 404
    assert len(response.content) == 0

def test_rest_get_hidden_tree():
    apteryx_set("/test/settings/debug", "")
    apteryx_set("/test/settings/enable", "")
    apteryx_set("/test/settings/priority", "")
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

# FLAGS_JSON_FORMAT_ROOT=off
def test_rest_get_drop_root():
    response = requests.get("{}{}/test/settings/priority".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Root": "off"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('"1"')

# FLAGS_JSON_FORMAT_MULTI=on
def test_rest_get_multi():
    response = requests.get("{}{}/test/settings/priority".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Multi": "on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads('[ { "priority": "1" } ]')

# SET

def test_rest_set_single_node():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": "5"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/priority") == "5"

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_set_value_name():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "disable"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "enable"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"

def test_rest_set_value_value():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "0"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "0"
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "1"}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"

def test_rest_set_node_null():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": ""}""")
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_rest_set_invalid_path():
    response = requests.post("{}{}/test/cabbage".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "enable"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/cabbage/debug") == "Not found"

def test_rest_set_invalid_enum_value():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"debug": "cabbage"}""")
    assert response.status_code == 400
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/debug") == "1"

def test_rest_set_readonly():
    response = requests.post("{}{}/test/state".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"counter": "123"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/state/counter") == "42"

def test_rest_set_hidden():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"hidden": "cabbage"}""")
    assert response.status_code == 403
    assert len(response.content) == 0
    assert apteryx_get("/test/settings/hidden") == "friend"

def test_rest_set_out_of_range_integer_string():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": "1"}""")
    assert response.status_code == 200
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": "0"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": "6"}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": "55"}""")
    assert response.status_code == 400
    assert apteryx_get("/test/settings/priority") == "1"

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_set_out_of_range_integer_integer():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": 1}""")
    assert response.status_code == 200
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": 0}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": 6}""")
    assert response.status_code == 400
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"priority": 55}""")
    assert response.status_code == 400
    assert apteryx_get("/test/settings/priority") == "1"

def test_rest_set_tree_static():
    tree = """
{
    "settings": {
        "enable": "false",
        "debug": "0",
        "priority": "5"
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads(tree)

def test_rest_set_tree_null_value():
    tree = """
{
    "settings": {
        "enable": "false",
        "debug": "",
        "priority": "5"
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": "false",
        "priority": "5"
    }
}
""")

def test_rest_set_tree_list_full_strings():
    tree = """
{
    "animals": { 
        "animal": {
            "frog": {
                "name": "frog",
                "type": "1"
            }
        }
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200
    response = requests.get("{}{}/test/animals".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
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
            "frog": {
                "name": "frog",
                "type": "1"
            },
            "mouse": {
                "name": "mouse",
                "type": "2",
                "colour": "grey"
            }
        }
    }
}
""")

def test_rest_set_tree_list_single_strings():
    tree = """
{
    "name": "frog",
    "type": "2"
}
"""
    response = requests.post("{}{}/test/animals/animal/frog".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    assert response.status_code == 200
    response = requests.get("{}{}/test/animals/animal/frog".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "frog": {
        "name": "frog",
        "type": "2"
    }
}
""")

def test_rest_set_tree_list_full_arrays():
    tree = """
{
    "animals": { 
        "animal": [
            {
                "name": "frog",
                "type": "2"
            }
        ]
    }
}
"""
    response = requests.post("{}{}/test".format(server_uri,docroot), verify=False, auth=server_auth, headers=json_headers, data=tree)
    assert response.status_code == 200
    response = requests.get("{}{}/test/animals".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
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
                "type": "2"
            },
            {
                "name": "mouse",
                "type": "2",
                "colour": "grey"
            }
        ]
    }
}
""")

def test_rest_set_true_false_string():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"enable": "false"}""")
    assert response.status_code == 200
    assert apteryx_get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"enable": "true"}""")
    assert response.status_code == 200
    assert apteryx_get("/test/settings/enable") == "true"

@pytest.mark.skipif(not json_types, reason="do not support JSON types")
def test_rest_set_true_false_boolean():
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"enable": false}""")
    assert response.status_code == 200
    assert apteryx_get("/test/settings/enable") == "false"
    response = requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data="""{"enable": true}""")
    assert response.status_code == 200
    assert apteryx_get("/test/settings/enable") == "true"

# DELETE

def test_rest_delete_single_node():
    response = requests.delete("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("{}{}/test/settings/debug".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_rest_delete_trunk():
    response = requests.delete("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.json() == json.loads('{}')

def test_rest_delete_list_entry():
    response = requests.delete("{}{}/test/animals/animal/cat".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert len(response.content) == 0
    response = requests.get("{}{}/test/animals".format(server_uri,docroot), verify=False, auth=server_auth, headers={"X-JSON-Array":"on"})
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
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
                "type": "2",
                "colour": "grey"
            }
        ]
    }
}
""")

# SEARCH 

def test_rest_search_node():
    response = requests.get("{}{}/test/settings/enable/".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "enable": []
}
""")

def test_rest_search_trunk():
    response = requests.get("{}{}/test/settings/".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "settings": [
        "debug",
        "enable",
        "priority"
    ]
}
""")

def test_rest_search_list():
    response = requests.get("{}{}/test/animals/animal/".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""
{
    "animal": [
        "cat",
        "dog",
        "mouse"
    ]
}
""")

@pytest.mark.skipif(not search_etag, reason="do not support ETAG on search")
def test_rest_search_etag_not_modified():
    response = requests.get("{}{}/test/animals/animal/".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers.get("ETag") != None
    assert response.headers.get("ETag") != "0"
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/animals/animal/".format(server_uri,docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0

# STREAMS

def test_rest_stream_event_node():
    url = "{}{}/test/settings/priority".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    apteryx_set("/test/settings/priority", "2")
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"priority": 2}':
            break

def test_rest_stream_json_node():
    url = "{}{}/test/settings/priority".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    apteryx_set("/test/settings/priority", "2")
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"priority": 2}'):
            break

def test_rest_stream_event_tree():
    url = "{}{}/test/settings".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    tree = """{"priority": "2", "enable": "false"}"""
    requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"settings": {"enable": false, "priority": 2}}':
            break

def test_rest_stream_json_tree():
    url = "{}{}/test/settings".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    tree = """{"priority": "2", "enable": "false"}"""
    requests.post("{}{}/test/settings".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"settings": {"enable": false, "priority": 2}}'):
            break

def test_rest_stream_event_list():
    url = "{}{}/test/animals".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'text/event-stream'}, timeout=5)
    assert response.status_code == 200
    tree = """{"name": "frog","type": "2"}"""
    requests.post("{}{}/test/animals/animal/frog".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line == 'data: {"animals": {"animal": [{"name": "frog", "type": "little"}]}}':
            break

def test_rest_stream_json_list():
    url = "{}{}/test/animals".format(server_uri,docroot)
    response = requests.get(url, stream=True, verify=False, auth=server_auth, headers={'Accept': 'application/stream+json'}, timeout=5)
    assert response.status_code == 200
    tree = """{"name": "frog","type": "2"}"""
    requests.post("{}{}/test/animals/animal/frog".format(server_uri,docroot), verify=False, auth=server_auth, data=tree)
    for line in response.iter_lines(decode_unicode=True):
        print(line)
        if line and json.loads(line.decode("utf-8")) == json.loads(b'{"animals": {"animal": [{"name": "frog", "type": "little"}]}}'):
            break

# QUERY

def test_rest_query_empty():
    response = requests.get("{}{}/test/state/uptime?".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_invalid_queries():
    queries = [
        "die",
        "die=",
        "die=now",
        "die=now&fields=counter",
        "fields=counter&die=now",
        # "&",
        "&&,",
        "fields=;",
        "fields=;",
        "fields=;;",
        # "fields=/",
        # "fields=//",
        "fields=(",
        "fields=)",
        "fields=()",
    ]
    for query in queries:
        print("Checking " + query)
        response = requests.get("{}{}/test/state?{}".format(server_uri,docroot,query), verify=False, auth=server_auth)
        assert response.status_code == 404
        assert len(response.content) == 0

def test_rest_query_field_empty():
    response = requests.get("{}{}/test/state/uptime?fields=".format(server_uri,docroot), verify=False, auth=server_auth)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response.json() == json.loads("""{}""")

def test_rest_query_field_one_node():
    response = requests.get("{}{}/test/state/uptime?fields=hours".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_two_nodes():
    response = requests.get("{}{}/test/state/uptime?fields=days;minutes".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_three_nodes():
    response = requests.get("{}{}/test/state/uptime?fields=days;minutes;hours".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_one_path():
    response = requests.get("{}{}/test/state?fields=uptime/days".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_two_paths():
    response = requests.get("{}{}/test/state?fields=uptime/days;uptime/seconds".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_three_paths():
    response = requests.get("{}{}/test/state?fields=uptime/days;uptime/seconds;uptime/hours".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_one_path_two_nodes():
    response = requests.get("{}{}/test/state?fields=uptime(days;seconds)".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_two_paths_two_nodes():
    response = requests.get("{}{}/test/state?fields=uptime(days;seconds);uptime(hours;minutes)".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_list_one_specific_node():
    response = requests.get("{}{}/test/animals/animal/mouse?fields=type".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_list_two_specific_nodes():
    response = requests.get("{}{}/test/animals/animal/mouse?fields=name;type".format(server_uri,docroot), verify=False, auth=server_auth)
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

def test_rest_query_field_list_all_nodes():
    response = requests.get("{}{}/test/animals/animal/*?fields=name".format(server_uri,docroot), verify=False, auth=server_auth)
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
    "mouse": {
        "name": "mouse"
    }
}
""")

def test_rest_query_field_etag_not_modified():
    response = requests.get("{}{}/test/settings?fields=priority".format(server_uri,docroot), verify=False, auth=server_auth)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers.get("ETag") != None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads("""
{
    "settings": {
        "priority": "1"
    }
}
""")
    tag1 = response.headers.get("ETag")
    response = requests.get("{}{}/test/settings?fields=priority".format(server_uri,docroot), verify=False, auth=server_auth, headers={"If-None-Match": str(tag1)})
    print(response.headers.get("ETag"))
    assert response.status_code == 304
    assert len(response.content) == 0
