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
#include <regex.h>

#define HTTP_CODE_OK                    200
#define HTTP_CODE_BAD_REQUEST           400
#define HTTP_CODE_FORBIDDEN             403
#define HTTP_CODE_INTERNAL_SERVER_ERROR 500

static void
apteryx_log_regex_error (int return_code, const char *regex)
{
    char message[100];

    regerror (return_code, NULL, message, sizeof (message));
    ERROR ("REST: %i (\"%s\") for regex %s", return_code, message, regex);
}

static int
apteryx_check_regex (const char *regex_str, const char *value, bool * matches)
{
    regex_t regex_obj;
    int rc;

    *matches = false;

    rc = regcomp (&regex_obj, regex_str, REG_EXTENDED);

    if (rc != 0)
    {
        apteryx_log_regex_error (rc, regex_str);
        return -1;
    }

    rc = regexec (&regex_obj, value, 0, NULL, 0);
    regfree (&regex_obj);

    if (rc == REG_ESPACE)
    {
        apteryx_log_regex_error (rc, regex_str);
        return -1;
    }

    *matches = (rc == 0);
    return 0;
}

static int
tree_to_json (GNode * node, json_t * json)
{
    int ret;

    if (APTERYX_HAS_VALUE (node))
    {
        ret =
            json_object_set_new (json, APTERYX_NAME (node),
                                 json_string (APTERYX_VALUE (node)));
    }
    else
    {
        json_t *obj = json_object ();
        GNode *child;
        for (child = g_node_first_child (node); child; child = g_node_next_sibling (child))
        {
            ret = tree_to_json (child, obj);
            if (ret != 0)
            {
                return ret;
            }
        }
        ret = json_object_set (json, APTERYX_NAME (node), obj);
    }
    if (ret != 0)
    {
        ERROR ("JSON: Failed to parse node %s\n", APTERYX_NAME (node));
    }
    return ret;
}

static json_t *
g_node_to_url_json (GNode * tree)
{
    GNode *child;
    json_t *json;

    /* Parse the tree to JSON */
    json = json_object ();
    for (child = g_node_first_child (tree); child; child = g_node_next_sibling (child))
    {
        int ret = tree_to_json (child, json);
        if (ret != 0)
        {
            json_decref (json);
            return NULL;
        }
    }
    return json;
}

static char *
rest_api_xml (void)
{
    char *resp = NULL;
    char *xmlbuf = sch_dump (g_schema);
    if (xmlbuf)
    {
        resp = g_strdup_printf ("Status: 200\r\n"
                                "Content-Type: txt/xml\r\n" "\r\n" "%s", (char *) xmlbuf);
        free (xmlbuf);
    }
    return resp;
}

static int
apteryx_json_search (sch_node *root, const char *path, char **data)
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
        return 403;
    }

    /* Do the Apteryx search */
    buffer = g_strdup_printf ("{\"%s\": [", len > 2 ? strrchr (_path, '/') + 1 : "");
    children = apteryx_search (path);
    for (iter = children; iter; iter = g_list_next (iter))
    {
        path = strrchr ((const char *) iter->data, '/') + 1;
        if (sch_validate_path (root, path, NULL, NULL) != NULL)
        {
            if (!first)
                buffer = g_strdup_printf ("%s,\"%s\"", buffer, path);
            else
                buffer = g_strdup_printf ("%s\"%s\"", buffer, path);
            first = false;
        }
    }
    buffer = g_strdup_printf ("%s]}", buffer);
    *data = buffer;

    g_list_free_full (children, free);
    free (_path);
    return HTTP_CODE_OK;
}

static char *
rest_api_search (const char *path)
{
    char *data = NULL;
    int rc = apteryx_json_search (g_schema, path, &data);
    return g_strdup_printf ("Status: %d\r\n" "\r\n" "%s", rc, data ? : "");
}

static char *
rest_api_get (const char *path)
{
    GNode *tree;
    json_t *json;
    char *data;

    VERBOSE ("GET %s\n", path);

    /* Get from Apteryx */
    tree = apteryx_get_tree (path);
    if (!tree)
    {
        ERROR ("\"%s\" not found\n", path);
        return NULL;
    }

    /* Convert to JSON */
    json = g_node_to_url_json (tree);
    if (!json)
    {
        ERROR ("Failed to convert Apteryx to JSON for path %s\n", path);
        apteryx_free_tree (tree);
        return NULL;
    }
    apteryx_free_tree (tree);

    /* Dump to the output */
    data = json_dumps (json, 0);
    if (!data)
    {
        ERROR ("Failed to format JSON for path %s\n", path);
        json_decref (json);
        return NULL;
    }
    json_decref (json);

    /* Add header */
    data = g_strdup_printf ("Status: 200\r\n"
                            "Content-Type: application/yang.data+json\r\n"
                            "\r\n" "%s", data);

    /* Return response */
    return data;
}

static sch_node *
api_child_get (sch_node * api_root, const char *search_name)
{
    sch_node *api_child;

    /* Don't get fooled if this node has value tags as children. */
    if (sch_node_is_leaf (api_root))
    {
        return NULL;
    }

    for (api_child = sch_first_child (api_root); api_child; api_child = sch_next_child (api_child))
    {
        char *api_child_name = sch_name (api_child);
        if (api_child_name &&
            (api_child_name[0] == '*' || strcmp (search_name, api_child_name) == 0))
        {
            free (api_child_name);
            break;
        }

        free (api_child_name);
    }

    return api_child;
}

static sch_node *
api_node_get (const char *path)
{
    char *path_cpy = strdup (path);
    char *component;
    char *saveptr = NULL;
    sch_node *api_node = (sch_node *) g_schema;

    for (component = strtok_r (path_cpy, "/", &saveptr); component;
         component = strtok_r (NULL, "/", &saveptr))
    {
        /* Restart from root on finding a proxy node */
        if (sch_node_has_mode_flag (api_node, 'p'))
        {
            api_node = (sch_node *) g_schema;
        }

        /* Get the node matching this component. */
        api_node = api_child_get (api_node, component);
        if (!api_node)
        {
            break;
        }
    }

    return api_node;
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
} json_to_tree_result_t;

static char *
node_to_path (sch_node * node)
{
    char *path = NULL;

    while (node)
    {
        char *tmp = NULL;
        char *name = sch_name (node);
        if (name == NULL)
        {
            break;
        }
        if (asprintf (&tmp, "/%s%s", name, path ? : "") >= 0)
        {
            free (path);
            path = tmp;
        }
        free (name);
        node = sch_parent (node);
    }
    return path;
}

static void
json_error (sch_node * node, char *msg)
{
    char *path = node_to_path (node);
    ERROR ("JSON: %s \"%s\"\n", msg, path ? : "<unknown>");
    free (path);
    return;
}

static json_to_tree_result_t
json_to_tree (sch_node * api_root, json_t * json_root, GNode * data_root)
{
    const char *key;
    json_t *object;
    int rc;

    json_object_foreach (json_root, key, object)
    {
        sch_node *api_child;
        GNode *data_child;

        api_child = api_child_get (api_root, key);
        if (!api_child)
        {
            json_error (api_root, "J2T_RES_NO_API_NODE");
            return J2T_RES_NO_API_NODE;
        }

        if (json_is_object (object))
        {
            data_child = g_node_new ((char *) key);
            rc = json_to_tree (api_child, object, data_child);
            if (rc != J2T_RES_SUCCESS)
            {
                /* We don't need to do anything with data_child; it must be NULL because this
                 * function only sets it to something significant on success. */
                g_node_destroy (data_child);
                return rc;
            }
        }
        else if (json_is_string (object))
        {
            const char *value = json_string_value (object);
            char *pattern = NULL;
            bool match;

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

            /* We only need to do a pattern check when setting a non-empty value; clearing a value
             * is always permitted. */
            if (value[0] != '\0')
            {
                pattern = sch_pattern (api_child);
            }

            /* "pattern" will sometimes be NULL even when setting a non-empty value because some writeable
             * nodes don't have patterns. If there is no pattern then accept anything. */
            if (pattern)
            {
                rc = apteryx_check_regex (pattern, value, &match);
                free (pattern);

                if (rc != 0)
                {
                    json_error (api_child, "J2T_RES_REGEX_COMPILATION_FAIL");
                    return J2T_RES_REGEX_COMPILATION_FAIL;
                }

                if (!match)
                {
                    json_error (api_child, "J2T_RES_REGEX_MISMATCH");
                    return J2T_RES_REGEX_MISMATCH;
                }
            }

            data_child = g_node_new ((char *) key);
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

    api_subtree = api_node_get (path);
    if (!api_subtree)
    {
        return HTTP_CODE_FORBIDDEN;
    }

    data = g_node_new ((char *) path);
    rc = json_to_tree (api_subtree, json, data);
    switch (rc)
    {
    case J2T_RES_SUCCESS:
        break;
    case J2T_RES_NO_API_NODE:
    case J2T_RES_VALUE_ON_CORE_NODE:
    case J2T_RES_PERMISSION_MISMATCH:
        g_node_destroy (data);
        return HTTP_CODE_FORBIDDEN;
    case J2T_RES_SLASH_IN_PATH_COMPONENT:
    case J2T_RES_REGEX_MISMATCH:
    case J2T_RES_UNSUPPORTED_JSON_TYPE:
    case J2T_RES_OBJECT_ON_LEAF_NODE:
    case J2T_RES_EMPTY_OBJECT:
        g_node_destroy (data);
        return HTTP_CODE_BAD_REQUEST;
    case J2T_RES_REGEX_COMPILATION_FAIL:
    default:
        g_node_destroy (data);
        return HTTP_CODE_INTERNAL_SERVER_ERROR;
    }
    set_successful = apteryx_set_tree (data);
    g_node_destroy (data);

    if (!set_successful)
    {
        // TODO error message
        return HTTP_CODE_BAD_REQUEST;
    }

    return HTTP_CODE_OK;
}

static char *
rest_api_post (const char *path, const char *data, int length)
{
    json_error_t error;
    json_t *json;
    int rc;

    json = json_loads (data, 0, &error);
    if (!json)
    {
        ERROR ("error: on line %d: %s\n", error.line, error.text);
        rc = HTTP_CODE_BAD_REQUEST;
    }
    else
    {
        rc = apteryx_json_set (path, json);
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
    int rc = apteryx_json_delete ((sch_node *) g_schema, path);
    return g_strdup_printf ("Status: %d\r\n" "\r\n", rc);
}

char *
rest_api (int flags, const char *path, const char *action, const char *data, int length)
{
    char *resp = NULL;

    /* Sanity check parameters */
    if (!path || !action ||
        !(flags & FLAGS_ACCEPT_JSON) ||
        strncmp (path, REST_API_PATH, strlen (REST_API_PATH)) != 0)
    {
        ERROR ("ERROR: invalid parameters (flags:0x%x, path:%s, action:%s)\n",
               flags, path, action);
        return NULL;
    }
    VERBOSE ("%s(0x%x) %s\n", action, flags, path);

    /* Process method */
    path = path + strlen (REST_API_PATH);
    if (strcmp (action, "GET") == 0)
    {
        if (strcmp (path, ".xml") == 0)
            resp = rest_api_xml ();
        else if (path[strlen (path) - 1] == '/')
            resp = rest_api_search (path);
        else
            resp = rest_api_get (path);
    }
    else if (strcmp (action, "POST") == 0 || strcmp (action, "PUT") == 0)
        resp = rest_api_post (path, data, length);
    else if (strcmp (action, "DELETE") == 0)
        resp = rest_api_delete (path);
    return resp;
}
