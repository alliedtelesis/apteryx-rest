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
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>
#include <stdbool.h>
#include <string.h>
#include <syslog.h>
#include <apteryx.h>

/* Defaults */
#define APP_NAME                    "apteryx-rest"
#define DEFAULT_APP_PID             "/var/run/"APP_NAME".pid"
#define DEFAULT_REST_SOCK           "/var/run/"APP_NAME".sock"
#define REST_API_PATH               "/api"

/* Debug */
extern bool debug;
extern bool verbose;
#define VERBOSE(fmt, args...) if (verbose) printf (fmt, ## args)
#define DEBUG(fmt, args...) if (debug) printf (fmt, ## args)
#define INFO(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_INFO, fmt, ## args); }
#define NOTICE(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_NOTICE, fmt, ## args); }
#define ERROR(fmt, args...) { if (debug) printf (fmt, ## args); else syslog (LOG_CRIT, fmt, ## args); }

/* Schema */
typedef void sch_node;
bool sch_load (const char *path);
void sch_unload (void);
sch_node* sch_root (void);
char* sch_dump (void);
sch_node* sch_validate_path (sch_node *root, const char *path, bool *read, bool *write);
sch_node* sch_child_get (sch_node *root, const char *name);
char* sch_node_to_path (sch_node *node);
sch_node* sch_path_to_node (const char *path);
bool sch_node_is_leaf (sch_node *node);
bool sch_node_is_list (sch_node *node, char **key);
bool sch_node_has_mode_flag (sch_node *node, char mode_flag);
bool sch_validate_pattern (sch_node *node, const char *value);

/* HTTP handler for rest */
#define FLAGS_CONTENT_JSON       (1 << 0)
#define FLAGS_CONTENT_XML        (1 << 1)
#define FLAGS_ACCEPT_JSON        (1 << 2)
#define FLAGS_ACCEPT_XML         (1 << 3)
#define FLAGS_JSON_FORMAT_ARRAYS (1 << 4)
#define FLAGS_JSON_FORMAT_ROOT   (1 << 5)
#define FLAGS_JSON_FORMAT_MULTI  (1 << 6)
typedef char* (*http_callback) (int flags, const char *path, const char *action, const char *if_none_match, const char *data, int length);

/* FastCGI */
bool fcgi_start (const char *socket, http_callback cb);
void fcgi_stop (void);

/* Rest */
extern bool rest_use_arrays;
char* rest_api (int flags, const char *path, const char *action, const char *if_none_match, const char *data, int length);

#endif /* _REST_H_ */
