import json
import pytest
import requests
from conftest import server_uri, server_auth, docroot, apteryx_set, get_restconf_headers


def test_restconf_query_empty():
    response = requests.get("{}{}/data/test/state/uptime?".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "hours": 50,
        "minutes": 30,
        "seconds": 20
    }
}
""")


def test_restconf_query_invalid_queries():
    queries = [
        "die",
        "die=",
        "die=now",
        "die=now&fields=enable",
        "fields=enable&die=now",
        # "&",
        "&&,",
        # "fields=;",
        # "fields=;;",
        # "fields=/",
        # "fields=//",
        # "fields=(",
        # "fields=)",
        # "fields=()",
        "fields=all&fields=all"
    ]
    for query in queries:
        print("Checking " + query)
        response = requests.get("{}{}/data/test/settings?{}".format(server_uri, docroot, query), headers=get_restconf_headers)
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


def test_restconf_query_content_all():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?content=all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": 1,
        "time": {
            "day": 5,
            "hour": 12,
            "active": true
        },
        "users": [{
            "name": "alfred",
            "age": 87,
            "active": true
        }]
    }
}
    """)


def test_restconf_query_content_config():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?content=config".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "volume": 1,
        "time": {
            "day": 5,
            "hour": 12
        },
        "time": {
            "day": 5,
            "hour": 12
        },
        "users": [{
            "name": "alfred",
            "age": 87
        }]
    }
}
    """)


def test_restconf_query_content_nonconfig():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?content=nonconfig".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "readonly": "yes",
        "time": {
            "active": true
        },
        "users": [{
            "active": true
        }]
    }
}
    """)


def test_restconf_query_depth_unbounded():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?depth=unbounded".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "time": {
            "active": true,
            "day": 5,
            "hour": 12
        },
        "users": [
            {
                "active": true,
                "age": 87,
                "name": "alfred"
            }
        ],
        "volume": 1
    }
}
    """)


def test_restconf_query_depth_1_leaf():
    response = requests.get("{}{}/data/test/settings/debug?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "debug": "enable"
}
    """)


def test_restconf_query_depth_1_trunk():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""{}""")


def test_restconf_query_depth_1_list():
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings/users?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""{}""")


def test_restconf_query_depth_2_trunk():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?depth=2".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": 1
    }
}
    """)


def test_restconf_query_depth_2_list():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings/users?depth=2".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "users": [
        {
            "name": "alfred",
            "age": 87,
            "active": true
        }
    ]
}
    """)


def test_restconf_query_depth_3():
    apteryx_set("/test/settings/time/day", "5")
    apteryx_set("/test/settings/time/hour", "12")
    apteryx_set("/test/settings/time/active", "true")
    apteryx_set("/test/settings/users/alfred/name", "alfred")
    apteryx_set("/test/settings/users/alfred/age", "87")
    apteryx_set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?depth=3".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "enable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "time": {
            "active": true,
            "day": 5,
            "hour": 12
        },
        "users": [
            {
                "name": "alfred",
                "age": 87,
                "active": true
            }
        ],
        "volume": 1
    }
}
    """)


def test_restconf_query_depth_4():
    response = requests.get("{}{}/data/test/animals?depth=4".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "big"
            },
            {
                "colour": "brown",
                "name": "dog"
            },
            {
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
                "name": "hamster",
                "type": "little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "little"
            },
            {
                "colour": "blue",
                "name": "parrot",
                "type": "big"
            }
        ]
    }
}
    """)


def test_restconf_query_depth_5():
    response = requests.get("{}{}/data/test/animals?depth=5".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "big"
            },
            {
                "colour": "brown",
                "name": "dog"
            },
            {
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
                "name": "hamster",
                "type": "little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "little"
            },
            {
                "colour": "blue",
                "name": "parrot",
                "toys": {
                    "toy": [
                        "puzzles",
                        "rings"
                    ]
                },
                "type": "big"
            }
        ]
    }
}
    """)


def test_restconf_query_field_one_node():
    response = requests.get("{}{}/data/test/state/uptime?fields=hours".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "hours": 50
    }
}
""")


def test_restconf_query_field_two_nodes():
    response = requests.get("{}{}/data/test/state/uptime?fields=days;minutes".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "minutes": 30
    }
}
""")


def test_restconf_query_field_three_nodes():
    response = requests.get("{}{}/data/test/state/uptime?fields=days;minutes;hours".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "uptime": {
        "days": 5,
        "hours": 50,
        "minutes": 30
    }
}
""")


def test_restconf_query_field_one_path():
    response = requests.get("{}{}/data/test/state?fields=uptime/days".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5
        }
    }
}
""")


def test_restconf_query_field_two_paths():
    response = requests.get("{}{}/data/test/state?fields=uptime/days;uptime/seconds".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "seconds": 20
        }
    }
}
""")


def test_restconf_query_field_three_paths():
    response = requests.get("{}{}/data/test/state?fields=uptime/days;uptime/seconds;uptime/hours".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "hours": 50,
            "seconds": 20
        }
    }
}
""")


def test_restconf_query_field_one_path_two_nodes():
    response = requests.get("{}{}/data/test/state?fields=uptime(days;seconds)".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "seconds": 20
        }
    }
}
""")


def test_restconf_query_field_two_paths_two_nodes():
    response = requests.get("{}{}/data/test/state?fields=uptime(days;seconds);uptime(hours;minutes)".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "state": {
        "uptime": {
            "days": 5,
            "hours": 50,
            "minutes": 30,
            "seconds": 20
        }
    }
}
""")


def test_restconf_query_field_list_one_specific_node():
    response = requests.get("{}{}/data/test/animals/animal=mouse?fields=type".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [{
        "type": "little"
    }]
}
""")


def test_restconf_query_field_list_two_specific_nodes():
    response = requests.get("{}{}/data/test/animals/animal=mouse?fields=name;type".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [{
        "name": "mouse",
        "type": "little"
    }]
}
""")


def test_restconf_query_field_list_all_nodes():
    response = requests.get("{}{}/data/test/animals/animal?fields=name".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat"
        },
        {
            "name": "dog"
        },
        {
            "name": "hamster"
        },
        {
            "name": "mouse"
        },
        {
            "name": "parrot"
        }
    ]
}
""")


def test_restconf_query_field_list_select_two_all_nodes():
    response = requests.get("{}{}/data/test/animals/animal=hamster/food?fields=name".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "food": [
        {
            "name": "banana"
        },
        {
            "name": "nuts"
        }
    ]
}
""")


@pytest.mark.skip(reason="not implemented yet")
def test_restconf_query_with_defaults_report_all_leaf():
    apteryx_set("/test/settings/debug", "")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "debug": "enable",
}
    """)


@pytest.mark.skip(reason="not implemented yet")
def test_restconf_query_with_defaults_trim_leaf():
    apteryx_set("/test/settings/debug", "disable")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=trim".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
}
    """)


@pytest.mark.skip(reason="not implemented yet")
def test_restconf_query_with_defaults_explicit_leaf():
    apteryx_set("/test/settings/debug", "disable")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=explicit".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "debug": "disable",
}
    """)


@pytest.mark.skip(reason="not implemented yet")
def test_restconf_query_with_defaults_report_all_tagged_not_supported():
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=report-all-tagged".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
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


# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=report-all
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=report-all-tagged
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=trim
# GET /restconf/data/example:interfaces/interface=eth1??with-defaults=explicit

# POST /restconf/data/example-jukebox:jukebox/playlist=Foo-One?insert=first
# POST /restconf/data/example-jukebox:jukebox/playlist=Foo-One?insert=after&point=%2Fexample-jukebox%3Ajukebox%2Fplaylist%3DFoo-One%2Fsong%3D1

# // filter = /event/event-class='fault'
# GET /streams/NETCONF?filter=%2Fevent%2Fevent-class%3D'fault'
# // filter = /event/severity<=4
# GET /streams/NETCONF?filter=%2Fevent%2Fseverity%3C%3D4
# // filter = /linkUp|/linkDown
# GET /streams/SNMP?filter=%2FlinkUp%7C%2FlinkDown
# // filter = /*/reporting-entity/card!='Ethernet0'
# GET /streams/NETCONF?filter=%2F*%2Freporting-entity%2Fcard%21%3D'Ethernet0'
# // filter = /*/email-addr[contains(.,'company.com')]
# GET /streams/critical-syslog?filter=%2F*%2Femail-addr[contains(.%2C'company.com')]
# // Note: The module name is used as the prefix.
# // filter = (/example-mod:event1/name='joe' and
# //           /example-mod:event1/status='online')
# GET /streams/NETCONF?filter=(%2Fexample-mod%3Aevent1%2Fname%3D'joe'%20and%20%2Fexample-mod%3Aevent1%2Fstatus%3D'online')
# // To get notifications from just two modules (e.g., m1 + m2)
# // filter=(/m1:* or /m2:*)
# GET /streams/NETCONF?filter=(%2Fm1%3A*%20or%20%2Fm2%3A*)
# // start-time = 2014-10-25T10:02:00Z
# GET /streams/NETCONF?start-time=2014-10-25T10%3A02%3A00Z
# // start-time = 2014-10-25T10:02:00Z
# // stop-time = 2014-10-25T12:31:00Z
# GET /mystreams/NETCONF?start-time=2014-10-25T10%3A02%3A00Z&stop-time=2014-10-25T12%3A31%3A00Z
