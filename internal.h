/**
 * @file internal.h
 * Internal header for apteryx-rest.
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
#ifndef _REST_H_
#define _REST_H_
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>
#include <ctype.h>
#include <stdbool.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <syslog.h>
#include <assert.h>
#include <apteryx.h>
#define APTERYX_XML_JSON
#include <apteryx-xml.h>

/* Defaults */
#define APP_NAME                    "apteryx-rest"
#define DEFAULT_APP_PID             "/var/run/"APP_NAME".pid"
#define DEFAULT_REST_SOCK           "/var/run/"APP_NAME".sock"

/* Debug */
extern bool debug;
extern bool verbose;
#define VERBOSE(fmt, args...) if (verbose) printf (fmt, ## args)
#define DEBUG(fmt, args...) if (debug) printf (fmt, ## args)
#define INFO(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_INFO, fmt, ## args); }
#define NOTICE(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_NOTICE, fmt, ## args); }
#define ERROR(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_CRIT, fmt, ## args); }

/* For very long logging lines split the output message up. */
#define LOG_CHUNK 128
#define LOG_FLEX 24

typedef enum
{
    LOG_NONE                    = 0,
    LOG_POST                    = (1 << 0),  /* Log POST requests */
    LOG_PUT                     = (1 << 1),  /* Log PUT requests */
    LOG_PATCH                   = (1 << 2),  /* Log PATCH requests */
    LOG_DELETE                  = (1 << 3),  /* Log DELETE requests */
    LOG_GET                     = (1 << 4),  /* Log GET requests */
    LOG_HEAD                    = (1 << 5),  /* Log HEAD requests */
} logging_flags;

/* HTTP handler for rest */
#define FLAGS_METHOD_POST           (1 << 0)
#define FLAGS_METHOD_GET            (1 << 1)
#define FLAGS_METHOD_PUT            (1 << 2)
#define FLAGS_METHOD_PATCH          (1 << 3)
#define FLAGS_METHOD_DELETE         (1 << 4)
#define FLAGS_METHOD_HEAD           (1 << 5)
#define FLAGS_METHOD_OPTIONS        (1 << 6)
#define FLAGS_METHOD_MASK           ((1 << 7) - 1)
#define FLAGS_CONTENT_JSON          (1 << 7)
#define FLAGS_CONTENT_XML           (1 << 8)
#define FLAGS_ACCEPT_JSON           (1 << 9)
#define FLAGS_ACCEPT_XML            (1 << 10)
#define FLAGS_JSON_FORMAT_ARRAYS    (1 << 11)
#define FLAGS_JSON_FORMAT_ROOT      (1 << 12)
#define FLAGS_JSON_FORMAT_MULTI     (1 << 13)
#define FLAGS_JSON_FORMAT_TYPES     (1 << 14)
#define FLAGS_JSON_FORMAT_NS        (1 << 15)
#define FLAGS_EVENT_STREAM          (1 << 16)
#define FLAGS_APPLICATION_STREAM    (1 << 17)
#define FLAGS_RESTCONF              (1 << 18)
#define FLAGS_CONDITIONS            (1 << 19)
#define FLAGS_IDREF_VALUES          (1 << 20)
#define FLAGS_PUT_KEY_VALUE_DATA    (1 << 21)   /* PUT data must be a key:value object */
#define FLAGS_PUT_REPLACE           (1 << 22)   /* PUT data replaces current contents */
#define FLAGS_CONFIG_ONLY           (1 << 23)   /* DELETE config only nodes */
extern int default_accept_encoding;
extern int default_content_encoding;
typedef void *req_handle;
void send_response (req_handle handle, const char *data, bool flush);
bool is_connected (req_handle handle, bool block);
typedef void (*req_callback) (req_handle handle, int flags, const char *rpath, const char *path,
                              const char *if_match, const char *if_none_match,
                              const char *if_modified_since, const char *if_unmodified_since,
                              const char *server_name, const char *server_port,
                              const char *remote_addr, const char *remote_user,
                              const char *data, int length);

/* FastCGI */
bool fcgi_start (const char *socket, req_callback cb);
void fcgi_stop (void);

/* Rest */
extern bool rest_use_arrays;
extern bool rest_use_types;
gboolean rest_init (const char *path);
void rest_api (req_handle handle, int flags, const char *rpath, const char *path,
               const char *if_match, const char *if_none_match,
               const char *if_modified_since, const char *if_unmodified_since,
               const char *server_name, const char *server_port,
               const char *remote_addr, const char *remote_user,
               const char *data, int length);
void rest_shutdown (void);
void yang_library_create (sch_instance *schema);
void restconf_monitoring_create (sch_instance *schema);

/* RPC */
typedef enum
{
    REST_RPC_E_NONE,
    REST_RPC_E_FAIL,
    REST_RPC_E_NOT_FOUND,
    REST_RPC_E_INTERNAL,
} rest_rpc_error;
bool rest_rpc_init (const char *path);
rest_rpc_error rest_rpc_execute (int flags, const char *path, GNode *input, GNode **output, char **error_message);
void rest_rpc_shutdown (void);

/* Logging */
extern int logging;

void logging_shutdown (void);
int logging_init (const char *path, const char *logging_arg);

#endif /* _REST_H_ */
