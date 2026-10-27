from pathlib import Path
import json,subprocess,hashlib,re
root=Path('/workspace/build01-hal-next/private-abi')
previous=Path('/workspace/build01-graphics-next/graphics/hal-build')
cmd=json.loads((previous/'compile-attempt-01.json').read_text())['command']
# Reuse the genuine Android/Bionic include closure and ARM flags; only input,
# output and compiler-generated depfile paths change.
fields=['version','numFds','numInts','share_fd','magic','flags','usage','size','width','height','format','stride','type','base','phy_addr','lockState','writeOwner','pid','yuv_info','fd','offset','ion_hnd']
source=root/'private_handle_layout.cpp'
lines=['#include "gralloc_priv.h"','#include <system/window.h>','extern "C" {','#define MEASURE(name, value) unsigned char measure_##name[(value) + 1];',
 'MEASURE(native_handle_size, sizeof(native_handle_t))',
 'MEASURE(private_handle_size, sizeof(private_handle_t))',
 'MEASURE(private_handle_align, __alignof__(private_handle_t))',
 'MEASURE(handle_sNumFds, private_handle_t::sNumFds)',
 'MEASURE(handle_numInts, (sizeof(private_handle_t)-sizeof(native_handle_t))/sizeof(int)-private_handle_t::sNumFds)',
 # magic stored as const scalar because using it as an array would allocate52MB.
 'extern const unsigned int handle_magic = private_handle_t::sMagic;']
for f in fields:
 lines+=['MEASURE('+f+'_offset, __builtin_offsetof(private_handle_t, '+f+'))','MEASURE('+f+'_size, sizeof(((private_handle_t*)0)->'+f+'))']
for f in ['width','height','stride','format','usage','handle']:
 lines+=['MEASURE(anativewindowbuffer_'+f+'_offset, __builtin_offsetof(ANativeWindowBuffer_t, '+f+'))']
lines+=['MEASURE(anativewindowbuffer_size, sizeof(ANativeWindowBuffer_t))','}']
source.write_text('\n'.join(lines)+'\n')
cmd[cmd.index('-MF')+1]=str(root/'private_handle_layout.d')
cmd[cmd.index('-o')+1]=str(root/'private_handle_layout.o')
# input is previousframebuffer before-o
for i,a in enumerate(cmd):
 if a.endswith('/framebuffer_device.cpp'):cmd[i]=str(source)
r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(root/'layout-compile.log').write_bytes(r.stdout)
assert r.returncode==0,r.stdout.decode()
nm='/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-nm'
symbols=subprocess.check_output([nm,'-S','--radix=d',str(root/'private_handle_layout.o')],text=True)
(root/'layout-symbols.txt').write_text(symbols)
values={}
for line in symbols.splitlines():
 m=re.match(r'\d+\s+(\d+)\s+\w\s+measure_(\w+)$',line)
 if m:values[m.group(2)]=int(m.group(1))-1
assert len(values)==56,len(values)
# Read the compiled scalar from its symbol in .rodata (not a copied value).
magic=re.search(r'^(\d+)\s+(\d+)\s+R\s+handle_magic$',symbols,re.M)
assert magic and int(magic.group(2))==4
objcopy='/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf-objcopy'
subprocess.run([objcopy,'-O','binary','-j','.rodata',str(root/'private_handle_layout.o'),str(root/'layout-rodata.bin')],check=True)
start=int(magic.group(1));values['handle_magic']=int.from_bytes((root/'layout-rodata.bin').read_bytes()[start:start+4],'little')
report={'scope':'Compile-time layout of the real full pinned gralloc header using ARMv7 softfp and real Android headers; no graphics execution or ABI compatibility claim.','command':cmd,'compile_exit_code':r.returncode,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256((root/'private_handle_layout.o').read_bytes()).hexdigest(),'values':values,'warnings':'GCC reports conditionally-supported offsetof on derived non-standard-layout private_handle_t; diagnostics preserved, not suppressed.'}
(root/'private-handle-layout.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(values,indent=2))
