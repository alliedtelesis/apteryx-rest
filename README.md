# RESTful API for Apteryx

## Build
Dependencies:
```
glib-2.0 libxml-2.0 fcgi-2.4.0 jansson-2.12 apteryx-4.32
```

Make and install:
```
./autogen.sh
./configure
make install
```

Run using modules installed in /etc/modules:
```
apteryx-rest -b -m /etc/modules -p /var/run/apteryx-rest.pid -s /var/run/apteryx-rest.sock

```

Run in with the default encoding set for restconf
```
apteryx-rest -b -m /etc/modules -p /var/run/apteryx-rest.pid -s /var/run/apteryx-rest.sock -e "application/yang-data+json"

```

Lighttpd:
```
server.stream-response-body = 2
fastcgi.server = (
    "/api" => (
        "fastcgi.handler" => (
            "docroot" => "/api",
            "socket" => "/var/run/apteryx-rest.sock",
            "check-local" => "disable",
        )
    )
)
```

NGINX
```
http {
    server {
        location /api {
            root /api;
            fastcgi_pass unix:/var/run/apteryx-rest.sock;
            fastcgi_buffering off;
            fastcgi_read_timeout 600s;
            fastcgi_param NO_BUFFERING "";
            fastcgi_param DOCUMENT_ROOT      $document_root;
            fastcgi_param REQUEST_METHOD     $request_method;
            fastcgi_param REQUEST_URI        $request_uri;
            fastcgi_param QUERY_STRING       $query_string;
            fastcgi_param CONTENT_TYPE       $content_type;
            fastcgi_param CONTENT_LENGTH     $content_length;
            fastcgi_param HTTP_IF_MATCH      $http_if_match;
            fastcgi_param HTTP_IF_NONE_MATCH $http_if_none_match;
            fastcgi_param HTTP_IF_MODIFIED_SINCE $http_if_modified_since;
            fastcgi_param HTTP_IF_UNMODIFIED_SINCE $http_if_unmodified_since;
        }
    }
}
```

## Demo and Tests
* Requires dev packages for glib-2.0 libxml-2.0 jansson-2.12
* builds apteryx, apteryx-xml, fcgi and lighttpd(or nginx)
* Starts apteryxd and apteryx-rest using data models in models/
* Starts lighttpd(or nginx) on localhost:8080
```
./run.sh

curl http://localhost:8080/api.xml

python3 -m pytest -v
python3 -m pytest -k restconf
python3 -m pytest -k test_restapi_get_single_node

google-chrome .gcov/index.html
```

## Protocol
* RESTful API over HTTP using HTTP GET, POST/PUT/PATCH and DELETE
* API and data model specified using XML
* JSON formatted content
* Data addressed using hierarchical path
* URL path only required to locate data in the model (does not require the query string component)
* Supports HTTP GET for retrieval of data (response body contains JSON formatted data)
* Supports HTTP POST for setting of data (request body contains JSON formatted data)
* Supports HTTP DELETE for recursively clearing (setting to NULL) all data from the specified path
* Empty responses imply default values
* Complex sets only modify the nodes spec

| Operation     | HTTP   | Apteryx |                                                                           |
| ------------- | -------| ------- | ------------------------------------------------------------------------- |
| **Create**    | POST   | SET     | All nodes are considered NULL until SET (they do not need to be created). |
| **Read**      | GET    | GET     | A NULL return implies default values.                                     |
| **Update**    | PUT    | SET     | No difference in operation as Create.                                     |
| **Delete**    | DELETE | SET     | Traverse all nodes from the specified root path and set them to NULL.     |

## HTTP Status Codes
| Code | Description    |                                                                            |
| ---- | -------------- | -------------------------------------------------------------------------- |
| 200  | OK             | The GET request was successful. The path was valid and the HTTP body contains the requested data. |
| 201  | Created        | The POST request was successful. The configuration change has been applied and the HTTP BODY is empty. |
| 204  | No Content     | The PUT/PATCH request was successful. The configuration change has been applied and the HTTP BODY is empty. |
| 304  | Not Modified   | This status is returned if the user has requested a conditional get and the resource (path and all sub-paths) has not changed since the last retrieval. |
| 400  | Bad Request    | The request is incorrectly formatted or contains invalid parameters that cannot be applied. To ensure compatibility with being a RESTful API, the API uses standard HTTP status codes. However, to help the user understand why the request failed, a 400 response also supplies a JSON formatted error value and message in the HTTP BODY. Error codes below 1000 refer to standard errno values from IEEE Std 1003.1-2001. Values above Bad Request 1000 are custom error codes for the specific feature and their definitions are specified in the API for that feature. Example error response: {"error":"-1004", "message":"IPv6 Address invalid for mode"} |
| 403  | Forbidden      | The user does not have authorization to access the requested URI. Either the path does not exist or the path has permissions that prevent the operation from being completed (e.g. read-only and a SET was attempted or write-only and a GET was attempted). |
| 404  | Not Found      | The requested URI does not exist. |
| 500  | Internal Error | Internal error (e.g. no memory) |

## API Schema
Specified in XML can can be retrieved from the device.

```
curl -u manager:friend -k https://<HOST>/api.xml

<?xml version="1.0" encoding="UTF-8"?>
<MODULE xmlns="https://github.com/alliedtelesis/apteryx"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="https://github.com/alliedtelesis/apteryx
    https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd">
    <NODE name="test" help="this is a test node">
        <NODE name="debug" mode="rw" default="0" help="Debug configuration" pattern="^(0|1)$">
            <VALUE name="disable" value="0" help="Debugging is disabled" />
            <VALUE name="enable" value="1" help="Debugging is enabled" />
        </NODE>
        <NODE name="state" mode="r" default="0" help="Read only field" >
          <VALUE name="up" value="0" help="State is up" />
          <VALUE name="down" value="1" help="State is down" />
        </NODE>
        <NODE name="list" help="this is a list of stuff">
            <NODE name="*" help="the list item">
                <NODE name="name" mode="rw" help="this is the list key"/>
                <NODE name="type" mode="rw" default="1" help="this is the list type">
                    <VALUE name="big" value="1"/>
                    <VALUE name="little" value="2"/>
                </NODE>
                <NODE name="sub-list" help="this is a list of stuff attached to a list">
                    <NODE name="*" help="the sublist item">
                        <NODE name="i-d" mode="rw" help="this is the sublist key"/>
                    </NODE>
                </NODE>
            </NODE>
        </NODE>
        <NODE name="trivial-list" help="this is a simple list of stuff">
            <NODE name="*" help="the list item" />
        </NODE>
    </NODE>
</MODULE>
```

## GET

* Get the list of firewall rules (note the ending slash to indicate only return direct children)
```
curl -u manager:friend -k https://<HOST>/api/firewall/fw_rules/

{"fw_rules": ["10","20"]}
```

* Get a single node's value
```
curl -u manager:friend -k https://<HOST>/api/firewall/fw_rules/10/application

{"application": "http"}
```

* Retrieve the entire rule
```
curl -s -u manager:friend -k https://<HOST>/api/firewall/fw_rules/10 | python -m json.tool
{
    "10": {
        "action": "1",
        "application": "http",
        "from": "private",
        "index": "10",
        "to": "public"
    }
}
```

* Retrieve the entire firewall configuration
```
curl -s -u manager:friend -k https://<HOST>/api/firewall | python -m json.tool
{
    "firewall": {
        "fw_rules": {
            "10": {
                "action": "1",
                "application": "http",
                "from": "private",
                "index": "10",
                "to": "public"
            },
            "20": {
                "action": "1",
                "application": "ftp",
                "from": "private",
                "index": "20",
                "to": "public"
            }
        },
        "settings": {
            "protect": "1",
            "state": "2"
        }
    }
}
```

## Conditional GET
HTTP "conditional gets" allow the client to request a resource only if the resource has changed since it was last retrieved. The API uses the "Entity Tag" mechanism to avoid the overhead of retrieving large sub-tree's when there have been no changes in that path (and all sub-paths).
Each GET response from the API contains the following header:

```Etag: 51676B1E00314```

The client can then do a conditional request with the following header:

```If-None-Match: 51676B1E00314```

e.g.
```
curl -u manager:friend -k https://<HOST>/api/firewall --header 'If-None-Match: 51676B1E00314'

304 Not Modified
```

## GET Format options
* Drop requested node from response
```
curl -s -u manager:friend -k https://<HOST>/api/firewall/settings/protect | python -m json.tool
{ "protect": "1" }
```
```
curl -s -u manager:friend -H "X-JSON-Root: off" -k https://<HOST>/api/firewall/settings/protect | python -m json.tool
"1"
```

* Emulate multiple responses by providing a top level array in response
```
curl -s -u manager:friend -k https://<HOST>/api/firewall/settings/protect | python -m json.tool
{ "protect": "1" }
```
```
curl -s -u manager:friend -H "X-JSON-Multi: on" -k https://<HOST>/api/firewall/settings/protect | python -m json.tool
[ { "protect": "1" } ]
```

* JSON arrays for list entries
```
curl -s -u manager:friend -H "X-JSON-Array: on" -k https://<HOST>/api/firewall/fw_rules | python -m json.tool
{
    "fw_rules": [
        {
            "index": "10",
            "to": "public",
            "application": "http",
            "from": "private",
            "action": "1"
        },
        {
            "index": "20",
            "to": "public",
            "application": "ftp",
            "from": "private",
            "action": "1"
        }
    ]
}
```

* JSON type encoding
```
curl -s -u manager:friend -k https://<HOST>/api/system/ram/free | python -m json.tool
{ "free": "1884040" }
```
```
curl -s -u manager:friend -H "X-JSON-Types: on" -k https://<HOST>/api/system/ram/free  | python -m json.tool
{ "free": 1884040 }
```

## GET Queries
Field queries as per [RFC8040:4.8.3](https://datatracker.ietf.org/doc/html/rfc8040#section-4.8.3)

```
curl -s -u manager:friend -k https://<HOST>/api/system/state/uptime?fields=hours
{
    "uptime": {
        "hours": "50"
    }
}
```

```
curl -s -u manager:friend -k https://<HOST>/api/system/state/uptime?fields=days;minutes
{
    "uptime": {
        "days": "5",
        "minutes": "30"
    }
}
```

```
curl -s -u manager:friend -k https://<HOST>/api/system/state?fields=uptime/days;uptime/seconds
{
    "state": {
        "uptime": {
            "days": "5",
            "seconds": "20"
        }
    }
}
```

```
curl -s -u manager:friend -k https://<HOST>/api/system/state?fields=uptime(days;seconds)
{
    "state": {
        "uptime": {
            "days": "5",
            "seconds": "20"
        }
    }
}
```

## POST
* Change the application attribute in firewall rule 10
```
curl -u manager:friend -k -H "Content-Type: application/json" -d \
'{"application":"skype"}' https://<HOST>/api/firewall/fw-rules/10
```

* Create a new rule 30
```
curl -u manager:friend -k -H "Content-Type: application/json" -d \
'{"30": {
    "index": "30",
    "to": "public",
    "application": "tftp",
    "from": "private",
    "action": "1",
}}' https://<HOST>/api/firewall/fw-rules
```

* Set the application on rule 10 to NULL (unset)
```
curl -u manager:friend -k -H "Content-Type: application/json" -d \
'{"application":""}' https://<HOST>/api/firewall/fw-rules/10
```

## DELETE
* Delete an entire firewall rule by pruning the sub-tree. Note that an HTTP delete is equivalent operation to a traversal and set to NULL.
```
curl -u manager:friend -k -X "DELETE" https://<HOST>/api/firewall/fw_rules/10
```

## STREAMS
* Send a GET request with content type text/event-stream to receive asynchronous changes for a path from the server

```
var source = new EventSource("/api/firewall");
source.onmessage = function(event) {
  console.log(event.data);
};
ƒ (event) {
  console.log(event.data);
}
{"state": 1}
{"state": 0}
```

```
curl -N -H "X-JSON-Types: on" -H "Accept:text/event-stream" http://localhost:8080/api/firewall/settings

data: {"state": 1}

data: {"state": 0}

```

```
curl -N -H "X-JSON-Types: on" -H "Accept:application/stream+json" http://localhost:8080/api/firewall/settings

{"state": 1}
{"state": 0}
```
