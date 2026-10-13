import apteryx
import json
import requests
from conftest import server_uri, server_auth, docroot, set_restconf_headers


def test_restconf_create_unique_violation():
    """
    Creating a new user (a distinct key from any existing user) with an email
    that duplicates an existing user's email should be rejected.
    """
    apteryx.set("/test/settings/users/bob/email", "bob@example.com")
    data = """{"users":[{"name":"alice","email":"bob@example.com"}]}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/settings/users/alice/email") is None
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors" : {
        "error" : [
        {
            "error-type" : "application",
            "error-tag" : "operation-failed",
            "error-message" : "value violates a unique constraint"
        }
        ]
    }
}
    """)


def test_restconf_create_unique_ok():
    """
    Creating a new user with a distinct email should succeed.
    """
    apteryx.set("/test/settings/users/bob/email", "bob@example.com")
    data = """{"users":[{"name":"alice","email":"alice@example.com"}]}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert apteryx.get("/test/settings/users/alice/email") == "alice@example.com"


def test_restconf_replace_unique_violation():
    """
    Replacing an existing entry so its email collides with another entry
    should be rejected.
    """
    apteryx.set("/test/settings/users/bob/email", "bob@example.com")
    apteryx.set("/test/settings/users/carol/name", "carol")
    apteryx.set("/test/settings/users/carol/email", "carol@example.com")
    data = """{"users":[{"name":"carol","email":"bob@example.com"}]}"""
    response = requests.put("{}{}/data/test/settings/users=carol".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/settings/users/carol/email") == "carol@example.com"


def test_restconf_update_unique_violation():
    """
    Merging just the email leaf of an existing entry (a bare PATCH) so that
    it collides with another entry's email should be rejected.
    """
    apteryx.set("/test/settings/users/bob/email", "bob@example.com")
    apteryx.set("/test/settings/users/dave/name", "dave")
    data = """{"email":"bob@example.com"}"""
    response = requests.patch("{}{}/data/test/settings/users=dave".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/settings/users/dave/email") is None


def test_restconf_create_unique_batch_violation():
    """
    Creating two new users with the same email in a single request should be
    rejected due to the unique email requirement.
    """
    data = """{"users":[{"name":"erin","email":"dup@example.com"},{"name":"frank","email":"dup@example.com"}]}"""
    response = requests.post("{}{}/data/test/settings".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/settings/users/erin/email") is None
    assert apteryx.get("/test/settings/users/frank/email") is None


def test_restconf_create_unique_violation_multi_key():
    """
    Creating a new friend (a distinct 2-part key from any existing friend)
    with an email that duplicates an existing friend's email should be
    rejected, the same as for a single-key list.
    """
    apteryx.set("/test/friends/fred_73/name", "fred")
    apteryx.set("/test/friends/fred_73/age", "73")
    apteryx.set("/test/friends/fred_73/email", "fred@example.com")
    data = """{"friends":[{"name":"mary","age":25,"email":"fred@example.com"}]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/friends/mary_25/email") is None


def test_restconf_create_unique_nested_violation():
    """
    Creating a gateway using a duplicate prefix should be rejected, even
    though the duplicate value is nested.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    data = """{"gateways":[{"name":"vlan11","config":{"sag":{"prefix":"10.0.0.0/24","mac":"00:00:00:00:00:01"}}}]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/gateways/vlan11/config/sag/prefix") is None


def test_restconf_create_unique_nested_ok():
    """
    Creating a new gateway with a distinct prefix should succeed, even
    though it shares its mac with an existing gateway.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    data = """{"gateways":[{"name":"vlan11","config":{"sag":{"prefix":"10.0.1.0/24","mac":"00:00:00:00:00:01"}}}]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert apteryx.get("/test/gateways/vlan11/config/sag/prefix") == "10.0.1.0/24"


def test_restconf_create_unique_nested_violation_mac_differs():
    """
    Creating a new gateway whose prefix duplicates an existing gateway's,
    but whose mac differs, should still be rejected, ensuring mac plays no
    part in the unique constraint check.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    data = """{"gateways":[{"name":"vlan11","config":{"sag":{"prefix":"10.0.0.0/24","mac":"00:00:00:00:00:02"}}}]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/gateways/vlan11/config/sag/prefix") is None


def test_restconf_replace_unique_nested_self_ok():
    """
    Replacing a gateway's own prefix with the value it already holds should
    succeed. The unique check must exclude an entry from being compared
    against its own current value.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    data = """{"gateways":[{"name":"vlan10","config":{"sag":{"prefix":"10.0.0.0/24","mac":"00:00:00:00:00:01"}}}]}"""
    response = requests.put("{}{}/data/test/gateways=vlan10".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert apteryx.get("/test/gateways/vlan10/config/sag/prefix") == "10.0.0.0/24"


def test_restconf_swap_unique_nested_ok():
    """
    Check that swapping the prefixes of two existing gateways in a single
    request succeeds.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    apteryx.set("/test/gateways/vlan11/name", "vlan11")
    apteryx.set("/test/gateways/vlan11/config/sag/prefix", "10.0.1.0/24")
    apteryx.set("/test/gateways/vlan11/config/sag/mac", "00:00:00:00:00:01")
    data = """
{
    "gateways": [
        {"name": "vlan10", "config": {"sag": {"prefix": "10.0.1.0/24"}}},
        {"name": "vlan11", "config": {"sag": {"prefix": "10.0.0.0/24"}}}
    ]
}
"""
    response = requests.patch("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 204
    assert apteryx.get("/test/gateways/vlan10/config/sag/prefix") == "10.0.1.0/24"
    assert apteryx.get("/test/gateways/vlan11/config/sag/prefix") == "10.0.0.0/24"


def test_restconf_reuse_unique_nested_after_delete_ok():
    """
    Deleting a gateway's prefix, then assigning that exact prefix to a
    different gateway in a later request, should succeed. E.g., deleting
    it must correctly free it up.
    """
    apteryx.set("/test/gateways/vlan10/name", "vlan10")
    apteryx.set("/test/gateways/vlan10/config/sag/prefix", "10.0.0.0/24")
    apteryx.set("/test/gateways/vlan10/config/sag/mac", "00:00:00:00:00:01")
    response = requests.delete("{}{}/data/test/gateways=vlan10/config/sag/prefix".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers)
    assert response.status_code == 204
    assert apteryx.get("/test/gateways/vlan10/config/sag/prefix") is None

    data = """{"gateways":[{"name":"vlan11","config":{"sag":{"prefix":"10.0.0.0/24","mac":"00:00:00:00:00:02"}}}]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 201
    assert apteryx.get("/test/gateways/vlan11/config/sag/prefix") == "10.0.0.0/24"


def test_restconf_create_unique_nested_batch_violation():
    """
    Creating two new gateways with the same prefix in a single request
    should be rejected due to the unique prefix requirement.
    """
    data = """{"gateways":[
        {"name":"vlan12","config":{"sag":{"prefix":"10.0.2.0/24","mac":"00:00:00:00:00:03"}}},
        {"name":"vlan13","config":{"sag":{"prefix":"10.0.2.0/24","mac":"00:00:00:00:00:04"}}}
    ]}"""
    response = requests.post("{}{}/data/test".format(server_uri, docroot), auth=server_auth, headers=set_restconf_headers, data=data)
    assert response.status_code == 409
    assert apteryx.get("/test/gateways/vlan12/config/sag/prefix") is None
    assert apteryx.get("/test/gateways/vlan13/config/sag/prefix") is None
