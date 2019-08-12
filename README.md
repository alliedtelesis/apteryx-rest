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

Lighttpd:
```
fastcgi.server = (
"/api" => (
  "fastcgi.handler" => (
    "socket" => "/var/run/apteryx-rest.sock",
    "check-local" => "disable",
    )
  )
)
```
## Unit tests
Uses GLib testing framework (https://developer.gnome.org/glib/stable/glib-Testing.html)
```
make test
```

Test arguments passed to GLib via $TEST_ARGS:
* -l: List test cases available in a test executable.
* --verbose: Run tests verbosely.
* -p PATH: Execute all tests matching the given path.
* -s PATH: Skip all tests matching the given path.

e.g.
```
make test TEST_ARGS="--verbose -p /get"
```

## Demo
* Requires installed glib-2.0 libxml-2.0 apteryx fcgi-2.4.0 jansson-2.12 lighttpd1.4
* Starts Apteryx with a simple demo schema
* Starts lighttpd on localhost:8080
```
./run.sh

curl http://localhost:8080/api.xml
```

## Protocol
* RESTful API over HTTP using HTTP GET, POST and DELETE
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
| **Delete**    | DELETE | PRUNE   | Traverse all nodes from the specified root path and set them to NULL.     |

## HTTP Status Codes
| Code | Description    |                                                                            |
| ---- | -------------- | -------------------------------------------------------------------------- |
| 200  | OK             | The request was successful. For a SET the configuration change has been applied and the HTTP BODY is empty. For a GET the path was valid and the HTTP body contains the requested data. |
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
curl -u manager:friend -k https://<HOST>/api/firewall/fw_rules/10

{"10": {
    "index": "10",
    "to": "public",
    "application": "http",
    "from": "private",
    "action": "1"
}}
```

* Retrieve the entire firewall configuration
```
curl -u manager:friend -k https://<HOST>/api/firewall

{"firewall": {
    "settings": {
        "protect": "1",
        "state": "2"
    },
    "fw_rules": {
        "10": {
            "index": "10",
            "to": "public",
            "application": "http",
            "from": "private",
            "action": "1"
        },
        "20": {
            "index": "20",
            "to": "public",
            "application": "ftp",
            "from": "private",
            "action": "1"
        }
    }
}}
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
