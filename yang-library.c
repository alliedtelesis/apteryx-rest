/**
 * @file yang-library.c
 *
 * Copyright 2023, Allied Telesis Labs New Zealand, Ltd
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
#include "models/ietf-yang-library.h"
#include "models/ietf-restconf-monitoring.h"

/* Name for the set of modules */
#define MODULES_STR "modules"

/* List of supported capabilities. This is hard-coded for now, if we add a
 * capability in the code, we need to update this table. Null terminate it
 * for ease of traversal.
 * Ref: http://www.iana.org/assignments/restconf-capability-urns/restconf-capability-urns.xhtml
 * Commented capabilities are those defined but not yet supported.
 */
char *restconf_capabilities[] =
{
    "urn:ietf:params:restconf:capability:defaults:1.0",
    "urn:ietf:params:restconf:capability:depth:1.0",
    "urn:ietf:params:restconf:capability:fields:1.0",
    "urn:ietf:params:restconf:capability:filter:1.0",
    // "urn:ietf:params:restconf:capability:replay:1.0",
    "urn:ietf:params:restconf:capability:with-defaults:1.0",
    // "urn:ietf:params:restconf:capability:yang-patch:1.0",    /* [RFC8072] */
    // "urn:ietf:params:restconf:capability:with-origin:1.0",   /* [RFC8527] */
    // "urn:ietf:params:restconf:capability:with-operational-defaults:1.0",    /* [RFC8527] */
    NULL
};

/*
 * A wrapper for APTERYX_LEAF.
 * @param root - The node the leaf will be added to
 * @param node_name - Name of the new node
 * @param value - Value to set the node to, or NULL to delete the leaf
 */
static GNode *
add_leaf (GNode *root, char *node_name, char *value)
{
    GNode *child_node = NULL;

    assert (root);

    if (value == NULL)
    {
        value = g_strdup ("");
    }

    child_node = APTERYX_LEAF (root, (gpointer) node_name, (gpointer) value);

    return child_node;
}

/**
 * Add a leaf to a node
 *
 * @param root - The node the leaf will be added to
 * @param node_name - Name of the new node
 * @param value - Value to set the node to, or NULL to delete the leaf
 *
 * @return a pointer to the leaf,  or NULL for failure
 */
static GNode *
add_leaf_strdup (GNode *root, const char *node_name, const char *value)
{
    if (root && node_name)
    {
        return add_leaf (root, g_strdup (node_name), g_strdup (value));
    }

    return NULL;
}

/**
 * Add an entry to the apteryx database for each model known to resconf
 *
 * @param root - The node the leaf will be added to
 */
static void
schema_set_model_information (sch_instance *schema, GNode *root)
{
    GNode *gnode;
    sch_loaded_model *loaded;
    GList *list;
    GList *loaded_models = sch_get_loaded_models (schema);

    for (list = g_list_first (loaded_models); list; list = g_list_next (list))
    {
        loaded = list->data;

        if (loaded->model && strlen (loaded->model))
        {
            gnode = add_leaf_strdup (root, YANG_LIBRARY_MODULE_SET_MODULE_PATH,
                                     loaded->model);

            add_leaf_strdup (gnode, MODULES_STATE_MODULE_NAME, loaded->model);
            if (loaded->version)
            {
                add_leaf_strdup (gnode, MODULES_STATE_MODULE_REVISION,
                                 loaded->version);
            }
            if (loaded->ns_href)
            {
                add_leaf_strdup (gnode, MODULES_STATE_MODULE_NAMESPACE, loaded->ns_href);
            }
        }
    }
}

/**
 * Given a schema create the Apteryx data for the ietf-yang-library model required
 * by restconf.
 *
 * @param g_schema - The root schema xml node
 */
void
yang_library_create (sch_instance *schema)
{
    GNode *root;
    GNode *modules;
    time_t now = time (NULL);
    char set_id[24];

    root = APTERYX_NODE (NULL, g_strdup (YANG_LIBRARY_PATH));
    modules = add_leaf_strdup (root, YANG_LIBRARY_SCHEMA_MODULE_SET, MODULES_STR);
    add_leaf_strdup (modules, YANG_LIBRARY_MODULE_SET_NAME, MODULES_STR);
    schema_set_model_information (schema, modules);

    apteryx_set_tree (root);
    apteryx_free_tree (root);

    /* Each time this routine is run the content-id will be set to a unique id based
     * on the clock */
    snprintf (set_id, sizeof (set_id), "%" PRIx64 "", now);
    apteryx_set (YANG_LIBRARY_CONTENT_ID, set_id);
}

/**
 * Create the Apteryx data for the ietf-restconf-monitoring model required by restconf.
 *
 * @param g_schema - The root schema xml node
 */
void
restconf_monitoring_create (sch_instance *schema)
{
    GNode *root;
    char **cap = restconf_capabilities;

    root = APTERYX_NODE (NULL, g_strdup (RESTCONF_STATE_CAPABILITIES_CAPABILITY));
    for (; *cap != NULL; cap++)
    {
        add_leaf_strdup (root, *cap, *cap);
    }

    apteryx_set_tree (root);
    apteryx_free_tree (root);
}
