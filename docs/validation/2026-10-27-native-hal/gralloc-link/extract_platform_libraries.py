from pathlib import Path
import hashlib,json,os,subprocess,re,shutil
root=Path(__file__).resolve().parent;ev=root/'evidence';reference=root/'reference';lib=reference/'system/lib';bin=reference/'system/bin'
lib.mkdir(parents=True,exist_ok=True);bin.mkdir(parents=True,exist_ok=True)
image=root/'reference-arm32-system.sparse-host.img'
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(root/'host-deps/root/usr/lib/x86_64-linux-gnu')
debugfs=root/'host-deps/root/usr/sbin/debugfs';readelf='/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-readelf'
records=[];queue=['libc.so','libdl.so','libm.so','liblog.so','libcutils.so','libhardware.so','libstdc++.so','libc++.so','libui.so','libutils.so','libEGL.so','libGLESv1_CM.so','libhardware_legacy.so','libsync.so']
# Runtime vendor libion is required by the actual Rockchip ion_get_phys interface.
vendor=Path('/workspace/build01-sd-next/vendor-sd/proprietary/lib')
shutil.copyfile(vendor/'libion.so',lib/'libion.so')
records.append({'name':'libion.so','source':'D042 vendor50c7170ecb4bd907059db37f09f4767b301f2d15/proprietary/lib/libion.so','source_path':str(vendor/'libion.so'),'sha256':hashlib.sha256((lib/'libion.so').read_bytes()).hexdigest(),'bytes':(lib/'libion.so').stat().st_size})
queue.append('libion.so');seen=set()
commands=[]
def dump(src,dest):
 cmd=[str(debugfs),'-R',f'dump {src} {dest}',str(image)]
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 commands.append({'command':cmd,'exit_code':p.returncode,'output':p.stdout.decode(errors='replace')})
 assert dest.is_file() and dest.stat().st_size>0,(src,p.stdout)
# Real ELF32 Android linker, not linker64.
dump('/bin/linker',bin/'linker');(bin/'linker').chmod(0o755)
while queue:
 name=queue.pop(0)
 if name in seen:continue
 assert re.fullmatch(r'[A-Za-z0-9_.+\-]+\.so',name),name
 seen.add(name);dest=lib/name
 if not dest.exists():
  dump('/lib/'+name,dest)
 if not any(r['name']==name for r in records):
  records.append({'name':name,'source':'officialAPI25_google_apis_arm32_system_image/lib/'+name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'bytes':dest.stat().st_size})
 raw=dest.read_bytes()
 assert raw[:4]==b'\x7fELF' and raw[4]==1 and int.from_bytes(raw[18:20],'little')==40,name
 dynamic=subprocess.check_output([readelf,'-d',str(dest)],text=True)
 (ev/(name+'.dynamic.txt')).write_text(dynamic)
 needed=re.findall(r'\(NEEDED\).*Shared library: \[([^]]+)\]',dynamic)
 for dep in needed:
  if dep not in seen:queue.append(dep)
 for record in records:
  if record['name']==name:record['needed']=needed;record['ELF_class']='ELF32';record['machine']='ARM'
assert (bin/'linker').read_bytes()[4]==1
result={'scope':'Actual ELF32/ARM platform libraries selectively extracted with read-only debugfs from checksum-verified official API25 image, plus pinned Rockchip vendor libion. Reference link/runtime only; no BSP or hardware compatibility approval.','archive_reference':'arm32-reference-acquisition.json','libraries':records,'linker':{'path':str(bin/'linker'),'bytes':(bin/'linker').stat().st_size,'sha256':hashlib.sha256((bin/'linker').read_bytes()).hexdigest()},'debugfs_commands':commands,'temporary_image_removed_after_extraction':False}
(ev/'platform-libraries.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'libraries':len(records),'extracted_bytes':sum(r['bytes'] for r in records),'names':[r['name'] for r in records]},indent=2))
