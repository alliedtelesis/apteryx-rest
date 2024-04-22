/**
 * @file main.c
 * Entry point for apteryx-rest
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
#include <glib-unix.h>

/* Mainloop handle */
GMainLoop *g_loop = NULL;

/* Debug */
bool debug = false;
bool verbose = false;

/* Format modes */
int default_accept_encoding = FLAGS_ACCEPT_JSON;
int default_content_encoding = FLAGS_CONTENT_JSON;
bool rest_use_arrays = false;
bool rest_use_types = false;

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
    printf ("Usage: %s [-h] [-b] [-d] [-v] [-a] [-t] [-m <path>] [-p <pidfile>]\n"
            "                [-n] [-l <port>] [-k <key>]\n"
            "                [-r] [-s <socket>] [-e <encoding>]\n"
            "  -h   show this help\n"
            "  -b   background mode\n"
            "  -d   enable debug\n"
            "  -v   enable verbose debug\n"
            "  -e   set default data encoding (defaults to \"application/json\")\n"
            "  -a   enable the use of JSON arrays for lists\n"
            "  -t   encode values as JSON types where possible\n"
            "  -m   search <path> for modules\n"
            "  -n   name of a file containing a list of supported models\n"
            "  -p   use <pidfile> (defaults to " DEFAULT_APP_PID ")\n"
            "  -s   rest socket <socket> (defaults to " DEFAULT_REST_SOCK ")\n", app_name);
}

int
main (int argc, char *argv[])
{
    const char *path = "./";
    const char *pid_file = DEFAULT_APP_PID;
    const char *socket = DEFAULT_REST_SOCK;
    int i = 0;
    bool background = false;
    char *supported = NULL;
    FILE *fp = NULL;
    int rc = EXIT_SUCCESS;

    /* Parse options */
    while ((i = getopt (argc, argv, "bdvatm:n:s:p:e:h")) != -1)
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
        case 'e':
            if (g_strcmp0 (optarg, "application/json") == 0)
            {
                default_content_encoding = FLAGS_CONTENT_JSON;
                default_accept_encoding = FLAGS_ACCEPT_JSON;
            }
            else if (g_strcmp0 (optarg, "application/yang-data+json") == 0)
            {
                default_content_encoding = FLAGS_CONTENT_JSON | FLAGS_RESTCONF;
                default_accept_encoding = FLAGS_ACCEPT_JSON | FLAGS_RESTCONF;
            }
            else
            {
                printf ("ERROR: Expect one of \"application/json\", \"application/yang-data+json\"\n");
                help (argv[0]);
                return 0;
            }
            break;
        case 'a':
            rest_use_arrays = true;
            break;
        case 't':
            rest_use_types = true;
            break;
        case 'm':
            path = optarg;
            break;
        case 'n':
            supported = optarg;
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

    /* Don't buffer stout */
    setvbuf (stdout, NULL, _IONBF, BUFSIZ);

    /* Create GLib loop early */
    g_loop = g_main_loop_new (NULL, true);

    /* Initialise Apteryx client library */
    apteryx_init (verbose);

    /* Initialise rest */
    if (!rest_init (path, supported))
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

    /* Cleanup rest */
    rest_shutdown ();

    /* Cleanup client library */
    apteryx_shutdown ();

    /* GLib main loop is done */
    g_main_loop_unref (g_loop);

    /* Remove the pid file */
    if (background)
        unlink (pid_file);

    return rc;
}
