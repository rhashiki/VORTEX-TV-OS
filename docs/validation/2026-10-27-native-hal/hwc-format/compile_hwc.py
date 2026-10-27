from pathlib import Path
import subprocess,json,hashlib,sys
root=Path('/workspace/build01-hal-next/hwc-format')
original=Path('/workspace/build01-hal-next/hwc')
base=Path('/workspace/build01-platform-next/research')
prior=Path('/workspace/build01-graphics-next/graphics/hal-build')
tool=Path('/workspace/build01-sd/kernel-work/toolchain')
source=root/'source'
phase=sys.argv[1]
labels=sys.argv[2:] or ['rk_hwcomposer','rk_hwcomposer_blit','rk_hwc_com','rga_api','rk_hwcomposer_htg','hwc_ipp','hwc_rga','TVInfo']
logdir=root/'evidence'/phase;logdir.mkdir(parents=True,exist_ok=True)
flags=['-std=gnu++11','-fno-exceptions','-fno-rtti','-fPIC','-march=armv7-a','-mfloat-abi=softfp','-mfpu=neon','-DANDROID','-D__ANDROID__','-D__ANDROID_API__=25','-DTARGET_BOARD_PLATFORM_RK322X','-DRK322X_BOX','-DRK_BOX','-DUSE_DMA_BUF','-DPLATFORM_SDK_VERSION=25','-DLOG_TAG="hwcomposer"','-Wall','-Wextra','-Werror=format','-nostdinc','-nostdinc++']
inc=[source,Path('/workspace/build01-graphics-next/graphics/libhardware/include'),base/'rockchip-system-core/include',base/'rockchip-system-core/include/system',base/'rockchip-system-core/libion/include',base/'rockchip-system-core/libion/kernel-headers',base/'rockchip-system-core/libsync/include',base/'mali-legacy/gralloc-rk3328',base/'rockchip-librkvpu',base/'rockchip-librkvpu/common/include',original/'native-headers/include',original/'native-headers/opengl/include',original/'legacy-headers/include',prior/'native-opengl-include']
sysinc=[prior/'libcxx-include',base/'rockchip-bionic/libc/include',base/'rockchip-bionic/libm/include',base/'rockchip-bionic/libm/include/arm',base/'rockchip-bionic/libc/arch-arm/include',base/'rockchip-bionic/libc/kernel/uapi',base/'rockchip-bionic/libc/kernel/uapi/asm-arm',base/'rockchip-bionic/libc/kernel/android/uapi',tool/'lib/gcc/arm-linux-gnueabihf/6.3.1/include']
results=[]
for label in labels:
 cmd=[str(tool/'bin/arm-linux-gnueabihf-g++'),'-c']+flags
 for path in inc:cmd+=['-I',str(path)]
 for path in sysinc:cmd+=['-isystem',str(path)]
 cmd+=['-MD','-MF',str(logdir/(label+'.d')),str(source/(label+'.cpp')),'-o',str(logdir/(label+'.o'))]
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (logdir/(label+'.log')).write_bytes(r.stdout)
 rec={'source':label+'.cpp','source_sha256':hashlib.sha256((source/(label+'.cpp')).read_bytes()).hexdigest(),'command':cmd,'exit_code':r.returncode,'log':str((logdir/(label+'.log')).relative_to(root))}
 if r.returncode==0:rec['object_sha256']=hashlib.sha256((logdir/(label+'.o')).read_bytes()).hexdigest()
 results.append(rec)
 print(label,r.returncode,r.stdout.decode(errors='replace')[:2200])
(logdir/'results.json').write_text(json.dumps(results,indent=2)+'\n')
