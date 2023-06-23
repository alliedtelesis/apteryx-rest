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
#define HTTP_CODE_NO_CONTENT            204
#define HTTP_CODE_NOT_MODIFIED          304
#define HTTP_CODE_BAD_REQUEST           400
#define HTTP_CODE_FORBIDDEN             403
#define HTTP_CODE_NOT_FOUND             404
#define HTTP_CODE_NOT_SUPPORTED         405
#define HTTP_CODE_CONFLICT              409
#define HTTP_CODE_PRECONDITION_FAILED   412
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
    else if (status == HTTP_CODE_PRECONDITION_FAILED)
    {
        json_object_set_new (error, "error-type", json_string ("application"));
        json_object_set_new (error, "error-tag", json_string ("operation-failed"));
        json_object_set_new (error, "error-message", json_string ("object modified"));
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

static GNode*
get_response_node (GNode *tree, int rdepth)
{
    GNode *rnode = tree;
    while (--rdepth && rnode)
        rnode = rnode->children;
    return rnode;
}

static char *
rest_api_get (int flags, const char *path, const char *if_none_match, const char *if_modified_since)
{
    const char *qmark;
    char *rpath = NULL;
    sch_node *qschema = NULL;
    char *apath = NULL;
    json_t *json = NULL;
    uint64_t ts = 0;
    int rc = HTTP_CODE_OK;
    GNode *query, *tree;
    char *json_string = NULL;
    char *resp = NULL;
    int schflags = 0;
    int qdepth, rdepth;
    int diff;

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
    if (flags & FLAGS_RESTCONF)
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
            break;
        case SCH_E_NOSCHEMANODE:
        default:
            rc = HTTP_CODE_NOT_FOUND;
        }
        goto exit;
    }
    if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
    {
        VERBOSE ("REST: Path \"%s\" not readable\n", path);
        rc = HTTP_CODE_FORBIDDEN;
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
        if (!sch_query_to_gnode (g_schema, qschema, qnode, qmark, schflags, &schflags))
        {
            rc = HTTP_CODE_BAD_REQUEST;
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
            sch_traverse_tree (g_schema, rschema, rnode, schflags | SCH_F_ADD_DEFAULTS);
        }
        else if (qdepth == rdepth && (sch_node_child_first (rschema) || sch_is_leaf (rschema)))
        {
            /* Nothing in the database, but we may have defaults! */
            tree = query;
            query = NULL;
            if ((g_node_max_height (tree) - 1) > qdepth)
            {
                GNode *child = g_node_first_child (qnode);
                qnode->children = NULL;
                if (child)
                    apteryx_free_tree (child);
            }
            sch_traverse_tree (g_schema, rschema, qnode, schflags | SCH_F_ADD_DEFAULTS);
        }
    }
    if (tree)
    {
        /* Get rid of any unwanted nodes */
        if (schflags & SCH_F_TRIM_DEFAULTS)
        {
            rnode = get_response_node (tree, rdepth);
            sch_traverse_tree (g_schema, rschema, rnode, schflags | SCH_F_TRIM_DEFAULTS);
        }

        /* Convert the result to JSON */
        rnode = get_response_node (tree, rdepth);
        if (rnode)
            json = sch_gnode_to_json (g_schema, rschema, rnode, schflags);
        if (json)
        {
            if (!(flags & FLAGS_JSON_FORMAT_ROOT) && !json_is_string (json))
            {
                /* Chop off the root node */
                json_t *json_new = json_object_iter_value (json_object_iter (json));
                json_incref (json_new);
                json_decref (json);
                json = json_new;
            }
            if (!(flags & FLAGS_RESTCONF) && qschema != rschema && sch_is_list (rschema))
            {
                /* Provide the list array object */
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

static char *
rest_api_post (int flags, const char *path, const char *data, int length, const char *if_match, const char *if_unmodified_since)
{
    GNode *root = NULL;
    GNode *tree = NULL;
    char *apath = NULL;
    sch_node *api_subtree = NULL;
    GNode *child;
    GNode *node;
    json_t *json;
    json_error_t error;
    char *resp = NULL;
    char *error_string = NULL;
    int schflags = 0;
    uint64_t ts = 0;
    bool res;
    int rc;

    /* Parsing options - always set arrays and types */
    schflags = SCH_F_JSON_ARRAYS | SCH_F_JSON_TYPES;
    if (verbose)
        schflags |= SCH_F_DEBUG;
    if (flags & FLAGS_RESTCONF)
        schflags |= SCH_F_NS_MODEL_NAME;
    schflags |= SCH_F_STRIP_DATA;

    /* Generate an aperyx tree from the path */
    root = sch_path_to_gnode (g_schema, NULL, path, schflags, &api_subtree);
    if (!root || !api_subtree)
    {
        VERBOSE ("REST: Path \"%s\" not found\n", path);
        rc = HTTP_CODE_NOT_FOUND;
        goto exit;
    }
    if (sch_is_leaf (api_subtree) && !sch_is_writable (api_subtree))
    {
        VERBOSE ("REST: Path \"%s\" not writable\n", path);
        rc = HTTP_CODE_FORBIDDEN;
        goto exit;
    }

    /* Find the end of the path node */
    child = root;
    while (child && g_node_first_child (child))
        child = g_node_first_child (child);

    /* Get a timestamp for the apteryx path */
    apath = apteryx_node_path (child);
    ts = apteryx_timestamp (apath);
    free (apath);
    if (if_match && if_match[0] != '\0' &&
        ts != strtoull (if_match, NULL, 16))
    {
        VERBOSE ("REST: Path \"%s\" modified since ETag:%s\n", path, if_match);
        rc = HTTP_CODE_PRECONDITION_FAILED;
        goto exit;
    }
    if (if_unmodified_since && if_unmodified_since[0] != '\0')
    {
        struct tm last_modified;
        time_t realtime;
        strptime (if_unmodified_since, "%a, %d %b %Y %H:%M:%S GMT", &last_modified);
        realtime = timegm (&last_modified);
        if ((ts / 1000000) != (realtime - g_boottime))
        {
            VERBOSE ("REST: Path \"%s\" modified since Time:%s\n", path, if_unmodified_since);
            rc =  HTTP_CODE_PRECONDITION_FAILED;
            goto exit;
        }
    }

    /* Parse the JSON data (support full path to leaf value) */
    if (sch_is_leaf (api_subtree))
    {
        char *name = sch_name (api_subtree);
        json_t *value = json_loadb (data, strlen (data), JSON_DECODE_ANY, &error);
        if (!value && data && data[0] != '{' && data[0] != '[')
        {
            value = json_stringn (data, strlen (data));
        }
        json = json_object ();
        json_object_set_new (json, name, value);
        free (name);
        /* Jump back node */
        api_subtree = sch_node_parent (api_subtree);
        node = child;
        child = child->parent;
        g_node_unlink (node);
        free (node->data);
        g_node_destroy (node);
    }
    else
    {
        json = json_loads (data, 0, &error);
        if (!json)
        {
            ERROR ("error: on line %d: %s\n", error.line, error.text);
            rc = HTTP_CODE_BAD_REQUEST;
            goto exit;
        }
    }

    /* Convert to GNode and validate the data */
    tree = sch_json_to_gnode (g_schema, api_subtree, json, schflags);
    json_decref (json);
    if (!tree)
    {
        switch (sch_last_err ())
        {
        case SCH_E_NOSCHEMANODE:
            rc = HTTP_CODE_NOT_FOUND;
            break;
        case SCH_E_NOTREADABLE:
        case SCH_E_NOTWRITABLE:
            rc = HTTP_CODE_FORBIDDEN;
            break;
        default:
            rc = HTTP_CODE_BAD_REQUEST;
            break;
        }
        goto exit;
    }

    /* Check for replace */
    if (flags & FLAGS_RESTCONF && flags & FLAGS_METHOD_PUT)
        sch_traverse_tree (g_schema, api_subtree, tree, schflags | SCH_F_ADD_MISSING_NULL);

    /* Write the combinded tree to apteryx */
    child->children = tree->children;
    if (flags & FLAGS_RESTCONF && flags & FLAGS_METHOD_POST)
        res = apteryx_cas_tree (root, 0);
    else
        res = apteryx_set_tree (root);
    if (res)
    {
        rc = flags & FLAGS_METHOD_POST ? HTTP_CODE_CREATED : HTTP_CODE_NO_CONTENT;
    }
    else if (errno == -EBUSY)
    {
        rc = HTTP_CODE_CONFLICT;
    }
    else
    {
        rc = HTTP_CODE_FORBIDDEN;
    }
    child->children = NULL;

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
    apteryx_free_tree (tree);
    apteryx_free_tree (root);
    return resp;
}

/* Implemented by doing a query and setting all data to NULL */
static char *
rest_api_delete (int flags, const char *path)
{
    sch_node *api_subtree = NULL;
    char *error_string = NULL;
    char *resp = NULL;
    int rc = HTTP_CODE_NO_CONTENT;
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
    else
        schflags |= SCH_F_CONFIG; /* We only want to delete config-nodes */

    /* Generate an aperyx query from the path */
    GNode *query = sch_path_to_gnode (g_schema, NULL, path, schflags, &api_subtree);
    if (!query || !api_subtree)
    {
        VERBOSE ("REST: Path \"%s\" not found\n", path);
        rc = HTTP_CODE_NOT_FOUND;
        goto exit;
    }
    if (sch_is_leaf (api_subtree) && !sch_is_writable (api_subtree))
    {
        VERBOSE ("REST: Path \"%s\" not writable\n", path);
        apteryx_free_tree (query);
        rc = HTTP_CODE_FORBIDDEN;
        goto exit;
    }

    int query_depth = g_node_max_height (query);
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
        if (!sch_traverse_tree (g_schema, api_subtree, rnode, schflags | SCH_F_SET_NULL))
            rc = HTTP_CODE_FORBIDDEN;
        else if (g_node_max_height (tree) <= query_depth)
             rc = HTTP_CODE_NOT_FOUND;
        else
            rc = apteryx_set_tree (tree) ? HTTP_CODE_NO_CONTENT : 400;

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
rest_api (req_handle handle, int flags, const char *rpath, const char *path,
          const char *if_match, const char *if_none_match,
          const char *if_modified_since, const char *if_unmodified_since,
          const char *data, int length)
{
    char *resp = NULL;

    VERBOSE ("REQ:\n[0x%x] %s\n", flags, path);
    if (data && data[0])
    {
        VERBOSE ("%s\n", data);
    }

    /* Process method */
    path = path + strlen (rpath);
    if (flags & FLAGS_RESTCONF)
    {
        if (strstr (path, "/data") == path)
            path += strlen ("/data");
        else if (flags & FLAGS_METHOD_GET)
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
                json_object_set_new (obj, "yang-library-version", json_string ("2019-01-04"));
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
    if (flags & FLAGS_METHOD_GET || flags & FLAGS_METHOD_HEAD)
    {
        if (strcmp (path, ".xml") == 0)
            resp = rest_api_xml ();
        else if (strcmp (path, ".html") == 0)
        {
            rest_api_html (handle);
            return;
        }
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
    else if (flags & (FLAGS_METHOD_POST|FLAGS_METHOD_PUT|FLAGS_METHOD_PATCH))
        resp = rest_api_post (flags, path, data, length, if_match, if_unmodified_since);
    else if (flags & FLAGS_METHOD_DELETE)
        resp = rest_api_delete (flags, path);
    else if (flags & FLAGS_METHOD_OPTIONS)
    {
        resp = g_strdup_printf ("Status: 200\r\n"
                        "Allow: GET,POST,PUT,PATCH,DELETE,HEAD,OPTIONS\r\n"
                        "Accept-Patch: %s\r\n"
                        "Content-Type: text/html\r\n\r\n",
                        flags & FLAGS_RESTCONF ? "application/yang-data+json" : "application/json");
    }
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

    return true;
}

void
rest_shutdown (void)
{
    /* Cleanup datamodels */
    if (g_schema)
        sch_free (g_schema);
}
