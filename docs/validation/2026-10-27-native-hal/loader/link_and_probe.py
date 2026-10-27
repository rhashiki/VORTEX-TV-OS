from pathlib import Path
import subprocess,json,hashlib,sys
root=Path('/workspace/build01-hal-next/loader');ev=root/'evidence'
base=Path('/workspace/build01-hal-next/gralloc-link')
ref=base/'reference';libs=ref/'system/lib'
cc='/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-gcc'
cmd=[cc,'-nostdlib','-fPIE','-pie','-march=armv7-a','-mfloat-abi=softfp','-mfpu=neon','-Wl,-e,_start','-Wl,--dynamic-linker,/system/bin/linker','-Wl,-z,defs','-Wl,--no-undefined','-Wl,--no-allow-shlib-undefined','-Wl,-z,relro','-Wl,-z,now',str(root/'crtbegin_dynamic1.o'),str(root/'crtbrand.o'),str(root/'hal_metadata_probe.o'),'-L'+str(libs),'-Wl,-rpath-link,'+str(libs),'-lc','-ldl','-lgcc',str(root/'crtend_android.o'),'-o',str(root/'hal_metadata_probe')]
p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(ev/'probe-link.log').write_bytes(p.stdout)
(ev/'probe-link.json').write_text(json.dumps({'command':cmd,'exit_code':p.returncode},indent=2)+'\n')
print('link',p.returncode,p.stdout.decode(errors='replace'))
if p.returncode:sys.exit(p.returncode)
qemu=root/'bin/qemu-arm-static'
cases=[('missing-file','/nonexistent-vortex-hal.so','gralloc',2),('missing-HMI',str(libs/'libm.so'),'gralloc',3),('gralloc',str(base/'artifacts/gralloc.rk30board.so'),'gralloc',0),('hwcomposer',str(base/'artifacts/hwcomposer.rk30board.so'),'hwcomposer',0),('wrong-id',str(base/'artifacts/gralloc.rk30board.so'),'not-gralloc',4)]
results=[]
for name,module,expected,expected_exit in cases:
 command=[str(qemu),'-L',str(ref),'-E','LD_LIBRARY_PATH=/system/lib',str(root/'hal_metadata_probe'),module,expected]
 try:
  proc=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25)
  code=proc.returncode;out=proc.stdout
 except subprocess.TimeoutExpired as e:
  code='timeout';out=e.stdout or b''
 (ev/(name+'.runtime.log')).write_bytes(out)
 record={'case':name,'command':command,'exit_code':code,'expected_exit_code':expected_exit,'status':'pass' if code==expected_exit else 'fail','log':name+'.runtime.log'}
 results.append(record)
 print(name,code,out.decode(errors='replace')[:3000])
 if name=='missing-file' and code!=expected_exit:break
(ev/'loader-smoke-result.json').write_text(json.dumps({'scope':'Actual Android ARM32 linker and HAL metadata under QEMU Linux user mode only; no HAL device open, graphics operation, full Android boot or hardware.','checks':results,'status':'pass' if len(results)==len(cases) and all(r['status']=='pass' for r in results) else 'fail','helper_sha256':hashlib.sha256((root/'hal_metadata_probe').read_bytes()).hexdigest()},indent=2)+'\n')
