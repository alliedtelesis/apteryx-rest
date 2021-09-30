/**
 * @file fcgi.c
 * FastCGI handler for Apteryx-rest
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
#include <sys/socket.h>
#include <fcgi_config.h>
#include <fcgiapp.h>

static http_callback g_cb;
static const char *g_socket = NULL;
static int g_sock = -1;
static GThread *g_thread = NULL;

static inline void
dump_param (FCGX_Request * r, char *e)
{
    char *p = FCGX_GetParam (e, r->envp);
    if (p)
        VERBOSE ("%s = '%s'\n", e, p);
}

static void
dump_request (FCGX_Request * r)
{
    VERBOSE ("Status: 200\r\n");
    VERBOSE ("Content-Type: text/html\r\n\r\n");
    dump_param (r, "QUERY_STRING");
    dump_param (r, "REQUEST_METHOD");
    dump_param (r, "CONTENT_TYPE");
    dump_param (r, "CONTENT_LENGTH");
    dump_param (r, "SCRIPT_FILENAME");
    dump_param (r, "SCRIPT_NAME");
    dump_param (r, "REQUEST_URI");
    dump_param (r, "DOCUMENT_URI");
    dump_param (r, "DOCUMENT_ROOT");
    dump_param (r, "SERVER_PROTOCOL");
    dump_param (r, "GATEWAY_INTERFACE");
    dump_param (r, "SERVER_SOFTWARE");
    dump_param (r, "REMOTE_ADDR");
    dump_param (r, "REMOTE_PORT");
    dump_param (r, "SERVER_ADDR");
    dump_param (r, "SERVER_PORT");
    dump_param (r, "SERVER_NAME");
    dump_param (r, "HTTP_COOKIE");
    dump_param (r, "HTTPS");
    dump_param (r, "HTTP_ACCEPT");
    dump_param (r, "HTTP_CONTENT_TYPE");
    dump_param (r, "HTTP_AUTHORIZATION");
    return;
}

static int
get_flags (FCGX_Request * r)
{
    int flags = 0;
    char *param;

    /* Parse content type */
    param = FCGX_GetParam ("HTTP_CONTENT_TYPE", r->envp);
    if (param)
    {
        if (g_strcmp0 (param, "application/json") == 0)
            flags |= FLAGS_CONTENT_JSON;
        if (g_strcmp0 (param, "application/yang.data+json") == 0)
            flags |= FLAGS_CONTENT_JSON;
        if (g_strcmp0 (param, "application/xml") == 0)
            flags |= FLAGS_CONTENT_XML;
        if (g_strcmp0 (param, "application/yang.data+xml") == 0)
            flags |= FLAGS_CONTENT_XML;
    }

    /* Parse accept types */
    param = FCGX_GetParam ("HTTP_ACCEPT", r->envp);
    if (param)
    {
        if (g_strrstr (param, "application/json") != 0)
            flags |= FLAGS_ACCEPT_JSON;
        if (g_strrstr (param, "application/yang.data+json") != 0)
            flags |= FLAGS_ACCEPT_JSON;
        if (g_strrstr (param, "application/xml") != 0)
            flags |= FLAGS_ACCEPT_XML;
        if (g_strrstr (param, "application/yang.data+xml") != 0)
            flags |= FLAGS_ACCEPT_XML;
        if (g_strrstr (param, "*/*") != 0)
            flags |= (FLAGS_ACCEPT_JSON | FLAGS_ACCEPT_XML);
    }

    /* JSON formatinng */
    param = FCGX_GetParam ("HTTP_X_JSON_ROOT", r->envp);
    flags |= FLAGS_JSON_FORMAT_ROOT;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_ROOT;      
    param = FCGX_GetParam ("HTTP_X_JSON_MULTI", r->envp);
    if (param && strcmp (param, "on") == 0)
        flags |= FLAGS_JSON_FORMAT_MULTI;
    /* Format lists as JSON arrays */
    if (rest_use_arrays)
        flags |= FLAGS_JSON_FORMAT_ARRAYS;
    param = FCGX_GetParam ("HTTP_X_JSON_ARRAY", r->envp);
    if (param && strcmp (param, "on") == 0)
        flags |= FLAGS_JSON_FORMAT_ARRAYS;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_ARRAYS;
    /* Encode values as JSON types */
    if (rest_use_types)
        flags |= FLAGS_JSON_FORMAT_TYPES;
    param = FCGX_GetParam ("HTTP_X_JSON_TYPES", r->envp);
    if (param && strcmp (param, "on") == 0)
        flags |= FLAGS_JSON_FORMAT_TYPES;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_TYPES;

    return flags;
}

static void *
handle_http (void *arg)
{
    FCGX_Request *request = (FCGX_Request *)arg;
    char *path, *action, *length, *if_none_match;
    int flags;
    char *data = NULL;
    int len = 0;
    char *resp;
    int i;

    /* Debug */
    if (verbose)
    {
        dump_request (request);
    }

    /* Process the request */
    path = FCGX_GetParam ("REQUEST_URI", request->envp);
    flags = get_flags (request);
    if_none_match = FCGX_GetParam ("If-None-Match", request->envp);
    action = FCGX_GetParam ("REQUEST_METHOD", request->envp);
    length = FCGX_GetParam ("CONTENT_LENGTH", request->envp);
    if (length != NULL)
    {
        len = strtol (length, NULL, 10);
        data = calloc (len + 1, 1);
        for (i = 0; i < len; i++)
        {
            if ((data[i] = FCGX_GetChar (request->in)) < 0)
            {
                ERROR ("ERROR: Not enough bytes received on standard input\n");
                break;
            }
        }
    }
    resp = g_cb (flags, path, action, if_none_match, data, len);
    free (data);

    /* Send the response */
    if (!resp)
    {
        resp = g_strdup_printf ("Status: 404\r\n"
                                "Content-Type: text/html\r\n\r\n"
                                "The requested URL %s was not found on this server.\n",
                                path);
    }
    FCGX_PutS (resp, request->out);
    free (resp);
    FCGX_Finish_r (request);
    g_free (request);

    return NULL;
}

static void *
handle_fcgi (void *arg)
{
    GThreadPool *workers = g_thread_pool_new ((GFunc)handle_http, NULL, -1, FALSE, NULL);
    while (workers)
    {
        FCGX_Request *request = g_malloc0 (sizeof (FCGX_Request));
        FCGX_InitRequest (request, g_sock, FCGI_FAIL_ACCEPT_ON_INTR);
        if (FCGX_Accept_r (request) < 0)
        {
            DEBUG ("FCGX_Accept_r: %s\n", strerror (errno));
            g_free (request);
            break;
        }
        DEBUG ("New FCGI connection\n");
        g_thread_pool_push (workers, request, NULL);
    }
    DEBUG ("Stopping FCGI handler\n");
    g_thread_pool_free (workers, true, false);
    return NULL;
}

bool
fcgi_start (const char *socket, http_callback cb)
{
    DEBUG ("Starting FCGI handler on %s\n", socket);
    g_socket = socket;
    g_cb = cb;

    /* Initialise the fastcgi library */
    if (FCGX_Init () != 0)
    {
        ERROR ("FCGX_Init failed: %s\n", strerror (errno));
        return false;
    }

    /* Open the user provided socket */
    if ((g_sock = FCGX_OpenSocket (g_socket, 10)) < 0)
    {
        ERROR ("FCGX_OpenSocket failed: %s\n", strerror (errno));
        return false;
    }

    /* Create a thread to handle requests */
    if ((g_thread = g_thread_new ("fcgi handler", &handle_fcgi, NULL)) == NULL)
    {
        ERROR ("Failed to launch FCGI handler thread\n");
        return false;
    }

    return true;
}

void
fcgi_stop (void)
{
    /* Shutdown any pending requests */
    FCGX_ShutdownPending ();

    /* Shutdown the socket */
    if (g_sock != -1)
    {
        shutdown (g_sock, SHUT_RD);
        unlink (g_socket);
    }

    /* Wait for the thread to complete */
    g_thread_join (g_thread);
}
