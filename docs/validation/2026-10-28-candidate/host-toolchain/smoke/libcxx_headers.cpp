#include <features.h>
#include <cstdlib>
#include <atomic>
#include <cstdio>
static_assert(__GLIBC__ == 2 && __GLIBC_MINOR__ == 15, "Wrong host sysroot");
int test_host_headers() { std::atomic<int> x(7); return x.load() + (std::malloc(0)==nullptr); }
