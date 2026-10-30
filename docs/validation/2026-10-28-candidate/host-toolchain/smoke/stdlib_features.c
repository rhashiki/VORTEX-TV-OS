#include <features.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
int main(void) { void *p=malloc(32); if (!p) return 4; free(p); printf("glibc_headers=%d.%d malloc_ok=1\n", __GLIBC__, __GLIBC_MINOR__); return 0; }
