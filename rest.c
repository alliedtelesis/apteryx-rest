/**
 * @file rest.c
 *
 * Copyright 2018, Allied Telesis Labs New Zealand, Ltd
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */
#include "internal.h"
/* From libapteryx */
extern bool add_callback (const char *type, const char *path, void *fn, bool value,
                          void *data, uint32_t flags, guint timeout_ms);
extern bool delete_callback (const char *type, const char *path, void *fn, void *data);
#include <jansson.h>

#define HTTP_CODE_OK                    200
#define HTTP_CODE_CREATED               201
#define HTTP_CODE_NO_CONTENT            204
#define HTTP_CODE_NOT_MODIFIED          304
#define HTTP_CODE_BAD_REQUEST           400
#define HTTP_CODE_FORBIDDEN             403
#define HTTP_CODE_NOT_FOUND             404
#define HTTP_CODE_NOT_SUPPORTED         405
#define HTTP_CODE_CONFLICT              409
#define HTTP_CODE_PRECONDITION_FAILED   412
#define HTTP_CODE_INTERNAL_SERVER_ERROR 500

typedef enum
{
    REST_E_TAG_NONE,
    REST_E_TAG_IN_USE,
    REST_E_TAG_INVALID_VALUE,
    REST_E_TAG_REQ_TOO_BIG,
    REST_E_TAG_RESP_TOO_BIG,
    REST_E_TAG_MISING_ATTRIB,
    REST_E_TAG_BAD_ATTRIB,
    REST_E_TAG_UNKNOWN_ATTRIB,
    REST_E_TAG_BAD_ELEMENT,
    REST_E_TAG_UNKNOWN_ELEMENT,
    REST_E_TAG_UNKNOWN_NS,
    REST_E_TAG_ACCESS_DENIED,
    REST_E_TAG_LOCK_DENIED,
    REST_E_TAG_RESOURCE_DENIED,
    REST_E_TAG_ROLLBACK_FAILED,
    REST_E_TAG_DATA_EXISTS,
    REST_E_TAG_DATA_MISSING,
    REST_E_TAG_OPER_NOT_SUPPORTED,
    REST_E_TAG_OPER_FAILED,
    REST_E_TAG_PARTIAL_OPER,
    REST_E_TAG_MALFORMED,
    REST_E_TAG_MAX,
} rest_e_tag;

typedef struct _log_params
{
    const char *remote_user;
    const char *remote_addr;
    char *key;
    int rc;
} log_params;

const char *error_tags[REST_E_TAG_MAX] = {
    "",
    "in-use",
    "invalid-value",
    "(request) too-big",
    "(response) too-big",
    "missing-attribute",
    "bad-attribute",
    "unknown-attribute",
    "bad-element",
    "unknown-element",
    "unknown-namespace",
    "access-denied",
    "lock-denied",
    "resource-denied",
    "rollback-failed",
    "data-exists",
    "data-missing",
    "operation-not-supported",
    "operation-failed",
    "partial-operation",
    "malformed-message"
};

static sch_instance *g_schema = NULL;
static time_t g_boottime = 0;

static char *
restconf_error (int status, rest_e_tag error_tag)
{
    json_t *json = json_object();
    json_t *errors = json_object();
    json_t *array = json_array ();
    json_t *error = json_object();
    char *output;

    if (status == HTTP_CODE_FORBIDDEN)
    {
        json_object_set_new (error, "error-type", json_string ("protocol"));
    }
    else if (status == HTTP_CODE_NOT_FOUND)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-message", json_string ("uri path not found"));
    }
    else if (status == HTTP_CODE_NOT_SUPPORTED)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-message", json_string ("requested operation is not supported"));
    }
    else if (status == HTTP_CODE_CONFLICT)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-message", json_string ("object already exists"));
    }
    else if (status == HTTP_CODE_PRECONDITION_FAILED)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-message", json_string ("object modified"));
    }
    else
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        if (error_tag == REST_E_TAG_INVALID_VALUE)
            json_object_set_new (error, "error-message", json_string ("Invalid input parameter"));
        else
            json_object_set_new (error, "error-message", json_string ("malformed request syntax"));
    }
    if (error_tag != REST_E_TAG_NONE)
    {
        json_object_set_new (error, "error-tag", json_string (error_tags[error_tag]));
    }
    json_array_append_new (array, error);
    json_object_set_new (errors, "error", array);
    json_object_set_new (json, "ietf-restconf:errors", errors);

    output = json_dumps (json, 0);
    json_decref (json);
    return output;
}

static void
log_get_head (int flags, const char *path, const char *remote_user,
              const char *remote_addr, int rc)
{
    if ((flags & FLAGS_METHOD_GET) && (logging & LOG_GET))
    {
        NOTICE ("GET   [%3d] %s@%s %s\n", rc, remote_user, remote_addr, path);
    }
    else if ((flags & FLAGS_METHOD_HEAD) && (logging & LOG_HEAD))
    {
        NOTICE ("HEAD  [%3d] %s@%s %s\n", rc, remote_user, remote_addr, path);
    }
}

static gboolean
log_modified_leafs (GNode *node, gpointer arg)
{
    log_params *params = (log_params *) arg;
    char *path = NULL;
    char *value = NULL;

    path = apteryx_node_path (node);
    value = strrchr (path, '/');
    if (value)
    {
        *value = '\0';
        value++;
    }
    if (!value || strlen (value) == 0)
    {
        value = "";
    }
    NOTICE ("%s[%3d] %s@%s %s=%s\n",
            params->key, params->rc, params->remote_user, params->remote_addr, path, value);

    g_free (path);
    return FALSE;
}

static gboolean
log_deleted_leafs (GNode *node, gpointer arg)
{
    log_params *params = (log_params *) arg;
    char *path = NULL;

    if (!node->data || strlen (node->data) == 0)
        node = node->parent;

    if (node)
    {
        path = apteryx_node_path (node);
        if (node->data)
            NOTICE ("%s[%3d] %s@%s %s\n",
                    params->key, params->rc, params->remote_user, params->remote_addr, path);
    }
    g_free (path);
    return FALSE;
}

static void
log_post_put_patch (int flags, const char *path, GNode *root, const char *remote_user,
                    const char *remote_addr, int rc)
{
    char *key = NULL;

    if ((flags & FLAGS_METHOD_POST) && (logging & LOG_POST))
        key = "POST  ";
    else if ((flags & FLAGS_METHOD_PUT) && (logging & LOG_PUT))
        key = "PUT   ";
    else if ((flags & FLAGS_METHOD_PATCH) && (logging & LOG_PATCH))
        key = "PATCH ";

    if (key)
    {
        log_params params;
        params.remote_user = remote_user;
        params.remote_addr = remote_addr;
        params.key = key;
        params.rc = rc;
        if (root)
            g_node_traverse (root, G_IN_ORDER, G_TRAVERSE_LEAVES, -1, log_modified_leafs,
                             (gpointer) &params);
        else
            NOTICE ("%s[%3d] %s@%s %s\n",
                    key, rc, remote_user, remote_addr, path);
    }
}

static void
log_delete (int flags, const char *path, GNode *tree, const char *remote_user,
            const char *remote_addr, int rc)
{
    char *key = NULL;

    if ((flags & FLAGS_METHOD_DELETE) && (logging & LOG_DELETE))
    {
        log_params params;
        key = "DELETE";

        params.remote_user = remote_user;
        params.remote_addr = remote_addr;
        params.key = key;
        params.rc = rc;

        if (tree)
            g_node_traverse (tree, G_IN_ORDER, G_TRAVERSE_LEAVES, -1, log_deleted_leafs,
                             (gpointer) &params);
        else
            NOTICE ("%s[%3d] %s@%s %s\n",
                    key, rc, remote_user, remote_addr, path);
    }
}

static char *
rest_api_xml (void)
{
    char *resp = NULL;
    char *xmlbuf = sch_dump_xml (g_schema);
    if (xmlbuf)
    {
        resp = g_strdup_printf ("Status: 200\r\n"
                                "Content-Type: text/xml\r\n" "\r\n" "%s", (char *) xmlbuf);
        free (xmlbuf);
    }
    return resp;
}

extern char api_html[];
static void
rest_api_html (req_handle handle)
{
    char *resp = g_strdup_printf ("Status: 200\r\n"
                                  "Content-Type: text/html\r\n" "\r\n");
    send_response (handle, resp, false);
    free (resp);
    send_response (handle, api_html, true);
    return;
}

sch_node *
rest_rpc_schema (sch_node *schema)
{
    sch_node *_schema;

    /* Executable nodes are RPC's */
    if (sch_is_executable (schema))
        return schema;
    /* Special case to support a container that also has an RPC with the same name */
    if (sch_is_list (schema))
        _schema = sch_node_child (sch_node_child_first (schema), "_");
    else
        _schema = sch_node_child (schema, "_");
    if (_schema && sch_is_executable (_schema))
        return _schema;
    /* Not an RPC */
    return NULL;
}

static char *
rest_rpc (int flags, GNode *node, sch_node *schema, json_t *json)
{
    char *path = apteryx_node_path (node);
    int schflags = 0;
    GNode *input = NULL;
    GNode *output = NULL;
    rest_e_tag error_tag = REST_E_TAG_NONE;
    char *error_string = NULL;
    char *data = NULL;
    char *resp;
    rest_rpc_error error;
    int rc;

    /* Special case: We consider /operations to be a root node and hence
       support non-native namespaces at this node. This allows us to have
       multiple data models with the same root rpc. */
    if (g_ascii_strncasecmp (path, "/operations", strlen("/operations")) == 0)
    {
        sch_ns *ns = sch_node_ns (schema);
        if (ns && !sch_ns_native (g_schema, ns))
        {
            const char *prefix = sch_ns_prefix (g_schema, ns);
            const char *name = APTERYX_NAME (node);
            char *_path = g_strdup_printf ("/operations/%s:%s", prefix, name);
            free (path);
            path = _path;
        }
    }

    /* Set formating flags for input/output */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (flags & FLAGS_JSON_FORMAT_NS)
        schflags |= (SCH_F_NS_MODEL_NAME|SCH_F_NS_PREFIX);
    if (flags & FLAGS_CONDITIONS)
        schflags |= SCH_F_CONDITIONS;

    if (json)
    {
        /* RESTCONF mandates "input" (or nothing) be the primary data object
        for rpc requests. In non-restconf mode we are more relaxed but to match
        the data model we need to provide that top level "input" node */
        if (!(flags & FLAGS_RESTCONF) && json_object_size (json))
        {
            const char *key = NULL;
            if (json_object_size (json) == 1)
            {
                key = json_object_iter_key (json_object_iter(json));
                char *colon = key ? strchr (key, ':') : NULL;
                if (colon) key = colon + 1;
                if (g_strcmp0 (key, "input") != 0)
                    key = NULL;
            }
            if (key == NULL)
            {
                json_t *obj = json_object ();
                json_object_set_new (obj, "input", json);
                json = obj;
            }
        }

        /* Parse the input - always set types */
        input = sch_json_to_gnode (g_schema, schema, json, schflags | SCH_F_JSON_TYPES);
        json_decref (json);

        /* Check parsing succeeded and we have input when required */
        if (!input)
        {
            switch (sch_last_err ())
            {
            case SCH_E_NOSCHEMANODE:
                rc = HTTP_CODE_NOT_FOUND;
                error_tag = REST_E_TAG_INVALID_VALUE;
                break;
            case SCH_E_NOTREADABLE:
            case SCH_E_NOTWRITABLE:
                rc = HTTP_CODE_FORBIDDEN;
                error_tag = REST_E_TAG_ACCESS_DENIED;
                break;
            default:
                rc = HTTP_CODE_BAD_REQUEST;
                error_tag = REST_E_TAG_INVALID_VALUE;
                break;
            }
            goto exit;
        }
    }

    error = rest_rpc_execute (flags, path, input, &output, &error_string);
    switch (error)
    {
        case REST_RPC_E_NONE:
            if (output)
                rc = HTTP_CODE_OK;
            else
                rc = HTTP_CODE_NO_CONTENT;
            break;
        case REST_RPC_E_FAIL:
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_OPER_FAILED;
            break;
        case REST_RPC_E_NOT_FOUND:
            rc = HTTP_CODE_NOT_SUPPORTED;
            error_tag = REST_E_TAG_OPER_NOT_SUPPORTED;
            break;
        case REST_RPC_E_INTERNAL:
            rc = HTTP_CODE_INTERNAL_SERVER_ERROR;
            error_tag = REST_E_TAG_OPER_FAILED;
            break;
        default:
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_INVALID_VALUE;
            break;
    }

    if (output)
    {
        /* Get schema output node */
        schema = sch_node_child (schema, "output");
        if (schema)
        {
            /* Convert the data to json from the expected path offset */
            json_t *json = sch_gnode_to_json (g_schema, schema, output, schflags);
            if (json && !(flags & FLAGS_RESTCONF))
            {
                /* Chop off the output node */
                json_t *json_new = json_object_iter_value (json_object_iter (json));
                json_incref (json_new);
                json_decref (json);
                json = json_new;
                /* If there is only one value in the output and we have been asked to
                strip root elements then remove the key and return the value only */
                if (!(flags & FLAGS_JSON_FORMAT_ROOT) && json_object_size (json) == 1)
                {
                    /* Chop off the root node */
                    json_t *json_new = json_object_iter_value (json_object_iter (json));
                    json_incref (json_new);
                    json_decref (json);
                    json = json_new;
                }
            }
            if (!json || (data = json_dumps (json, JSON_ENCODE_ANY)) == NULL)
            {
                ERROR ("REST: Failed to convert rpc output to json\n");
                rc = HTTP_CODE_INTERNAL_SERVER_ERROR;
            }
            apteryx_free_tree (output);
            if (json)
                json_decref (json);
        }
        else
        {
            ERROR ("REST: no output node in schema\n");
            rc = HTTP_CODE_INTERNAL_SERVER_ERROR;
        }
    }

exit:
    if (!data && rc >= 400 && rc <= 500)
    {
        if (flags & FLAGS_RESTCONF)
        {
            json_t *json = json_object();
            json_t *errors = json_object();
            json_t *array = json_array ();
            json_t *error = json_object();
            json_object_set_new (error, "error-type", json_string ("application"));
            if (error_tag != REST_E_TAG_NONE)
                json_object_set_new (error, "error-tag", json_string (error_tags[error_tag]));
            if (error_string)
                json_object_set_new (error, "error-message", json_string (error_string));
            json_array_append_new (array, error);
            json_object_set_new (errors, "error", array);
            json_object_set_new (json, "ietf-restconf:errors", errors);
            data = json_dumps (json, 0);
            json_decref (json);
        }
        else if (error_string)
        {
            json_t *json = json_object();
            json_object_set_new (json, "message", json_string (error_string));
            data = json_dumps (json, 0);
            json_decref (json);
        }
    }

    resp = g_strdup_printf ("Status: %d\r\n"
                            "Content-Type: %s\r\n"
                            "\r\n" "%s", rc,
                            flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                            data ? : "");
    free (data);
    free (error_string);
    apteryx_free_tree (input);
    free (path);
    return resp;
}

static int
apteryx_json_search (const char *path, char **data)
{
    sch_node *root, *node;
    char *_path;
    int len;
    GList *children, *iter;
    bool first = true;
    char *buffer;

    /* Create a version of the path without the trailing '/' */
    _path = strdup (path);
    len = strlen (path);
    _path[len - 1] = '\0';

    /* Validate starting path */
    if ((root = sch_lookup (g_schema, _path)) == NULL)
    {
        free (_path);
        return HTTP_CODE_NOT_FOUND;
    }
    if (!sch_is_readable (root))
    {
        free (_path);
        return HTTP_CODE_FORBIDDEN;
    }

    /* Do the Apteryx search */
    *data = g_strdup_printf ("{\"%s\": [", len > 2 ? strrchr (_path, '/') + 1 : "");
    children = apteryx_search (path);
    children = g_list_sort (children, (GCompareFunc) strcasecmp);
    for (iter = children; iter; iter = g_list_next (iter))
    {
        path = strrchr ((const char *) iter->data, '/') + 1;
        if ((node = sch_node_child (root, path)) != NULL && sch_is_readable (node))
        {
            buffer = *data;
            *data = g_strdup_printf ("%s%s\"%s\"", buffer, first ? "" : ",", path);
            free (buffer);
            first = false;
        }
    }
    buffer = *data;
    *data = g_strdup_printf ("%s]}", buffer);
    free (buffer);

    g_list_free_full (children, free);
    free (_path);
    return HTTP_CODE_OK;
}

static char *
rest_api_search (int flags, const char *path, const char *if_none_match, const char *if_modified_since,
                 const char *remote_user, const char *remote_addr)
{
    char *_path;
    char *data = NULL;
    uint64_t ts = 0;
    char *resp;
    int rc;

    _path = strdup (path);
    _path[strlen (path) - 1] = '\0';
    ts = apteryx_timestamp (_path);
    g_free (_path);
    if (if_none_match && if_none_match[0] != '\0' &&
        ts == strtoull (if_none_match, NULL, 16))
    {
        rc = HTTP_CODE_NOT_MODIFIED;
        goto exit;
    }

    rc = apteryx_json_search (path, &data);

  exit:
    if (logging)
        log_get_head (FLAGS_METHOD_GET, path, remote_user, remote_addr, rc);

    resp = g_strdup_printf ("Status: %d\r\n"
                            "Etag: %" PRIX64 "\r\n"
                            "Content-Type: application/json\r\n"
                            "\r\n" "%s", rc, ts, data ? : "");
    free (data);
    return resp;
}

static GNode*
get_response_node (GNode *tree, int rdepth)
{
    GNode *rnode = tree;
    while (--rdepth && rnode)
        rnode = rnode->children;
    return rnode;
}

static char *
rest_api_get (int flags, const char *path, const char *if_none_match, const char *if_modified_since,
              const char *remote_user, const char *remote_addr)
{
    const char *qmark;
    char *rpath = NULL;
    sch_node *qschema = NULL;
    char *apath = NULL;
    json_t *json = NULL;
    uint64_t ts = 0;
    int rc = HTTP_CODE_OK;
    rest_e_tag error_tag = REST_E_TAG_NONE;
    GNode *query, *tree;
    char *json_string = NULL;
    char *resp = NULL;
    int schflags = 0;
    int qdepth, rdepth;
    int param_depth = 0;
    int diff;

    /* If a request is made to /restconf/data (in which case the path is now empty) it is analogous to a
       request to /restconf/data/ietf-yang-library:yang-library */
    if (!strlen (path) && (flags & FLAGS_RESTCONF))
        path = "/ietf-yang-library:yang-library";

    /* Separate the path from any query string */
    qmark = strchr (path, '?');
    if (qmark)
    {
        path = (const char *) (rpath = strndup (path, rpath - path));
        qmark += 1;
    }

    /* Parsing options */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (flags & FLAGS_CONDITIONS)
        schflags |= SCH_F_CONDITIONS;
    if (flags & FLAGS_IDREF_VALUES)
        schflags |= SCH_F_IDREF_VALUES;
    if (flags & FLAGS_JSON_FORMAT_NS)
    {
        schflags |= SCH_F_NS_MODEL_NAME;
        /* If the prefix/model name is not specified in the request
           then dont include it in the reply */
        char *colon = strchr (path, ':');
        char *slash = strchr (path, '/');
        if (slash)
            slash = strchr (slash + 1, '/');
        if (colon && (!slash || colon < slash))
            schflags |= SCH_F_NS_PREFIX;
    }

    /* Convert the path to a GNode tree to use as the base of the apteryx query */
    query = sch_path_to_gnode (g_schema, NULL, path, schflags, &qschema);
    if (!query || !qschema)
    {
        VERBOSE ("REST: Path \"%s\" invalid\n", path);
        switch (sch_last_err ())
        {
        case SCH_E_NOTREADABLE:
        case SCH_E_NOTWRITABLE:
            rc = HTTP_CODE_FORBIDDEN;
            error_tag = REST_E_TAG_ACCESS_DENIED;
            break;
        case SCH_E_NOSCHEMANODE:
        default:
            rc = HTTP_CODE_NOT_FOUND;
            error_tag = REST_E_TAG_INVALID_VALUE;
        }
        goto exit;
    }
    if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
    {
        VERBOSE ("REST: Path \"%s\" not readable\n", path);
        rc = HTTP_CODE_FORBIDDEN;
        error_tag = REST_E_TAG_ACCESS_DENIED;
        goto exit;
    }

    /* Get the depth of the response which is the depth of the query
       OR the up until the first path wildcard */
    qdepth = g_node_max_height (query);
    rdepth = 1;
    GNode *rnode = query;
    while (rnode &&
           g_node_n_children (rnode) == 1 &&
           g_strcmp0 (APTERYX_NAME (g_node_first_child (rnode)), "*") != 0)
    {
        rnode = g_node_first_child (rnode);
        rdepth++;
    }
    sch_node *rschema = qschema;
    diff = qdepth - rdepth;
    while (diff--)
        rschema = sch_node_parent (rschema);
    if (sch_node_parent (rschema) && sch_is_list (sch_node_parent (rschema)))
    {
        /* We need to present the list rather than the key */
        rschema = sch_node_parent (rschema);
        rdepth--;
    }
    GNode *qnode = rnode;
    while (qnode->children)
        qnode = qnode->children;

    /* Handle GET RPC's */
    sch_node *rpcschema = rest_rpc_schema (qschema);
    if (rpcschema)
    {
        /* Check RPC supports GET */
        if (flags & FLAGS_RESTCONF || !sch_is_readable (rpcschema))
        {
            VERBOSE ("REST: GET RPC not supported for %s\n", path);
            error_tag = REST_E_TAG_OPER_NOT_SUPPORTED;
            rc = HTTP_CODE_NOT_SUPPORTED;
        }
        else
        {
            resp = rest_rpc (flags, qnode, rpcschema, NULL);
        }
        goto exit;
    }

    /* Get a timestamp for the root of the query path */
    apath = apteryx_node_path (rnode);
    ts = apteryx_timestamp (apath);
    free (apath);
    if (if_none_match && if_none_match[0] != '\0' &&
        ts == strtoull (if_none_match, NULL, 16))
    {
        VERBOSE ("REST: Path \"%s\" not modified since ETag:%s\n", rpath, if_none_match);
        resp = g_strdup_printf ("Status: %d\r\n"
                                "Content-Type: application/json\r\n\r\n",
                                HTTP_CODE_NOT_MODIFIED);
        goto exit;
    }
    if (if_modified_since && if_modified_since[0] != '\0')
    {
        struct tm last_modified;
        time_t realtime;
        strptime (if_modified_since, "%a, %d %b %Y %H:%M:%S GMT", &last_modified);
        realtime = timegm (&last_modified);
        if ((ts / 1000000) <= (realtime - g_boottime))
        {
            VERBOSE ("REST: Path \"%s\" not modified since Time:%s\n", rpath, if_modified_since);
            rc = HTTP_CODE_NOT_MODIFIED;
            resp = g_strdup_printf ("Status: %d\r\n"
                                    "Content-Type: application/json\r\n\r\n",
                                    HTTP_CODE_NOT_MODIFIED);
            goto exit;
        }
    }

    /* Parse the query if provided */
    if (qmark)
    {
        /* Parse the query and attach to the tree */
        if (!sch_query_to_gnode (g_schema, qschema, qnode, qmark, schflags, &schflags, &param_depth))
        {
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_INVALID_VALUE;
            goto exit;
        }
    }
    /* Without a query we may need to add a wildcard to get everything from here down */
    if (!query || (qdepth == g_node_max_height (query) && !(schflags & SCH_F_DEPTH_ONE)))
    {
        if (qschema && sch_node_child_first (qschema) && !(schflags & SCH_F_STRIP_DATA))
        {
            /* Get everything from here down if we do not already have a star */
            if (!g_node_first_child (qnode) && g_strcmp0 (APTERYX_NAME (qnode), "*") != 0)
            {
                APTERYX_NODE (qnode, g_strdup ("*"));
                DEBUG ("%*s%s\n", qdepth * 2, " ", "*");
            }
        }
    }

    /* Query the database */
    tree = apteryx_query (query);
    if (schflags & SCH_F_ADD_DEFAULTS)
    {
        if (tree)
        {
            rnode = get_response_node (tree, rdepth);
            sch_traverse_tree (g_schema, rschema, rnode, schflags | SCH_F_ADD_DEFAULTS, 0);
        }
        else if (qdepth == rdepth && (sch_node_child_first (rschema) || sch_is_leaf (rschema)))
        {
            /* Nothing in the database, but we may have defaults! */
            tree = query;
            query = NULL;
            if (g_node_max_height (tree) > qdepth)
            {
                GNode *child = g_node_first_child (qnode);
                qnode->children = NULL;
                if (child)
                    apteryx_free_tree (child);
            }
            sch_traverse_tree (g_schema, rschema, qnode, schflags | SCH_F_ADD_DEFAULTS, 0);
        }
    }
    if (tree)
    {
        /* Get rid of any unwanted nodes */
        if (schflags & SCH_F_TRIM_DEFAULTS)
        {
            rnode = get_response_node (tree, rdepth);
            sch_traverse_tree (g_schema, rschema, rnode, schflags | SCH_F_TRIM_DEFAULTS, 0);
        }

        if ((schflags & SCH_F_DEPTH) && param_depth)
        {
            rnode = get_response_node (tree, rdepth);
            sch_trim_tree_by_depth (g_schema, rschema, rnode, schflags, param_depth);
        }

        /* Convert the result to JSON */
        rnode = get_response_node (tree, rdepth);
        if (rnode)
        {
            VERBOSE ("JSON:\n");
            json = sch_gnode_to_json (g_schema, rschema, rnode, schflags);
        }
        if (json)
        {
            if ((!(flags & FLAGS_JSON_FORMAT_ROOT) ||
                 (!(flags & FLAGS_RESTCONF) && qschema != rschema && sch_is_list (rschema)))
                && !json_is_string (json))
            {
                /* Chop off the root node */
                json_t *json_new = json_object_iter_value (json_object_iter (json));
                json_incref (json_new);
                json_decref (json);
                json = json_new;
            }
            if (flags & FLAGS_JSON_FORMAT_MULTI)
            {
                /* Top level array */
                json_t *json_new = json_array ();
                json_array_append_new (json_new, json);
                json = json_new;
            }
        }
        else
        {
            json = json_object();
        }
        apteryx_free_tree (tree);
    }
    else
    {
        if ((schflags & SCH_F_DEPTH) && qschema && qnode)
            json = sch_gnode_to_json (g_schema, qschema, qnode, schflags);
        else
            json = json_object();
    }

    json_string = json_dumps (json, JSON_ENCODE_ANY);
exit:
    if (logging)
        log_get_head (flags, path, remote_user, remote_addr, rc);

    if (!resp)
    {
        if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499 && !json_string)
        {
            json_string = restconf_error (rc, error_tag);
        }
        char last_modified[128];
        time_t realtime = (time_t) (g_boottime + (ts / 1000000));
        struct tm *my_tm = gmtime (&realtime);
        strftime (last_modified, 128, "%a, %d %b %Y %H:%M:%S GMT", my_tm);
        resp = g_strdup_printf ("Status: %d\r\n"
                                "Last-Modified: %s\r\n"
                                "ETag: %" PRIX64 "\r\n"
                                "Content-Type: %s\r\n"
                                "\r\n" "%s", rc, last_modified, ts,
                                flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                                json_string ? : "");
    }
    free (json_string);
    if (json)
        json_decref (json);
    apteryx_free_tree (query);
    free (rpath);
    return resp;
}

static bool
restconf_is_list_key_leaf_update (sch_node *api_subtree, GNode *child, GNode *tnode)
{
    sch_node *parent1 = sch_node_parent (api_subtree);
    sch_node *parent2 = sch_node_parent (parent1);   /* Might need to go up another level */
    sch_node *list_parent = NULL;
    bool key_update = false;
    bool case1 = true;

    if (parent1 && sch_is_list (parent1))
    {
        list_parent = parent1;
    }
    else if (parent2 && sch_is_list (parent2))
    {
        list_parent = parent2;
        case1 = false;
    }
    if (list_parent)
    {
        char *key = sch_list_key (list_parent);
        char *list_name = sch_name (list_parent);
        if (g_strcmp0 (list_name, APTERYX_NAME (tnode)) == 0)
        {
            tnode = tnode->children;
        }
        for (GNode *node = g_node_first_sibling (tnode); node; node = g_node_next_sibling (node))
        {
            if (g_strcmp0 (key, APTERYX_NAME (node)) == 0 && node->children)
            {
                char *value = APTERYX_NAME (node->children);
                char *path = apteryx_node_path (child);
                char *query = case1 ? g_strdup_printf ("%s/%s", path, key) : g_strdup (path);
                char *res = apteryx_get (query);
                if (res && g_strcmp0 (res, value))
                    key_update = true;

                g_free (res);
                g_free (path);
                g_free (query);
                break;
            }
        }
        g_free (list_name);
        g_free (key);
    }
    return key_update;
}

static char *
rest_api_post (int flags, const char *path, const char *data, int length, const char *if_match,
               const char *if_unmodified_since, const char *if_none_match, const char *server_name,
               const char *server_port, const char *remote_user, const char *remote_addr)
{
    GNode *root = NULL;
    GNode *tree = NULL;
    char *apath = NULL;
    sch_node *api_subtree = NULL;
    GNode *child = NULL;
    GNode *node;
    GNode *children = NULL;
    json_t *json = NULL;
    json_error_t error;
    char *resp = NULL;
    char *error_string = NULL;
    char *location = NULL;
    int schflags = 0;
    uint64_t ts = 0;
    bool res;
    int rc;
    rest_e_tag error_tag = REST_E_TAG_NONE;

    /* Parsing options - always set arrays and types */
    schflags = SCH_F_JSON_ARRAYS | SCH_F_JSON_TYPES | SCH_F_MODIFY_DATA;
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_NS)
        schflags |= SCH_F_NS_MODEL_NAME;
    schflags |= SCH_F_STRIP_DATA;

    /* Generate an aperyx tree from the path */
    root = sch_path_to_gnode (g_schema, NULL, path, schflags, &api_subtree);
    if (!root || !api_subtree)
    {
        VERBOSE ("REST: Path \"%s\" not found\n", path);
        rc = HTTP_CODE_NOT_FOUND;
        error_tag = REST_E_TAG_INVALID_VALUE;
        goto exit;
    }

    /* Check if this is an RPC */
    sch_node *rpcschema = rest_rpc_schema (api_subtree);
    if (rpcschema)
        api_subtree = rpcschema;

    /* Make sure any leaf nodes are writable */
    if ((sch_is_leaf (api_subtree) && !sch_is_writable (api_subtree)))
    {
        VERBOSE ("REST: Path \"%s\" not writable\n", path);
        rc = HTTP_CODE_FORBIDDEN;
        error_tag = REST_E_TAG_ACCESS_DENIED;
        goto exit;
    }

    /* Find the end of the path node */
    child = root;
    while (child && g_node_first_child (child))
        child = g_node_first_child (child);

    if (!rpcschema)
    {
        /* Get a timestamp for the apteryx path */
        apath = apteryx_node_path (child);
        ts = apteryx_timestamp (apath);
        free (apath);
        if (if_match && if_match[0] != '\0' &&
            ts != strtoull (if_match, NULL, 16))
        {
            VERBOSE ("REST: Path \"%s\" modified since ETag:%s\n", path, if_match);
            rc = HTTP_CODE_PRECONDITION_FAILED;
            error_tag = REST_E_TAG_OPER_FAILED;
            goto exit;
        }
        if (if_none_match && if_none_match[0] != '\0' &&
            ts == strtoull (if_none_match, NULL, 16))
        {
            VERBOSE ("REST: Path \"%s\" unmodified since ETag:%s\n", path, if_none_match);
            rc = HTTP_CODE_PRECONDITION_FAILED;
            error_tag = REST_E_TAG_OPER_FAILED;
            goto exit;
        }
        if (if_unmodified_since && if_unmodified_since[0] != '\0')
        {
            struct tm last_modified;
            time_t realtime;
            strptime (if_unmodified_since, "%a, %d %b %Y %H:%M:%S GMT", &last_modified);
            realtime = timegm (&last_modified);
            if ((ts / 1000000) > (realtime - g_boottime))
            {
                VERBOSE ("REST: Path \"%s\" modified since Time:%s\n", path, if_unmodified_since);
                rc =  HTTP_CODE_PRECONDITION_FAILED;
                error_tag = REST_E_TAG_OPER_FAILED;
                goto exit;
            }
        }
    }

    /* Run check For PUT requiring data to be a key/value object. */
    if (flags & FLAGS_PUT_KEY_VALUE_DATA && flags & FLAGS_METHOD_PUT)
    {
        char *data_resource_name;
        sch_node *parent = sch_node_parent (api_subtree);
        json_t *put_value = json_loadb (data, strlen (data), JSON_DECODE_ANY, &error);

        /* Find the data resource node name - go up one if we are at a list key node */
        if (sch_is_list (parent))
        {
            data_resource_name = sch_name (parent);
            api_subtree = parent;
        }
        else
        {
            data_resource_name = sch_name (api_subtree);
        }
        if (json_object_size (put_value) != 1 || json_object_get (put_value, data_resource_name) == NULL)
        {
            VERBOSE ("RESTCONF: Data \"%s\" is not a single key:value (child=%s, schema=%s)\n", data, data_resource_name,
                     sch_name (api_subtree));
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_INVALID_VALUE;
            g_free (data_resource_name);
            goto exit;
        }
        json = put_value;
        g_free (data_resource_name);
    }
    /* Parse the JSON data (support full path to leaf value) */
    else if (length && sch_is_leaf (api_subtree))
    {
        char *name;
        sch_node *pschema = sch_node_parent (api_subtree);
        json_t *value = json_loadb (data, strlen (data), JSON_DECODE_ANY, &error);
        if (!value && data && data[0] != '{' && data[0] != '[')
        {
            value = json_stringn (data, strlen (data));
        }
        if (sch_is_leaf_list (pschema))
        {
            if (json_is_integer (value))
                name = g_strdup_printf ("%" JSON_INTEGER_FORMAT, json_integer_value (value));
            else if (json_is_boolean (value))
                name = g_strdup_printf ("%s", json_is_true (value) ? "true" : "false");
            else
                name = g_strdup_printf ("%s", json_string_value (value));
        }
        else
            name = sch_name (api_subtree);
        json = json_object ();
        json_object_set_new (json, name, value);
        free (name);
        /* Jump back node */
        api_subtree = pschema;
        node = child;
        child = child->parent;
        g_node_unlink (node);
        free (node->data);
        g_node_destroy (node);
    }
    else if (length)
    {
        json = json_loads (data, 0, &error);
        if (!json && rpcschema && !(flags & FLAGS_RESTCONF))
        {
            /* In non RESTCONF mode we support single input parameters without keys in RPC's */
            sch_node *ischema = sch_node_child (api_subtree, "input");
            sch_node *ichild = ischema ? sch_node_child_first (ischema) : NULL;
            if (ischema && ichild && !sch_node_next_sibling (ichild))
            {
                json_t *value = json_loads (data, JSON_DECODE_ANY, &error);
                if (!value && data && data[0] != '{' && data[0] != '[')
                    value = json_stringn (data, strlen (data));
                if (value)
                {
                    char *name = sch_name (ichild);
                    json = json_object ();
                    json_object_set_new (json, name, value);
                    free (name);
                }
            }
        }
        if (!json)
        {
            ERROR ("error: on line %d: %s\n", error.line, error.text);
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_MALFORMED;
            goto exit;
        }
    }

    /* Handle rpc's */
    if (rpcschema)
    {
        resp = rest_rpc (flags, child, rpcschema, json);
        goto exit;
    }

    /* Convert to GNode and validate the data */
    if (json)
    {
        if (flags & FLAGS_PUT_KEY_VALUE_DATA && flags & FLAGS_METHOD_PUT)
        {
            tree = sch_json_to_gnode (g_schema, sch_node_parent (api_subtree), json, schflags);
        }
        else
        {
            tree = sch_json_to_gnode (g_schema, api_subtree, json, schflags);
        }
        json_decref (json);
    }

    if (tree && (flags & FLAGS_RESTCONF))
    {
        bool not_supported = false;
        if (flags & (FLAGS_METHOD_PUT | FLAGS_METHOD_PATCH))
        {
            /* For a restconf PUT or PATCH do not allow the change of an existing list key field */
            if (restconf_is_list_key_leaf_update (api_subtree, child, tree->children))
            {
                not_supported = true;
            }
        }

        if (flags & (FLAGS_METHOD_PUT | FLAGS_METHOD_PATCH | FLAGS_METHOD_POST) &&
            sch_is_leaf_list (api_subtree))
        {
            /* A leaf list entry should be fully defined in the data portion of the set */
            not_supported = true;
        }

        if (not_supported)
        {
            apteryx_free_tree (tree);
            tree = NULL;
            rc = HTTP_CODE_NOT_SUPPORTED;
            error_tag = REST_E_TAG_OPER_NOT_SUPPORTED;
            goto exit;
        }
    }

    /* Check parsing succeeded and we have input when required */
    if (!tree)
    {
        switch (sch_last_err ())
        {
        case SCH_E_NOSCHEMANODE:
            rc = HTTP_CODE_NOT_FOUND;
            error_tag = REST_E_TAG_INVALID_VALUE;
            break;
        case SCH_E_NOTREADABLE:
        case SCH_E_NOTWRITABLE:
            rc = HTTP_CODE_FORBIDDEN;
            error_tag = REST_E_TAG_ACCESS_DENIED;
            break;
        default:
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_INVALID_VALUE;
            break;
        }
        goto exit;
    }

    /* Check for replace  - don't traverse tree if PUT is just setting a leaf */
    if (flags & FLAGS_PUT_REPLACE && flags & FLAGS_METHOD_PUT)
    {
        GNode *node;

        /* Adjust the tree by ditching the first node under the root node. */
        node = tree;
        tree = tree->children;
        g_node_unlink (tree);
        g_free (node->data);
        g_node_destroy (node);
        g_free (tree->data);
        tree->data = g_strdup ("/");
        if (!sch_is_leaf (api_subtree))
        {
            sch_traverse_tree (g_schema, api_subtree, tree, schflags | SCH_F_ADD_MISSING_NULL, 0);
        }
    }

    /* Write the combined tree to apteryx */
    child->children = tree->children;
    children = tree->children;
    tree->children = NULL;

    /* Fixup the parent pointers for the children that now in the root tree */
    for (GNode *cnode = child->children; cnode; cnode = cnode->next)
        cnode->parent = child;

    if ((flags & FLAGS_CONDITIONS) &&
        (flags & (FLAGS_METHOD_PUT | FLAGS_METHOD_PATCH | FLAGS_METHOD_POST)))
    {
        if (!sch_apply_conditions (g_schema, NULL, root, schflags))
        {
            rc = HTTP_CODE_NOT_FOUND;
            error_tag = REST_E_TAG_INVALID_VALUE;
            goto exit;
        }
    }

    if (flags & FLAGS_RESTCONF && flags & FLAGS_METHOD_POST)
    {
        res = apteryx_cas_tree (root, 0);
        if (res)
            location = g_strdup_printf ("https://%s:%s%s/%s", server_name, server_port,
                                        path, APTERYX_NAME (children));
    }
    else
        res = apteryx_set_tree (root);
    if (res)
    {
        rc = flags & FLAGS_METHOD_POST ? HTTP_CODE_CREATED : HTTP_CODE_NO_CONTENT;
    }
    else if (errno == -EBUSY)
    {
        rc = HTTP_CODE_CONFLICT;
        error_tag = REST_E_TAG_DATA_EXISTS;
    }
    else
    {
        rc = HTTP_CODE_FORBIDDEN;
        error_tag = REST_E_TAG_ACCESS_DENIED;
    }

exit:
    if (logging)
        log_post_put_patch (flags, path, root, remote_user, remote_addr, rc);

    if (!resp)
    {
        if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499)
        {
            error_string = restconf_error (rc, error_tag);
        }
        if (location)
        {
            resp = g_strdup_printf ("Status: %d\r\n"
                                    "Content-Type: %s\r\n"
                                    "Location: %s\r\n"
                                    "\r\n" "%s", rc,
                                    flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                                    location, error_string ? : "");
            g_free (location);
        }
        else
            resp = g_strdup_printf ("Status: %d\r\n"
                                    "Content-Type: %s\r\n"
                                    "\r\n" "%s", rc,
                                    flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                                    error_string ? : "");
    }
    free (error_string);
    apteryx_free_tree (tree);
    apteryx_free_tree (root);
    return resp;
}

/* Implemented by doing a query and setting all data to NULL */
static char *
rest_api_delete (int flags, const char *path, const char *remote_user, const char *remote_addr)
{
    sch_node *api_subtree = NULL;
    char *error_string = NULL;
    char *resp = NULL;
    char *name = NULL;
    int rc = HTTP_CODE_NO_CONTENT;
    rest_e_tag error_tag = REST_E_TAG_NONE;
    int schflags = SCH_F_MODIFY_DATA; /* We are going to modify the tree */

    /* Parsing options */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (flags & FLAGS_JSON_FORMAT_NS)
        schflags |= SCH_F_NS_MODEL_NAME;
    else
        schflags |= SCH_F_CONFIG; /* We only want to delete config-nodes */

    /* Generate an aperyx query from the path */
    GNode *query = sch_path_to_gnode (g_schema, NULL, path, schflags, &api_subtree);
    if (!query || !api_subtree)
    {
        VERBOSE ("REST: Path \"%s\" not found\n", path);
        rc = HTTP_CODE_NOT_FOUND;
        error_tag = REST_E_TAG_INVALID_VALUE;
        goto exit;
    }
    if (sch_is_leaf (api_subtree) && !sch_is_writable (api_subtree))
    {
        VERBOSE ("REST: Path \"%s\" not writable\n", path);
        apteryx_free_tree (query);
        rc = HTTP_CODE_FORBIDDEN;
        error_tag = REST_E_TAG_ACCESS_DENIED;
        goto exit;
    }

    int query_depth = g_node_max_height (query);

    /* Handle DELETE RPC's */
    sch_node *rpcschema = rest_rpc_schema (api_subtree);
    if (rpcschema)
    {
        /* Do not support DELETE when using pure restconf */
        if (flags & FLAGS_RESTCONF)
        {
            error_tag = REST_E_TAG_OPER_NOT_SUPPORTED;
            rc = HTTP_CODE_NOT_SUPPORTED;
        }
        else
        {
            resp = rest_rpc (flags, get_response_node (query, query_depth), rpcschema, NULL);
        }
        apteryx_free_tree (query);
        goto exit;
    }

    /* We may want to get everything from here down */
    if (sch_node_child_first (api_subtree))
    {
        GNode *child = query;
        while (child->children)
            child = child->children;
        /* Get everything from here down if we do not already have a star */
        if (g_strcmp0 (APTERYX_NAME (child), "*") != 0)
        {
            DEBUG ("%*s%s\n", g_node_max_height (query) * 2, " ", "*");
            APTERYX_NODE (child, g_strdup ("*"));
        }
    }

    /* Query the database */
    GNode *tree = apteryx_query (query);
    apteryx_free_tree (query);
    if (tree)
    {
        /* Set all leaves to NULL if we are allowed */
        GNode *rnode = get_response_node (tree, query_depth);

        /* Special treatment is required for the deletion of a leaf list item */
        if (api_subtree && sch_is_leaf (api_subtree) && (name = sch_name (api_subtree)) &&
            sch_is_leaf_list (sch_node_parent (api_subtree)) &&
            g_strcmp0 (name, "*") == 0)
        {
            if (rnode && rnode->children->data)
            {
                free (rnode->children->data);
                rnode->children->data = g_strdup ("");
                if (apteryx_set_tree (tree))
                {
                    rc = HTTP_CODE_NO_CONTENT;
                }
                else
                {
                    rc = HTTP_CODE_BAD_REQUEST;
                    error_tag = REST_E_TAG_INVALID_VALUE;
                }
            }
        }
        else if (!sch_traverse_tree (g_schema, api_subtree, rnode, schflags | SCH_F_SET_NULL, 0))
        {
            rc = HTTP_CODE_FORBIDDEN;
            error_tag = REST_E_TAG_ACCESS_DENIED;
        }
        else if (g_node_max_height (tree) <= query_depth)
        {
            rc = HTTP_CODE_NOT_FOUND;
            error_tag = REST_E_TAG_INVALID_VALUE;
        }
        else if (apteryx_set_tree (tree))
        {
            rc = HTTP_CODE_NO_CONTENT;
        }
        else
        {
            rc = HTTP_CODE_BAD_REQUEST;
            error_tag = REST_E_TAG_INVALID_VALUE;
        }
        g_free (name);

        if (logging)
            log_delete (flags, path, tree, remote_user, remote_addr, rc);

        apteryx_free_tree (tree);
    }
    else if (logging)
        log_delete (flags, path, NULL, remote_user, remote_addr, rc);

exit:
    if (!resp)
    {
        if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499)
        {
            error_string = restconf_error (rc, error_tag);
        }
        resp = g_strdup_printf ("Status: %d\r\n"
                                "Content-Type: %s\r\n"
                                "\r\n" "%s", rc,
                                flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                                error_string ? : "");
        free (error_string);
    }
    return resp;
}

static char *
rest_api_options (int flags, const char *path)
{
    sch_node *schema;
    sch_ns *ns;
    char *resp = NULL;
    char *error_string = NULL;
    char *options = NULL;
    char *key;
    char *colon;
    char *_path = g_strdup (path);
    char *ptr = strchr (_path, '=');
    int len = 0;
    int rc = HTTP_CODE_NOT_FOUND;

    /* Substitute key equals value with a slash to make the sch_lookup work */
    while (ptr)
    {
        *ptr = '/';
        ptr = strchr (ptr, '=');
    }

    ptr = _path;
    if (ptr[0] == '/')
    {
        ptr++;
    }

    key = strchr (ptr, '/');
    if (key)
    {
        len = key - ptr;
        key = g_strndup (ptr, len);
    }
    else
    {
        key = g_strdup (ptr);
    }

    colon = strchr (key, ':');
    if (colon)
    {
        *colon = '\0';
        colon++;
        ptr += colon - key;
    }

    ns = sch_lookup_ns (g_schema, NULL, key, SCH_F_NS_MODEL_NAME, false);
    schema = sch_lookup_with_ns (g_schema, ns, ptr);
    g_free (_path);
    g_free (key);

    if (schema)
    {
        options = g_strdup_printf ("%s%s%s", sch_is_readable (schema) ? "GET,HEAD,OPTIONS" : "",
                                    sch_is_writable (schema) ? "," : "",
                                    sch_is_writable (schema) ? "POST,PUT,PATCH,DELETE" : "");
        rc = HTTP_CODE_OK;
    }

    if (rc == HTTP_CODE_OK)
    {
        resp = g_strdup_printf ("Status: %u\r\n"
                        "Allow: %s\r\n"
                        "Accept-Patch: %s\r\n"
                        "Content-Type: text/html\r\n\r\n", rc, options,
                        flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json");
        g_free (options);
    }
    else
    {
        if (flags & FLAGS_RESTCONF)
        {
            error_string = restconf_error (rc, REST_E_TAG_INVALID_VALUE);
        }
        resp = g_strdup_printf ("Status: %d\r\n"
                                "Content-Type: %s\r\n"
                                "\r\n" "%s", rc,
                                flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                                error_string ? : "");
        free (error_string);
    }
    return resp;
}

typedef struct WatchRequest
{
    req_handle handle;
    int flags;
    sch_node *api;
    char *path;
    char *wpath;
} WatchRequest;
static GList *g_watch_requests = NULL;
static pthread_mutex_t g_watch_lock = PTHREAD_MUTEX_INITIALIZER;

static bool
watch_callback (GNode * root, void *arg)
{
    WatchRequest *req = (WatchRequest *) arg;
    GNode *node;
    json_t *json;
    char *data;
    int schflags = 0;

    /* Protect the watch request list */
    pthread_mutex_lock (&g_watch_lock);

    /* Make sure the request is still valid */
    if (!g_list_find (g_watch_requests, req))
    {
        ERROR ("REST: Watch callback no longer valid\n");
        goto exit;
    }

    VERBOSE ("REST(%p): Watch callback for \"%s\"\n", req->handle, req->path);

    /* Find the node representing the requested data */
    node = apteryx_path_node (root, req->path);
    if (!node)
    {
        ERROR ("REST(%p): Watch callback could not find requested node in data\n", req->handle);
        goto exit;
    }

    /* Convert the data to json from the expected path offset */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (req->flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (req->flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (req->flags & FLAGS_JSON_FORMAT_NS)
        schflags |= (SCH_F_NS_MODEL_NAME|SCH_F_NS_PREFIX);
    if (req->flags & FLAGS_CONDITIONS)
        schflags |= SCH_F_CONDITIONS;

    json = sch_gnode_to_json (g_schema, req->api, node, schflags);
    if (!json || (data = json_dumps (json, JSON_ENCODE_ANY)) == NULL)
    {
        ERROR ("REST(%p): Failed to convert watch callback data to json\n", req->handle);
        if (json)
            json_decref (json);
        goto exit;
    }

    /* Send the event */
    if (req->flags & FLAGS_EVENT_STREAM)
        send_response (req->handle, "data: ", true);
    send_response (req->handle, data, true);
    if (req->flags & FLAGS_EVENT_STREAM)
        send_response (req->handle, "\r\n\r\n", true);
    else
        send_response (req->handle, "\r\n", true);
    json_decref (json);
    free (data);

exit:
    pthread_mutex_unlock (&g_watch_lock);
    apteryx_free_tree (root);
    return true;
}

static void
rest_api_watch (req_handle handle, int flags, const char *path)
{
    sch_node *api_subtree = sch_lookup (g_schema, path);
    if (!api_subtree)
    {
        char *resp = g_strdup_printf ("Status: 404\r\n"
                                      "Content-Type: text/html\r\n\r\n"
                                      "The requested URL %s was not found on this server.\n",
                                      path);
        send_response (handle, resp, false);
        g_free (resp);
        return;
    }

    WatchRequest *req = g_malloc0 (sizeof (WatchRequest));
    req->handle = handle;
    req->flags = flags | FLAGS_JSON_FORMAT_ARRAYS | FLAGS_JSON_FORMAT_TYPES;
    req->api = api_subtree;
    req->path = g_strdup (path);
    if (sch_is_leaf (api_subtree))
        req->wpath = g_strdup (path);
    else
        req->wpath = g_strdup_printf ("%s/*", path);
    DEBUG ("REST(%p): Adding watch for \"%s\"\n", req->handle, path);
    pthread_mutex_lock (&g_watch_lock);
    g_watch_requests = g_list_append (g_watch_requests, req);
    pthread_mutex_unlock (&g_watch_lock);
    add_callback (APTERYX_WATCHERS_PATH, req->wpath, (void *) watch_callback, true,
                  (void *) req, 1, 0);

    send_response (handle, "Status: 200\r\n", false);
    send_response (handle, "Connection: 'keep-alive'\r\n", false);
    if (flags & FLAGS_APPLICATION_STREAM)
        send_response (handle, "Content-type: application/stream+json\r\n", false);
    else
        send_response (handle, "Content-type: text/event-stream\r\n", false);
    send_response (handle, "Cache-Control: 'no-cache'\r\n", false);
    send_response (handle, "\r\n\r\n", true);

    while (is_connected (req->handle, true))
    {
        usleep (1000000);
    }
    DEBUG ("REST(%p): Removing watch for \"%s\"\n", req->handle, path);
    pthread_mutex_lock (&g_watch_lock);
    g_watch_requests = g_list_remove (g_watch_requests, req);
    pthread_mutex_unlock (&g_watch_lock);
    delete_callback (APTERYX_WATCHERS_PATH, req->wpath, (void *) watch_callback, (void *) req);
    g_free (req->path);
    g_free (req->wpath);
    g_free (req);
}

static void
rest_decode_uri (char *path)
{
    char *in = path;
    char *out = path;

    while (*in)
    {
        if(*in == '%' && strlen (in) > 2 && isxdigit (in[1]) && isxdigit (in[2]))
        {
            char char_1;
            char char_2;

            char_1 = toupper (in[1]);
            if(char_1 >= 'A')
                char_1 -= ('A' - 10);
            else
                char_1 -= '0';

            char_2 = toupper (in[2]);
            if(char_2 >= 'A')
                char_2 -= ('A' - 10);
            else
                char_2 -= '0';

            *out++ = (char_1 * 16) + char_2;
            in +=3;
        }
        else
            *out++ = *in++;
    }
    *out++ = '\0';
}

void
rest_api (req_handle handle, int flags, const char *rpath, const char *path,
          const char *if_match, const char *if_none_match,
          const char *if_modified_since, const char *if_unmodified_since,
          const char *server_name, const char *server_port,
          const char *remote_addr, const char *remote_user,
          const char *data, int length)
{
    char *resp = NULL;
    char *new_path = NULL;

    VERBOSE ("REQ:\n[0x%x] %s\n", flags, path);

    /* Check for encoded special characters of the form "%" HEXDIG HEXDIG (RFC 3986 section 2.1) */
    new_path = g_strdup (path);
    rest_decode_uri (new_path);
    path = new_path;

    if (data && data[0])
    {
        VERBOSE ("%s\n", data);
    }

    /* Process method */
    path = path + strlen (rpath);
    if (flags & FLAGS_RESTCONF)
    {
        json_t *json = NULL;
        int rc = HTTP_CODE_OK;
        if (g_ascii_strncasecmp (path, "/data", strlen("/data")) == 0)
            path += strlen ("/data");
        else if (flags & FLAGS_METHOD_GET && g_strcmp0 (path, "/operations") == 0)
        {
            json = json_object();
            json_t *obj = json_object ();
            sch_node *schema = sch_lookup (g_schema, path);
            sch_node *child = schema ? sch_node_child_first (schema) : NULL;
            while (child)
            {
                char *name = sch_name (child);
                char *model = sch_model (child, false);
                char *fname = g_strdup_printf ("%s:%s", model, name);
                char *rpcpath = g_strdup_printf ("%s/operations/%s", rpath, fname);
                json_object_set_new (obj, fname, json_string (rpcpath));
                free (rpcpath);
                free (fname);
                free (model);
                free (name);
                child = sch_node_next_sibling (child);
            }
            json_object_set_new (json, "ietf-restconf:operations", obj);
        }
        else if (flags & FLAGS_METHOD_GET && g_strcmp0 (path, "/yang-library-version") == 0)
        {
            json = json_object();
            json_object_set_new (json, "yang-library-version", json_string ("2019-01-04"));
        }
        else if (flags & FLAGS_METHOD_GET && path[0] == '\0')
        {
            json = json_object();
            json_t *obj = json_object();
            json_object_set_new (obj, "data", json_object ());
            json_object_set_new (obj, "operations", json_object ());
            json_object_set_new (obj, "yang-library-version", json_string ("2019-01-04"));
            char *root_resource = g_strdup_printf ("ietf-restconf:%s", rpath + 1);
            json_object_set_new (json, root_resource, obj);
            free (root_resource);
        }
        if (json)
        {
            char *json_str = json_dumps (json, 0);
            resp = g_strdup_printf ("Status: %d\r\n"
                    "Content-Type: application/yang-data+json\r\n"
                    "\r\n" "%s",
                    rc, json_str ? : "");
            free (json_str);
            json_decref (json);
            VERBOSE ("RESP:\n%s\n", resp);
            send_response (handle, resp, false);
            g_free (resp);
            g_free (new_path);
            return;
        }
    }
    if (flags & FLAGS_METHOD_GET || flags & FLAGS_METHOD_HEAD)
    {
        if (strcmp (path, ".xml") == 0)
            resp = rest_api_xml ();
        else if (strcmp (path, ".html") == 0)
        {
            rest_api_html (handle);
            g_free (new_path);
            return;
        }
        else if (flags & (FLAGS_EVENT_STREAM | FLAGS_APPLICATION_STREAM))
        {
            rest_api_watch (handle, flags, path);
            g_free (new_path);
            return;
        }
        else if (strlen (path) && path[strlen (path) - 1] == '/')
            resp = rest_api_search (flags, path, if_none_match, if_modified_since,
                                    remote_user, remote_addr);
        else
            resp = rest_api_get (flags, path, if_none_match, if_modified_since,
                                 remote_user, remote_addr);
        if ((flags & FLAGS_METHOD_HEAD) && resp)
        {
            g_free (resp);
            resp = g_strdup_printf ("Status: %d\r\n"
                        "Content-Type: %s\r\n\r\n", HTTP_CODE_OK,
                        flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json");
        }
    }
    else if (flags & (FLAGS_METHOD_POST|FLAGS_METHOD_PUT|FLAGS_METHOD_PATCH))
        resp = rest_api_post (flags, path, data, length, if_match, if_unmodified_since,
                              if_none_match, server_name, server_port, remote_user, remote_addr);
    else if (flags & FLAGS_METHOD_DELETE)
        resp = rest_api_delete (flags, path, remote_user, remote_addr);
    else if (flags & FLAGS_METHOD_OPTIONS)
        resp = rest_api_options (flags, path);

    if (!resp)
    {
        resp = g_strdup_printf ("Status: 501\r\n"
                                "Content-Type: text/html\r\n\r\n"
                                "Operation not implemented for \"%s\".\n",
                                path);
    }

    VERBOSE ("RESP:\n%s\n", resp);
    send_response (handle, resp, false);
    g_free (resp);
    g_free (new_path);
    return;
}

gboolean
rest_init (const char *path)
{
    struct sysinfo info;
    struct timespec monotime;
    struct timespec monotime_raw;

    /* Calculate boot time in seconds since the Epoch */
    sysinfo (&info);
    g_boottime = time (NULL) - info.uptime;
    /* Allow for adjusted time */
    clock_gettime(CLOCK_MONOTONIC, &monotime);
    clock_gettime(CLOCK_MONOTONIC_RAW, &monotime_raw);
    g_boottime += (monotime.tv_sec - monotime_raw.tv_sec);

    /* Load Data Models */
    g_schema = sch_load (path);
    if (!g_schema)
    {
        return false;
    }

    yang_library_create (g_schema);
    restconf_monitoring_create (g_schema);

    /* Register with the YANG condition parser */
    sch_condition_register (debug, verbose);


    return true;
}

void
rest_shutdown (void)
{
    /* Cleanup datamodels */
    if (g_schema)
        sch_free (g_schema);
}
