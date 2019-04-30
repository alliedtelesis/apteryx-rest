#!/bin/bash
ROOT=`pwd`

# Check required libraries and tools
if ! pkg-config --exists glib-2.0 libxml-2.0; then
        echo "Please install glib-2.0 (sudo apt-get install libglib2.0-dev libxml2-dev)"
        exit 1
fi

# Build needed packages
BUILD=$ROOT/.build
mkdir -p $BUILD
cd $BUILD

# Check Apteryx install
if [ ! -f apteryx/libapteryx.so ]; then
        echo "Building Apteryx from source."
        git clone https://github.com/alliedtelesis/apteryx.git
        cd apteryx
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
        cd $BUILD
fi

# Check lighttpd
if [ ! -f lighttpd1.4/src/lighttpd ]; then
        echo "Building lighttpd from source."
        git clone https://git.lighttpd.net/lighttpd/lighttpd1.4.git
        cd lighttpd1.4
        ./autogen.sh
        ./configure --prefix=/usr --without-bzip2
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
        cd $BUILD
fi

# Check fastcgi
if [ ! -f usr/lib/libfcgi.so ]; then
        echo "Building fcgi from source."
        if [ ! -d fcgi-2.4.0 ]; then
                wget -nc https://github.com/LuaDist/fcgi/archive/2.4.0.tar.gz
                tar -zxf 2.4.0.tar.gz
        fi
        cd fcgi-2.4.0
        ./configure --prefix=/usr
        sed -i '1s/^/#include <stdio.h>/' libfcgi/fcgio.cpp
        make install DESTDIR=$BUILD
        if [ ! -f $BUILD/usr/include/fcgi_config.h  ] ; then
                cp include/*.h $BUILD/usr/include/
	        mv $BUILD/usr/include/fcgi_config_x86.h $BUILD/usr/include/fcgi_config.h 
        fi
        cd $BUILD
fi

# Check jansson
if [ ! -f usr/lib/libjansson.so ]; then
        echo "Building jansson from source."
        if [ ! -d jansson-2.12 ]; then
                wget -nc http://www.digip.org/jansson/releases/jansson-2.12.tar.gz
                tar -zxf jansson-2.12.tar.gz
        fi
        cd jansson-2.12
        ./configure --prefix=/usr
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
        cd $BUILD
fi

cd $ROOT

# Build
make V=1 SYSROOT=$BUILD
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

# Start Apteryx and populate the database
export LD_LIBRARY_PATH=$BUILD/usr/lib
$BUILD/usr/bin/apteryxd -b

# Create an example module
mkdir -p $BUILD/modules
echo '<?xml version="1.0" encoding="UTF-8"?>
<MODULE xmlns="https://github.com/alliedtelesis/apteryx"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="https://github.com/alliedtelesis/apteryx
	https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd">
	<NODE name="interfaces">
		<NODE name="interface" help="Interface List">
			<NODE name="*" help="Interface Name">
				<NODE name="name" mode="rw" help="Interface name" />
				<NODE name="type" mode="rw" help="Interface type" pattern="^(eth|ppp)$" />
				<NODE name="enabled" mode="rw" default="0" help="Interface admin status">
					<VALUE name="disabled" value="0" help="The interface is disabled" />
					<VALUE name="enabled" value="1" help="The interface is enabled" />
				</NODE>
			</NODE>
		</NODE>
	</NODE>
</MODULE>
' > $BUILD/modules/interfaces.xml

# Start rest
# TEST_WRAPPER="valgrind --leak-check=full"
LD_LIBRARY_PATH=$BUILD/usr/lib G_SLICE=always-malloc \
        $TEST_WRAPPER ./apteryx-rest -b -m $BUILD/modules -p $BUILD/apteryx-rest.pid \
        -s $BUILD/apteryx-rest.sock
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
sleep 0.5

# Run lighttpd
sudo killall lighttpd &> /dev/null
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
fastcgi.debug = 1
fastcgi.server = (
"/api" => (
  "fastcgi.handler" => (
    "socket" => "'$BUILD'/apteryx-rest.sock",
    "check-local" => "disable",
    )
  )
)
' > $BUILD/lighttpd.conf
$BUILD/usr/sbin/lighttpd -f $BUILD/lighttpd.conf -m $BUILD/usr/lib
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

## Testing
APTERYX=$BUILD/usr/bin/apteryx

echo -ne "API"
res=`curl -sG http://127.0.0.1:8080/api.xml`
[[ $res == *"The interface is disabled"* ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "POST"
res=`curl -s -X POST -d '{"name":"eth2","type":"eth","enabled":"true"}' http://127.0.0.1:8080/api/interfaces/interface/eth2`
res=$($APTERYX -g /interfaces/interface/eth2/name)
[[ $res == "eth2" ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "POST(tree)"
res=`curl -sX POST -d '{"eth1":{"name":"eth1","type":"eth","enabled":"true"}}' http://127.0.0.1:8080/api/interfaces/interface`
res=$($APTERYX -g /interfaces/interface/eth1/name)
[[ $res == "eth1" ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "POST(pattern mismatch)"
res=`curl -sX POST -d '{"type":"cat"}' http://127.0.0.1:8080/api/interfaces/interface/eth2`
res=$($APTERYX -g /interfaces/interface/eth2/type)
[[ $res == "eth" ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "GET"
res=`curl -sG http://127.0.0.1:8080/api/interfaces/interface/eth1`
[[ "$res" == '{"type": "eth", "enabled": "true", "name": "eth1"}' ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "SEARCH"
res=`curl -sG http://127.0.0.1:8080/api/interfaces/interface/`
[[ "$res" == '{"interface": ["eth2","eth1"]}' ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "DELETE"
res=`curl -sX "DELETE" http://127.0.0.1:8080/api/interfaces/interface/eth1`
res=$($APTERYX -t /interfaces/interface/eth1)
[[ $res == "" ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

echo -ne "DELETE(trunk)"
res=`curl -sX "DELETE" http://127.0.0.1:8080/api/interfaces/interface`
res=$($APTERYX -t)
[[ $res == '' ]] && (echo " - pass";) || (echo -e " - FAIL\n$res";)

# Stop lighttpd
sudo killall lighttpd
# Stop apteryx-rest
sudo killall apteryx-rest &> /dev/null
sudo kill `pidof valgrind.bin` &> /dev/null
# Stop Apteryx
$BUILD/usr/bin/apteryx -t
killall apteryxd
