/**
 * @file logging.c
 * Handler of the logging configuration file
 *
 * Copyright 2024, Allied Telesis Labs New Zealand, Ltd
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
#include <sys/inotify.h>

#define READ_BUF_SIZE 512

static int inotify_fd = -1;
static GIOChannel *channel = NULL;
static char *logging_filename = NULL;

/* Logging flags */
int logging = LOG_NONE;

static int
load_logging_options (void)
{
    FILE *fp = NULL;
    gchar **split;
    char *buf;
    int count;
    int i;
    logging_flags flags = LOG_NONE;
    int ret = 0;

    buf = g_malloc0 (READ_BUF_SIZE);
    fp = fopen (logging_filename, "r");
    if (fp && buf)
    {
        if (fgets (buf, READ_BUF_SIZE, fp) != NULL)
        {
            /* Remove any trailing LF */
            buf[strcspn(buf, "\n")] = '\0';
            split = g_strsplit (buf, " ", 6);
            count = g_strv_length (split);
            for (i = 0; i < count; i++)
            {
                if (g_strcmp0 (split[i], "post") == 0)
                    flags |= LOG_POST;
                else if (g_strcmp0 (split[i], "put") == 0)
                    flags |= LOG_PUT;
                else if (g_strcmp0 (split[i], "patch") == 0)
                    flags |= LOG_PATCH;
                else if (g_strcmp0 (split[i], "delete") == 0)
                    flags |= LOG_DELETE;
                else if (g_strcmp0 (split[i], "get") == 0)
                    flags |= LOG_GET;
                else if (g_strcmp0 (split[i], "head") == 0)
                    flags |= LOG_HEAD;
            }
            g_strfreev (split);
        }
        fclose (fp);
    }
    else
    {
        ret = -1;
    }
    g_free (buf);
    logging = flags;

    return ret;
}

/**
 * Handles an inotify event indicating that the logging options file may have
 * been modified and reloads the logging options in the file if necessary
 */
static int
logging_file_update (void)
{
    char *buf;
    int len;
    int ret = -1;

    /* Got a notify event informing the logging file has been modified */
    if (inotify_fd >= 0)
    {
        buf = g_malloc0 (READ_BUF_SIZE);
        len = read (inotify_fd, buf, READ_BUF_SIZE);
        if (len)
            ret = load_logging_options ();

        g_free (buf);
    }

    return ret;
}

static gboolean
logging_options_reload (GIOChannel *source, GIOCondition condition, gpointer data)
{
    logging_file_update ();
    return TRUE;
}

static int
logging_open_inotify (void)
{
    if (inotify_fd < 0)
    {
        /* inotify doesn't tell us about creation of the tracelog_control file
         * unless we listen to inotify events for the whole directory */
        inotify_fd = inotify_init ();
        inotify_add_watch (inotify_fd, logging_filename,
                           IN_MODIFY | IN_DELETE | IN_MOVE);
    }

    return inotify_fd;
}

void
logging_shutdown (void)
{
    if (inotify_fd >= 0)
        close (inotify_fd);

    if (channel)
        g_io_channel_shutdown (channel, false, NULL);

    if (logging_filename)
        g_free (logging_filename);
}

int
logging_init (const char *path, const char *logging_arg)
{
    if (!path || !logging_arg)
        return -1;

    logging_filename = g_strdup_printf ("%s/%s", path, logging_arg);

    /* Read the current setting */
    if (load_logging_options () < 0)
        return -1;

    /* Add an inotify watch for logging changes */
    if (logging_open_inotify () < 0)
        return -1;

    channel = g_io_channel_unix_new (logging_open_inotify ());
    g_io_add_watch (channel, G_IO_IN, logging_options_reload, NULL);

    openlog ("restconf", LOG_PID | LOG_NDELAY, LOG_USER);

    return 0;
}
