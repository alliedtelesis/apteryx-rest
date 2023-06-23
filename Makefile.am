bin_PROGRAMS = apteryx-rest
apteryx_rest_SOURCES = main.c fcgi.c rest.c yang-library.c api_html.c
apteryx_rest_CFLAGS = @LIBFCGI_CFLAGS@ @APTERYX_XML_CFLAGS@ @JANSSON_CFLAGS@ @LIBXML2_CFLAGS@ @APTERYX_CFLAGS@ @GLIB_CFLAGS@
apteryx_rest_LDADD = @LIBFCGI_LIBS@ @APTERYX_XML_LIBS@ @JANSSON_LIBS@ @LIBXML2_LIBS@ @APTERYX_LIBS@ @GLIB_LIBS@

EXTRA_DIST = models/ietf-yang-library.yang models/ietf-restconf-monitoring.yang
BUILT_SOURCES = models/ietf-yang-library.h models/ietf-restconf-monitoring.h models/ietf-yang-library.xml models/ietf-restconf-monitoring.xml api_html.c
CLEANFILES = $(BUILT_SOURCES)

include_HEADERS = models/ietf-yang-library.h models/ietf-restconf-monitoring.h
schemadir = $(destdir)/etc/apteryx/schema
schema_DATA = models/ietf-yang-library.xml models/ietf-restconf-monitoring.xml

api_html.c: api.html Makefile
	@echo '__asm__(".align 8; .global api_html; api_html: .incbin \"api.html\"; .byte 0;");' > api_html.c

models/ietf-yang-library.h: models/ietf-yang-library.yang
	$(PYANG) -p . -f cpaths -o $@ $<

models/ietf-restconf-monitoring.h: models/ietf-restconf-monitoring.yang
	$(PYANG) -p . -f cpaths -o $@ $<

models/ietf-yang-library.xml: models/ietf-yang-library.yang
	$(PYANG) -p . -f apteryx-xml $< > $@

models/ietf-restconf-monitoring.xml: models/ietf-restconf-monitoring.yang
	$(PYANG) -p . -f apteryx-xml $< > $@
