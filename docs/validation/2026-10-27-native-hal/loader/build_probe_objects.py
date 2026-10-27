from pathlib import Path
import subprocess,hashlib,json
root=Path('/workspace/build01-hal-next/loader');ev=root/'evidence';ev.mkdir(exist_ok=True)
bionic=Path('/workspace/build01-platform-next/research/rockchip-bionic')
tool=Path('/workspace/build01-sd/kernel-work/toolchain')
cc=tool/'bin/arm-linux-gnueabihf-gcc'
flags=['-c','-std=gnu99','-O2','-fPIE','-fno-omit-frame-pointer','-fno-stack-protector','-march=armv7-a','-marm','-mfloat-abi=softfp','-mfpu=neon','-D__ANDROID__','-DANDROID','-DPLATFORM_SDK_VERSION=25','-nostdinc','-Wall','-Wextra']
for p in [bionic/'libc/include',bionic/'libc/arch-arm/include',bionic/'libc/kernel/uapi',bionic/'libc/kernel/uapi/asm-arm',bionic/'libc/kernel/android/uapi',tool/'lib/gcc/arm-linux-gnueabihf/6.3.1/include']:
 flags+=['-isystem',str(p)]
flags+=['-I','/workspace/build01-graphics-next/graphics/libhardware/include','-I','/workspace/build01-platform-next/research/rockchip-system-core/include']
results=[]
for name,src in [('crtbegin_dynamic1',bionic/'libc/arch-common/bionic/crtbegin.c'),('crtend_android',bionic/'libc/arch-common/bionic/crtend.S'),('crtbrand',bionic/'libc/arch-common/bionic/crtbrand.S'),('hal_metadata_probe',root/'hal_metadata_probe.c')]:
 out=root/(name+'.o');log=ev/(name+'.compile.log')
 cmd=[str(cc),*flags,'-MD','-MF',str(ev/(name+'.d')),str(src),'-o',str(out)]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 log.write_bytes(p.stdout)
 data={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'command':cmd,'exit_code':p.returncode,'log':str(log)}
 if p.returncode==0:data['object_sha256']=hashlib.sha256(out.read_bytes()).hexdigest()
 results.append(data)
(root/'evidence/probe-object-build.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps([{'source':r['source'],'exit_code':r['exit_code'],'log':r['log']} for r in results],indent=2))
assert all(r['exit_code']==0 for r in results)
