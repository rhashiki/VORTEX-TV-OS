from pathlib import Path
import json,subprocess,hashlib
root=Path(__file__).resolve().parent;ev=root/'evidence';out=root/'crt';out.mkdir(exist_ok=True)
bionic=Path('/workspace/build01-platform-next/research/rockchip-bionic')
base=json.loads((root/'compile-gralloc-result.json').read_text())['objects'][0]['command']
base=base[:base.index('-MD')]
base[0]=base[0].replace('g++','gcc')
base=[a for a in base if a not in ['-fno-exceptions','-fno-rtti']]
base=['-std=gnu11' if a=='-std=gnu++11' else a for a in base]
base+=['-fno-stack-protector','-fno-omit-frame-pointer','-fno-builtin','-I',str(bionic/'libc/private')]
records=[]
for n in ['crtbegin_so.c','crtend_so.S','crtbrand.S']:
 src=bionic/'libc/arch-common/bionic'/n
 obj=out/(n.rsplit('.',1)[0]+'.o')
 cmd=base+['-MD','-MF',str(out/(obj.stem+'.d')),str(src),'-o',str(obj)]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (ev/(obj.stem+'-compile.log')).write_bytes(p.stdout)
 record={'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'command':cmd,'exit_code':p.returncode}
 if p.returncode==0:record.update({'object':str(obj),'sha256':hashlib.sha256(obj.read_bytes()).hexdigest()})
 records.append(record)
 print(n,p.returncode,p.stdout.decode(errors='replace')[:300])
(root/'shared-crt-compile.json').write_text(json.dumps({'source_revision':'8b2e5b977118ebb8447cdf429c4a6be534c4fd1b','records':records},indent=2)+'\n')
