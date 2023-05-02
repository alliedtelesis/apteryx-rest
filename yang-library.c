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

/* Name for the set of modules */
#define MODULES_STR "modules"

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
 * Traverse each of the top level nodes of the schema which each represent an
 * added model
 *
 * @param root - The node the leaf will be added to
 * @param node - The root schema xml node
 */
static void
traverse_schema_add_models (GNode *root, sch_node *node)
{
    sch_node *sch_child;
    GNode *gnode;

    for (sch_child = sch_node_child_first (node); sch_child;
         sch_child = sch_node_next_sibling (sch_child))
    {
        char *model = sch_model (sch_child, true);
        if (model && strlen (model))
        {
            char *revision = sch_version (sch_child);
            char *namespace = sch_namespace (sch_child);
            gnode = add_leaf_strdup (root, YANGLIB_YANG_LIBRARY_MODULE_SET_MODULE_PATH,
                                     model);

            add_leaf_strdup (gnode, YANGLIB_MODULES_STATE_MODULE_NAME, model);
            if (revision)
            {
                add_leaf_strdup (gnode, YANGLIB_MODULES_STATE_MODULE_REVISION, revision);
            }
            if (namespace)
            {
                add_leaf_strdup (gnode, YANGLIB_MODULES_STATE_MODULE_NAMESPACE, namespace);
            }
            g_free (namespace);
            g_free (revision);
            g_free (model);
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
yang_library_create (sch_instance *g_schema)
{
    GNode *root;
    GNode *modules;
    time_t now = time (NULL);
    char set_id[24];

    root = APTERYX_NODE (NULL, g_strdup (YANGLIB_YANG_LIBRARY_PATH));
    modules = add_leaf_strdup (root, YANGLIB_YANG_LIBRARY_SCHEMA_MODULE_SET, MODULES_STR);
    add_leaf_strdup (modules, YANGLIB_YANG_LIBRARY_MODULE_SET_NAME, MODULES_STR);

    /* Each time this routine is run the content-id will be set to a unique id based
     * on the clock */
    snprintf (set_id, sizeof (set_id), "%" PRIx64 "", now);
    add_leaf_strdup (root, YANGLIB_YANG_LIBRARY_CONTENT_ID, set_id);

    traverse_schema_add_models (modules, g_schema);

    apteryx_set_tree (root);
    apteryx_free_tree (root);
}
