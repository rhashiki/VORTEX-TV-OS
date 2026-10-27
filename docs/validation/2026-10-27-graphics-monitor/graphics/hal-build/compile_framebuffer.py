from pathlib import Path
import subprocess,json,hashlib
root=Path('/workspace/build01-graphics-next/graphics/hal-build');base=Path('/workspace/build01-platform-next/research')
tool=Path('/workspace/build01-sd/kernel-work/toolchain')
gral=base/'mali-legacy/gralloc-rk3328';bionic=base/'rockchip-bionic';libhardware=Path('/workspace/build01-graphics-next/graphics/libhardware')
cmd=[str(tool/'bin/arm-linux-gnueabihf-g++'),'-c','-std=gnu++11','-fPIC','-march=armv7-a','-mfloat-abi=softfp','-mfpu=neon','-DANDROID','-D__ANDROID__','-D__ANDROID_API__=25','-DGRALLOC_32_BITS','-DSTANDARD_LINUX_SCREEN','-DPLATFORM_SDK_VERSION=25','-DLOG_TAG="gralloc"','-nostdinc','-nostdinc++']
for p in [gral,libhardware/'include',base/'rockchip-system-core/include',root/'native-opengl-include']:
 cmd+=['-I',str(p)]
for p in [root/'libcxx-include',bionic/'libc/include',bionic/'libc/arch-arm/include',bionic/'libc/kernel/uapi',bionic/'libc/kernel/uapi/asm-arm',bionic/'libc/kernel/android/uapi',tool/'lib/gcc/arm-linux-gnueabihf/6.3.1/include']:
 cmd+=['-isystem',str(p)]
cmd+=['-MD','-MF',str(root/'framebuffer_device.d'),str(gral/'framebuffer_device.cpp'),'-o',str(root/'framebuffer_device.o')]
result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(root/'compile-attempt-01.log').write_bytes(result.stdout)
(root/'compile-attempt-01.json').write_text(json.dumps({'command':cmd,'exit_code':result.returncode,'source_sha256':hashlib.sha256((gral/'framebuffer_device.cpp').read_bytes()).hexdigest()},indent=2)+'\n')
print(result.stdout.decode(errors='replace'));print('exit',result.returncode)
