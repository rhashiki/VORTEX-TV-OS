/* Metadata only. Never invokes HAL open, power hooks, ALSA, or hardware IO. */
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
#include <hardware/hardware.h>
#include <hardware/power.h>
int main(int argc,char **argv,char **envp) {
 (void)envp;
 if(argc!=4 || (strcmp(argv[3],"device") && strcmp(argv[3],"module")))return 64;
 void *handle=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
 if(!handle){fprintf(stderr,"DLOPEN_FAILED: %s\n",dlerror());return 2;}
 const hw_module_t *module=(const hw_module_t*)dlsym(handle,HAL_MODULE_INFO_SYM_AS_STR);
 if(!module){fprintf(stderr,"HMI_MISSING: %s\n",dlerror());dlclose(handle);return 3;}
 if(module->tag!=HARDWARE_MODULE_TAG || !module->id || strcmp(module->id,argv[2]) || !module->methods || (!strcmp(argv[3],"device") && !module->methods->open)) {
  fprintf(stderr,"HMI_INVALID tag=%u id=%s\n",module->tag,module->id?module->id:"(null)");dlclose(handle);return 4;
 }
 if(!strcmp(argv[2],POWER_HARDWARE_MODULE_ID)) {
  const power_module_t *power=(const power_module_t*)module;
  if(!power->init || !power->setInteractive || !power->powerHint){fprintf(stderr,"POWER_HOOK_MISSING\n");dlclose(handle);return 4;}
 }
 printf("HAL_METADATA_OK id=%s module_api=%u hal_api=%u name=%s mode=%s open_present=%d\n",module->id,module->module_api_version,module->hal_api_version,module->name?module->name:"(null)",argv[3],module->methods->open!=NULL);
 if(dlclose(handle)){fprintf(stderr,"DLCLOSE_FAILED: %s\n",dlerror());return 5;}
 return 0;
}
