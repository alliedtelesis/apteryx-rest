/**
 * @file rpc.c
 *
 * Copyright 2024, Allied Telesis Labs New Zealand, Ltd
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
#include <lua.h>
#include <lualib.h>
#include <lauxlib.h>
#include <fnmatch.h>

struct rpc_handler {
    char *path;
    int flags;
    int ref;
};

#define REST_RPC_CB_TABLE_REGISTRY_INDEX "rest_rpc_cb_table"
static pthread_mutex_t g_ls_lock = PTHREAD_MUTEX_INITIALIZER;
static GList *g_rpcs = NULL;
static lua_State *g_ls = NULL;

static void
rpc_free (struct rpc_handler *rpc)
{
    free (rpc->path);
    free (rpc);
}

static gint
rpc_cmp (struct rpc_handler *rpc, const char *path)
{
    return fnmatch (rpc->path, path, 0);
}

static GList *
rpc_find (int flags, const char *path)
{
    return g_list_find_custom (g_rpcs, (gpointer) path, (GCompareFunc) rpc_cmp);
}

static void
rpc_lua_error (lua_State *ls, int res)
{
    switch (res)
    {
    case LUA_ERRRUN:
        ERROR ("LUA: %s\n", lua_tostring (ls, -1));
        lua_pop (ls, 1);
        break;
    case LUA_ERRSYNTAX:
        ERROR ("LUA: %s\n", lua_tostring (ls, -1));
        lua_pop (ls, 1);
        break;
    case LUA_ERRMEM:
        ERROR ("LUA: Memory allocation error\n");
        break;
    case LUA_ERRERR:
        ERROR ("LUA: Error handler error\n");
        break;
    case LUA_ERRFILE:
        ERROR ("LUA: Couldn't open file\n");
        break;
    default:
        ERROR ("LUA: Unknown error\n");
        break;
    }
}

static int
find_callback (lua_State *L, int index)
{
    int ref = 0;
    luaL_checktype (L, -1, LUA_TTABLE);
    /* lua_next pops requested key and pushes next key and value */
    lua_pushnil (L); /* push nil key to get first table entry */
    while (lua_next (L, -2))
    {
        if (lua_rawequal (L, index, -1))
        {
            ref = lua_tonumber (L, -2);
            lua_pop (L, 2); /* pop key and value */
            break;
        }
        lua_pop(L, 1); /* pop value but leave key on stack for lua_next */
    }
    return ref;
}

static int
ref_callback (lua_State* L, int index)
{
    luaL_checktype (L, index, LUA_TFUNCTION);
    lua_pushlightuserdata (L, REST_RPC_CB_TABLE_REGISTRY_INDEX);
    lua_gettable (L, LUA_REGISTRYINDEX);
    int ref = find_callback (L, index);
    if (ref == 0)
    {
        lua_pushvalue (L, index);
        ref = luaL_ref (L, -2);
    }
    lua_pop (L, 1); /* pop table */
    return ref;
}

static bool
push_callback (lua_State* L, size_t ref)
{
    if (L == NULL)
        return false;
    lua_pushlightuserdata (L, REST_RPC_CB_TABLE_REGISTRY_INDEX);
    lua_gettable (L, LUA_REGISTRYINDEX);
    if (lua_isnil (L, -1))
    {
        ERROR ("LUA: Callback not found\n");
        lua_pop (L, 1); /* pop nil */
        return false;
    }
    lua_rawgeti (L, -1, ref);
    if (!lua_isfunction (L, -1))
    {
        ERROR ("LUA: Callback not a function\n");
        lua_pop (L, 1);
        return false;
    }
    return true;
}

static const char *
lua_apteryx_tostring (lua_State *L, int i)
{
    const char *ret = NULL;
    int abs_index = lua_absindex (L, i);

    switch (lua_type (L, i))
    {
    case LUA_TNIL:
        return NULL;
    case LUA_TBOOLEAN:
        return lua_toboolean (L, i) ? "1" : "0";
    default:
        lua_getglobal (L, "tostring");
        lua_pushvalue (L, abs_index);
        lua_call (L, 1, 1);
        ret = lua_tostring (L, -1);
        lua_pop (L, 1);
    }

    return ret;
}

static void
_lua_apteryx_tree2dict (lua_State *L, GNode *this)
{
    GNode *child = NULL;

    if (!(this->children))
    {
        /* Something is wrong, either a value has been stored on a trunk
         * or get_tree was called on a leaf node. Both we do not support */
        return;
    }

    lua_pushstring (L, APTERYX_NAME (this));
    /* is this a leaf? */
    if (APTERYX_HAS_VALUE (this))
    {
        lua_pushstring (L, APTERYX_VALUE (this));
    }
    else
    {
        lua_newtable (L);
        for (child = g_node_first_child (this); child; child = g_node_next_sibling (child))
        {
            _lua_apteryx_tree2dict (L, child);
        }
    }

    lua_settable (L, -3);
}

static inline void
lua_apteryx_tree2dict (lua_State *L, GNode *this)
{
    GNode *child = NULL;
    lua_newtable (L);
    if (this)
    {
        for (child = g_node_first_child (this); child; child = g_node_next_sibling (child))
        {
            _lua_apteryx_tree2dict (L, child);
        }
    }
}

static bool
_lua_apteryx_dict2tree (lua_State *L, GNode *n, bool leaves)
{
    bool ret = false;
    GNode *c = NULL;
    const char *value = NULL;

    lua_pushnil (L);
    while (lua_next (L, -2))
    {
        if (lua_type (L, -1) == LUA_TTABLE)
        {
            lua_pushvalue (L, -2);
            c = APTERYX_NODE (n, strdup ((char *) lua_tostring (L, -1)));
            lua_pop (L, 1);
            _lua_apteryx_dict2tree (L, c, leaves);
            ret = true;
        }
        else
        {
            value = lua_apteryx_tostring (L, -1);
            if (value)
            {
                lua_pushvalue (L, -2);
                APTERYX_LEAF (n, strdup ((char *) lua_tostring (L, -1)), strdup (value));
                lua_pop (L, 1);
                ret = true;
            }
        }
        lua_pop (L, 1);
    }
    return ret;
}

static inline GNode *
lua_apteryx_dict2tree (lua_State *L, const char *path, int index)
{
    GNode *root = NULL;
    root = APTERYX_NODE (NULL, (char *) strdup (path));
    lua_pushvalue (L, index); /* Make sure the table is on the top */
    if (!_lua_apteryx_dict2tree (L, root, true))
    {
        apteryx_free_tree (root);
        root = NULL;
    }
    lua_pop (L, 1);
    return root;
}

rest_rpc_error
rest_rpc_execute (int flags, const char *path, GNode *input, GNode **output, char **error_message)
{
    rest_rpc_error rc = REST_RPC_E_NONE;
    GNode *root = NULL;
    lua_State *L = g_ls;

    VERBOSE ("RPC: %s\n", path);

    pthread_mutex_lock (&g_ls_lock);

    GList *entry = rpc_find (flags, path);
    if (entry)
    {
        struct rpc_handler *rpc = (struct rpc_handler *) entry->data;
        int ssize = lua_gettop (L);
        int rcount;

        /* Check this RPC supports the requested operation */
        if (!((flags & FLAGS_METHOD_MASK) & (rpc->flags & FLAGS_METHOD_MASK)))
        {
            pthread_mutex_unlock (&g_ls_lock);
            ERROR ("RPC[%s]: does not support method (flags:0x%08x)\n", rpc->path, flags);
            return REST_RPC_E_NOT_FOUND;
        }

        /* Load rpc function onto the lua stack */
        if (!push_callback (L, rpc->ref))
        {
            pthread_mutex_unlock (&g_ls_lock);
            ERROR ("RPC[%s]: at ref 0x%08x not found\n", rpc->path, rpc->ref);
            return REST_RPC_E_INTERNAL;
        }

        /* Input - without the top level input node */
        if (input)
            lua_apteryx_tree2dict (L, g_node_first_child (input));
        else
            lua_newtable (L);
        /* Path */
        lua_pushstring (L, path);
        if (flags & FLAGS_METHOD_POST)
            lua_pushstring (L, "POST");
        else if (flags & FLAGS_METHOD_GET)
            lua_pushstring (L, "GET");
        else if (flags & FLAGS_METHOD_PUT)
            lua_pushstring (L, "PUT");
        else if (flags & FLAGS_METHOD_PATCH)
            lua_pushstring (L, "PATCH");
        else if (flags & FLAGS_METHOD_DELETE)
            lua_pushstring (L, "DELETE");
        else if (flags & FLAGS_METHOD_HEAD)
            lua_pushstring (L, "HEAD");
        else if (flags & FLAGS_METHOD_OPTIONS)
            lua_pushstring (L, "OPTIONS");

        /* Call RPC */
        int res = lua_pcall (L, 3, LUA_MULTRET, 0);
        if (res != 0)
            rpc_lua_error (L, res);

        /* SUCCESS Lua stack = 1=input(table), 2=true(boolean)
                               1=input(table), 2=output(table)
                               1=input(table), 2=true(boolean), 3=output(table)
           FAILURE Lua stack = 1=input(table), 2=false(boolean), 3=nil
                               1=input(table), 2=false(boolean), 3=message(string)
                               1=input(table), 2=false(boolean), 3=message(string)
         */
        rcount = lua_gettop (L) - 1;
        if (rcount == 1 && lua_isboolean (L, 2))
        {
            if (!lua_toboolean (L, 2))
                rc = REST_RPC_E_FAIL;
            lua_pop (L, 2);
        }
        else if (rcount == 1 && lua_istable (L, 2))
        {
            root = lua_apteryx_dict2tree (L, "output", 2);
            lua_pop (L, 2);
        }
        else if (rcount == 2 && lua_isboolean (L, 2) && lua_toboolean (L, 2) && lua_istable (L, 3))
        {
            root = lua_apteryx_dict2tree (L, "output", 3);
            lua_pop (L, 3);
        }
        else if (rcount == 2 && lua_isboolean (L, 2) && !lua_toboolean (L, 2) && lua_isstring (L, 3))
        {
            *error_message = g_strdup ((char *) lua_tostring (L, 3));
            rc = REST_RPC_E_FAIL;
            lua_pop (L, 3);
        }
        else if (rcount == 2 && lua_isboolean (L, 2) && !lua_toboolean (L, 2) && lua_istable (L, 3))
        {
            root = lua_apteryx_dict2tree (L, "output", 3);
            rc = REST_RPC_E_FAIL;
            lua_pop (L, 3);
        }
        else
        {
            ERROR ("RPC[%s]: did not return a valid response\n", path);
            for (int i = 1; i <= rcount; i++)
                ERROR(" [%d] = %s\n", i, lua_typename (L, lua_type (L, i + 1)));
            while (lua_gettop (L))
                lua_pop (L, 1);
            pthread_mutex_unlock (&g_ls_lock);
            return REST_RPC_E_INTERNAL;
        }

        /* Sanity check the stack */
        if (lua_gettop (L) != ssize)
        {
            ERROR ("RPC[%s]: changed the stack (%d -> %d)\n", path, ssize, lua_gettop (L));
            while (lua_gettop (L))
                lua_pop (L, 1);
        }
    }
    else
    {
        ERROR ("RPC: rpc for path '%s' not found\n", path);
        *error_message = g_strdup_printf ("rpc %s not found", path);
        rc = REST_RPC_E_NOT_FOUND;
    }

    pthread_mutex_unlock (&g_ls_lock);

    *output = root;
    return rc;
}

static void
rpc_push (struct rpc_handler *rpc, int *count)
{
    lua_State *L = g_ls;

    lua_newtable (L);

    /* Methods */
    lua_pushstring (L, "methods");
    lua_newtable (L);
    int nmethods = 1;
    if (rpc->flags & FLAGS_METHOD_GET)
    {
        lua_pushstring (L, "GET");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_POST)
    {
        lua_pushstring (L, "POST");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_PUT)
    {
        lua_pushstring (L, "PUT");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_PATCH)
    {
        lua_pushstring (L, "PATCH");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_DELETE)
    {
        lua_pushstring (L, "DELETE");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_HEAD)
    {
        lua_pushstring (L, "HEAD");
        lua_rawseti (L, -2, nmethods++);
    }
    if (rpc->flags & FLAGS_METHOD_OPTIONS)
    {
        lua_pushstring (L, "OPTIONS");
        lua_rawseti (L, -2, nmethods++);
    }
    lua_settable (L, -3);

    /* Path */
    lua_pushstring (L, "path");
    lua_pushstring (L, rpc->path);
    lua_settable (L, -3);

    lua_rawseti (L, -2, *count);
    (*count)++;
}

bool
rest_rpc_init (const char *path)
{
    struct dirent *entry;
    DIR *dir;

    /* New lua state with a table in the registry to stor callbacks */
    g_ls = luaL_newstate ();
    luaL_openlibs (g_ls);
    lua_pushlightuserdata (g_ls, REST_RPC_CB_TABLE_REGISTRY_INDEX);
    lua_newtable (g_ls);
    lua_settable (g_ls, LUA_REGISTRYINDEX);

    /* Find all the LUA files in this folder */
    dir = opendir (path);
    if (dir == NULL)
    {
        DEBUG ("RPC: No script files in \"%s\"", path);
        return true;
    }

    /* Load and execute all LUA files */
    for (entry = readdir (dir); entry; entry = readdir (dir))
    {
        const char *ext = strrchr (entry->d_name, '.');
        if (ext && strcmp (".lua", ext) == 0)
        {
            char *filename = g_strdup_printf ("%s/%s", path, entry->d_name);
            lua_State *L = g_ls;
            int error;

            DEBUG ("RPC: Load Lua file \"%s\"\n", filename);
            error = luaL_loadfile (L, filename);
            free (filename);
            if (error != 0)
            {
                rpc_lua_error (L, error);
                lua_pop (L, 1); /* Pop filename */
                continue;
            }

            error = lua_pcall (L, 0, 1, 0);
            if (error != 0)
            {
                rpc_lua_error (L, error);
                continue;
            }

            if (lua_gettop (L) != 1 || !lua_istable (L, -1))
            {
                DEBUG ("RPC: \"%s\" did not return a table\n", entry->d_name);
                continue;
            }

            /* Expect table of { path=string, methods={string,}, handler=fn } */
            lua_pushnil (L);
            while (lua_next (L, 1) != 0)
            {
                struct rpc_handler *rpc = g_malloc0 (sizeof (struct rpc_handler));

                /* Parse the handler parameters */
                if (lua_istable (L, 3))
                {
                    if (lua_getfield (L, 3, "path"))
                    {
                        rpc->path = g_strdup (lua_tostring (L, 4));
                        lua_pop (L, 1);
                    }
                    if (lua_getfield (L, 3, "methods"))
                    {
                        lua_pushnil (L);
                        while (lua_next (L, -2) != 0)
                        {
                            if (lua_isstring (L, 6))
                            {
                                const char *method = lua_tostring (L, 6);
                                if (g_strcmp0 (method, "POST") == 0)
                                    rpc->flags |= FLAGS_METHOD_POST;
                                else if (g_strcmp0 (method, "GET") == 0)
                                    rpc->flags |= FLAGS_METHOD_GET;
                                else if (g_strcmp0 (method, "PUT") == 0)
                                    rpc->flags |= FLAGS_METHOD_PUT;
                                else if (g_strcmp0 (method, "PATCH") == 0)
                                    rpc->flags |= FLAGS_METHOD_PATCH;
                                else if (g_strcmp0 (method, "DELETE") == 0)
                                    rpc->flags |= FLAGS_METHOD_DELETE;
                                else if (g_strcmp0 (method, "HEAD") == 0)
                                    rpc->flags |= FLAGS_METHOD_HEAD;
                                else if (g_strcmp0 (method, "OPTIONS") == 0)
                                    rpc->flags |= FLAGS_METHOD_OPTIONS;
                            }
                            lua_pop (L, 1);
                        }
                        lua_pop (L, 1);
                    }
                    if (lua_getfield (L, 3, "handler"))
                    {
                        rpc->ref = ref_callback (L, 4);
                        lua_pop (L, 1);
                    }
                }

                /* Check we have enough info */
                if (rpc->path && rpc->flags && rpc->ref)
                {
                    DEBUG ("    RPC[0x%04x]: %s\n", rpc->flags, rpc->path);
                    g_rpcs = g_list_prepend (g_rpcs, (gpointer) rpc);
                }
                else
                {
                    ERROR ("Failed to parse an RPC handler from %s\n", entry->d_name);
                    if (rpc->path)
                        free (rpc->path);
                    free (rpc);
                }

                lua_pop (L, 1);
            }
            lua_pop (L, 1); /* pop the table */
        }
    }
    (void) closedir (dir);
    g_rpcs = g_list_reverse (g_rpcs);

    /* Push the rpc table to the lua instance */
    int count = 1;
    lua_newtable (g_ls);
    g_list_foreach (g_rpcs, (GFunc) rpc_push, (gpointer) &count);
    lua_setglobal (g_ls, "_RPCS");

    return true;
}

void
rest_rpc_shutdown (void)
{
    g_list_foreach (g_rpcs, (GFunc) rpc_free, NULL);
    if (g_ls)
    {
        lua_close (g_ls);
        g_ls = NULL;
    }
}
