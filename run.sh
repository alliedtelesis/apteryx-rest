#!/bin/bash
ROOT=`pwd`

# Start Apteryx
apteryxd -b
apteryx -s /firewall/settings/protect 1
apteryx -s /firewall/settings/state 2
apteryx -s /firewall/fw_rules/10/index 10
apteryx -s /firewall/fw_rules/10/to public
apteryx -s /firewall/fw_rules/10/application http
apteryx -s /firewall/fw_rules/10/from private
apteryx -s /firewall/fw_rules/10/action 1
apteryx -s /firewall/fw_rules/20/index 20
apteryx -s /firewall/fw_rules/20/to public
apteryx -s /firewall/fw_rules/20/application ftp
apteryx -s /firewall/fw_rules/20/from private
apteryx -s /firewall/fw_rules/20/action 1

# Create an example module
echo '<?xml version="1.0" encoding="UTF-8"?>
<MODULE xmlns="https://github.com/alliedtelesis/apteryx"
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xsi:schemaLocation="https://github.com/alliedtelesis/apteryx
	https://github.com/alliedtelesis/apteryx/releases/download/v2.10/apteryx.xsd">
	<NODE name="firewall">
		<NODE name="settings">
			<NODE name="protect" mode="rw" default="0" help="Firewall configuration" pattern="^(0|1)$">
				<VALUE name="disable" value="0" help="Disable Firewall"/>
				<VALUE name="enable" value="1" help="Enable Firewall"/>
			</NODE>
			<NODE name="state" mode="r" default="0" help="Status of the firewall">
				<VALUE name="unknown" value="-1" help="The status is unknown" />
				<VALUE name="disabled" value="0" help="Firewall is disabled" />
				<VALUE name="loading" value="1" help="Starting the firewall" />
				<VALUE name="running" value="2" help="Firewall is running" />
			</NODE>
		</NODE>
		<NODE name="fw_rules">
			<NODE name="*" help="Unique identifier for rule - integer">
				<NODE name="index" mode="rw" help="Index for rule, rules are processed in index order, rules are added when this field is set" pattern="^{{range(1,65535)}}$"/>
				<NODE name="to" mode="rw" help="Entity to match as destination" pattern="^{{entity}}$"/>
				<NODE name="from" mode="rw" help="Entity to match as source" pattern="^{{entity}}$"/>
				<NODE name="application" mode="rw" help="Application to match" pattern="^{{application}}$"/>
				<NODE name="action" mode="rw" help="Action to apply for this rule" pattern="^(0|1|2|4)$">
					<VALUE name="deny" value="0" help="Deny the packet" />
					<VALUE name="permit" value="1" help="Permit the packet" />
					<VALUE name="reject" value="2" help="Reject the packet" />
					<VALUE name="log" value="4" help="Log the packet" />
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
