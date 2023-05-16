#!/bin/bash
ROOT=`pwd`
ACTION=$1

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
        # Stop lighttpd
        killall lighttpd &> /dev/null
        killall nginx &> /dev/null
        # Stop apteryx-rest
        killall apteryx-rest &> /dev/null
        kill `pidof valgrind.bin` &> /dev/null
        # Stop Apteryx
        killall -9 apteryxd &> /dev/null
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
        make install DESTDIR=$BUILD APTERYX_PATH=$BUILD/apteryx
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Check fcgi
if [ ! -d fcgi-2.4.0 ]; then
        echo "Building fcgi from source."
        wget https://github.com/LuaDist/fcgi/archive/2.4.0.tar.gz
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        tar -zxf 2.4.0.tar.gz
fi
if [ ! -f $BUILD/usr/lib/libfcgi.so ]; then
        cd fcgi-2.4.0
        ./configure --prefix=/usr
        sed -i 's/SUBDIRS = libfcgi cgi-fcgi examples include/SUBDIRS = libfcgi cgi-fcgi include/g' Makefile
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Build web server
if [ "$1" == "nginx" ]; then
    # Build nginx
    if [ ! -d nginx-1.20.0 ]; then
            echo "Building nginx from source."
            wget http://nginx.org/download/nginx-1.20.0.tar.gz
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
            tar -zxf nginx-1.20.0.tar.gz
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
    fi
    if [ ! -f $BUILD/usr/sbin/nginx ]; then
            cd nginx-1.20.0
            ./configure --prefix=/var/www/html --sbin-path=/usr/sbin/nginx --conf-path=$BUILD/nginx.conf \
            --http-log-path=$BUILD/access.log --error-log-path=$BUILD/error.log --with-pcre \
            --lock-path=$BUILD/nginx.lock --pid-path=$BUILD/nginx.pid --with-http_ssl_module \
            --modules-path=$BUILD/modules
            make install DESTDIR=$BUILD
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
            cd $BUILD
    fi
else
    # Build lighttpd
    if [ ! -d lighttpd-1.4.53 ]; then
            echo "Building lighttpd from source."
            wget https://download.lighttpd.net/lighttpd/releases-1.4.x/lighttpd-1.4.53.tar.xz
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
            tar -xf lighttpd-1.4.53.tar.xz
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
    fi
    if [ ! -f $BUILD/usr/sbin/lighttpd ]; then
            cd lighttpd-1.4.53
            ./configure --prefix=/usr --disable-ipv6 CFLAGS=-Wno-error
            make install DESTDIR=$BUILD
            rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
            cd $BUILD
    fi
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
                LIBFCGI_CFLAGS=-I$BUILD/usr/include LIBFCGI_LIBS=-lfcgi
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi
make -C $BUILD/../
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

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
if [ "$1" == "nginx" ]; then
    echo Running nginx ...
    killall nginx &> /dev/null
    echo '
    daemon on;
    error_log /dev/stdout debug;
    pid '$BUILD'/nginx.pid;
    events {
        worker_connections 768;
    }
    http {
        server {
            listen 8080;
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
else
    echo Running lighttpd ...
    killall lighttpd &> /dev/null
    echo '
    server.document-root = "./"
    server.port = 8080
    server.modules += ("mod_fastcgi")
    mimetype.assign = (
    ".html" => "text/html",
    ".txt" => "text/plain",
    ".xml" => "text/xml",
    ".jpg" => "image/jpeg",
    ".png" => "image/png"
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
fi

# Parameters
if [ $ACTION == "test" ]; then
        PARAM="-b"
else
        PARAM="-v"
fi

# Start apteryx-rest
rm -f $BUILD/apteryx-rest.sock
# TEST_WRAPPER="gdb -ex run --args"
# TEST_WRAPPER="valgrind --leak-check=full"
# TEST_WRAPPER="valgrind --tool=cachegrind"
G_SLICE=always-malloc LD_LIBRARY_PATH=$BUILD/usr/lib \
        $TEST_WRAPPER ../apteryx-rest $PARAM -m ../models/ -p apteryx-rest.pid -s apteryx-rest.sock
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
sleep 0.5
cd $BUILD/../

if [ $ACTION == "test" ]; then
        python3 -m pytest -v
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi

# Gcov
mkdir -p .gcov
mv -f *.gcno .gcov/ 2>/dev/null || true
mv -f *.gcda .gcov/ 2>/dev/null || true
lcov -q --capture --directory . --output-file .gcov/coverage.info &> /dev/null
genhtml -q .gcov/coverage.info --output-directory .gcov/

# Done - cleanup
quit 0
