/**
 * @file fcgi.c
 * FastCGI handler for Apteryx-rest
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
#include <sys/socket.h>
#include <poll.h>
#undef PACKAGE
#undef VERSION
#include <fcgi_config.h>
#include <fcgiapp.h>

static req_callback g_cb;
static const char *g_socket = NULL;
static int g_sock = -1;
static GThread *g_thread = NULL;

static void
dump_request (FCGX_Request * r)
{
    char **envp = r->envp;
    VERBOSE ("FCGI_PARAMS:\n");
    while (envp && *envp) {
        VERBOSE ("%s\n", *envp);
        envp++;
    }
    return;
}

static int
get_flags (FCGX_Request * r)
{
    int flags = 0;
    char *param;

    /* Method */
    param = FCGX_GetParam ("REQUEST_METHOD", r->envp);
    if (g_strcmp0 (param, "GET") == 0)
        flags |= FLAGS_METHOD_GET;
    else if (g_strcmp0 (param, "POST") == 0)
        flags |= FLAGS_METHOD_POST;
    else if (g_strcmp0 (param, "PUT") == 0)
        flags |= FLAGS_METHOD_PUT;
    else if (g_strcmp0 (param, "PATCH") == 0)
        flags |= FLAGS_METHOD_PATCH;
    else if (g_strcmp0 (param, "DELETE") == 0)
        flags |= FLAGS_METHOD_DELETE;
    else if (g_strcmp0 (param, "HEAD") == 0)
        flags |= FLAGS_METHOD_HEAD;
    else if (g_strcmp0 (param, "OPTIONS") == 0)
        flags |= FLAGS_METHOD_OPTIONS;
    else
    {
        ERROR ("Method \"%s\" not allowed\n", param);
        return -405;
    }

    /* Parse content type */
    param = FCGX_GetParam ("HTTP_CONTENT_TYPE", r->envp);
    if (!param)
        param = FCGX_GetParam ("CONTENT_TYPE", r->envp);
    if (param)
    {
        if (g_strcmp0 (param, "application/json") == 0)
            flags |= FLAGS_CONTENT_JSON;
        else if (g_strcmp0 (param, "application/yang-data+json") == 0)
            flags |= FLAGS_CONTENT_JSON | FLAGS_RESTCONF;
        // else if (g_strcmp0 (param, "application/xml") == 0)
        //     flags |= FLAGS_CONTENT_XML;
        // else if (g_strcmp0 (param, "application/yang.data+xml") == 0)
        //     flags |= FLAGS_CONTENT_XML | FLAGS_RESTCONF;
        else
        {
            ERROR ("Media-Type \"%s\" not allowed\n", param);
            return -415;
        }
    }
    else if (flags & (FLAGS_METHOD_POST|FLAGS_METHOD_PUT|FLAGS_METHOD_PATCH))
    {
        /* Assume default encoding */
        flags |= default_content_encoding;
    }

    /* Parse accept types */
    param = FCGX_GetParam ("HTTP_ACCEPT", r->envp);
    if (param)
    {
        if (g_strrstr (param, "application/json") != 0)
            flags |= FLAGS_ACCEPT_JSON;
        else if (g_strrstr (param, "application/yang-data+json") != 0)
            flags |= FLAGS_ACCEPT_JSON | FLAGS_RESTCONF;
        // if (g_strrstr (param, "application/xml") != 0)
        //     flags |= FLAGS_ACCEPT_XML;
        // if (g_strrstr (param, "application/yang-data+xml") != 0)
        //     flags |= FLAGS_ACCEPT_XML | FLAGS_RESTCONF;
        else if (g_strrstr (param, "text/event-stream") != 0)
            flags |= FLAGS_EVENT_STREAM | FLAGS_ACCEPT_JSON;
        else if (g_strrstr (param, "application/stream+json") != 0)
            flags |= FLAGS_APPLICATION_STREAM | FLAGS_ACCEPT_JSON;
        /* Any encoding - use default */
        else if (g_strrstr (param, "*/*") != 0)
            flags |= default_accept_encoding;
        else
        {
            ERROR ("Media-Type \"%s\" not allowed\n", param);
            return -415;
        }
    }

    /* JSON formatinng */
    param = FCGX_GetParam ("HTTP_X_JSON_ROOT", r->envp);
    if (!param)
        param = FCGX_GetParam ("HTTP_X-JSON_Root", r->envp);
    flags |= FLAGS_JSON_FORMAT_ROOT;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_ROOT;
    param = FCGX_GetParam ("HTTP_X_JSON_MULTI", r->envp);
    if (!param)
        param = FCGX_GetParam ("HTTP_X-JSON-Multi", r->envp);
    if (param && strcmp (param, "on") == 0)
        flags |= FLAGS_JSON_FORMAT_MULTI;
    /* Format lists as JSON arrays */
    if (rest_use_arrays)
        flags |= FLAGS_JSON_FORMAT_ARRAYS;
    param = FCGX_GetParam ("HTTP_X_JSON_ARRAY", r->envp);
    if (!param)
        param = FCGX_GetParam ("HTTP_X-JSON-Array", r->envp);
    if (flags & FLAGS_RESTCONF || (param && strcmp (param, "on") == 0))
        flags |= FLAGS_JSON_FORMAT_ARRAYS;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_ARRAYS;
    /* Encode values as JSON types */
    if (rest_use_types)
        flags |= FLAGS_JSON_FORMAT_TYPES;
    param = FCGX_GetParam ("HTTP_X_JSON_TYPES", r->envp);
    if (!param)
        param = FCGX_GetParam ("HTTP_X-JSON-Types", r->envp);
    if (flags & FLAGS_RESTCONF || (param && strcmp (param, "on") == 0))
        flags |= FLAGS_JSON_FORMAT_TYPES;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_TYPES;
    /* Prefix model names */
    param = FCGX_GetParam ("HTTP_X_JSON_NAMESPACE", r->envp);
    if (!param)
        param = FCGX_GetParam ("HTTP_X-JSON-Namespace", r->envp);
    if (flags & FLAGS_RESTCONF || (param && strcmp (param, "on") == 0))
        flags |= FLAGS_JSON_FORMAT_NS;
    if (param && strcmp (param, "off") == 0)
        flags &= ~FLAGS_JSON_FORMAT_NS;

    return flags;
}

static void *
handle_http (void *arg)
{
    FCGX_Request *request = (FCGX_Request *) arg;
    char *rpath, *path, *length, *if_match, *if_none_match, *if_modified_since, *if_unmodified_since;
    int flags;
    char *data = NULL;
    int len = 0;
    int i;
    int rc = 0;

    DEBUG ("FCGI(%p): New connection\n", request);

    /* Debug */
    if (verbose)
    {
        dump_request (request);
    }

    /* Process the request */
    rpath = FCGX_GetParam ("DOCUMENT_ROOT", request->envp);
    path = FCGX_GetParam ("REQUEST_URI", request->envp);
    flags = get_flags (request);
    if (flags < 0)
    {
        rc = -(flags);
        goto exit;
    }
    if_match = FCGX_GetParam ("HTTP_IF_MATCH", request->envp);
    if_none_match = FCGX_GetParam ("HTTP_IF_NONE_MATCH", request->envp);
    if_modified_since = FCGX_GetParam ("HTTP_IF_MODIFIED_SINCE", request->envp);
    if_unmodified_since = FCGX_GetParam ("HTTP_IF_UNMODIFIED_SINCE", request->envp);
    length = FCGX_GetParam ("CONTENT_LENGTH", request->envp);
    if (!rpath || !path)
    {
        ERROR ("Invalid server configuration (flags:0x%x, rpath:%s, path:%s)\n",
               flags, rpath, path);
        rc = 500;
        goto exit;
    }
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
    g_cb ((req_handle) request, flags, rpath, path, if_match, if_none_match, if_modified_since, if_unmodified_since, data, len);

exit:
    if (rc)
    {
        char *resp = g_strdup_printf ("Status: %d\r\n"
                                      "Content-Type: text/html\r\n\r\n"
                                      "Error. Check device log for more detail\n",
                                      rc);
        VERBOSE ("RESP:\n%s\n", resp);
        send_response (request, resp, false);
        free (resp);
    }
    free (data);
    DEBUG ("FCGI(%p): Closing connection\n", request);
    FCGX_Finish_r (request);
    g_free (request);
    return NULL;
}

static void *
handle_fcgi (void *arg)
{
    GThreadPool *workers = g_thread_pool_new ((GFunc) handle_http, NULL, -1, FALSE, NULL);
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
        g_thread_pool_push (workers, request, NULL);
    }
    DEBUG ("Stopping FCGI handler\n");
    g_thread_pool_free (workers, true, false);
    return NULL;
}

bool
fcgi_start (const char *socket, req_callback cb)
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
send_response (req_handle handle, const char *data, bool flush)
{
    FCGX_Request *request = (FCGX_Request *) handle;
    DEBUG ("FCGI(%p): send %lu bytes\n", request, strlen (data));
    FCGX_PutS (data, request->out);
    if (flush)
        FCGX_FFlush (request->out);
}

bool
is_connected (req_handle handle, bool block)
{
    FCGX_Request *request = (FCGX_Request *) handle;
    struct pollfd pfd;
    pfd.fd = request->ipcFd;
    pfd.events = POLLERR | POLLHUP;
    pfd.revents = 0;
    poll (&pfd, 1, block ? -1 : 1000);
    if (pfd.revents & (POLLERR | POLLHUP))
        return false;
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
