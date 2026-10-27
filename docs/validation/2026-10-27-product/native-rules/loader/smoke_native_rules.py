from pathlib import Path
import hashlib,json,subprocess,sys,argparse
root=Path('/workspace/build01-product-next/native-rules')
ap=argparse.ArgumentParser();ap.add_argument('--artifacts',type=Path,default=root/'artifacts');ap.add_argument('--evidence',type=Path,default=root/'loader/evidence');args=ap.parse_args()
ev=args.evidence;ev.mkdir(parents=True,exist_ok=True)
old=Path('/workspace/build01-hal-next/loader')
ref=Path('/workspace/build01-hal-next/gralloc-link/reference')
qemu=old/'bin/qemu-arm-static';probe=old/'hal_metadata_probe'
cases=[('missing-file','/nonexistent-vortex-hal.so','gralloc',2),('missing-HMI',str(ref/'system/lib/libm.so'),'gralloc',3),('gralloc',str(args.artifacts/'gralloc.rk30board.so'),'gralloc',0),('hwcomposer',str(args.artifacts/'hwcomposer.rk30board.so'),'hwcomposer',0),('wrong-id',str(args.artifacts/'gralloc.rk30board.so'),'not-gralloc',4)]
checks=[]
for name,path,expected,code in cases:
 cmd=[str(qemu),'-L',str(ref),'-E','LD_LIBRARY_PATH=/system/lib',str(probe),path,expected]
 try:
  p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=25);actual=p.returncode;out=p.stdout
 except subprocess.TimeoutExpired as e:actual='timeout';out=e.stdout or b''
 (ev/f'{name}.runtime.log').write_bytes(out)
 checks.append({'case':name,'command':cmd,'exit_code':actual,'expected_exit_code':code,'status':'pass' if actual==code else 'fail','log':f'{name}.runtime.log'})
 print(name,actual,out.decode(errors='replace').strip())
record={'scope':'Actual Android ARM32 dynamic linker resolves new Android.mk-built HALs with RTLD_NOW under QEMU Linux user mode. Tag/id/method pointers checked; version/name printed only. HAL open never invoked, DSO constructors/destructors may execute. No rendering, full Android boot, SD media or physical-board validation.', 'status':'pass' if all(c['status']=='pass' for c in checks) else 'fail','checks':checks,'inputs':[],'tested_modules':{},'runtime_warning':'Legacy Android linker reports unsupported DF_1_PIE/NOW flags of existing GNU-linked probe; warning preserved, no suppression.'}
for p in [qemu,probe,old/'evidence/qemu-provision.json',ref/'system/bin/linker']:
 record['inputs'].append({'path':str(p),'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
for name in ['gralloc.rk30board.so','hwcomposer.rk30board.so']:
 p=args.artifacts/name;record['tested_modules'][name]={'size_bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(ev/'loader-smoke-result.json').write_text(json.dumps(record,indent=2)+'\n')
sys.exit(0 if record['status']=='pass' else 1)
