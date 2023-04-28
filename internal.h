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
#include <stdbool.h>
#include <string.h>
#include <sys/sysinfo.h>
#include <syslog.h>
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

/* HTTP handler for rest */
#define FLAGS_METHOD_POST           (1 << 0)
#define FLAGS_METHOD_GET            (1 << 1)
#define FLAGS_METHOD_PUT            (1 << 2)
#define FLAGS_METHOD_PATCH          (1 << 3)
#define FLAGS_METHOD_DELETE         (1 << 4)
#define FLAGS_METHOD_HEAD           (1 << 5)
#define FLAGS_METHOD_OPTIONS        (1 << 6)
#define FLAGS_CONTENT_JSON          (1 << 7)
#define FLAGS_CONTENT_XML           (1 << 8)
#define FLAGS_ACCEPT_JSON           (1 << 9)
#define FLAGS_ACCEPT_XML            (1 << 10)
#define FLAGS_JSON_FORMAT_ARRAYS    (1 << 11)
#define FLAGS_JSON_FORMAT_ROOT      (1 << 12)
#define FLAGS_JSON_FORMAT_MULTI     (1 << 13)
#define FLAGS_JSON_FORMAT_TYPES     (1 << 14)
#define FLAGS_EVENT_STREAM          (1 << 15)
#define FLAGS_APPLICATION_STREAM    (1 << 16)
#define FLAGS_RESTCONF              (1 << 17)
typedef void *req_handle;
void send_response (req_handle handle, const char *data, bool flush);
bool is_connected (req_handle handle, bool block);
typedef void (*req_callback) (req_handle handle, int flags, const char *rpath, const char *path,
                              const char *if_match, const char *if_none_match,
                              const char *if_modified_since, const char *if_unmodified_since,
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
               const char *data, int length);
void rest_shutdown (void);

#endif /* _REST_H_ */
