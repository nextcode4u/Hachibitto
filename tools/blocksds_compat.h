/* SPDX-License-Identifier: MIT
 * Header-only SDK compatibility, used only by the optional BlocksDS build.
 */
#ifndef ARGV_BLOCKSDS_COMPAT_H
#define ARGV_BLOCKSDS_COMPAT_H
#include <stdio.h>
#include <stdarg.h>
#include <malloc.h>
#include <sys/stat.h>
#include <time.h>
#include <strings.h>
/* Avoid collisions with the SDK's own heap-query helpers. */
#define getHeapStart argv_legacy_getHeapStart
#define getHeapEnd argv_legacy_getHeapEnd
#define getHeapLimit argv_legacy_getHeapLimit
static inline int iprintf(const char *format, ...)
{
    va_list args;
    va_start(args, format);
    int result = vprintf(format, args);
    va_end(args);
    return result;
}
static inline int siprintf(char *buffer, const char *format, ...)
{
    va_list args;
    va_start(args, format);
    int result = vsprintf(buffer, format, args);
    va_end(args);
    return result;
}
#endif
