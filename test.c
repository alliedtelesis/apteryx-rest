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

static void test_schema_load (void)
{
    g_assert_null (sch_root ());
    g_assert_true (sch_load ("."));
    g_assert_nonnull (sch_root ());
    sch_unload ();
    g_assert_null (sch_root ());
}

static void test_rest_schema (void)
{
    char *buffer;

    g_assert_true (sch_load ("."));
    buffer = rest_api (FLAGS_ACCEPT_JSON, "/api.xml", "GET", NULL, 0);
    g_assert_nonnull (g_strrstr (buffer, "<MODULE xmlns=\"https://github.com/alliedtelesis/apteryx\""));
    g_assert_nonnull (g_strrstr (buffer, "this is a test node"));
    g_assert_null (g_strrstr (buffer, "that will be merged"));
    g_assert_nonnull (g_strrstr (buffer, "Read only field"));
    free (buffer);
    sch_unload ();
}

int main (int argc, char *argv[])
{
    int rc;

    generate_test_schemas ();

    g_test_init (&argc, &argv, NULL);
    g_test_add_func ("/schema/load", test_schema_load);
    g_test_add_func ("/rest/schema", test_rest_schema);
    rc = g_test_run();

    destroy_test_schemas ();
    return rc;
}
