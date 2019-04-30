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
typedef void sch_instance;
typedef void sch_node;
extern sch_instance *g_schema;
sch_instance* sch_load (const char *path);
void sch_free (sch_instance *schema);
sch_node* sch_lookup (sch_instance *schema, const char *path);
bool sch_is_leaf (sch_node *node);
bool sch_is_readable (sch_node *node);
bool sch_is_writable (sch_node *node);
bool sch_is_config (sch_node *node);
char* sch_name (sch_node *node);
char* sch_pattern (sch_node *node);
char* sch_translate_to (sch_node *node, char *value);
char* sch_translate_from (sch_node *node, char *value);

sch_node* sch_validate_path (sch_instance *schema, const char *path, bool *read, bool *write);
bool sch_node_is_api_node (sch_node *node);
bool sch_node_is_leaf (sch_node *node);
bool sch_node_has_mode_flag (sch_node *node, char mode_flag);
char* sch_dump (sch_instance *schema);
sch_node* sch_parent (sch_node *node);
sch_node* sch_first_child (sch_node *node);
sch_node* sch_next_child (sch_node *node);

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
