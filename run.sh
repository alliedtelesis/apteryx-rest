#!/bin/bash
ROOT=`pwd`

# Start Apteryx
apteryxd -b

# Create an example module
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
' > interfaces.xml

# Start rest
# TEST_WRAPPER="valgrind --leak-check=full"
G_SLICE=always-malloc $TEST_WRAPPER ./apteryx-rest -b -m ./ -p apteryx-rest.pid -s apteryx-rest.sock
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
sleep 0.5

# Run lighttpd
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
fastcgi.debug = 1
fastcgi.server = (
"/api" => (
  "fastcgi.handler" => (
    "socket" => "'$ROOT'/apteryx-rest.sock",
    "check-local" => "disable",
    )
  )
)
' > lighttpd.conf
lighttpd -D -f lighttpd.conf
rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi

# Stop lighttpd
killall lighttpd &> /dev/null
# Stop apteryx-rest
killall apteryx-rest &> /dev/null
kill `pidof valgrind.bin` &> /dev/null
# Stop Apteryx
apteryx -t
killall -9 apteryxd
rm -f /tmp/apteryx
rm interfaces.xml
rm lighttpd.conf
