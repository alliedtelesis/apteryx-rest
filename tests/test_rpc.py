import json
import requests
from conftest import server_uri, server_auth, docroot, set_restconf_headers, apteryx_get, apteryx_set


def test_restconf_rpc_no_input():
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/system/reboot-info/reboot-time") == "Not found"
    assert apteryx_get("/system/reboot-info/message") == "Not found"
    assert apteryx_get("/system/reboot-info/language") == "Not found"


def test_restconf_rpc_empty_input():
    data = ""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/system/reboot-info/reboot-time") == "Not found"
    assert apteryx_get("/system/reboot-info/message") == "Not found"
    assert apteryx_get("/system/reboot-info/language") == "Not found"


def test_restconf_rpc_with_input():
    data = """
{
    "input": {
        "delay": 2,
        "message": "Rebooting because I can"
    }
}
"""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/system/reboot-info/reboot-time") == "2"
    assert apteryx_get("/system/reboot-info/message") == "Rebooting because I can"
    assert apteryx_get("/system/reboot-info/language") == "Not found"


def test_restconf_rpc_invalid_input():
    data = """
{
    "input": {
        "delay": 2,
        "cabbage": "tastes like feet"
    }
}
"""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
            "error-tag" : "invalid-value"
        }
        ]
    }
}
    """)


def test_restconf_rpc_invalid_path():
    response = requests.post("{}{}/operations/testing-4:reboot/input/delay".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
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


def test_restconf_rpc_invalid_get_operation():
    response = requests.get("{}{}/operations/testing-4:get-reboot-info".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 405
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-not-supported",
            "error-message" : "requested operation is not supported"
        }
        ]
    }
}
    """)


def test_restconf_rpc_invalid_delete_operation():
    response = requests.delete("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 405
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-not-supported",
            "error-message" : "requested operation is not supported"
        }
        ]
    }
}
    """)


def test_restconf_rpc_invalid_get_input_node():
    response = requests.get("{}{}/operations/testing-4:reboot/delay".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
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
            "error-message": "uri path not found"
        }
        ]
    }
}
    """)


def test_restconf_rpc_bad_handler():
    data = """
{
    "input": {
        "language": ""
    }
}
"""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 500
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed"
        }
        ]
    }
}
    """)


def test_restconf_rpc_fail_no_message():
    data = """
{
    "input": {
        "delay": 2,
        "language": "de"
    }
}
"""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
            "error-tag" : "operation-failed"
        }
        ]
    }
}
    """)


def test_restconf_rpc_fail_with_message():
    data = """
{
    "input": {
        "delay": 2,
        "language": "de-DE"
    }
}
"""
    response = requests.post("{}{}/operations/testing-4:reboot".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
            "error-tag" : "operation-failed",
            "error-message" : "do not support language de-DE"
        }
        ]
    }
}
    """)


def test_restconf_rpc_with_output():
    apteryx_set("/system/reboot-info/reboot-time", "2")
    apteryx_set("/system/reboot-info/message", "Rebooting because I can")
    response = requests.post("{}{}/operations/testing-4:get-reboot-info".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing-4:output": {
        "reboot-time": 2,
        "message": "Rebooting because I can"
    }
}
    """)


def test_restconf_rpc_invalid_get_output_node():
    response = requests.get("{}{}/operations/testing-4:get-reboot-info/reboot-time".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
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
            "error-message": "uri path not found"
        }
        ]
    }
}
    """)


def test_restconf_action_no_input():
    apteryx_set("/t4:test/state/age", "100")
    response = requests.post("{}{}/data/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t4:test/state/age") == "Not found"


def test_restconf_action_empty_input():
    apteryx_set("/t4:test/state/age", "100")
    data = ""
    response = requests.post("{}{}/data/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t4:test/state/age") == "Not found"


def test_restconf_action_with_input():
    data = """
{
    "input": {
        "delay": 55
    }
}
"""
    response = requests.post("{}{}/data/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t4:test/state/age") == "55"


def test_restconf_action_no_input_node():
    data = """
{
    "delay": 55
}
"""
    response = requests.post("{}{}/data/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
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
            "error-tag" : "invalid-value"
        }
        ]
    }
}
    """)


def test_restconf_action_invalid_get_operation():
    response = requests.get("{}{}/data/testing-4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 405
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-not-supported",
            "error-message" : "requested operation is not supported"
        }
        ]
    }
}
    """)


def test_restconf_action_invalid_delete_operation():
    response = requests.delete("{}{}/data/testing-4:test/state/reset".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 405
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-not-supported",
            "error-message" : "requested operation is not supported"
        }
        ]
    }
}
    """)


def test_restconf_action_with_output():
    apteryx_set("/t4:test/state/age", "5")
    response = requests.post("{}{}/data/testing-4:test/state/get-last-reset-time".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing-4:output": {
        "last-reset": 5
    }
}
    """)


def test_restconf_rpc_list_no_input():
    response = requests.post("{}{}/data/testing-4:test/state/users=fred/set-age".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t4:test/state/users/fred/age") == "Not found"


def test_restconf_rpc_list_with_input():
    data = """
{
    "input": {
        "age": 74
    }
}
"""
    response = requests.post("{}{}/data/testing-4:test/state/users=fred/set-age".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert len(response.content) == 0
    assert apteryx_get("/t4:test/state/users/fred/age") == "74"
