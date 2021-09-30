/*
 * @file test.c
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

bool debug = false;
bool verbose = false;
bool rest_use_arrays = false;

#define TEST_PATH       "/test"
#define TEST_SETUP      g_assert_true (sch_load ("."));
#define TEST_TEARDOWN   { sch_unload (); g_assert_true (assert_apteryx_empty ()); }

static void generate_test_schemas (void)
{
    FILE *xml;

    xml = fopen ("test1.xml", "w");
    if (xml)
    {
        fprintf (xml,
"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
"<MODULE xmlns=\"https://github.com/alliedtelesis/apteryx\"\n"
"    xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
"    xsi:schemaLocation=\"https://github.com/alliedtelesis/apteryx\n"
"    https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd\">\n"
"    <NODE name=\"test\" help=\"this is a test node\">\n"
"        <NODE name=\"debug\" mode=\"rw\" default=\"0\" help=\"Debug configuration\" pattern=\"^(0|1)$\">\n"
"            <VALUE name=\"disable\" value=\"0\" help=\"Debugging is disabled\" />\n"
"            <VALUE name=\"enable\" value=\"1\" help=\"Debugging is enabled\" />\n"
"        </NODE>\n"
"        <NODE name=\"list\" help=\"this is a list of stuff\">\n"
"            <NODE name=\"*\" help=\"the list item\">\n"
"                <NODE name=\"name\" mode=\"rw\" help=\"this is the list key\"/>\n"
"                <NODE name=\"type\" mode=\"rw\" default=\"1\" help=\"this is the list type\">\n"
"                    <VALUE name=\"big\" value=\"1\"/>\n"
"                    <VALUE name=\"little\" value=\"2\"/>\n"
"                </NODE>\n"
"                <NODE name=\"sub-list\" help=\"this is a list of stuff attached to a list\">\n"
"                    <NODE name=\"*\" help=\"the sublist item\">\n"
"                        <NODE name=\"i-d\" mode=\"rw\" help=\"this is the sublist key\"/>\n"
"                    </NODE>\n"
"                </NODE>\n"
"            </NODE>\n"
"        </NODE>\n"
"        <NODE name=\"trivial-list\" help=\"this is a simple list of stuff\">\n"
"            <NODE name=\"*\" help=\"the list item\" />\n"
"        </NODE>\n"
"    </NODE>\n"
"</MODULE>\n");
        fclose (xml);
    }
    xml = fopen ("test2.xml", "w");
    if (xml)
    {
        fprintf (xml,
"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
"<MODULE xmlns=\"https://github.com/alliedtelesis/apteryx\"\n"
"	xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n"
"	xsi:schemaLocation=\"https://github.com/alliedtelesis/apteryx\n"
"	https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd\">\n"
"	<NODE name=\"test\" help=\"this is a test node that will be merged\">\n"
"		<NODE name=\"state\" mode=\"r\" default=\"0\" help=\"Read only field\" >\n"
"			<VALUE name=\"up\" value=\"0\" help=\"State is up\" />\n"
"			<VALUE name=\"down\" value=\"1\" help=\"State is down\" />\n"
"		</NODE>\n"
"		<NODE name=\"kick\" mode=\"w\" help=\"Write only field\" pattern=\"^(0|1)$\" />\n"
"		<NODE name=\"secret\" mode=\"h\" help=\"Hidden field\" />\n"
"	</NODE>\n"
"</MODULE>\n");
        fclose (xml);
    }
}

static void destroy_test_schemas ()
{
    unlink ("test1.xml");
    unlink ("test2.xml");
}

static bool
assert_apteryx_empty (void)
{
    GList *paths = apteryx_search ("/");
    GList *iter;
    bool ret = true;
    for (iter = paths; iter; iter = g_list_next (iter))
    {
        char *path = (char *) (iter->data);
        if (strncmp (TEST_PATH, path, strlen (TEST_PATH)) == 0)
        {
            if (ret) fprintf (stderr, "\n");
            fprintf (stderr, "ERROR: Node still set: %s\n", path);
            ret = false;
        }
    }
    g_list_free_full (paths, free);
    return ret;
}

static void test_schema_load (void)
{
    g_assert_null (sch_root ());
    g_assert_true (sch_load ("."));
    g_assert_nonnull (sch_root ());
    sch_unload ();
    g_assert_null (sch_root ());
}

static void test_schema_get (void)
{
    char *buffer;

    TEST_SETUP
    buffer = rest_api (FLAGS_ACCEPT_JSON, "/api.xml", "GET", NULL, NULL, 0);
    g_assert_nonnull (g_strrstr (buffer, "<MODULE xmlns=\"https://github.com/alliedtelesis/apteryx\""));
    g_assert_nonnull (g_strrstr (buffer, "this is a test node"));
    g_assert_null (g_strrstr (buffer, "that will be merged"));
    g_assert_nonnull (g_strrstr (buffer, "Read only field"));
    free (buffer);
    TEST_TEARDOWN
}

static void test_set_node (void)
{
    char *data = "{\"debug\": \"0\"}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    char *buffer = apteryx_get ("/test/debug");
    g_assert_cmpstr (buffer, ==, "0");
    free (buffer);
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_set_node_null (void)
{
    char *data = "{\"debug\": \"\"}";
    int len = strlen (data);

    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_null (apteryx_get ("/test/debug"));
    free (resp);
    TEST_TEARDOWN
}

static void test_set_node_invalid (void)
{
    char *data = "{\"debug\": \"not_valid\"}";
    int len = strlen (data);

    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    char *buffer = apteryx_get ("/test/debug");
    g_assert_cmpstr (buffer, ==, "0");
    free (buffer);
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_set_tree (void)
{
    char *data = "{\"list\": {\"fred\": {\"name\": \"fred\"}}}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    char *buffer = apteryx_get ("/test/list/fred/name");
    g_assert_cmpstr (buffer, ==, "fred");
    free (buffer);
    free (resp);
    apteryx_set ("/test/list/fred/name", NULL);
    TEST_TEARDOWN
}

static void test_set_tree_null (void)
{
    char *data = "{\"list\": {\"fred\": {\"name\": \"\"}}}";
    int len = strlen (data);

    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_null (apteryx_get ("/test/list/fred/name"));
    free (resp);
    TEST_TEARDOWN
}

static void test_set_list (void)
{
    char *data = "{\"list\": {\"fred\": {\"name\": \"fred\"}, \"tom\": {\"name\": \"tom\"}}}";
    int len = strlen (data);
    char *buffer;

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 200"));
    buffer = apteryx_get ("/test/list/fred/name");
    g_assert_cmpstr (buffer, ==, "fred");
    free (buffer);
    buffer = apteryx_get ("/test/list/tom/name");
    g_assert_cmpstr (buffer, ==, "tom");
    free (buffer);
    free (resp);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_set_array (void)
{
    char *data = "{\"list\": [{\"name\": \"fred\"}, {\"name\": \"tom\"}]}";
    int len = strlen (data);
    char *buffer;

    TEST_SETUP
    rest_use_arrays = true;
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 200"));
    rest_use_arrays = false;
    buffer = apteryx_get ("/test/list/fred/name");
    g_assert_cmpstr (buffer, ==, "fred");
    free (buffer);
    buffer = apteryx_get ("/test/list/tom/name");
    g_assert_cmpstr (buffer, ==, "tom");
    free (buffer);
    free (resp);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_set_status_200 (void)
{
    char *data = "{\"debug\": \"0\"}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 200"));
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_set_status_400 (void)
{
    char *data = "cabbage";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 400"));
    free (resp);
    TEST_TEARDOWN
}

static void test_set_status_403 (void)
{
    char *data = "{\"state\": \"up\"}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 403"));
    free (resp);
    TEST_TEARDOWN
}

static void test_set_status_404 (void)
{
    char *data = "{\"cabbage\": \"0\"}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 404"));
    free (resp);
    TEST_TEARDOWN
}

static void test_set_hidden (void)
{
    char *data = "{\"secret\": \"0\"}";
    int len = strlen (data);

    TEST_SETUP
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "POST", NULL, data, len);
    g_assert_nonnull (g_strrstr (resp, "Status: 403"));
    free (resp);
    TEST_TEARDOWN
}

static void test_get_node (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    char *json = strstr (resp, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"debug\": \"0\"}");
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_tree (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *buffer = rest_api (FLAGS_ACCEPT_JSON, "/api/test", "GET", NULL, NULL, 0);
    char *json = strstr (buffer, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"test\": {\"debug\": \"0\"}}");
    free (buffer);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_list (void)
{
    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    apteryx_set ("/test/list/tom/name", "tom");
    char *buffer = rest_api (FLAGS_ACCEPT_JSON, "/api/test/list", "GET", NULL, NULL, 0);
    char *json = strstr (buffer, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"list\": {\"fred\": {\"name\": \"fred\"}, \"tom\": {\"name\": \"tom\"}}}");
    free (buffer);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_get_array (void)
{
    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    apteryx_set ("/test/list/tom/name", "tom");
    rest_use_arrays = true;
    char *buffer = rest_api (FLAGS_ACCEPT_JSON, "/api/test/list", "GET", NULL, NULL, 0);
    rest_use_arrays = false;
    char *json = strstr (buffer, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"list\": [{\"name\": \"fred\"}, {\"name\": \"tom\"}]}");
    free (buffer);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_get_etag (void)
{
    char *resp1, *resp2, *resp3;
    char *etag1, *etag2, *etag3;

    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    resp1 = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    etag1 = g_strrstr (resp1, "Etag");
    g_assert_nonnull (etag1);
    resp2 = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    etag2 = g_strrstr (resp2, "Etag");
    g_assert_nonnull (etag2);
    g_assert_cmpstr (etag1, ==, etag2);
    apteryx_set ("/test/debug", "1");
    resp3 = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    etag3 = g_strrstr (resp3, "Etag");
    g_assert_nonnull (etag3);
    g_assert_cmpstr (etag1, !=, etag3);
    free (resp1);
    free (resp2);
    free (resp3);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_status_200 (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    g_assert_nonnull (g_strrstr (resp, "Status: 200"));
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_status_304 (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", NULL, NULL, 0);
    char *etag = g_strrstr (resp, "Etag: ");
    g_assert_nonnull (etag);
    uint64_t ts = strtoull (etag + 6, NULL, 16);
    free (resp);
    g_assert_cmpuint (ts, !=, 0);
    etag = g_strdup_printf ("%"PRIX64, ts);
    resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "GET", etag, NULL, 0);
    g_assert_nonnull (g_strrstr (resp, "Status: 304"));
    free (resp);
    free (etag);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_status_403 (void)
{
    TEST_SETUP
    apteryx_set ("/test/kick", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/kick", "GET", NULL, NULL, 0);
    g_assert_nonnull (g_strrstr (resp, "Status: 403"));
    free (resp);
    apteryx_set ("/test/kick", NULL);
    TEST_TEARDOWN
}

static void test_get_status_404 (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/cabbage", "GET", NULL, NULL, 0);
    g_assert_nonnull (g_strrstr (resp, "Status: 404"));
    free (resp);
    apteryx_set ("/test/debug", NULL);
    TEST_TEARDOWN
}

static void test_get_hidden (void)
{
    TEST_SETUP
    apteryx_set ("/test/secret", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/secret", "GET", NULL, NULL, 0);
    g_assert_nonnull (g_strrstr (resp, "Status: 403"));
    free (resp);
    apteryx_set ("/test/secret", NULL);
    TEST_TEARDOWN
}

static void test_search_node (void)
{
    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    apteryx_set ("/test/list/tom/name", "tom");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/list/fred/name/", "GET", NULL, NULL, 0);
    char *json = strstr (resp, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"name\": []}");
    free (resp);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_search_trunk (void)
{
    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    apteryx_set ("/test/list/tom/name", "tom");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/list/", "GET", NULL, NULL, 0);
    char *json = strstr (resp, "\r\n\r\n");
    json = json ? json + 4 : "";
    g_assert_cmpstr (json, ==, "{\"list\": [\"fred\",\"tom\"]}");
    free (resp);
    apteryx_set ("/test/list/fred/name", NULL);
    apteryx_set ("/test/list/tom/name", NULL);
    TEST_TEARDOWN
}

static void test_delete_node (void)
{
    TEST_SETUP
    apteryx_set ("/test/debug", "0");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/debug", "DELETE", NULL, NULL, 0);
    g_assert_null (apteryx_get ("/test/debug"));
    free (resp);
    TEST_TEARDOWN
}

static void test_delete_trunk (void)
{
    TEST_SETUP
    apteryx_set ("/test/list/fred/name", "fred");
    char *resp = rest_api (FLAGS_ACCEPT_JSON, "/api/test/list", "DELETE", NULL, NULL, 0);
    g_assert_null (apteryx_get ("/test/list/fred/name"));
    free (resp);
    TEST_TEARDOWN
}

int main (int argc, char *argv[])
{
    int rc;

    g_test_init (&argc, &argv, NULL);
    debug = verbose = g_test_verbose ();
    apteryx_init (verbose);
    generate_test_schemas ();
    g_test_add_func ("/schema/load", test_schema_load);
    g_test_add_func ("/schema/get", test_schema_get);
    g_test_add_func ("/set/node", test_set_node);
    g_test_add_func ("/set/node/null", test_set_node_null);
    g_test_add_func ("/set/node/invalid", test_set_node_invalid);
    g_test_add_func ("/set/tree", test_set_tree);
    g_test_add_func ("/set/tree/null", test_set_tree_null);
    g_test_add_func ("/set/list", test_set_list);
    g_test_add_func ("/set/array", test_set_array);
    g_test_add_func ("/set/status/200", test_set_status_200);
    g_test_add_func ("/set/status/400", test_set_status_400);
    g_test_add_func ("/set/status/403", test_set_status_403);
    g_test_add_func ("/set/status/404", test_set_status_404);
    g_test_add_func ("/set/hidden", test_set_hidden);
    g_test_add_func ("/get/node", test_get_node);
    g_test_add_func ("/get/tree", test_get_tree);
    g_test_add_func ("/get/list", test_get_list);
    g_test_add_func ("/get/array", test_get_array);
    g_test_add_func ("/get/etag", test_get_etag);
    g_test_add_func ("/get/status/200", test_get_status_200);
    g_test_add_func ("/get/status/304", test_get_status_304);
    g_test_add_func ("/get/status/403", test_get_status_403);
    g_test_add_func ("/get/status/404", test_get_status_404);
    g_test_add_func ("/get/hidden", test_get_hidden);
    g_test_add_func ("/search/node", test_search_node);
    g_test_add_func ("/search/trunk", test_search_trunk);
    g_test_add_func ("/delete/node", test_delete_node);
    g_test_add_func ("/delete/trunk", test_delete_trunk);
    rc = g_test_run();
    destroy_test_schemas ();
    apteryx_shutdown ();
    return rc;
}
