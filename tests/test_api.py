import apteryx
import json
import pytest
import requests
import time
from conftest import server_uri, server_auth, docroot, get_restconf_headers, set_restconf_headers


@pytest.mark.skip(reason="requires target specific http server configuration")
def test_restconf_root_discovery():
    # Accept: application/xrd+xml
    response = requests.get("http://{}/.well-known/host-meta".format(server_uri))
    print(response)
    assert response.status_code == 200
    # assert response.headers["Content-Type"] == "application/xrd+xml"
    assert "restconf" in response
    assert docroot in response


def test_restconf_root_resource():
    response = requests.get("{}{}".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:%s": {
        "data": {},
        "operations": {},
        "yang-library-version": "2019-01-04"
    }
}
""" % (docroot[1:]))


def test_restconf_operations_list():
    response = requests.get("{}{}/operations".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:operations" : {
            "testing-4:reboot": "%s/operations/testing-4:reboot",
            "testing-4:get-reboot-info": "%s/operations/testing-4:get-reboot-info",
            "testing-4:get-rpcs": "%s/operations/testing-4:get-rpcs"
    }
}""" % (docroot, docroot, docroot))


def test_restconf_yang_library_version():
    response = requests.get("{}{}/yang-library-version".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "yang-library-version" : "2019-01-04" }')


def test_restconf_valid_content_length():
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert int(response.headers["Content-Length"]) == len(response.content)
    assert response.json() == json.loads('{ "enable": true }')


def test_restconf_zero_content_length():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": "2"}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    print(response.headers)
    assert response.status_code == 201
    assert int(response.headers["Content-Length"]) == len(response.content) == 0


def test_restconf_get_timestamp_node():
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") is not None and response.headers.get("Last-Modified") != "0"
    # assert response.headers.get("Last-Modified") == time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    assert response.json() == json.loads('{ "enable": true }')


def test_restconf_get_timestamp_namespace():
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("Last-Modified"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("Last-Modified") is not None
    assert time.strftime("%a, %d %b", time.gmtime()) in response.headers.get("Last-Modified")
    assert response.json() == json.loads('{ "testing:enable": true }')


def test_restconf_get_timestamp_trunk():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("Last-Modified"))
    assert response.headers.get("Last-Modified") is not None
    assert time.strftime("%a, %d %b", time.gmtime()) in response.headers.get("Last-Modified")


def test_restconf_get_timestamp_config_changes():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("Last-Modified"))
    timestamp = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.headers.get("Last-Modified") is not None and response.headers.get("Last-Modified") != timestamp


@pytest.mark.skip(reason="we update timestamps for all resource (config/state) changes")
def test_restconf_get_timestamp_state_no_change():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("Last-Modified"))
    timestamp = response.headers.get("Last-Modified")
    time.sleep(1)
    apteryx.set("/test/settings/readonly", "false")
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.headers.get("Last-Modified") is not None and response.headers.get("Last-Modified") == timestamp


def test_restconf_get_if_modified_since():
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    last_modified = response.headers.get("Last-Modified")
    assert response.json() == json.loads('{ "enable": true }')
    headers = {**get_restconf_headers, 'If-Modified-Since': last_modified}
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 304
    assert len(response.content) == 0
    time.sleep(1)
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Last-Modified") is not None and response.headers.get("Last-Modified") != last_modified
    assert response.json() == json.loads('{ "enable": false }')


def test_restconf_get_if_modified_since_namespace():
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    last_modified = response.headers.get("Last-Modified")
    assert response.json() == json.loads('{ "testing:enable": true }')
    headers = {**get_restconf_headers, 'If-Modified-Since': last_modified}
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 304
    assert len(response.content) == 0
    time.sleep(1)
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Last-Modified") is not None and response.headers.get("Last-Modified") != last_modified
    assert response.json() == json.loads('{ "testing:enable": false }')


def test_restconf_get_etag():
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "enable": true }')


def test_restconf_get_etag_namespace():
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    print(response.headers.get("ETag"))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads('{ "testing:enable": true }')


def test_restconf_get_etag_trunk():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("ETag"))
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"


def test_restconf_get_etag_config_changes():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("ETag"))
    etag = response.headers.get("ETag")
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != etag


@pytest.mark.skip(reason="we update etag for all resource (config/state) changes")
def test_restconf_get_etag_state_no_change():
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    print(response.headers.get("ETag"))
    etag = response.headers.get("ETag")
    apteryx.set("/test/settings/readonly", "false")
    response = requests.get("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") == etag


def test_restconf_get_if_none_match():
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    etag = response.headers.get("Etag")
    assert response.json() == json.loads('{ "enable": true }')
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers={**get_restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 304
    assert len(response.content) == 0
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/test/settings/enable".format(server_uri, docroot), auth=server_auth, headers={**get_restconf_headers, 'If-None-Match': etag})
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Etag") is not None and response.headers.get("Etag") != etag
    assert response.json() == json.loads('{ "enable": false }')


def test_restconf_get_if_none_match_namespace():
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    etag = response.headers.get("Etag")
    assert response.json() == json.loads('{ "testing:enable": true }')
    headers = {**get_restconf_headers, 'If-None-Match': etag}
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 304
    assert len(response.content) == 0
    apteryx.set("/test/settings/enable", "false")
    response = requests.get("{}{}/data/testing:test/settings/enable".format(server_uri, docroot), auth=server_auth, headers=headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Etag") is not None and response.headers.get("Etag") != etag
    assert response.json() == json.loads('{ "testing:enable": false }')


def test_restconf_get_if_none_match_put():
    response = requests.get(f"{server_uri}{docroot}/test/settings/enable", auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    etag = response.headers.get("Etag")
    assert response.json() == json.loads('{ "enable": true }')
    headers_get_inm = {**set_restconf_headers, 'If-None-Match': etag}
    response = requests.get(f"{server_uri}{docroot}/test/settings/enable", auth=server_auth, headers=headers_get_inm)
    assert response.status_code == 304
    assert len(response.content) == 0
    data = """{"enable": "false"}"""
    headers = {**set_restconf_headers, 'If-None-Match': etag}
    response = requests.put(f"{server_uri}{docroot}/test/settings/enable", data=data, auth=server_auth, headers=headers)
    assert response.status_code == 412
    headers = {**set_restconf_headers}
    response = requests.put(f"{server_uri}{docroot}/test/settings/enable", data=data, auth=server_auth, headers=headers)
    assert response.status_code == 204
    response = requests.get(f"{server_uri}{docroot}/test/settings/enable", auth=server_auth, headers=headers_get_inm)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers.get("Etag") is not None and response.headers.get("Etag") != etag
    assert response.json() == json.loads('{ "enable": false }')


# TODO 3.5.3. Any reserved characters MUST be percent-encoded, according to Sections 2.1 and 2.5 of [RFC3986].
# TODO 3.5.4.  Default Handling

# TODO 7.  Error Reporting
#  error-type = transport|rpc|protocol|application
#           | error-tag               | status code      |
#           +-------------------------+------------------+
#           | in-use                  | 409              |
#           | invalid-value           | 400, 404, or 406 |
#           | (request) too-big       | 413              |
#           | (response) too-big      | 400              |
#           | missing-attribute       | 400              |
#           | bad-attribute           | 400              |
#           | unknown-attribute       | 400              |
#           | bad-element             | 400              |
#           | unknown-element         | 400              |
#           | unknown-namespace       | 400              |
#           | access-denied           | 401 or 403       |
#           | lock-denied             | 409              |
#           | resource-denied         | 409              |
#           | rollback-failed         | 500              |
#           | data-exists             | 409              |
#           | data-missing            | 409              |
#           | operation-not-supported | 405 or 501       |
#           | operation-failed        | 412 or 500       |
#           | partial-operation       | 500              |
#           | malformed-message       | 400              |

def test_restconf_error_not_found():
    response = requests.get("{}{}/data/test/settings/invalid".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
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


def test_restconf_error_hidden_node():
    response = requests.get("{}{}/data/test/settings/hidden".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
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


def test_restconf_error_read_only():
    data = """{"counter": "123"}"""
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


def test_restconf_error_write_only():
    response = requests.get("{}{}/data/test/settings/writeonly".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
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


def test_restconf_error_unknown_namespace():
    response = requests.get("{}{}/data/cabbage:test/settings/writeonly".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 400 or response.status_code == 404
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    if response.status_code == 400:
        assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "unknown-namespace"
            "error-message" : "namespace not found"
        }
        ]
    }
}
    """)
    else:
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


def test_restconf_unsupported_method():
    response = requests.request("TRACE", "{}{}/data/".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 405


def test_restconf_unsupported_encoding():
    response = requests.get("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Accept": "text/html"})
    assert response.status_code == 406
    response = requests.get("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Accept": "application/xml"})
    assert response.status_code == 406
    response = requests.get("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Accept": "application/yang.data+xml"})
    assert response.status_code == 406
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Content-Type": "text/html"}, data="""Hello World""")
    assert response.status_code == 415
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Content-Type": "application/xml"}, data="""<cat></cat>""")
    assert response.status_code == 415
    content = """<settings><priority>1</priority></settings>"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers={"Content-Type": "application/yang.data+xml"}, data=content)
    assert response.status_code == 415


def test_restconf_options_rw():
    response = requests.options("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    assert response.headers["allow"] == "GET,HEAD,OPTIONS,POST,PUT,PATCH,DELETE"
    assert response.headers["accept-patch"] == "application/yang-data+json"


def test_restconf_options_r():
    response = requests.options("{}{}/data/test/state/counter".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    assert response.headers["allow"] == "GET,HEAD,OPTIONS"
    assert response.headers["accept-patch"] == "application/yang-data+json"


def test_restconf_options_container():
    response = requests.options("{}{}/data/test/animals".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    assert response.headers["allow"] == "GET,HEAD,OPTIONS,POST,PUT,PATCH,DELETE"
    assert response.headers["accept-patch"] == "application/yang-data+json"


def test_restconf_options_container_state_r():
    response = requests.options("{}{}/data/test/state".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) == 0
    assert response.headers["allow"] == "GET,HEAD,OPTIONS"
    assert response.headers["accept-patch"] == "application/yang-data+json"


def test_restconf_head():
    response = requests.head("{}{}/data/test/settings/priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.content == b''


def test_restconf_path_normalisation_double_slash():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": 2}"""
    response = requests.post("{}{}/data//test//settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "2"
    response = requests.get("{}{}/data//test//settings//priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 2 }')


def test_restconf_path_normalisation_relative():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": 2}"""
    response = requests.post("{}{}/data/test/../test/settings/../settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "2"
    response = requests.get("{}{}/data/test/../test/settings/../settings/priority/../priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 2 }')


def test_restconf_path_normalisation_dot():
    apteryx.set("/test/settings/priority", "")
    data = """{"priority": 2}"""
    response = requests.post("{}{}/data/./test/./settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert len(response.content) == 0
    assert apteryx.get("/test/settings/priority") == "2"
    response = requests.get("{}{}/data/./test/./settings/./priority".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads('{ "priority": 2 }')
