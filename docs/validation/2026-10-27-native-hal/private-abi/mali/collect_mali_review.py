from pathlib import Path
import hashlib,json,subprocess,struct
root=Path(__file__).resolve().parent
vendor=Path('/workspace/build01-sd-next/vendor-sd')
blob=vendor/'proprietary/lib/egl/libGLES_mali.so'
tool=Path('/workspace/build01-sd/kernel-work/toolchain/bin')
commands=[]
def run(args,out):
 p=subprocess.run([str(a) for a in args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 assert p.returncode==0,out
 (root/out).write_bytes(p.stdout)
 commands.append({'argv':[str(a) for a in args],'exit_code':p.returncode,'output':out})
run([tool/'arm-linux-gnueabihf-readelf','-h','-d','-A',blob],'elf-metadata.txt')
run([tool/'arm-linux-gnueabihf-readelf','--dyn-syms','-W',blob],'dynamic-symbols.txt')
for label,start,end in [('initialize-gralloc',0xf794,0xf804),('flags-sharefd',0xf644,0xf794),('validation-and-fields',0x10224,0x103c8),('validation-second-path',0x106ac,0x107f4),('yuv-validation-lock',0x118ac,0x11a70),('format-read',0x12668,0x126c0)]:
 run([tool/'arm-linux-gnueabihf-objdump','-d','--start-address='+hex(start),'--stop-address='+hex(end),blob],label+'.txt')
original=subprocess.check_output(['git','show','HEAD:proprietary/lib/egl/libGLES_mali.so'],cwd=vendor)
assert original==blob.read_bytes()
b=blob.read_bytes();phoff=struct.unpack_from('<I',b,28)[0];phentsize,phnum=struct.unpack_from('<HH',b,42)
headers=[struct.unpack_from('<IIIIIIII',b,phoff+i*phentsize) for i in range(phnum)]
module_id_address=0xf7b8+8+0x10cb25
module_id=None
for ptype,off,va,pa,filesz,memsz,flags,align in headers:
 if ptype==1 and va<=module_id_address<va+filesz:
  pos=off+module_id_address-va
  module_id=b[pos:b.index(0,pos)].decode('ascii')
assert module_id=='gralloc'
result={
 'schema_version':1,
 'scope':'Read-only static ELF/disassembly inspection of named public platform entry points and adjacent unnamed helper ranges; no blob execution, no full private ABI approval.',
 'blob':{'repository':'https://github.com/D042888-2/android_vendor_rockchip_rk322x','revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=vendor,text=True).strip(),'file':'proprietary/lib/egl/libGLES_mali.so','size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'matches_pinned_git_blob':True},
 'ELF':{'class':'ELF32','machine':'ARM','byte_order':'little-endian','EABI':'5','float_calling_convention':'soft-float ABI per ELF e_flags; NEON/VFP attributes also present','SONAME':'libGLES_mali.so','stripped':True,'DT_NEEDED':['libutils.so','libcutils.so','libbinder.so','libc.so','libdl.so','libui.so','libhardware.so','liblog.so','libc++.so','libm.so']},
 'gralloc_module_lookup':{'function':'__egl_platform_initialize_android','function_address':'0x0000f794','hw_get_module_call':'0x0000f7c0','module_id_string_address':hex(module_id_address),'module_id':module_id},
 'observed_handle_validation':{'helper_start':'0x00010224','buffer_handle_load':'0x00010264: ldr r4,[fp,#60]','checks':[{'address':'0x10278-0x10280','handle_offset':0,'required_value':12,'interpretation':'native_handle version'},{'address':'0x10284-0x10288','handle_offset':4,'required_value':1,'interpretation':'native_handle numFds'},{'address':'0x1028c-0x10294','handle_offset':8,'required_value':22,'interpretation':'native_handle numInts'},{'address':'0x10298-0x102a8','handle_offset':16,'required_value':'0x03141592','interpretation':'private magic'}],'same_checks_second_path':'0x106f0-0x10724','same_checks_yuv_path':'0x118dc-0x11918','implied_serialized_handle_size_bytes':104,'size_derivation':'12 + 4*(1 fd + 22 ints); this is derived from checks, not proof of every field or native_handle_create behavior.'},
 'observed_private_field_reads':[{'address':'0x102ac','handle_offset':20,'interpretation':'flags; subsequent tests of bits1,2,4 match selected source FRAMEBUFFER/UMP/ION flag constants','test_addresses':['0x102b0','0x102b8','0x102c0']},{'address':'0x10344','handle_offset':88,'interpretation':'framebuffer branch fd used as ioctl first argument, matching source fd field'},{'address':'0x10354','handle_offset':92,'interpretation':'framebuffer branch offset value, source semantic comparison still requires measured source layout'},{'address':'0x10374','handle_offset':56,'interpretation':'base address read in buffer-lock/import path'},{'address':'0x10380','handle_offset':28,'interpretation':'size read in buffer-lock/import path'},{'address':'0x103a4-0x103ac','handle_offset':40,'interpretation':'format read after reloading handle from buffer+60'},{'address':'0xf64c,0xf664,0xf680','handle_offset':12,'interpretation':'helper loads buffer handle via r1+60, tests flags at+20 then imports the handle+12 value on ION branch; candidate calls this share_fd'}],
 'gralloc_callback_offsets':[{'address':'0x1038c,0x103a0','module_offset':136,'role':'lock-shaped callback with rect and vaddr output arguments'},{'address':'0x11970-0x1197c','module_offset':140,'role':'unlock-shaped callback with module and handle arguments'}],
 'assessment':'The blob validates the selected legacy handle fingerprint and uses several field offsets consistent with the proposed source layout. Parent full-header ARM probe must independently measure those source offsets before claiming field-level equality. This audit does not establish complete Mali private ABI compatibility.',
 'limits':['No vendor GPU execution, EGL initialization, buffer allocation/import, ioctl, mapping, rendering or hardware exercised.','Most local symbols are stripped. Objdump labels such as exported_symbol+offset denote nearest public symbol, not trustworthy original names for local helpers. Helpers are identified by address ranges only.','Observed handle checks cover fingerprint and selected reads; other paths, lifetime, usage, cache/coherency, fences, pixel formats and allocator semantics remain unverified.','Loading ELF metadata does not validate that DT_NEEDED libraries exist, export required versions or will load on the future Android image.'],
 'commands':commands}
(root/'mali-static-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'blob':result['blob'],'observed_validation':result['observed_handle_validation'],'field_count':len(result['observed_private_field_reads'])},indent=2))
