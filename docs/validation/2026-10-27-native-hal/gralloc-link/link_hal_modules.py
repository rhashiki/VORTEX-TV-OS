from pathlib import Path
import subprocess,json,hashlib,re
root=Path(__file__).resolve().parent;ev=root/'evidence';art=root/'artifacts';art.mkdir(exist_ok=True)
tool=Path('/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-gcc');readelf=tool.with_name('arm-linux-gnueabihf-readelf')
lib=root/'reference/system/lib';crt=root/'crt'
sets={
 'gralloc.rk30board.so':{'objects':sorted((root/'objects').glob('*.o')),'libraries':['liblog.so','libcutils.so','libGLESv1_CM.so','libion.so','libhardware.so','libstdc++.so','libc++.so','libc.so','libm.so','libdl.so']},
 'hwcomposer.rk30board.so':{'objects':sorted(Path('/workspace/build01-hal-next/hwc-format/evidence/final').glob('*.o')),'libraries':['libhardware.so','liblog.so','libui.so','libEGL.so','libcutils.so','libion.so','libhardware_legacy.so','libsync.so','libstdc++.so','libc++.so','libc.so','libm.so','libdl.so']}}
results=[]
for name,selection in sets.items():
 objs=selection['objects'];assert len(objs)==(4 if name.startswith('gralloc.') else 8),(name,objs)
 cmd=[str(tool),'-nostdlib','-shared','-march=armv7-a','-mfloat-abi=softfp','-mfpu=neon','-Wl,--no-undefined','-Wl,--no-allow-shlib-undefined','-Wl,-z,defs','-Wl,-z,relro','-Wl,-z,now','-Wl,--hash-style=both','-Wl,-soname,'+name,'-Wl,-rpath-link,'+str(lib),'-Wl,-Map,'+str(ev/(name+'.map')),str(crt/'crtbegin_so.o'),str(crt/'crtbrand.o'),*[str(p) for p in objs],'-L'+str(lib),'-Wl,--no-as-needed',*['-l:'+n for n in selection['libraries']],str(crt/'crtend_so.o'),'-o',str(art/name)]
 p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (ev/(name+'.link.log')).write_bytes(p.stdout)
 item={'module':name,'scope':'Manual strict reference link against real API25 ARM platform libraries plus pinned vendorlibion, not an AOSP build or hardware validation.','command':cmd,'exit_code':p.returncode,'object_inputs':[{'path':str(o),'sha256':hashlib.sha256(o.read_bytes()).hexdigest()} for o in objs],'libraries':selection['libraries']}
 if p.returncode==0:
  module=art/name
  item.update({'path':str(module),'bytes':module.stat().st_size,'sha256':hashlib.sha256(module.read_bytes()).hexdigest()})
  for flags,suffix in [(['-h','-A','-d'],'elf'),(['-Ws'],'symbols')]:
   raw=subprocess.check_output([str(readelf),*flags,str(module)],text=True)
   (ev/(name+'.'+suffix+'.txt')).write_text(raw)
  dynamic=subprocess.check_output([str(readelf),'-d',str(module)],text=True)
  item['DT_NEEDED']=re.findall(r'\(NEEDED\).*Shared library: \[([^]]+)\]',dynamic)
 print(name,p.returncode,p.stdout.decode(errors='replace')[:1800])
 results.append(item)
(ev/'hal-link-results.json').write_text(json.dumps({'platform_reference':'API25/ARM32 GoogleSDKreferenceELFs, vendor50c7170... libion','modules':results,'fake_stubs_used':False,'unresolved_symbol_suppression':False},indent=2)+'\n')
