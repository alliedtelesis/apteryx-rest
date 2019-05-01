# RESTful API for Apteryx

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
| 400  | Bad Request    | The request is incorrectly formatted or contains invalid parameters that cannot be applied. To ensure compatibility with being a RESTful API, the WebGUI API uses standard HTTP status codes. However, to help the user understand why the request failed, a 400 response also supplies a JSON formatted error value and message in the HTTP BODY. Error codes below 1000 refer to standard errno values from IEEE Std 1003.1-2001. Values above Bad Request 1000 are custom error codes for the specific feature and their definitions are specified in the API for that feature. Example error response: {"error":"-1004", "message":"IPv6 Address invalid for mode"} |
| 403  | Forbidden      | The user does not have authorization to access the requested URI. Either the path does not exist or the path has permissions that prevent the operation from being completed (e.g. read-only and a SET was attempted or write-only and a GET was attempted). |
| 404  | Not Found      | The requested URI does not exist. |
| 500  | Internal Error | Internal error (e.g. no memory) |

## API
Specified in XML can can be retrieved from teh device.

```
curl -u manager:friend -k https:// <IP Address/Host Name>/api.xml
```

```
<?xml version="1.0" encoding="UTF-8"?>
<MODULE xmlns="https://github.com/alliedtelesis/apteryx"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="https://github.com/alliedtelesis/apteryx
	https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd">
	<NODE name="interfaces">
		<NODE name="interface" help="Interface List">
			<NODE name="*" help="Interface Name">
				<NODE name="name" mode="rw" help="Interface name" />
				<NODE name="type" mode="rw" help="Interface type" pattern="^(eth|ppp)$" />
				<NODE name="enabled" mode="rw" default="0" help="Interface admin status">
					<VALUE name="disabled" value="0" help="The interface is disabled" />
					<VALUE name="enabled" value="1" help="The interface is enabled" />
				</NODE>
			</NODE>
		</NODE>
	</NODE>
</MODULE>
```
