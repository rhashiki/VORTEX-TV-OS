from pathlib import Path
import json,hashlib
root=Path('/workspace/build01-product-next/native-rules');tree=root/'tree'
refs=Path('/workspace/build01-hal-next/gralloc-link/reference/system/lib')
module=tree/'vendor/vortex/reference-libraries';module.mkdir(parents=True,exist_ok=True)
(module/'lib').mkdir(exist_ok=True)
headers={
 'liblog':['system/core/include'],
 'libcutils':['system/core/include'],
 'libhardware':['hardware/libhardware/include'],
 'libhardware_legacy':['/workspace/build01-hal-next/hwc/legacy-headers/include'],
 'libion':['system/core/libion/include','system/core/libion/kernel-headers'],
 'libui':['frameworks/native/include'],
 'libEGL':['frameworks/native/opengl/include'],
 'libGLESv1_CM':['frameworks/native/opengl/include'],
 'libsync':['system/core/libsync/include'],
 'libc++':['external/libcxx/include'],
 'libc':['bionic/libc/include','bionic/libc/arch-arm/include','bionic/libc/kernel/uapi','bionic/libc/kernel/uapi/asm-arm'],
 'libm':['bionic/libm/include','bionic/libm/include/arm']}
lines=['# Reference-only real ELF modules for this thin-tree experiment.', '# These are actual hashed runtime DSOs, not generated stubs or a source BSP.', 'LOCAL_PATH := $(call my-dir)']
records=[]
for src in sorted(refs.glob('*.so')):
 dst=module/'lib'/src.name
 if not dst.exists():dst.symlink_to(src)
 name=src.stem
 lines+=['','include $(CLEAR_VARS)',f'LOCAL_MODULE := {name}','LOCAL_MODULE_CLASS := SHARED_LIBRARIES','LOCAL_MODULE_SUFFIX := .so',f'LOCAL_SRC_FILES := lib/{src.name}','LOCAL_MULTILIB := 32','LOCAL_MODULE_TAGS := optional','LOCAL_CXX_STL := none','LOCAL_SYSTEM_SHARED_LIBRARIES :=','LOCAL_CHECK_ELF_FILES := false']
 # Nougat has no LOCAL_CHECK_ELF_FILES gate; actual source/ELF checks are external.
 lines=[l for l in lines if l!='LOCAL_CHECK_ELF_FILES := false']
 if headers.get(name):lines+=['LOCAL_EXPORT_C_INCLUDE_DIRS := '+' '.join(headers[name])]
 lines+=['include $(BUILD_PREBUILT)']
 records.append({'module':name,'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()})
(module/'Android.mk').write_text('\n'.join(lines)+'\n')
(root/'reference-modules.json').write_text(json.dumps({'scope':'Genuine BUILD_PREBUILT modules with real reference ELF inputs only; not a source-built platform.','modules':records},indent=2)+'\n')
print('Real reference modules:',len(records))
