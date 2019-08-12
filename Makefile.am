bin_PROGRAMS = apteryx-rest
apteryx_rest_SOURCES = main.c fcgi.c schema.c rest.c
apteryx_rest_CFLAGS = @JANSSON_CFLAGS@ @LIBXML2_CFLAGS@ @APTERYX_CFLAGS@ @GLIB_CFLAGS@
apteryx_rest_LDFLAGS = -lfcgi
apteryx_rest_LDADD = @JANSSON_LIBS@ @LIBXML2_LIBS@ @APTERYX_LIBS@ @GLIB_LIBS@


if HAVE_TESTS
noinst_PROGRAMS = unittest
unittest_SOURCES = test.c rest.c schema.c
unittest_CFLAGS = $(apteryx_rest_CFLAGS) -g -fprofile-arcs -fprofile-dir=gcov -ftest-coverage
unittest_LDADD = $(apteryx_rest_LDADD)

# TEST_WRAPPER="G_SLICE=always-malloc valgrind --leak-check=full" make test
# TEST_WRAPPER="gdb" make test
# make test TEST_ARGS="-h"
test: unittest
	@echo "Running unit tests"
	@if test -e /tmp/apteryxd.pid; then \
		kill -TERM `cat /tmp/apteryxd.pid` && sleep 0.1; \
	fi; \
	rm -f /tmp/apteryxd.pid; \
	rm -f /tmp/apteryxd.run; \
	apteryxd -b -p /tmp/apteryxd.pid -r /tmp/apteryxd.run && sleep 0.1; \
	mkdir -p gcov; \
	eval LD_LIBRARY_PATH=/usr/local/lib LUA_CPATH=.libs/?.so $(TEST_WRAPPER) ./unittest $(TEST_ARGS); \
	mv *.gcno gcov/ 2> /dev/null; \
	lcov -q --capture --directory . --output-file gcov/coverage.info; \
	genhtml -q gcov/coverage.info --output-directory gcov; \
	kill -TERM `cat /tmp/apteryxd.pid`;
	@echo "Tests have been run!"
endif