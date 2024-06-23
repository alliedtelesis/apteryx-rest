AC_INIT([apteryx_rest], [1.0])
AM_INIT_AUTOMAKE([-Wall -Werror foreign])

AC_PROG_CC_STDC
AM_PROG_AR

LT_INIT([disable-static pic-only])

AC_CONFIG_MACRO_DIRS([m4])

PKG_CHECK_MODULES([GLIB],[glib-2.0])
PKG_CHECK_MODULES([APTERYX],[apteryx])
PKG_CHECK_MODULES([LIBXML2],[libxml-2.0])
PKG_CHECK_MODULES([JANSSON],[jansson])
PKG_CHECK_MODULES([APTERYX_XML],[apteryx-xml])
PKG_CHECK_MODULES([LIBFCGI],[libfcgi])
PKG_CHECK_MODULES([LUA], [lua], , [
    PKG_CHECK_MODULES([LUA], [lua5.4], , [
        PKG_CHECK_MODULES([LUA], [lua5.3], , [
            PKG_CHECK_MODULES([LUA], [lua5.2])
        ])
    ])
])

AC_ARG_WITH([pyang],
  [AS_HELP_STRING([--with-pyang], [path to pyang])],
  [use_pyang=$withval],
  [use_pyang="pyang"])
AC_SUBST(PYANG, $use_pyang)

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
