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

bool
sch_node_is_api_node (sch_node *node)
{
    xmlNode *xml = (xmlNode *) node;
    /* Is the XML node type "NODE"? This only checks the first
     * letter because there is nothing else that begins with 'N'. */
    return (xml->name[0] == 'N');
}

bool
sch_node_is_leaf (sch_node *node)
{
    xmlNode *xml = (xmlNode *) node;
    /* If there is a VALUE tag then assume that no child NODEs will be found. */
    return !xml->children || !sch_node_is_api_node ((sch_node *) xml->children);
}

bool
sch_node_has_mode_flag (sch_node *node, char mode_flag)
{
    xmlNode *xml = (xmlNode *) node;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    bool has_flag = mode && strchr (mode, mode_flag);
    xmlFree (mode);
    return has_flag;
}

/* Check path validity against the tree */
sch_node *
sch_validate_path (sch_instance *schema, const char *path, bool *read, bool *write)
{
    xmlNode *node = (xmlNode *) schema;
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

/* List full paths for all XML files in the search path */
static void
list_xml_files (GList **files, const char *path)
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
        dp = opendir (dpath);
        if (dp != NULL)
        {
            while ((ep = readdir (dp)))
            {
                char *filename = NULL;
                if ((fnmatch ("*.xml", ep->d_name, FNM_PATHNAME) != 0) &&
                    (fnmatch ("*.xml.gz", ep->d_name, FNM_PATHNAME) != 0))
                {
                    continue;
                }
                if (asprintf (&filename, "%s/%s", dpath, ep->d_name) > 0)
                {
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
merge_nodes (xmlNode *orig, xmlNode *new, int depth)
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
cleanup_nodes (xmlNode *node)
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
sch_instance *
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
            syslog (LOG_ERR, "LUA: failed to parse \"%s\"", filename);
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

    return (sch_instance *) xmlDocGetRootElement (doc);
}

void
sch_free (sch_instance *schema)
{
    xmlNode *xml = (xmlNode *) schema;
    xmlFreeDoc (xml->doc);
}

static gboolean
match_name (const char *s1, const char *s2)
{
    char c1, c2;
    do
    {
        c1 = *s1;
        c2 = *s2;
        if (c1 == '\0' && c2 == '\0')
            return true;
        if (c1 == '-')
            c1 = '_';
        if (c2 == '-')
            c2 = '_';
        s1++;
        s2++;
    } while (c1 == c2);
    return false;
}

static xmlNode *
lookup_node (xmlNode *node, const char *path)
{
    xmlNode *n;
    char *name, *mode;
    char *key = NULL;
    int len;

    if (!node)
    {
        return NULL;
    }

    if (path[0] == '/')
    {
        path++;
    }
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
        {
            continue;
        }
        name = (char *) xmlGetProp (n, (xmlChar *) "name");
        if (name && (name[0] == '*' || match_name (name, key)))
        {
            free (key);
            if (path)
            {
                mode = (char *) xmlGetProp (n, (xmlChar *) "mode");
                if (mode && strchr (mode, 'p') != NULL)
                {
                    xmlFree (name);
                    xmlFree (mode);
                    /* restart search from root */
                    return lookup_node (xmlDocGetRootElement (node->doc), path);
                }
                xmlFree (name);
                if (mode)
                {
                    xmlFree (mode);
                }
                return lookup_node (n, path);
            }
            xmlFree (name);
            return n;
        }

        if (name)
        {
            xmlFree (name);
        }
    }

    free (key);
    return NULL;
}

sch_node *
sch_lookup (sch_instance *schema, const char *path)
{
    return lookup_node ((xmlNode *) schema, path);
}

bool
sch_is_leaf (sch_node *node)
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
sch_is_readable (sch_node *node)
{
    xmlNode *xml = (xmlNode *) node;
    bool access = false;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    if (!mode || strchr (mode, 'r') != NULL)
    {
        access = true;
    }
    free (mode);
    return access;
}

bool
sch_is_writable (sch_node *node)
{
    xmlNode *xml = (xmlNode *) node;
    bool access = false;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    if (mode && strchr (mode, 'w') != NULL)
    {
        access = true;
    }
    free (mode);
    return access;
}

bool
sch_is_config (sch_node *node)
{
    xmlNode *xml = (xmlNode *) node;
    bool access = false;
    char *mode = (char *) xmlGetProp (xml, (xmlChar *) "mode");
    if (mode && strchr (mode, 'c') != NULL)
    {
        access = true;
    }
    free (mode);
    return access;
}

char *
sch_translate_to (sch_node *node, char *value)
{
    xmlNode *xml = (xmlNode *) node;
    xmlNode *n;
    char *val;

    /* Get the default if needed - untranslated */
    if (!value)
    {
        value = (char *) xmlGetProp (node, (xmlChar *) "default");
    }

    /* Find the VALUE node with this value */
    for (n = xml->children; n && value; n = n->next)
    {
        if (n->type == XML_ELEMENT_NODE && n->name[0] == 'V')
        {
            val = (char *) xmlGetProp (n, (xmlChar *) "value");
            if (val && strcmp (value, val) == 0)
            {
                free (value);
                free (val);
                return (char *) xmlGetProp (n, (xmlChar *) "name");
            }
            free (val);
        }
    }
    return value;
}

char *
sch_translate_from (sch_node *node, char *value)
{
    xmlNode *xml = (xmlNode *) node;
    xmlNode *n;
    char *val;

    /* Find the VALUE node with this name */
    for (n = xml->children; n && value; n = n->next)
    {
        if (n->type == XML_ELEMENT_NODE && n->name[0] == 'V')
        {
            val = (char *) xmlGetProp (n, (xmlChar *) "name");
            if (val && strcmp (value, val) == 0)
            {
                free (value);
                free (val);
                return (char *) xmlGetProp (n, (xmlChar *) "value");
            }
            free (val);
        }
    }
    return value;
}

char*
sch_name (sch_node *node)
{
    return (char *) xmlGetProp (node, (xmlChar *) "name");
}

char*
sch_pattern (sch_node *node)
{
    return (char *) xmlGetProp (node, (xmlChar *) "pattern");
}

sch_node*
sch_parent (sch_node *node)
{
    return ((xmlNode *) node)->parent;
}

sch_node*
sch_first_child (sch_node *node)
{
    return ((xmlNode *) node)->children;
}

sch_node*
sch_next_child (sch_node *node)
{
    return ((xmlNode *) node)->next;
}

char *
sch_dump (sch_instance *schema)
{
    xmlChar *xmlbuf = NULL;
    int bufsize;

    xmlDocDumpFormatMemory (((xmlNode *) schema)->doc, &xmlbuf, &bufsize, 1);
    return (char *) xmlbuf;
}

