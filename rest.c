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
                          void *data, uint32_t flags);
extern bool delete_callback (const char *type, const char *path, void *fn, void *data);
#include <jansson.h>

#define HTTP_CODE_OK                    200
#define HTTP_CODE_CREATED               201
#define HTTP_CODE_NOT_MODIFIED          304
#define HTTP_CODE_BAD_REQUEST           400
#define HTTP_CODE_FORBIDDEN             403
#define HTTP_CODE_NOT_FOUND             404
#define HTTP_CODE_NOT_SUPPORTED         405
#define HTTP_CODE_CONFLICT              409
#define HTTP_CODE_INTERNAL_SERVER_ERROR 500

static sch_instance *g_schema = NULL;
static time_t g_boottime = 0;

static char *
restconf_error (int status)
{
    json_t *json = json_object();
    json_t *errors = json_object();
    json_t *array = json_array ();
    json_t *error = json_object();
    char *output;

    if (status == HTTP_CODE_FORBIDDEN)
    {
        json_object_set_new (error, "error-type", json_string ("protocol"));
        json_object_set_new (error, "error-tag", json_string ("access-denied"));
    }
    else if (status == HTTP_CODE_NOT_FOUND)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-tag", json_string ("invalid-value"));
        json_object_set_new (error, "error-message", json_string ("uri path not found"));
    }
    else if (status == HTTP_CODE_NOT_SUPPORTED)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-tag", json_string ("operation-not-supported"));
        json_object_set_new (error, "error-message", json_string ("requested operation is not supported"));
    }
    else if (status == HTTP_CODE_CONFLICT)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-tag", json_string ("data-exists"));
        json_object_set_new (error, "error-message", json_string ("object already exists"));
    }
    else
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-tag", json_string ("malformed-message"));
        json_object_set_new (error, "error-message", json_string ("malformed request syntax"));
    }
    json_array_append_new (array, error);
    json_object_set_new (errors, "error", array);
    json_object_set_new (json, "ietf-restconf:errors", errors);

    output = json_dumps (json, 0);
    json_decref (json);
    return output;
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
    if ((root = sch_lookup (g_schema, _path)) == NULL || !sch_is_readable (root))
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
rest_api_search (const char *path, const char *if_none_match, const char *if_modified_since)
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
    resp = g_strdup_printf ("Status: %d\r\n"
                            "Etag: %" PRIX64 "\r\n"
                            "Content-Type: application/json\r\n"
                            "\r\n" "%s", rc, ts, data ? : "");
    free (data);
    return resp;
}

static json_t *
get_response_node (const char *path, json_t *root)
{
    const char *s;
    int slashes;
    int equals;
    int depth;

    for (s=path, slashes=0; s[slashes]; s[slashes]=='/' ? slashes++ : *s++);
    for (s=path, equals=0; s[equals]; s[equals]=='=' ? equals++ : *s++);
    depth = slashes + (equals > 0 ? equals - 1 : 0) - 1;
    depth = slashes + equals - 1;
    /* Special case of list-identifier at end */
    if (strrchr (path, '=') > strrchr (path, '/'))
        depth--;
    while (root && depth > 0)
    {
        if (json_is_array (root))
            root = json_array_get(root, 0);
        else
        {
            void *iter = json_object_iter (root);
            /* May have asked for a wildcard list in the path */
            if (json_object_iter_next (root, iter))
                break;
            root = json_object_iter_value (iter);
        }
        depth--;
    }
    return root;
}

static char *
rest_api_get (int flags, const char *path, const char *if_none_match, const char *if_modified_since)
{
    char *rpath = NULL;
    json_t *json = NULL;
    uint64_t ts = 0;
    int rc = HTTP_CODE_OK;
    GNode *query, *tree;
    char *json_string = NULL;
    char *resp = NULL;
    int schflags = 0;

    /* Get the path without any query string */
    rpath = strchr (path, '?');
    if (rpath)
        rpath = strndup (path, rpath - path);
    else
        rpath = strdup (path);

    /* Parsing options */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (flags & FLAGS_RESTCONF)
        schflags |= SCH_F_NS_MODEL_NAME;

    /* Generate an aperyx query from the path */
    query = sch_path_to_query (g_schema, NULL, path, schflags);
    if (!query)
    {
        VERBOSE ("REST: Path \"%s\" invalid\n", path);
        switch (sch_last_err ())
        {
        case SCH_E_INVALIDQUERY:
            rc = HTTP_CODE_BAD_REQUEST;
            break;
        case SCH_E_NOTREADABLE:
        case SCH_E_NOTWRITABLE:
            rc = HTTP_CODE_FORBIDDEN;
            break;
        case SCH_E_NOSCHEMANODE:
        default:
            rc = HTTP_CODE_NOT_FOUND;
        }
        goto exit;
    }

    /* Get a timestamp for the path */
    ts = apteryx_timestamp (rpath);
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

    /* Query the database */
    tree = apteryx_query (query);
    if (tree)
    {
        /* Convert the result to JSON */
        json = sch_gnode_to_json (g_schema, NULL, tree, schflags);
        if (json)
        {
            json_t *json_new = get_response_node (rpath, json);
            if (!(flags & FLAGS_JSON_FORMAT_ROOT) && !json_is_string (json))
            {
                /* Chop off the root node */
                json_new = json_object_iter_value (json_object_iter (json_new));
            }
            json_incref (json_new);
            json_decref (json);
            json = json_new;
            if (flags & FLAGS_JSON_FORMAT_MULTI)
            {
                /* Top level array */
                json_new = json_array ();
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
        json = json_object();
    }
    if (!(flags & FLAGS_JSON_FORMAT_ROOT) &&
        (json_is_string (json) || json_is_integer (json) || json_is_boolean (json)))
    {
        if (flags & FLAGS_JSON_FORMAT_TYPES && json_is_integer (json))
            json_string = g_strdup_printf ("%" JSON_INTEGER_FORMAT, json_integer_value (json));
        else if (flags & FLAGS_JSON_FORMAT_TYPES && json_is_boolean (json))
            json_string = g_strdup_printf ("%s", json_is_true (json) ? "true" : "false");
        else
            json_string = g_strdup_printf ("\"%s\"", json_string_value (json));
    }
    else
        json_string = json_dumps (json, 0);
exit:
    if (!resp)
    {
        if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499 && !json_string)
        {
            json_string = restconf_error (rc);
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

static int
apteryx_json_set (const char *path, json_t * json)
{
    sch_node *api_subtree;
    GNode *tree = NULL;
    bool set_successful;
    int schflags;

    api_subtree = sch_lookup (g_schema, path);
    if (!api_subtree)
    {
        return HTTP_CODE_FORBIDDEN;
    }

    schflags = SCH_F_JSON_ARRAYS | SCH_F_JSON_TYPES;
    if (verbose)
        schflags |= SCH_F_DEBUG;
    tree = sch_json_to_gnode (g_schema, api_subtree, json, schflags);
    if (!tree)
    {
        switch (sch_last_err ())
        {
        case SCH_E_NOSCHEMANODE:
            return HTTP_CODE_NOT_FOUND;
        case SCH_E_NOTREADABLE:
        case SCH_E_NOTWRITABLE:
            return HTTP_CODE_FORBIDDEN;
        default:
            return HTTP_CODE_BAD_REQUEST;
        }
    }
    free (tree->data);
    tree->data = g_strdup (path);

    set_successful = apteryx_set_tree (tree);
    apteryx_free_tree (tree);

    if (!set_successful)
    {
        // TODO error message
        return HTTP_CODE_BAD_REQUEST;
    }

    return HTTP_CODE_OK;
}

static char *
rest_api_post (int flags, const char *path, const char *data, int length)
{
    json_error_t error;
    json_t *json;
    char *error_string = NULL;
    char *resp = NULL;
    int rc;

    json = json_loads (data, 0, &error);
    if (json)
    {
        rc = apteryx_json_set (path, json);
        json_decref (json);
    }
    else if (!(flags & FLAGS_JSON_FORMAT_ROOT))
    {
        sch_node *node;
        char *escaped = NULL;

        /* Remove quotes around data if they exist */
        if (strlen (data) > 1 && data[0] == '"' && data[strlen (data) - 1] == '"')
        {
            escaped = g_strndup (data + 1, strlen (data) - 2);
        }
        else
        {
            escaped = g_strdup (data);
        }

        /* Manage value with no key */
        node = sch_lookup (g_schema, path);
        if (!node || !sch_is_leaf (node) || !sch_is_writable (node))
        {
            rc = HTTP_CODE_FORBIDDEN;
        }
        else if (!apteryx_set (path, escaped ? escaped : data))
        {
            rc = HTTP_CODE_BAD_REQUEST;
        }
        else
        {
            rc = HTTP_CODE_OK;
        }

        g_free (escaped);
    }
    else
    {
        ERROR ("error: on line %d: %s\n", error.line, error.text);
        rc = HTTP_CODE_BAD_REQUEST;
    }
    if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499)
    {
        error_string = restconf_error (rc);
    }
    resp = g_strdup_printf ("Status: %d\r\n"
                            "Content-Type: %s\r\n"
                            "\r\n" "%s", rc,
                            flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                            error_string ? : "");
    free (error_string);
    return resp;
}

static gboolean
set_data_null (GNode *node, gpointer data)
{
    int *rc = (int *) data;
    char *path = apteryx_node_path (node->parent);
    sch_node *schema = sch_lookup (g_schema, path);
    free (path);

    if (schema && sch_is_hidden (schema))
    {
        // TODO Pretend it is not here rather than letting it be set again
        return false;
    }
    else if (schema == NULL || !sch_is_writable (schema))
    {
        *rc = HTTP_CODE_FORBIDDEN;
        return true;
    }

    /* Otherwise we can set this to null */
    free (node->data);
    node->data = strdup ("");
    return false;
}

/* Implemented by doing a query and setting all data to NULL */
static char *
rest_api_delete (int flags, const char *path)
{
    char *error_string = NULL;
    char *resp = NULL;
    int rc = HTTP_CODE_OK;
    int schflags = 0;

    /* Parsing options */
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_JSON_FORMAT_ARRAYS)
        schflags |= SCH_F_JSON_ARRAYS;
    if (flags & FLAGS_JSON_FORMAT_TYPES)
        schflags |= SCH_F_JSON_TYPES;
    if (flags & FLAGS_RESTCONF)
        schflags |= SCH_F_NS_MODEL_NAME;

    /* Generate an aperyx query from the path */
    GNode *query = sch_path_to_query (g_schema, NULL, path, schflags);
    if (!query)
    {
        VERBOSE ("REST: Path \"%s\" not found\n", path);
        rc = HTTP_CODE_FORBIDDEN;
        goto exit;
    }

    /* Query the database */
    GNode *tree = apteryx_query (query);
    apteryx_free_tree (query);
    if (tree)
    {
        /* Set all leaves to NULL if we are allowed */
        g_node_traverse (tree, G_IN_ORDER, G_TRAVERSE_LEAVES, -1, set_data_null, &rc);
        if (rc == HTTP_CODE_OK)
            rc = apteryx_set_tree (tree) ? HTTP_CODE_OK : 400;
        apteryx_free_tree (tree);
    }

exit:
    if (flags & FLAGS_RESTCONF && rc >= 400 && rc <= 499)
    {
        error_string = restconf_error (rc);
    }
    resp = g_strdup_printf ("Status: %d\r\n"
                            "Content-Type: %s\r\n"
                            "\r\n" "%s", rc,
                            flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json",
                            error_string ? : "");
    free (error_string);
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
                  (void *) req, 1);

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

void
rest_api (req_handle handle, int flags, const char *rpath, const char *path, const char *action,
          const char *if_none_match, const char *if_modified_since, const char *data, int length)
{
    char *resp = NULL;

    /* Sanity check parameters */
    if (!rpath || !path || !action || !(flags & FLAGS_ACCEPT_JSON))
    {
        ERROR ("ERROR: invalid parameters (flags:0x%x, rpath:%s, path:%s, action:%s)\n",
               flags, rpath, path, action);
        resp = g_strdup_printf ("Status: 500\r\n"
                        "Content-Type: text/html\r\n\r\n"
                        "Invalid parameters (flags:0x%x, rpath:%s, path:%s, action:%s)\n",
                        flags, rpath, path, action);
        send_response (handle, resp, false);
        g_free (resp);
        return;
    }
    VERBOSE ("%s(0x%x) %s\n", action, flags, path);

    /* Process method */
    path = path + strlen (rpath);
    if (flags & FLAGS_RESTCONF)
    {
        if (strstr (path, "/data") == path)
            path += strlen ("/data");
        else if (strcmp (action, "GET") == 0)
        {
            json_t *json = json_object();
            json_t *obj = json;
            if (path[0] == 0)
            {
                obj = json_object();
                json_object_set_new (json, "ietf-restconf:restconf", obj);
                json_object_set_new (obj, "data", json_object ());
            }
            if (path[0] == 0 || g_strcmp0 (path, "/operations") == 0)
                json_object_set_new (obj, "operations", json_object ());
            if (path[0] == 0 || g_strcmp0 (path, "/yang-library-version") == 0)
                json_object_set_new (obj, "yang-library-version", json_string ("2016-06-21"));
            char *json_string = json_dumps (json, 0);
            resp = g_strdup_printf ("Status: 200\r\n"
                    "Content-Type: application/yang-data+json\r\n"
                    "\r\n" "%s",
                    json_string ? : "");
            free (json_string);
            json_decref (json);
            send_response (handle, resp, false);
            g_free (resp);
            return;
        }
    }
    if (strcmp (action, "GET") == 0 || strcmp (action, "HEAD") == 0)
    {
        if (strcmp (path, ".xml") == 0)
            resp = rest_api_xml ();
        else if (flags & (FLAGS_EVENT_STREAM | FLAGS_APPLICATION_STREAM))
        {
            rest_api_watch (handle, flags, path);
            return;
        }
        else if (path[strlen (path) - 1] == '/')
            resp = rest_api_search (path, if_none_match, if_modified_since);
        else
            resp = rest_api_get (flags, path, if_none_match, if_modified_since);
    }
    else if (strcmp (action, "POST") == 0 || strcmp (action, "PUT") == 0 || strcmp (action, "PATCH") == 0)
        resp = rest_api_post (flags, path, data, length);
    else if (strcmp (action, "DELETE") == 0)
        resp = rest_api_delete (flags, path);
    else if (strcmp (action, "OPTIONS") == 0)
    {
        resp = g_strdup_printf ("Status: 200\r\n"
                        "Allow: GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS\r\n"
                        "Accept-Patch: %s\r\n"
                        "Content-Type: text/html\r\n\r\n",
                        flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json");
    }
    if (!resp)
    {
        resp = g_strdup_printf ("Status: 404\r\n"
                                "Content-Type: text/html\r\n\r\n"
                                "The requested URL %s was not found on this server.\n",
                                path);
    }

    VERBOSE ("RESP:\n%s\n", resp);
    send_response (handle, resp, false);
    g_free (resp);
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

    return true;
}

void
rest_shutdown (void)
{
    /* Cleanup datamodels */
    if (g_schema)
        sch_free (g_schema);
}
