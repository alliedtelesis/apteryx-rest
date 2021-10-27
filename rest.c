/**
 * @file rest.c
 *
 * Copyright 2018, Allied Telesis Labs New Zealand, Ltd
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this library. If not, see <http://www.gnu.org/licenses/>
 */
#include "internal.h"
#include <jansson.h>

#define HTTP_CODE_OK                    200
#define HTTP_CODE_NOT_MODIFIED          304
#define HTTP_CODE_BAD_REQUEST           400
#define HTTP_CODE_FORBIDDEN             403
#define HTTP_CODE_NOT_FOUND             404
#define HTTP_CODE_INTERNAL_SERVER_ERROR 500

static char *
rest_api_xml (void)
{
    char *resp = NULL;
    char *xmlbuf = sch_dump ();
    if (xmlbuf)
    {
        resp = g_strdup_printf ("Status: 200\r\n"
                                "Content-Type: txt/xml\r\n" "\r\n" "%s", (char *) xmlbuf);
        free (xmlbuf);
    }
    return resp;
}

static int
apteryx_json_search (sch_node * root, const char *path, char **data)
{
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
    if ((root = sch_validate_path (root, _path, NULL, NULL)) == NULL)
    {
        free (_path);
        return HTTP_CODE_FORBIDDEN;
    }

    /* Do the Apteryx search */
    *data = g_strdup_printf ("{\"%s\": [", len > 2 ? strrchr (_path, '/') + 1 : "");
    children = apteryx_search (path);
    for (iter = children; iter; iter = g_list_next (iter))
    {
        path = strrchr ((const char *) iter->data, '/') + 1;
        if (sch_validate_path (root, path, NULL, NULL) != NULL)
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
rest_api_search (const char *path)
{
    char *data = NULL;
    char *resp;
    int rc;

    rc = apteryx_json_search (sch_root (), path, &data);
    resp = g_strdup_printf ("Status: %d\r\n" "\r\n" "%s", rc, data ? : "");
    free (data);
    return resp;
}

static json_t *
encode_json_type (char *val)
{
    json_t *json = NULL;
    json_int_t i;
    char *p;

    if (*val != '\0')
    {
        i = strtoll (val, &p, 10);
        if (*p == '\0')
            json = json_integer (i);
        if (g_strcmp0 (val, "true") == 0)
            json = json_true ();
        if (g_strcmp0 (val, "false") == 0)
            json = json_false ();
    }
    if (!json)
        json = json_string (val);
    return json;
}

static json_t *
_tree_to_json (sch_node * api_root, GNode * data_root, bool use_json_arrays, bool use_json_types)
{
    if (APTERYX_HAS_VALUE (data_root))
    {
        /* Assumption: mode fields will only be present on leaf nodes. */
        if (!sch_node_has_mode_flag (api_root, 'r'))
        {
            return NULL;
        }
        if (use_json_types)
            return encode_json_type (APTERYX_VALUE (data_root));
        return json_string (APTERYX_VALUE (data_root));
    }
    else
    {
        GNode *data_child;
        json_t *json_root;
        bool child_added = false;
        bool print_as_array = false;

        if (use_json_arrays)
        {
            print_as_array = sch_node_is_list (api_root, NULL);
        }

        /* Create a JSON node to match the current data node. If it turns out that there
         * are no readable children then this will be thrown away. */
        if (print_as_array)
            json_root = json_array ();
        else
            json_root = json_object ();
        for (data_child = g_node_first_child (data_root); data_child;
             data_child = g_node_next_sibling (data_child))
        {
            sch_node *api_child;
            json_t *json_child;

            api_child = sch_child_get (api_root, APTERYX_NAME (data_child));
            if (!api_child)
            {
                continue;
            }

            json_child = _tree_to_json (api_child, data_child, use_json_arrays, use_json_types);
            if (json_child)
            {
                if (print_as_array)
                    json_array_append (json_root, json_child);
                else
                    json_object_set (json_root, APTERYX_NAME (data_child), json_child);
                json_decref (json_child);
                child_added = true;
            }
        }

        return (child_added) ? json_root : NULL;
    }
}

static json_t *
tree_to_json (sch_node * api_root, GNode * data_root, bool use_json_arrays, bool use_json_types)
{
    json_t *json_root = json_object ();
    if (data_root)
    {
        json_t *json_child = _tree_to_json (api_root, data_root, use_json_arrays, use_json_types);
        if (json_child)
        {
            char *slash;
            char *name;

            /* The root of the data tree may hold multiple path components separated
             * by slashes. We only want the last component. */
            slash = strrchr (APTERYX_NAME (data_root), '/');
            name = (slash) ? slash + 1 : APTERYX_NAME (data_root);
            json_object_set (json_root, name, json_child);
            json_decref (json_child);
        }
    }
    return json_root;
}

static char *
rest_api_get (int flags, const char *path, const char *if_none_match)
{
    sch_node *api_subtree;
    GNode *data;
    json_t *json;
    char *json_string = NULL;
    int rc = HTTP_CODE_OK;
    char *resp;
    uint64_t ts = 0;
    bool json_arrays = (flags & FLAGS_JSON_FORMAT_ARRAYS);
    bool json_types = (flags & FLAGS_JSON_FORMAT_TYPES);

    api_subtree = sch_path_to_node (path);
    if (!api_subtree)
    {
        rc = HTTP_CODE_NOT_FOUND;
        goto exit;
    }

    if (sch_node_is_leaf (api_subtree) && !sch_node_has_mode_flag (api_subtree, 'r'))
    {
        rc = HTTP_CODE_FORBIDDEN;
        goto exit;
    }

    ts = apteryx_timestamp (path);
    if (if_none_match && ts == strtoull (if_none_match, NULL, 16))
    {
        rc = HTTP_CODE_NOT_MODIFIED;
        goto exit;
    }

    data = apteryx_get_tree (path);
    json = tree_to_json (api_subtree, data, json_arrays, json_types);
    apteryx_free_tree (data);

    /* Process requested JSON format options */
    if (!(flags & FLAGS_JSON_FORMAT_ROOT) && !json_is_string (json))
    {
        /* Chop off the root node */
        void *iter = json_object_iter (json);
        json_t *json_new = json_object_iter_value (iter);
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

    /* Dump to the output */
    if (!(flags & FLAGS_JSON_FORMAT_ROOT) &&
        (json_is_string (json) || json_is_integer (json) || json_is_boolean (json)))
    {
        if (json_types && json_is_integer (json))
        {
            json_string = g_strdup_printf ("%d", json_integer_value (json));
        }
        else if (json_types && json_is_boolean (json))
        {
            json_string = g_strdup_printf ("%s", json_is_true (json) ? "true" : "false");
        }
        else
        {
            json_string = g_strdup_printf ("\"%s\"", json_string_value (json));
        }
    }
    else
        json_string = json_dumps (json, 0);
    if (!json_string)
    {
        ERROR ("Failed to format JSON for path %s\n", path);
        json_decref (json);
        return NULL;
    }
    json_decref (json);

  exit:
    /* Add header */
    resp = g_strdup_printf ("Status: %d\r\n"
                            "Etag: %" PRIX64 "\r\n"
                            "Content-Type: application/yang.data+json\r\n"
                            "\r\n" "%s", rc, ts, json_string ? : "");
    free (json_string);

    /* Return response */
    return resp;
}

typedef enum
{
    J2T_RES_SUCCESS,
    J2T_RES_NO_API_NODE,
    J2T_RES_VALUE_ON_CORE_NODE,
    J2T_RES_OBJECT_ON_LEAF_NODE,
    J2T_RES_EMPTY_OBJECT,
    J2T_RES_PERMISSION_MISMATCH,
    J2T_RES_REGEX_MISMATCH,
    J2T_RES_REGEX_COMPILATION_FAIL,
    J2T_RES_UNSUPPORTED_JSON_TYPE,
    J2T_RES_SLASH_IN_PATH_COMPONENT,
    J2T_RES_ARRAY_NOT_LIST,
} json_to_tree_result_t;

static void
json_error (sch_node * node, char *msg)
{
    char *path = sch_node_to_path (node);
    ERROR ("JSON: %s \"%s\"\n", msg, path ? : "<unknown>");
    free (path);
    return;
}

static json_to_tree_result_t
json_to_tree (sch_node * api_root, json_t * json_root, GNode * data_root)
{
    const char *key;
    json_t *json;
    int rc;

    json_object_foreach (json_root, key, json)
    {
        sch_node *api_child;
        GNode *data_child;

        api_child = sch_child_get (api_root, key);
        if (!api_child)
        {
            json_error (api_root, "J2T_RES_NO_API_NODE");
            return J2T_RES_NO_API_NODE;
        }

        if (json_is_array (json))
        {
            char *key_name = NULL;
            size_t index;
            json_t *json_array;
            sch_node *api_array;
            GNode *data_array;

            if (!sch_node_is_list (api_child, &key_name) || key_name == NULL)
            {
                json_error (api_root, "J2T_RES_ARRAY_NOT_LIST");
                return J2T_RES_ARRAY_NOT_LIST;
            }

            data_child = g_node_new (g_strdup (key));
            json_array_foreach (json, index, json_array)
            {
                json_t *json_key = json_object_get (json_array, key_name);
                const char *key_array = json_string_value (json_key);

                api_array = sch_child_get (api_child, key_array);
                if (!api_array)
                {
                    json_error (api_child, "J2T_RES_NO_API_NODE");
                    free (data_child->data);
                    g_node_destroy (data_child);
                    free (key_name);
                    return J2T_RES_NO_API_NODE;
                }

                data_array = g_node_new (g_strdup (key_array));
                rc = json_to_tree (api_array, json_array, data_array);
                if (rc != J2T_RES_SUCCESS)
                {
                    /* We don't need to do anything with data_child; it must be NULL because this
                     * function only sets it to something significant on success. */
                    free (data_array->data);
                    g_node_destroy (data_array);
                    free (data_child->data);
                    g_node_destroy (data_child);
                    free (key_name);
                    return rc;
                }
                g_node_prepend (data_child, data_array);
            }
            free (key_name);
        }
        else if (json_is_object (json))
        {
            data_child = g_node_new (g_strdup (key));
            rc = json_to_tree (api_child, json, data_child);
            if (rc != J2T_RES_SUCCESS)
            {
                /* We don't need to do anything with data_child; it must be NULL because this
                 * function only sets it to something significant on success. */
                free (data_child->data);
                g_node_destroy (data_child);
                return rc;
            }
        }
        else if (json_is_string (json) || json_is_integer (json) || json_is_boolean (json))
        {
            char *value;

            if (!sch_node_is_leaf (api_child))
            {
                json_error (api_child, "J2T_RES_VALUE_ON_CORE_NODE");
                return J2T_RES_VALUE_ON_CORE_NODE;
            }

            if (!sch_node_has_mode_flag (api_child, 'w') &&
                !sch_node_has_mode_flag (api_child, 'x'))
            {
                json_error (api_child, "J2T_RES_PERMISSION_MISMATCH");
                return J2T_RES_PERMISSION_MISMATCH;
            }

            /* Format value always as a string */
            if (json_is_integer (json))
            {
                value = g_strdup_printf ("%d", json_integer_value (json));
            }
            else if (json_is_boolean (json))
            {
                value = g_strdup_printf ("%s", json_is_true (json) ? "true" : "false");
            }
            else
            {
                value = g_strdup (json_string_value (json));
            }
                        
            /* We only need to do a pattern check when setting a non-empty value; clearing a value
             * is always permitted. */
            if (value && value[0] != '\0')
            {
                if (!sch_validate_pattern (api_child, value))
                {
                    json_error (api_child, "J2T_RES_REGEX_MISMATCH");
                    free (value);
                    return J2T_RES_REGEX_MISMATCH;
                }
            }

            data_child = g_node_new (g_strdup (key));
            g_node_prepend_data (data_child, (char *) value);
        }
        else
        {
            json_error (api_child, "J2T_RES_UNSUPPORTED_JSON_TYPE");
            return J2T_RES_UNSUPPORTED_JSON_TYPE;
        }

        g_node_prepend (data_root, data_child);
    }

    return J2T_RES_SUCCESS;
}

static int
apteryx_json_set (const char *path, json_t * json)
{
    sch_node *api_subtree;
    GNode *data = NULL;
    int rc;
    bool set_successful;

    api_subtree = sch_path_to_node (path);
    if (!api_subtree)
    {
        return HTTP_CODE_FORBIDDEN;
    }

    data = g_node_new (g_strdup (path));
    rc = json_to_tree (api_subtree, json, data);
    switch (rc)
    {
    case J2T_RES_SUCCESS:
        break;
    case J2T_RES_NO_API_NODE:
        apteryx_free_tree (data);
        return HTTP_CODE_NOT_FOUND;
    case J2T_RES_VALUE_ON_CORE_NODE:
    case J2T_RES_PERMISSION_MISMATCH:
        apteryx_free_tree (data);
        return HTTP_CODE_FORBIDDEN;
    case J2T_RES_SLASH_IN_PATH_COMPONENT:
    case J2T_RES_REGEX_MISMATCH:
    case J2T_RES_UNSUPPORTED_JSON_TYPE:
    case J2T_RES_OBJECT_ON_LEAF_NODE:
    case J2T_RES_EMPTY_OBJECT:
    case J2T_RES_ARRAY_NOT_LIST:
        apteryx_free_tree (data);
        return HTTP_CODE_BAD_REQUEST;
    case J2T_RES_REGEX_COMPILATION_FAIL:
    default:
        apteryx_free_tree (data);
        return HTTP_CODE_INTERNAL_SERVER_ERROR;
    }
    set_successful = apteryx_set_tree (data);
    apteryx_free_tree (data);

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
        bool write;
        char *escaped = NULL;

        /* Remove quotes around data if they exist */
        if (strlen(data) > 1 && data[0] == '"' && data[strlen (data) - 1] == '"')
        {
            escaped = g_strndup (data + 1, strlen (data) - 2);
        }
        else
        {
            escaped = g_strdup (data);
        }

        /* Manage value with no key */
        node = sch_validate_path (sch_root (), path, NULL, &write);
        if (!node || !write || !sch_node_is_leaf (node))
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
    return g_strdup_printf ("Status: %d\r\n" "\r\n", rc);
}

static int
apteryx_json_delete (sch_node * root, const char *path)
{
    GList *children, *iter;
    char *_path;
    int rc = HTTP_CODE_OK;
    bool writable;

    /* Search the path */
    _path = g_strdup_printf ("%s/", path);
    children = apteryx_search (_path);
    free (_path);

    /* Check for leaf */
    if (!children)
    {
        /* Validate path */
        if (!sch_validate_path (root, path, NULL, &writable) || !writable)
        {
            /* Pretend success for invalid or hidden paths */
            rc = HTTP_CODE_OK;
        }
        /* Set to NULL */
        else if (!apteryx_set (path, NULL))
        {
            // TODO path error
            rc = 400;
        }
    }
    else
    {
        /* Delete all children */
        for (iter = children; iter; iter = g_list_next (iter))
        {
            rc = apteryx_json_delete (root, (char *) iter->data);
            if (rc != HTTP_CODE_OK)
                break;
        }
        g_list_free_full (children, free);
    }

    return rc;
}

static char *
rest_api_delete (const char *path)
{
    int rc = apteryx_json_delete (sch_root (), path);
    return g_strdup_printf ("Status: %d\r\n" "\r\n", rc);
}

typedef struct WatchRequest
{
    req_handle handle;
    int flags;
    sch_node *api;
    char *path;
    char *wpath;
} WatchRequest;

static bool
watch_callback (GNode *root, void *data)
{
    WatchRequest *req = (WatchRequest *) data;
    GNode *node = apteryx_path_node (root, req->path);
    if (!node)
        return false;
    json_t *json = tree_to_json (req->api, node, true, true);
    apteryx_free_tree (root);
    void *iter = json_object_iter (json);
    json_t *json_new = json_object_iter_value (iter);
    json_incref (json_new);
    json_decref (json);
    json = json_new;
    char *json_string = json_dumps (json, 0);

    /* Send the event */
    if (req->flags & FLAGS_EVENT_STREAM)
        send_response (req->handle, "data: ", false);
    send_response (req->handle, json_string, false);
    if (req->flags & FLAGS_EVENT_STREAM)
        send_response (req->handle, "\r\n\r\n", true);
    else
        send_response (req->handle, "\r\n", true);
    json_decref (json);
    free (json_string);

    return true;
}

static void
rest_api_watch (req_handle handle, int flags, const char *path)
{
    sch_node *api_subtree = sch_path_to_node (path);
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
    req->flags = flags;
    req->api = api_subtree;
    req->path = g_strdup (path);
    if (sch_node_is_leaf (api_subtree) )
        req->wpath = g_strdup (path);
    else
        req->wpath = g_strdup_printf ("%s/*", path);
    add_callback (APTERYX_WATCHERS_PATH, req->wpath, (void *)watch_callback, true, (void *) req, 1);

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

    delete_callback (APTERYX_WATCHERS_PATH, req->wpath, (void *)watch_callback);
    g_free (req->path);
    g_free (req->wpath);
    g_free (req);
}

void
rest_api (req_handle handle, int flags, const char *path, const char *action,
          const char *if_none_match, const char *data, int length)
{
    char *resp = NULL;

    /* Sanity check parameters */
    if (!path || !action ||
        !(flags & FLAGS_ACCEPT_JSON) ||
        strncmp (path, REST_API_PATH, strlen (REST_API_PATH)) != 0)
    {
        ERROR ("ERROR: invalid parameters (flags:0x%x, path:%s, action:%s)\n",
               flags, path, action);
        return;
    }
    VERBOSE ("%s(0x%x) %s\n", action, flags, path);

    /* Process method */
    path = path + strlen (REST_API_PATH);
    if (strcmp (action, "GET") == 0)
    {
        if (strcmp (path, ".xml") == 0)
            resp = rest_api_xml ();
        else if (flags & (FLAGS_EVENT_STREAM | FLAGS_APPLICATION_STREAM))
        {
            rest_api_watch (handle, flags, path);
            return;
        }
        else if (path[strlen (path) - 1] == '/')
            resp = rest_api_search (path);
        else
            resp = rest_api_get (flags, path, if_none_match);
    }
    else if (strcmp (action, "POST") == 0 || strcmp (action, "PUT") == 0)
        resp = rest_api_post (flags, path, data, length);
    else if (strcmp (action, "DELETE") == 0)
        resp = rest_api_delete (path);
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
