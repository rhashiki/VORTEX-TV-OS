from pathlib import Path
import subprocess,json,hashlib
root=Path('/workspace/build01-graphics-next/graphics/hal-build');base=Path('/workspace/build01-platform-next/research')
original=base/'mali-legacy/gralloc-rk3328';clone=root/'gralloc-source'
first=json.loads((root/'compile-attempt-01.json').read_text())
results=[]
for name in ['gralloc_module.cpp','alloc_device.cpp','rockchip_alloc_device.cpp']:
 cmd=first['command'][:-7]
 # Original tail is -MD -MF dependency source -o object; remove exactly six items.
 cmd=first['command'][:first['command'].index('-MD')]
 cmd=[str(clone) if c==str(original) else c for c in cmd]
 cmd+=['-I',str(base/'rockchip-system-core/libion/include')]
 stem=Path(name).stem
 cmd+=['-MD','-MF',str(root/(stem+'.d')),str(clone/name),'-o',str(root/(stem+'.o'))]
 result=subprocess.run(cmd,cwd=clone,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (root/(stem+'-attempt-01.log')).write_bytes(result.stdout)
 record={'source':name,'source_sha256':hashlib.sha256((clone/name).read_bytes()).hexdigest(),'command':cmd,'exit_code':result.returncode}
 if result.returncode==0:
  record['object_sha256']=hashlib.sha256((root/(stem+'.o')).read_bytes()).hexdigest()
 (root/(stem+'-attempt-01.json')).write_text(json.dumps(record,indent=2)+'\n');results.append(record)
 print(name,'exit',result.returncode);print(result.stdout.decode(errors='replace'))
(root/'remaining-results.json').write_text(json.dumps(results,indent=2)+'\n')
# Baseline: same untouched TU and flags against the original complete libhardware header.
cmd=first['command'][:]
cmd=[str(base/'rockchip-libhardware/include') if c=='/workspace/build01-graphics-next/graphics/libhardware/include' else c for c in cmd]
cmd=[str(root/'framebuffer_device-before.d') if c==str(root/'framebuffer_device.d') else c for c in cmd]
cmd=[str(root/'framebuffer_device-before.o') if c==str(root/'framebuffer_device.o') else c for c in cmd]
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(root/'framebuffer_device-before.log').write_bytes(r.stdout)
(root/'framebuffer_device-before.json').write_text(json.dumps({'command':cmd,'exit_code':r.returncode,'scope':'Baseline can compile despite the original unsafe 904-byte ioctl declaration.'},indent=2)+'\n')
print('baseline framebuffer',r.returncode)
