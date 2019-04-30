/**
 * @file internal.h
 * Internal header for apteryx-rest.
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
#ifndef _REST_H_
#define _REST_H_
#include <stdio.h>
#include <assert.h>
#include <stdbool.h>
#include <inttypes.h>
#include <string.h>
#include <sys/socket.h>
#include <syslog.h>
#include <glib.h>
#include <glib-unix.h>
#include <apteryx.h>
#include <apteryx-xml.h>

/* Defaults */
#define APP_NAME                    "apteryx-rest"
#define DEFAULT_APP_PID             "/var/run/"APP_NAME".pid"
#define DEFAULT_REST_SOCK           "/var/run/"APP_NAME".sock"
#define REST_API_PATH               "/api"

/* Helper */
#define STR_HELPER(x) #x
#define STR(x) STR_HELPER(x)

/* GLib Main Loop */
extern GMainLoop *g_loop;

/* Global schema */
extern sch_instance *g_schema;

/* Debug */
extern bool debug;
extern bool verbose;
#define VERBOSE(fmt, args...) if (verbose) printf (fmt, ## args)
#define DEBUG(fmt, args...) if (debug) printf (fmt, ## args)
#define INFO(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_INFO, fmt, ## args); }
#define NOTICE(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_NOTICE, fmt, ## args); }
#define ERROR(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_CRIT, fmt, ## args); }
#define FATAL(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_CRIT, fmt, ## args); g_main_loop_quit (g_loop); }
#define ASSERT(assertion, rcode, fmt, args...) { \
    if (!(assertion)) { \
        if (debug) printf (fmt, ## args); \
        else syslog (LOG_CRIT, fmt, ## args); \
        g_main_loop_quit (g_loop); \
        rcode; \
    } \
}

/* HTTP handler for rest */
#define FLAGS_CONTENT_JSON       (1 << 0)
#define FLAGS_CONTENT_XML        (1 << 1)
#define FLAGS_ACCEPT_JSON        (1 << 2)
#define FLAGS_ACCEPT_XML         (1 << 3)
typedef char* (*http_callback) (int flags, const char *path, const char *action, const char *data, int length);

/* FastCGI */
bool fcgi_start (const char *socket, http_callback cb);
void fcgi_stop (void);

/* Rest */
char* rest_api (int flags, const char *path, const char *action, const char *data, int length);

#endif /* _REST_H_ */
