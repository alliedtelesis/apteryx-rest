/**
 * @file schema.c
 * Utilities for validating paths against the XML schema.
 *
 * Copyright 2016, Allied Telesis Labs New Zealand, Ltd
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
#include <fnmatch.h>
#include <libxml/parser.h>
#include <libxml/tree.h>
#include <regex.h>

/* Loaded schema root */
static xmlNode *g_schema = NULL;

/* List full paths for all XML files in the search path */
static void
list_xml_files (GList ** files, const char *path)
{
    DIR *dp;
    struct dirent *ep;
    char *saveptr = NULL;
    char *cpath;
    char *dpath;

    cpath = strdup (path);
    dpath = strtok_r (cpath, ":", &saveptr);
    while (dpath != NULL)
    {
        VERBOSE ("SCHEMA: Looking for schema files in \"%s\"\n", dpath);
        dp = opendir (dpath);
        if (dp != NULL)
        {
            while ((ep = readdir (dp)))
            {
                char *filename = NULL;
                if ((fnmatch ("*.xml", ep->d_name, FNM_PATHNAME) != 0) &&
                    (fnmatch ("*.xml.gz", ep->d_name, FNM_PATHNAME) != 0))
                {
                    VERBOSE ("SCHEMA: Ignoring \"%s\"\n", ep->d_name);
                    continue;
                }
                if (asprintf (&filename, "%s/%s", dpath, ep->d_name) > 0)
                {
                    VERBOSE ("SCHEMA: Adding \"%s\"\n", ep->d_name);
                    *files = g_list_append (*files, filename);
                }
            }
            (void) closedir (dp);
        }
        dpath = strtok_r (NULL, ":", &saveptr);
    }
    free (cpath);
    return;
}

/* Merge nodes from a new tree to the original tree */
static void
merge_nodes (xmlNode * orig, xmlNode * new, int depth)
{
    xmlNode *n;
    xmlNode *o;

    for (n = new; n; n = n->next)
    {
        char *orig_name = NULL;
        char *new_name;
        if (n->type != XML_ELEMENT_NODE)
        {
            continue;
        }
        new_name = (char *) xmlGetProp (n, (xmlChar *) "name");
        if (new_name)
        {
            for (o = orig; o; o = o->next)
            {
                orig_name = (char *) xmlGetProp (o, (xmlChar *) "name");
                if (orig_name)
                {
                    if (strcmp (new_name, orig_name) == 0)
                    {
                        xmlFree (orig_name);
                        break;
                    }
                    xmlFree (orig_name);
                }
            }
            xmlFree (new_name);
            if (o)
            {
                merge_nodes (o->children, n->children, depth + 1);
            }
            else
            {
                xmlAddPrevSibling (orig, xmlCopyNode (n, 1));
            }
        }
    }
    return;
}

/* Remove unwanted nodes and attributes from a parsed tree */
static void
cleanup_nodes (xmlNode * node)
{
    xmlNode *n, *next;

    n = node;
    while (n)
    {
        next = n->next;
        if (n->type == XML_ELEMENT_NODE)
        {
            cleanup_nodes (n->children);
            xmlSetNs (n, NULL);
        }
        else
        {
            xmlUnlinkNode (n);
            xmlFreeNode (n);
        }
        n = next;
    }
}

/* Parse all XML files in the search path and merge trees */
bool
sch_load (const char *path)
{
    xmlDoc *doc = NULL;
    GList *files = NULL;
    GList *iter;

    list_xml_files (&files, path);
    for (iter = files; iter; iter = g_list_next (iter))
    {
        char *filename = (char *) iter->data;
        xmlDoc *new = xmlParseFile (filename);
        if (new == NULL)
        {
            ERROR ("SCH: failed to parse \"%s\"", filename);
            continue;
        }
        cleanup_nodes (xmlDocGetRootElement (new)->children);
        if (doc == NULL)
        {
            doc = new;
        }
        else
        {
            merge_nodes (xmlDocGetRootElement (doc)->children,
                         xmlDocGetRootElement (new)->children, 0);
            xmlFreeDoc (new);
        }
    }
    g_list_free_full (files, free);

    g_schema = (sch_node *) xmlDocGetRootElement (doc);
    return true;
}

void
sch_unload (void)
{
    if (g_schema)
    {
        xmlFreeDoc (g_schema->doc);
        g_schema = NULL;
    }
}

sch_node *
sch_root (void)
{
    return (sch_node *) g_schema;
}

char *
sch_dump (void)
{
    xmlChar *xmlbuf = NULL;
    int bufsize;

    xmlDocDumpFormatMemory (g_schema->doc, &xmlbuf, &bufsize, 1);
    return (char *) xmlbuf;
}

/* Check path validity against the tree */
sch_node *
sch_validate_path (sch_node * root, const char *path, bool * read, bool * write)
{
    xmlNode *node = (xmlNode *) root;
    xmlNode *n;
    char *name, *mode;
    char *key = NULL;
    int len;

    if (read)
        *read = false;
    if (write)
        *write = false;

    if (path[0] == '/')
        path++;
    key = strchr (path, '/');
    if (key)
    {
        len = key - path;
        key = strndup (path, len);
        path += len;
    }
    else
    {
        key = strdup (path);
        path = NULL;
    }

    for (n = node->children; n; n = n->next)
    {
        if (n->type != XML_ELEMENT_NODE)
            continue;
        mode = (char *) xmlGetProp (n, (xmlChar *) "mode");
        name = (char *) xmlGetProp (n, (xmlChar *) "name");
        if (name && (name[0] == '*' || strcmp (name, key) == 0))
        {
            free (key);
            if (path)
            {
                if (mode && strchr (mode, 'p') != NULL)
                {
                    xmlFree (name);
                    xmlFree (mode);
                    /* restart search from root
                     *
                     * currently proxies are only used to redirect to the root
                     * node of another stack members database. So for now we can
                     * simply re-validate from root.
                     */
                    return sch_validate_path (g_schema, path, read, write);
                }
                xmlFree (name);
                xmlFree (mode);
                return sch_validate_path (n, path, read, write);
            }
            if (read && (!mode || strchr (mode, 'r') != NULL))
                *read = true;
            if (write && mode && strchr (mode, 'w') != NULL)
                *write = true;
            xmlFree (name);
            if (mode)
                xmlFree (mode);
            return n;
        }

        if (name)
            xmlFree (name);
        if (mode)
            xmlFree (mode);
    }

    free (key);
    return NULL;
}

bool
sch_node_is_leaf (sch_node * node)
{
    xmlNode *xml = (xmlNode *) node;
    xmlNode *n;

    if (!xml->children)
    {
        return true;
    }
    for (n = xml->children; n; n = n->next)
    {
        if (n->type == XML_ELEMENT_NODE && n->name[0] == 'N')
        {
            return false;
        }
    }
    return true;
}

bool
sch_node_has_mode_flag (sch_node * node, char mode_flag)
{
    xmlNode *xml = (xmlNode *) node;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    bool has_flag = mode && strchr (mode, mode_flag);
    xmlFree (mode);
    return has_flag;
}

char *
sch_node_to_path (sch_node * node)
{
    char *path = NULL;

    while (node)
    {
        char *tmp = NULL;
        char *name = (char *) xmlGetProp (node, (xmlChar *) "name");
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
        node = ((xmlNode *) node)->parent;
    }
    return path;
}

sch_node *
sch_child_get (sch_node * root, const char *name)
{
    sch_node *child;

    /* Don't get fooled if this node has value tags as children. */
    if (sch_node_is_leaf (root))
    {
        return NULL;
    }

    for (child = ((xmlNode *) root)->children; child; child = ((xmlNode *) child)->next)
    {
        char *child_name = (char *) xmlGetProp (child, (xmlChar *) "name");
        if (child_name && (child_name[0] == '*' || strcmp (name, child_name) == 0))
        {
            free (child_name);
            break;
        }
        free (child_name);
    }

    return child;
}

static bool
node_has_mode_flag (sch_node * node, char mode_flag)
{
    xmlNode *xml = (xmlNode *) node;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    bool has_flag = mode && strchr (mode, mode_flag);
    xmlFree (mode);
    return has_flag;
}

sch_node *
sch_path_to_node (const char *path)
{
    sch_node *node = (sch_node *) g_schema;
    char *path_cpy = strdup (path);
    char *component;
    char *saveptr = NULL;

    for (component = strtok_r (path_cpy, "/", &saveptr); component;
         component = strtok_r (NULL, "/", &saveptr))
    {
        /* Restart from root on finding a proxy node */
        if (node_has_mode_flag (node, 'p'))
        {
            node = (sch_node *) g_schema;
        }

        /* Get the node matching this component. */
        node = sch_child_get (node, component);
        if (!node)
        {
            break;
        }
    }

    free (path_cpy);
    return node;
}

bool
sch_validate_pattern (sch_node * node, const char *value)
{
    char *pattern = (char *) xmlGetProp (node, (xmlChar *) "pattern");
    if (pattern)
    {
        char message[100];
        regex_t regex_obj;
        int rc;

        rc = regcomp (&regex_obj, pattern, REG_EXTENDED);
        if (rc != 0)
        {
            regerror (rc, NULL, message, sizeof (message));
            ERROR ("SCHEMA: %i (\"%s\") for regex %s", rc, message, pattern);
            xmlFree (pattern);
            return false;
        }

        rc = regexec (&regex_obj, value, 0, NULL, 0);
        regfree (&regex_obj);
        if (rc == REG_ESPACE)
        {
            regerror (rc, NULL, message, sizeof (message));
            ERROR ("SCHEMA: %i (\"%s\") for regex %s", rc, message, pattern);
            xmlFree (pattern);
            return false;
        }

        xmlFree (pattern);
        return (rc == 0);
    }
    return true;
}
