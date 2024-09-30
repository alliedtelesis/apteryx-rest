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
#define SCHEMA_STR "schema"
#define DATASTORE_STR "datastore"
#define COMMON_STR "common"

/* List of supported capabilities. This is hard-coded for now, if we add a
 * capability in the code, we need to update this table. Null terminate it
 * for ease of traversal.
 * Ref: http://www.iana.org/assignments/restconf-capability-urns/restconf-capability-urns.xhtml
 * Commented capabilities are those defined but not yet supported.
 */
char *restconf_capabilities[] =
{
    "urn:ietf:params:restconf:capability:defaults:1.0?basic-mode=explicit",
    "urn:ietf:params:restconf:capability:depth:1.0",
    "urn:ietf:params:restconf:capability:fields:1.0",
    // "urn:ietf:params:restconf:capability:filter:1.0",
    // "urn:ietf:params:restconf:capability:replay:1.0",
    "urn:ietf:params:restconf:capability:with-defaults:1.0",
    // "urn:ietf:params:restconf:capability:yang-patch:1.0",    /* [RFC8072] */
    // "urn:ietf:params:restconf:capability:with-origin:1.0",   /* [RFC8527] */
    // "urn:ietf:params:restconf:capability:with-operational-defaults:1.0",    /* [RFC8527] */
    NULL
};

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
        APTERYX_LEAF (root, g_strdup (*cap), g_strdup (*cap));
    }

    apteryx_set_tree (root);
    apteryx_free_tree (root);
}
