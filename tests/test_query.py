import apteryx
import json
import pytest
import requests
from conftest import server_uri, server_auth, docroot, get_restconf_headers, rfc3986_reserved


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
        "fields=;",
        "fields=;;",
        # "fields=/",
        # "fields=//",
        "fields=(",
        "fields=)",
        "fields=()",
        "fields=(node;node1)(node2;node3)",
        "depth=1&depth=100",
        "content=config&content=nonconfig",
        "fields=all&fields=all",
        "with-defaults=report-all&with-defaults=trim"
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
    "ietf-restconf:errors": {
        "error": [
            {
                "error-message": "Invalid input parameter",
                "error-tag": "invalid-value",
                "error-type": "application"
            }
        ]
    }
}
        """)


def test_restconf_query_content_all():
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
        "volume": "1",
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
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
        "volume": "1",
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
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
        "volume": "1"
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
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""{"settings": {}}""")


def test_restconf_query_depth_1_list():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings/users?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "users": [
        {}
    ]
}
    """) or response.json() == json.loads("""
{
    "users": [
    ]
}
    """)


def test_restconf_query_depth_2_trunk():
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
        "time": {},
        "users": [],
        "volume": "1"
    }
}
    """)


def test_restconf_query_depth_2_list():
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    response = requests.get("{}{}/data/test/settings/users?depth=2".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "users": [
        {
            "active": true,
            "age": 87,
            "name": "alfred"
        }
    ]
}
   """)


def test_restconf_query_depth_3():
    apteryx.set("/test/settings/time/day", "5")
    apteryx.set("/test/settings/time/hour", "12")
    apteryx.set("/test/settings/time/active", "true")
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
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
                "active": true,
                "age": 87,
                "name": "alfred"
            }
        ],
        "volume": "1"
    }
}
    """)


def test_restconf_query_animals_animal_depth_1():
    response = requests.get("{}{}/data/test/animals/animal?depth=1".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {}
    ]
}
    """) or response.json() == json.loads("""
{
    "animal": [
    ]
}
    """)


def test_restconf_query_animals_depth_2():
    response = requests.get("{}{}/data/test/animals?depth=2".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": []
    }
}
    """)


def test_restconf_query_animals_animal_depth_2():
    response = requests.get("{}{}/data/test/animals/animal?depth=2".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        },
        {
            "colour": "brown",
            "name": "dog"
        },
        {
            "food": [],
            "name": "hamster",
            "type": "animal-testing-types:little"
        },
        {
            "colour": "grey",
            "name": "mouse",
            "type": "animal-testing-types:little"
        },
        {
            "colour": "blue",
            "name": "parrot",
            "toys": {},
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_query_animals_depth_3():
    response = requests.get("{}{}/data/test/animals?depth=3".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "animal-testing-types:big"
            },
            {
                "colour": "brown",
                "name": "dog"
            },
            {
                "food": [],
                "name": "hamster",
                "type": "animal-testing-types:little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "animal-testing-types:little"
            },
            {
                "colour": "blue",
                "name": "parrot",
                "toys": {},
                "type": "animal-testing-types:big"
            }
        ]
    }
}
    """)


def test_restconf_query_animals_animal_depth_3():
    response = requests.get("{}{}/data/test/animals/animal?depth=3".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        },
        {
            "colour": "brown",
            "name": "dog"
        },
        {
            "food": [],
            "name": "hamster",
            "type": "animal-testing-types:little"
        },
        {
            "colour": "grey",
            "name": "mouse",
            "type": "animal-testing-types:little"
        },
        {
            "colour": "blue",
            "name": "parrot",
            "toys": {},
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_query_animals_depth_4():
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
                "type": "animal-testing-types:big"
            },
            {
                "colour": "brown",
                "name": "dog"
            },
            {
                "food": [],
                "name": "hamster",
                "type": "animal-testing-types:little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "animal-testing-types:little"
            },
            {
                "colour": "blue",
                "name": "parrot",
                "toys": {},
                "type": "animal-testing-types:big"
            }
        ]
    }
}
    """)


def test_restconf_query_animals_animal_depth_4():
    response = requests.get("{}{}/data/test/animals/animal?depth=4".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
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
            "type": "animal-testing-types:little"
        },
        {
            "colour": "grey",
            "name": "mouse",
            "type": "animal-testing-types:little"
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
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_query_animals_depth_5():
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
                "type": "animal-testing-types:big"
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
                "type": "animal-testing-types:little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "animal-testing-types:little"
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
                "type": "animal-testing-types:big"
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
        "type": "animal-testing-types:little"
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
        "type": "animal-testing-types:little"
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


_animals_all_name = """
{
    "animals": {
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
}
"""
_animal_all_name = """
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
"""
_animals_mouse_name = """
{
    "animals": {
        "animal": [
            {
                "name": "mouse"
            }
        ]
    }
}
"""


def test_restconf_query_field_wild_index_1():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal(*/name)", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_all_name)


def test_restconf_query_field_wild_index_2():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals/animal?fields=*/name", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animal_all_name)


def test_restconf_query_field_specific_index_1():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal/mouse(name)", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_mouse_name)


def test_restconf_query_field_specific_index_2():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal(mouse/name)", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_mouse_name)


def test_restconf_query_field_specific_index_by_key_with_reserved_characters():
    for c in rfc3986_reserved:
        name = f"fred{c}jones"
        encoded = f"fred%{ord(c):02X}jones"
        key = name if c != '/' else encoded
        apteryx.set(f"/test/settings/users/{key}/name", name)
        apteryx.set(f"/test/settings/users/{key}/age", "82")
        response = requests.get(f"{server_uri}{docroot}/data/testing:test/settings?fields=users({encoded}/name)", verify=False, auth=server_auth, headers=get_restconf_headers)
        message = f"Failed to process reserved character '{name}'"
        assert response.status_code == 200, message
        assert response.headers["Content-Type"] == "application/yang-data+json", message
        assert response.json() == {"testing:settings": {"users": [{"name": name}]}}, message


@pytest.mark.skip(reason="Needs a fix to query result to json conversion")
def test_restconf_query_field_mixed_index_1():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal(mouse/name;*/type)", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": {
            "cat": {
                "type": "animal-testing-types:1"
            },
            "hamster": {
                "type": "animal-testing-types:2"
            },
            "mouse": {
                "name": "mouse"
            },
            "parrot": {
                "type": "animal-testing-types:1"
            }
        }
    }
}
    """)


@pytest.mark.skip(reason="Needs a fix to query result to json conversion")
def test_restconf_query_field_mixed_index_2():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal(mouse/name;type)", verify=False, auth=server_auth, headers=get_restconf_headers)
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


def test_restconf_query_field_no_index_1():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals?fields=animal(name)", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animals_all_name)


def test_restconf_query_field_no_index_2():
    response = requests.get(f"{server_uri}{docroot}/data/test/animals/animal?fields=name", verify=False, auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers.get("ETag") is not None and response.headers.get("ETag") != "0"
    assert response.json() == json.loads(_animal_all_name)


def test_restconf_query_field_ns_aug():
    response = requests.get(f"{server_uri}{docroot}/data/testing-2:test?fields=settings/testing2-augmented:speed", auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing-2:test": {
        "settings": {
            "testing2-augmented:speed": "2"
        }
    }
}
""")


def test_restconf_query_field_ns_none():
    response = requests.get(f"{server_uri}{docroot}/data/testing-2:test?fields=settings/speed", auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "testing-2:test": {
        "settings": {
            "testing2-augmented:speed": "2"
        }
    }
}
""")


def test_restconf_query_field_ns_bad():
    response = requests.get(f"{server_uri}{docroot}/data/testing-2:test?fields=settings/test-dodgy:speed", auth=server_auth, headers=get_restconf_headers)
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.status_code == 400
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "ietf-restconf:errors": {
        "error": [
            {
                "error-message": "Invalid input parameter",
                "error-tag": "invalid-value",
                "error-type": "application"
            }
        ]
    }
}
""")


def test_restconf_query_with_defaults_explicit_leaf():
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=explicit".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "debug": "disable"
}
    """)


def test_restconf_query_with_defaults_trim_leaf():
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=trim".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
}
    """)


def test_restconf_query_with_defaults_report_all_leaf():
    apteryx.set("/test/settings/debug", "")
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "debug": "disable"
}
    """)


@pytest.mark.skip(reason="do not support tagging of default values")
def test_restconf_query_with_defaults_report_all_tagged():
    response = requests.get("{}{}/data/test/settings/debug?with-defaults=report-all-tagged".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "debug": "disable",
    "@debug" : {
        "ietf-netconf-with-defaults:default" : true
    }
}
    """)


def test_restconf_query_with_defaults_explicit_trunk():
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/data/test/settings?with-defaults=explicit".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "disable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "volume": "1"
    }
}
    """)


def test_restconf_query_with_defaults_trim_trunk_data():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "false")
    apteryx.set("/test/settings/debug", "0")
    response = requests.get("{}{}/data/test/settings?with-defaults=trim".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "settings": {
        "enable": true,
        "priority": 1,
        "users": [
            {
                "name": "alfred",
                "age": 87
            }
        ],
        "volume": "1"
    }
}
    """)


def test_restconf_query_with_defaults_report_all_trunk_data():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/debug", "")
    response = requests.get("{}{}/data/test/settings?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "disable",
        "enable": true,
        "priority": 1,
        "readonly": "yes",
        "time": {
            "active": false
        },
        "users": [
            {
                "active": false,
                "age": 87,
                "name": "alfred"
            }
        ],
        "volume": "1"
    }
}
    """)


def test_restconf_query_with_defaults_report_all_trunk_empty():
    apteryx.set("/test/settings/debug", "")
    apteryx.set("/test/settings/enable", "")
    apteryx.set("/test/settings/priority", "")
    apteryx.set("/test/settings/hidden", "")
    apteryx.set("/test/settings/readonly", "")
    apteryx.set("/test/settings/volume", "")
    response = requests.get("{}{}/data/test/settings?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "settings": {
        "debug": "disable",
        "enable": false,
        "readonly": "yes",
        "time": {
            "active": false
        }
    }
}
    """)


def test_restconf_query_with_defaults_empty_node():
    response = requests.get("{}{}/data/testing:test/settings/empty?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    if len(response.content) != 0:
        print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert (response.status_code == 204 and len(response.content) == 0) or (response.status_code == 200 and response.json() == json.loads('{"testing:empty": {}}'))


def test_restconf_query_with_defaults_empty_list():
    response = requests.get("{}{}/data/test/settings/users?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{}
    """)


def test_restconf_query_with_defaults_empty_leaf_list():
    apteryx.set("/test/settings/users/fred/name", "fred")
    response = requests.get("{}{}/data/test/settings/users=fred/groups?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{}
    """)


def test_restconf_query_with_defaults_explicit_list():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    apteryx.set("/test/settings/users/mildred/name", "mildred")
    apteryx.set("/test/settings/users/mildred/age", "84")
    apteryx.set("/test/settings/users/mildred/active", "false")
    response = requests.get("{}{}/data/test/settings/users?with-defaults=explicit".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "users": [
        {
            "active": true,
            "age": 87,
            "name": "alfred"
        },
        {
            "active": false,
            "age": 84,
            "name": "mildred"
        }
    ]
}
    """)


def test_restconf_query_with_defaults_trim_list():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    apteryx.set("/test/settings/users/mildred/name", "mildred")
    apteryx.set("/test/settings/users/mildred/age", "84")
    apteryx.set("/test/settings/users/mildred/active", "false")
    response = requests.get("{}{}/data/test/settings/users?with-defaults=trim".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.headers["Content-Type"] == "application/yang-data+json"
    assert response.json() == json.loads("""
{
    "users": [
        {
            "active": true,
            "age": 87,
            "name": "alfred"
        },
        {
            "age": 84,
            "name": "mildred"
        }
    ]
}
    """)


def test_restconf_query_with_defaults_report_all_list():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/users/alfred/active", "true")
    apteryx.set("/test/settings/users/mildred/name", "mildred")
    apteryx.set("/test/settings/users/mildred/age", "84")
    response = requests.get("{}{}/data/test/settings/users?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "users": [
        {
            "active": true,
            "age": 87,
            "name": "alfred"
        },
        {
            "active": false,
            "age": 84,
            "name": "mildred"
        }
    ]
}
    """)


def test_restconf_query_animals_animal_report_all_1():
    response = requests.get("{}{}/data/test/animals?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animals": {
        "animal": [
            {
                "name": "cat",
                "type": "animal-testing-types:big"
            },
            {
                "colour": "brown",
                "name": "dog",
                "type": "animal-testing-types:big"
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
                "type": "animal-testing-types:little"
            },
            {
                "colour": "grey",
                "name": "mouse",
                "type": "animal-testing-types:little"
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
                "type": "animal-testing-types:big"
            }
        ]
    }
}
    """)


def test_restconf_query_animals_animal_report_all_2():
    response = requests.get("{}{}/data/test/animals/animal?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "name": "cat",
            "type": "animal-testing-types:big"
        },
        {
            "colour": "brown",
            "name": "dog",
            "type": "animal-testing-types:big"
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
            "type": "animal-testing-types:little"
        },
        {
            "colour": "grey",
            "name": "mouse",
            "type": "animal-testing-types:little"
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
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_query_animals_animal_report_all_3():
    response = requests.get("{}{}/data/test/animals/animal/dog?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "animal": [
        {
            "colour": "brown",
            "name": "dog",
            "type": "animal-testing-types:big"
        }
    ]
}
    """)


def test_restconf_query_with_defaults_report_all_level_1():
    response = requests.get("{}{}/data/interfaces/interface?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "interface": [
        {
            "mtu": 8192,
            "name": "eth0",
            "status": "up"
        },
        {
            "mtu": 1500,
            "name": "eth1",
            "status": "up"
        },
        {
            "mtu": 9000,
            "name": "eth2",
            "status": "not feeling so good"
        },
        {
            "mtu": 1500,
            "name": "eth3",
            "status": "waking up"
        }
    ]
}
    """)


def test_restconf_query_with_defaults_report_all():
    response = requests.get("{}{}/data/interfaces?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "interfaces": {
        "interface": [
            {
                "mtu": 8192,
                "name": "eth0",
                "status": "up"
            },
            {
                "mtu": 1500,
                "name": "eth1",
                "status": "up"
            },
            {
                "mtu": 9000,
                "name": "eth2",
                "status": "not feeling so good"
            },
            {
                "mtu": 1500,
                "name": "eth3",
                "status": "waking up"
            }
        ]
    }
}
    """)


def test_restconf_query_with_defaults_interfaces_report_all_leaf():
    response = requests.get("{}{}/data/interfaces/interface/eth0/status?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "status": "up"
}
    """)


def test_restconf_query_with_defaults_report_all_specific_leaf():
    response = requests.get("{}{}/data/interfaces/interface/eth1/status?with-defaults=report-all".format(server_uri, docroot), auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "status": "up"
}
    """)


def test_restconf_query_proxy_with_defaults_report_all_leaf():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    apteryx.set("/test/settings/debug", "")
    response = requests.get("{}{}/data/logical-elements:logical-elements/logical-element/loopy/test/settings/debug?with-defaults=report-all".format(server_uri, docroot),
                            auth=server_auth, headers=get_restconf_headers)
    assert response.status_code == 200
    assert len(response.content) > 0
    print(json.dumps(response.json(), indent=4, sort_keys=True))
    assert response.json() == json.loads("""
{
    "testing:debug": "disable"
}
    """)


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
