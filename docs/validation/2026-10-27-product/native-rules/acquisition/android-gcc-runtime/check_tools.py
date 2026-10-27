from pathlib import Path
import json,subprocess,hashlib,os,re
root=Path('/workspace/build01-product-next/native-rules/acquisition/android-gcc-runtime');prefix=Path('/workspace/build01-product-next/native-rules/tree/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9/bin/arm-linux-androideabi-')
records=[]
def run(label,args,input=None):
 p=subprocess.run(args,input=input,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (root/(label+'.log')).write_bytes(p.stdout)
 records.append({'label':label,'command':args,'exit_code':p.returncode,'log':label+'.log'})
 return p
for name in ['gcc','g++','ld']:
 p=run(name+'-version',[str(prefix)+name,'--version']);print(name,p.returncode,p.stdout.decode().splitlines()[0]);assert p.returncode==0
for name in ['gcc','g++','as','ld']:
 p=run(name+'-ldd',['ldd',str(prefix)+name]);assert b'not found' not in p.stdout
out=root/'empty-arm.o';p=run('empty-arm-compile',[str(prefix)+'gcc','-c','-x','c','-fPIC','-march=armv7-a','-mfpu=neon','-mfloat-abi=softfp','-o',str(out),'-'],b'int vortex_tool_probe;\n');assert p.returncode==0,p.stdout
p=run('empty-arm-readelf',[str(prefix)+'readelf','-h','-A',str(out)]);assert p.returncode==0 and b'ARM' in p.stdout
assert b'VFP registers' not in p.stdout
selected={}
for name,arg in [('libgcc','-print-libgcc-file-name'),('libatomic','-print-file-name=libatomic.a')]:
 p=run(name+'-selected',[str(prefix)+'gcc','-march=armv7-a','-mthumb','-mfpu=neon','-mfloat-abi=softfp',arg]);assert p.returncode==0
 path=Path(p.stdout.decode().strip()).resolve();assert path.is_file()
 p=run(name+'-archive-attributes',[str(prefix)+'readelf','-h','-A',str(path)]);assert p.returncode==0
 assert b'VFP registers' not in p.stdout
 assert b'hard-float ABI' not in p.stdout
 syms=run(name+'-archive-symbols',[str(prefix)+'nm','-g','--defined-only',str(path)])
 selected[name]={'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size,'ARM_members':p.stdout.count(b'Machine:                           ARM'),'hard_VFP_calling_convention_diagnostics':0}
result={'scope':'Genuine official Android GCC4.9 host tools and selected runtime archive readiness; no HAL/platform build in this task.','tool_prefix':str(prefix),'commands':records,'selected_runtime_archives':selected,'empty_ARM_softfp_object_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'source_revision':'0390252b6bcc6217966ade31d07f8b12f6f78f89','system_packages_changed':False}
(root/'readiness.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(selected,indent=2))
