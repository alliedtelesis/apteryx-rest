# Makefile for apteryx-rest
ifneq ($(V),1)
	Q=@
endif

SYSROOT ?= .
SRCDIR ?= .
DESTDIR ?= ./
PREFIX ?= /usr/
CC := $(CROSS_COMPILE)gcc
LD := $(CROSS_COMPILE)ld
PKG_CONFIG ?= pkg-config
INDENT = VERSION_CONTROL=none indent -npro -gnu -nut -bli0 -c1 -cd1 -cp1 -i4 -l92 -ts4 -nbbo -sc

CFLAGS := $(CFLAGS) -g -O2
EXTRA_CFLAGS += -Werror -Wall -Wno-comment -std=c99 -D_GNU_SOURCE -fPIC
EXTRA_CFLAGS += -I$(SRCDIR) -I$(SYSROOT)/usr/include
EXTRA_CFLAGS += `$(PKG_CONFIG) --cflags glib-2.0`
EXTRA_LDFLAGS += `$(PKG_CONFIG) --libs-only-l glib-2.0`
EXTRA_LDFLAGS += -L$(SYSROOT)/usr/lib -lfcgi -ljansson -lapteryx-schema -lapteryx
# TODO
EXTRA_CFLAGS += `$(PKG_CONFIG) --cflags libxml-2.0`
EXTRA_LDFLAGS += `$(PKG_CONFIG) --libs libxml-2.0`

DAEMON = apteryx-rest

SOURCE := main.c fcgi.c rest.c

OBJS=$(SOURCE:%.c=%.o)

all:$(DAEMON)

%.o: %.c
	@echo "Compiling "$<""
	$(Q)$(CC) $(CFLAGS) $(EXTRA_CFLAGS) -c $< -o $@

$(DAEMON): $(OBJS)
	@echo "Building $@"
	$(Q)$(CC) $(CFLAGS) $(EXTRA_CFLAGS) -o $@ $(OBJS) $(EXTRA_LDFLAGS)

indent:
	@echo "Fixing coding-style..."
	$(Q)$(INDENT) $(SOURCE)

install: all
	@install -d $(DESTDIR)/$(PREFIX)/bin
	@install -D $(DAEMON) $(DESTDIR)/$(PREFIX)/bin/

clean:
	@echo "Cleaning..."
	$(Q)rm -fr $(DAEMON) $(OBJS)

.SECONDARY:
.PHONY: all clean indent
