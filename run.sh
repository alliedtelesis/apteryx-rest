#!/bin/bash
ROOT=`pwd`
ACTION=$1

# Defaults
HTTP_SERVER="${HTTP_SERVER:-lighttpd}"
if [[ "$HTTP_SERVER" != "lighttpd" && "$HTTP_SERVER" != "nginx" && "$HTTP_SERVER" != "appweb" ]] ; then
        echo "Invalid HTTP_SERVER. Must be one of; lighttpd, nginx or appweb"
        exit 1
fi
LIGHTTPD_URL="${LIGHTTPD_URL:-https://download.lighttpd.net/lighttpd/releases-1.4.x/lighttpd-1.4.53.tar.xz}"
NGINX_URL="${NGINX_URL:-http://nginx.org/download/nginx-1.27.2.tar.gz}"
APPWEB_URL="${APPWEB_URL:-https://github.com/AbsoluteZero-ljz/appweb/archive/refs/tags/v8.2.3.tar.gz}"
APPWEB_HANDLER="${APPWEB_HANDLER:-fastHandler}"
FCGI_URL="${FCGI_URL:-https://github.com/LuaDist/fcgi/archive/2.4.0.tar.gz}"

# Check required libraries and tools
if ! pkg-config --exists glib-2.0 libxml-2.0 cunit jansson; then
        echo "Please install glib-2.0, libxml-2.0, jansson and cunit"
        echo "(sudo apt-get install build-essential libglib2.0-dev libxml2-dev libcunit1-dev libjansson-dev libpcre3-dev zlib1g zlib1g-dev libssl-dev libgd-dev libxml2-dev uuid-dev libbz2-dev)"
        exit 1
fi

# Build needed packages
BUILD=$ROOT/.build
mkdir -p $BUILD
cd $BUILD

# Generic cleanup
function quit {
        RC=$1
        # Stop web-server
        killall -q lighttpd
        killall -q appweb
        killall -q nginx
        # Stop apteryx-rest
        killall -q apteryx-rest
        kill `pidof valgrind.bin` &> /dev/null
        # Stop Apteryx
        killall -q -9 apteryxd
        rm -f /tmp/apteryx
        exit $RC
}

# Check Apteryx install
if [ ! -d apteryx ]; then
        echo "Downloading Apteryx"
        git clone --depth 1 https://github.com/alliedtelesis/apteryx.git
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi
if [ ! -f $BUILD/usr/lib/libapteryx.so ]; then
        echo "Building Apteryx"
        cd apteryx
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Check Apteryx XML Schema library
if [ ! -d apteryx-xml ]; then
        echo "Downloading apteryx-xml"
        git clone --depth 1 https://github.com/alliedtelesis/apteryx-xml.git
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi
if [ ! -f $BUILD/usr/lib/libapteryx-schema.so ]; then
        echo "Building apteryx-xml"
        cd apteryx-xml
        rm -f $BUILD/usr/lib/libapteryx-xml.so
        rm -f $BUILD/usr/lib/libapteryx-schema.so
        export EXTRA_CFLAGS="-fprofile-arcs -ftest-coverage"
        export EXTRA_LDFLAGS="-fprofile-arcs -ftest-coverage"
        make install DESTDIR=$BUILD APTERYX_PATH=$BUILD/apteryx
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi
mkdir -p $BUILD/etc/restconf
rm -f $BUILD/etc/restconf/*
cp $BUILD/apteryx-xml/models/*.xml $BUILD/etc/restconf/
cp $BUILD/apteryx-xml/models/*.map $BUILD/etc/restconf/
rm -fr $BUILD/usr/share/restconf
mkdir -p $BUILD/usr/share/restconf
cp $BUILD/apteryx-xml/models/*.lua $BUILD/usr/share/restconf/

# Check fcgi
if [ ! -f $BUILD/usr/lib/libfcgi.so ]; then
        echo "Building fcgi."
        wget -nc $FCGI_URL
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        FILE="$(basename $FCGI_URL)"
        DIR=$(tar tf $FILE | sed -e 's@/.*@@' | uniq)
        if [ ! -d $DIR ]; then
                tar -zxf $FILE
                rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        fi
        cd $DIR
        ./configure --prefix=/usr
        sed -i 's/SUBDIRS = libfcgi cgi-fcgi examples include/SUBDIRS = libfcgi cgi-fcgi include/g' Makefile
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Build web server
if [ "$HTTP_SERVER" == "lighttpd" ] && [ ! -f $BUILD/usr/sbin/lighttpd ]; then
        echo "Building lighttpd."
        wget -nc $LIGHTTPD_URL
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        FILE="$(basename $LIGHTTPD_URL)"
        DIR=$(tar tf $FILE | sed -e 's@/.*@@' | uniq)
        if [ ! -d $DIR ]; then
                tar -xf $FILE
                rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        fi
        cd $DIR
        ./configure --prefix=/usr --disable-ipv6 CFLAGS=-Wno-error
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
elif [ "$HTTP_SERVER" == "nginx" ] && [ ! -f $BUILD/usr/sbin/nginx ]; then
        echo "Building nginx."
        wget -nc $NGINX_URL
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        FILE="$(basename $NGINX_URL)"
        DIR=$(tar ztf $FILE | sed -e 's@/.*@@' | uniq)
        if [ ! -d $DIR ]; then
                tar -zxf $FILE
                rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        fi
        cd $DIR
        ./configure --prefix=/var/www/html --sbin-path=/usr/sbin/nginx --conf-path=$BUILD/nginx.conf \
        --http-log-path=$BUILD/access.log --error-log-path=$BUILD/error.log --with-pcre \
        --lock-path=$BUILD/nginx.lock --pid-path=$BUILD/nginx.pid --with-http_ssl_module \
        --modules-path=$BUILD/modules
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
elif [ "$HTTP_SERVER" == "appweb" ] && [ ! -f $BUILD/usr/sbin/appweb ]; then
        echo "Building appweb."
        wget -nc $APPWEB_URL
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        FILE="$(basename $APPWEB_URL)"
        DIR=$(tar ztf $FILE | sed -e 's@/.*@@' | uniq)
        if [ ! -d $DIR ]; then
                tar -zxf $FILE
                rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
                cd $DIR
                # Disable appweb redirect handling as we do not need it but do need the location header
                sed -i 's/scaselesscmp(key, "location")/scaselesscmp(key, "ignore")/g' src/modules/fastHandler.c
                rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
                # Fixup appweb broken chunking
                sed -i 's/tx->headerSize = mpr/else\n        mprPutStringToBuf(buf, "\\r\\n");\n    tx->headerSize = mpr/g' src/http/httpLib.c
                sed -i 's/\\r\\n%zx\\r\\n/%zx\\r\\n/g' src/http/httpLib.c
                sed -i 's/\\r\\n0\\r\\n\\r\\n/0\\r\\n\\r\\n/g' src/http/httpLib.c
                sed -i 's/setChunkPrefix(q, packet);/setChunkPrefix(q, packet);\n            mprPutStringToBuf(packet->content, "\\r\\n");/g' src/http/httpLib.c
                cd ..
        fi
        cd $DIR
        export LDFLAGS="$(pkg-config --libs glib-2.0) -L$BUILD/usr/lib"
        export CFLAGS="$(pkg-config --cflags glib-2.0) -I$BUILD/usr/include"
        ME_COM_FAST=1 ME_COM_APTERYX=1 make
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        mkdir -p $BUILD/usr/sbin
        cp build/linux-x64-default/bin/appweb $BUILD/usr/sbin/
        mkdir -p $BUILD/usr/lib
        cp build/linux-x64-default/bin/*.so $BUILD/usr/lib/
        cd $BUILD
fi

# Build
echo "Building apteryx-restconf"
if [ ! -f $BUILD/../Makefile ]; then
        export CFLAGS="-g -Wall -Werror -I$BUILD/usr/include -fprofile-arcs -ftest-coverage"
        export LDFLAGS=-L$BUILD/usr/lib
        export PKG_CONFIG_PATH=$BUILD/usr/lib/pkgconfig
        cd $BUILD/../
        ./autogen.sh
        ./configure \
                LIBFCGI_CFLAGS=-I$BUILD/usr/include LIBFCGI_LIBS=-lfcgi \
                --with-pyang="pyang --plugindir $BUILD/apteryx-xml/ -p $BUILD/../models"
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi
make -C $BUILD/../
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
cp $BUILD/../models/*.xml $BUILD/etc/restconf/
cp $BUILD/../models/*.map $BUILD/etc/restconf/
cp $BUILD/../models/*.lua $BUILD/usr/share/restconf/

# Check tests
echo Checking pytest coding style ...
flake8 --max-line-length=180 ../tests/test*.py
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Start Apteryx and populate the database
export LD_LIBRARY_PATH=$BUILD/usr/lib
rm -f /tmp/apteryx
$BUILD/usr/bin/apteryxd -b
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Run web server
if [ "$HTTP_SERVER" == "lighttpd" ]; then
        echo Running lighttpd ...
        killall lighttpd &> /dev/null
        echo '
        server.document-root = "'$BUILD'/../"
        index-file.names = ( "index.html" )
        server.port = 8080
        server.modules += ("mod_fastcgi")
        mimetype.assign = (
        ".html" => "text/html",
        ".txt" => "text/plain",
        ".xml" => "text/xml",
        ".jpg" => "image/jpeg",
        ".png" => "image/png",
        ".css" => "text/css",
        )
        server.stream-response-body = 2
        fastcgi.debug = 1
        fastcgi.server = (
        "/api" => (
                "fastcgi.handler" => (
                "docroot" => "/api",
                "socket" => "'$BUILD'/apteryx-rest.sock",
                "check-local" => "disable",
                )
        ),
        )
        server.errorlog = "'$BUILD'/lighttpd.log"
        ' > $BUILD/lighttpd.conf
        $BUILD/usr/sbin/lighttpd -f $BUILD/lighttpd.conf -m $BUILD/usr/lib
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
elif [ "$HTTP_SERVER" == "nginx" ]; then
        echo Running nginx ...
        killall nginx &> /dev/null
        echo '
        daemon on;
        # error_log /dev/stdout debug;
        pid '$BUILD'/nginx.pid;
        events {
                worker_connections 768;
        }
        http {
                server {
                        listen 8080;
                        access_log off;
                        location /api {
                                root /api;
                                fastcgi_pass unix:'$BUILD'/apteryx-rest.sock;
                                fastcgi_buffering off;
                                fastcgi_read_timeout 1d;
                                fastcgi_param NO_BUFFERING "";
                                fastcgi_param DOCUMENT_ROOT      $document_root;
                                fastcgi_param REQUEST_METHOD     $request_method;
                                fastcgi_param REQUEST_URI        $request_uri;
                                fastcgi_param QUERY_STRING       $query_string;
                                fastcgi_param CONTENT_TYPE       $content_type;
                                fastcgi_param CONTENT_LENGTH     $content_length;
                                fastcgi_param HTTP_IF_MATCH      $http_if_match;
                                fastcgi_param HTTP_IF_NONE_MATCH $http_if_none_match;
                                fastcgi_param HTTP_IF_MODIFIED_SINCE $http_if_modified_since;
                                fastcgi_param HTTP_IF_UNMODIFIED_SINCE $http_if_unmodified_since;
                        }
                        error_page   500 502 503 504  /50x.html;
                        location = /50x.html {
                                root   html;
                        }
                }
                merge_slashes off; # Just to test our own code
                access_log /dev/stdout;
                client_body_temp_path '$BUILD'/nginx-client-body;
                proxy_temp_path '$BUILD'/nginx-proxy;
                fastcgi_temp_path '$BUILD'/nginx-fastcgi;
                uwsgi_temp_path '$BUILD'/nginx-uwsgi;
                scgi_temp_path '$BUILD'/nginx-scgi;
        }
        ' > $BUILD/nginx.conf
        $BUILD/usr/sbin/nginx
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
elif [ "$HTTP_SERVER" == "appweb" ]; then
        echo Running appweb ...
        killall appweb &> /dev/null
        > $BUILD/appweb.conf
        if [ "$APPWEB_HANDLER" == "apteryxHandler" ]; then
                echo '
        LoadModule ApteryxHandler '$BUILD'/usr/lib/libmod_apteryx.so
        ApteryxSchemaPath '$BUILD'/etc/restconf/
                ' > $BUILD/appweb.conf
        fi
        echo '
        Listen 8080
        FastConnect 127.0.0.1:9047 keep multiplex=1000
        <Route ^/api>
                Documents "/api"
                Prefix /api
                Methods set GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD
                SetHandler '$APPWEB_HANDLER'
                SessionCookie disable
                Header set Cache-Control   "no-store"
        </Route>
        ' >> $BUILD/appweb.conf
        (set -m; $BUILD/usr/sbin/appweb --config $BUILD/appweb.conf &)
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi

# Parameters
if [ "$ACTION" == "test" ]; then
        PARAM="-b"
else
        PARAM="-v"
fi
if [ "$HTTP_SERVER" == "appweb" ]; then
        SOCK="127.0.0.1:9047"
else
        SOCK="apteryx-rest.sock"
fi

# Start apteryx-rest
rm -f $BUILD/apteryx-rest.sock
# TEST_WRAPPER="gdb -ex run --args"
# TEST_WRAPPER="valgrind --leak-check=full"
# TEST_WRAPPER="valgrind --tool=cachegrind"
# TEST_WRAPPER="valgrind --tool=callgrind"
G_SLICE=always-malloc LD_LIBRARY_PATH=$BUILD/usr/lib LUA_CPATH="$BUILD/usr/lib/lib?.so;;" \
        $TEST_WRAPPER ../apteryx-rest $PARAM -m $BUILD/etc/restconf/ -r $BUILD/usr/share/restconf/ -p apteryx-rest.pid -s $SOCK
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
sleep 0.5
cd $BUILD/../

if [ "$ACTION" == "test" ]; then
        python3 -m pytest -v
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi

# Gcov
mkdir -p .gcov
find . -path ./.gcov -prune -o -name '*.gcno' -exec mv {} .gcov/ \;
find . -path ./.gcov -prune -o -name '*.gcda' -exec mv {} .gcov/ \;
mv -f $BUILD/apteryx-xml/*.gcno .gcov/ 2>/dev/null || true
mv -f $BUILD/apteryx-xml/*.gcda .gcov/ 2>/dev/null || true
lcov -q --capture --directory . --output-file .gcov/coverage.info &> /dev/null
genhtml -q .gcov/coverage.info --output-directory .gcov/

# Done - cleanup
quit 0
