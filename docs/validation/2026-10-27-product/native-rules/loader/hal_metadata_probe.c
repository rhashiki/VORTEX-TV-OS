/* Loader/metadata probe only. Does not call a HAL device open or GPU operation. */
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <hardware/hardware.h>

int main(int argc, char **argv, char **envp) {
    (void)envp;
    if (argc != 3) {
        fprintf(stderr, "usage: hal_metadata_probe module-path expected-id\n");
        return 64;
    }
    void *handle = dlopen(argv[1], RTLD_NOW | RTLD_LOCAL);
    if (!handle) {
        fprintf(stderr, "DLOPEN_FAILED: %s\n", dlerror());
        return 2;
    }
    const hw_module_t *module = (const hw_module_t *)dlsym(handle, HAL_MODULE_INFO_SYM_AS_STR);
    if (!module) {
        fprintf(stderr, "HMI_MISSING: %s\n", dlerror());
        dlclose(handle);
        return 3;
    }
    if (module->tag != HARDWARE_MODULE_TAG || !module->id || strcmp(module->id, argv[2]) ||
            !module->methods || !module->methods->open) {
        fprintf(stderr, "HMI_INVALID tag=%u id=%s\n", module->tag, module->id ? module->id : "(null)");
        dlclose(handle);
        return 4;
    }
    printf("HAL_METADATA_OK id=%s module_api=%u hal_api=%u name=%s\n",
           module->id, module->module_api_version, module->hal_api_version,
           module->name ? module->name : "(null)");
    if (dlclose(handle)) {
        fprintf(stderr, "DLCLOSE_FAILED: %s\n", dlerror());
        return 5;
    }
    return 0;
}
