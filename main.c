/**
 * @file main.c
 * Entry point for apteryx-rest
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
#include <glib-unix.h>

/* Mainloop handle */
GMainLoop *g_loop = NULL;

/* Global schema */
sch_instance *g_schema = NULL;

/* Debug */
bool debug = false;
bool verbose = false;

static gboolean
termination_handler (gpointer arg1)
{
    GMainLoop *loop = (GMainLoop *) arg1;
    g_main_loop_quit (loop);
    return false;
}

void
help (char *app_name)
{
    printf ("Usage: %s [-h] [-b] [-d] [-v] [-m <path>] [-p <pidfile>]\n"
            "                [-n] [-l <port>] [-k <key>]\n"
            "                [-r] [-s <socket>]\n"
            "  -h   show this help\n"
            "  -b   background mode\n"
            "  -d   enable debug\n"
            "  -v   enable verbose debug\n"
            "  -m   search <path> for modules\n"
            "  -p   use <pidfile> (defaults to " DEFAULT_APP_PID ")\n"
            "  -s   rest socket <socket> (defaults to " DEFAULT_REST_SOCK ")\n", app_name);
}

int
main (int argc, char *argv[])
{
    const char *path = NULL;
    const char *pid_file = DEFAULT_APP_PID;
    const char *socket = DEFAULT_REST_SOCK;
    int i = 0;
    bool background = false;
    FILE *fp = NULL;
    int rc = EXIT_SUCCESS;

    /* Parse options */
    while ((i = getopt (argc, argv, "bdvm:s:p:h")) != -1)
    {
        switch (i)
        {
        case 'b':
            background = true;
            break;
        case 'd':
            debug = true;
            break;
        case 'v':
            debug = true;
            verbose = true;
            break;
        case 'm':
            path = optarg;
            break;
        case 's':
            socket = optarg;
            break;
        case 'p':
            pid_file = optarg;
            break;
        case '?':
        case 'h':
        default:
            help (argv[0]);
            return 0;
        }
    }

    /* Daemonize */
    if (background && fork () != 0)
    {
        /* Parent */
        return 0;
    }

    /* Create GLib loop early */
    g_loop = g_main_loop_new (NULL, true);

    /* Initialise Apteryx client library */
    apteryx_init (verbose);

    /* Initialse XML library */
    g_schema = sch_load (path);
    if (!g_schema)
    {
        ERROR ("ERROR: Failed to load modules at path \"%s\"\n", path);
        rc = EXIT_FAILURE;
        goto exit;
    }

    /* Create pid file */
    if (background)
    {
        fp = fopen (pid_file, "w");
        if (!fp)
        {
            ERROR ("ERROR: Failed to create PID file %s\n", pid_file);
            rc = EXIT_FAILURE;
            goto exit;
        }
        fprintf (fp, "%d\n", getpid ());
        fclose (fp);
    }

    /* Start FCGI */
    if (!fcgi_start (socket, rest_api))
    {
        rc = EXIT_FAILURE;
        goto exit;
    }

    /* GLib main loop with graceful termination */
    g_unix_signal_add (SIGINT, termination_handler, g_loop);
    g_unix_signal_add (SIGTERM, termination_handler, g_loop);
    signal (SIGPIPE, SIG_IGN);
    g_main_loop_run (g_loop);

  exit:

    /* Cleanup FCGI */
    fcgi_stop ();

    /* Cleanup client library */
    apteryx_shutdown ();

    /* GLib main loop is done */
    g_main_loop_unref (g_loop);

    /* Remove the pid file */
    if (background)
        unlink (pid_file);

    return rc;
}
