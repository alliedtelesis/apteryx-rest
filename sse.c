/**
 * @file sse.c
 * Example code for receiving SSE events
 * gcc -o sse sse.c `pkg-config --cflags libcurl` `pkg-config --libs libcurl`
 * ./sse http://localhost:8080/api/test/settings
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
#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <curl/curl.h>

static size_t
on_data (char *data, size_t size, size_t nmemb, void *userdata)
{
    //Find data in event-source if using RFC encoding
    //json_t *json = json_loads (data, 0, &error);
    //json_to_tree (schema, json, data);
    printf ("%.*s", (int) (size * nmemb), data);
    return size * nmemb;
}

int
main (int argc, char *argv[])
{
    const char *url = argv[1];
    struct curl_slist *headers = NULL;
    long response_code;
    CURLcode res;
    CURL *curl;

    if (argc != 2)
    {
        printf ("Usage: %s <url>", argv[0]);
        exit (1);
    }

    curl_global_init (CURL_GLOBAL_ALL);

    curl = curl_easy_init ();
    curl_easy_setopt (curl, CURLOPT_VERBOSE, 1);
    curl_easy_setopt (curl, CURLOPT_NOPROGRESS, 1);
    curl_easy_setopt (curl, CURLOPT_USERAGENT, "sse/1.0");
    curl_easy_setopt (curl, CURLOPT_FOLLOWLOCATION, 1);
    curl_easy_setopt (curl, CURLOPT_MAXREDIRS, 10);
    curl_easy_setopt (curl, CURLOPT_SSL_VERIFYPEER, 0L);

    curl_easy_setopt (curl, CURLOPT_URL, url);
    headers = curl_slist_append (headers, "Accept: text/event-stream");
    headers = curl_slist_append (headers, "X-JSON-Types: on");
    headers = curl_slist_append (headers, "X-JSON-Arrays: on");
    curl_easy_setopt (curl, CURLOPT_HTTPHEADER, headers); 
    curl_easy_setopt (curl, CURLOPT_WRITEFUNCTION, on_data);
    curl_easy_setopt (curl, CURLOPT_TCP_KEEPALIVE, 1L);

    curl_easy_setopt (curl, CURLOPT_TIMEOUT, 0);

    res = curl_easy_perform (curl);
    if (res != CURLE_OK)
    {
        fprintf (stderr, "Curl failure %d\n", res);
        exit (1);
    }
    curl_easy_getinfo (curl, CURLINFO_RESPONSE_CODE, &response_code); 
    if (response_code < 200 || response_code >= 300)
    {
        const char* effective_url = NULL;
        curl_easy_getinfo (curl, CURLINFO_EFFECTIVE_URL, &effective_url); 
        fprintf (stderr, "%s: HTTP(S) status code %ld\n", effective_url, response_code);
        exit (1);
    }
    curl_slist_free_all (headers);
    curl_easy_cleanup (curl);

    return 0;
}
