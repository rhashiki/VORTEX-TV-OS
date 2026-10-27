from pathlib import Path
import subprocess,json,hashlib,shutil
root=Path(__file__).resolve().parent
src=Path('/workspace/build01-platform-next/research/mali-legacy/gralloc-rk3328')
out=root/'objects';out.mkdir(exist_ok=True)
local=root/'gralloc-source'
if not local.exists():
 subprocess.run(['git','worktree','add','--detach',str(local),'c92fb8cd8becd57b025149f2861a2072b092ddea'],cwd=src,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 subprocess.run(['git','apply','/workspace/vortex-build/rom/platform-reference/graphics/patches/0002-gralloc-select-mali400-for-rk322x.patch'],cwd=local,check=True)
 shutil.copyfile('/workspace/build01-graphics-next/graphics/hal-build/gralloc-source/version.h',local/'version.h')
old=Path('/workspace/build01-graphics-next/graphics/hal-build')
cmd=json.loads((old/'compile-attempt-01.json').read_text())['command']
base=cmd[:cmd.index('-MD')]
base=[str(local) if p==str(src) else p for p in base]
base+=['-fno-exceptions','-fno-rtti','-fno-strict-aliasing','-I','/workspace/build01-platform-next/research/rockchip-system-core/libion/include']
result=[]
for name in ['gralloc_module','alloc_device','framebuffer_device','rockchip_alloc_device']:
 p=local/(name+'.cpp');obj=out/(name+'.o')
 c=base+['-MD','-MF',str(out/(name+'.d')),str(p),'-o',str(obj)]
 r=subprocess.run(c,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (out/(name+'.log')).write_bytes(r.stdout)
 item={'source':str(p),'source_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'command':c,'exit_code':r.returncode}
 if r.returncode==0:item.update({'object':str(obj),'sha256':hashlib.sha256(obj.read_bytes()).hexdigest(),'bytes':obj.stat().st_size})
 result.append(item)
 if r.returncode:print(r.stdout.decode());break
(root/'compile-gralloc-result.json').write_text(json.dumps({'scope':'Manual ARMv7 softfp object compilation, Android-compatible no-exceptions/no-rtti flags; not AOSP make build or linked HAL.','generated_version_header_sha256':hashlib.sha256((local/'version.h').read_bytes()).hexdigest(),'objects':result},indent=2)+'\n')
print(json.dumps([{'source':i['source'],'exit_code':i['exit_code'],'sha256':i.get('sha256')} for i in result],indent=2))
