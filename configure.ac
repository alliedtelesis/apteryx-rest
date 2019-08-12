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
AC_CHECK_HEADERS([fcgi_config.h])

AC_ARG_ENABLE([tests],
[  --enable-tests          build unit tests (default=yes)],
[case "${enableval}" in
  yes) tests=true ;;
  no)  tests=false ;;
  *) AC_MSG_ERROR([bad value ${enableval} for --enable-tests]) ;;
esac],[tests=true])
AM_CONDITIONAL([HAVE_TESTS], [test x$tests = xtrue])

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
