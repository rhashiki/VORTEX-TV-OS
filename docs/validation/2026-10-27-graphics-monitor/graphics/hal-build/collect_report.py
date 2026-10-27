from pathlib import Path
import hashlib,json,subprocess,re
root=Path('/workspace/build01-graphics-next/graphics/hal-build');base=Path('/workspace/build01-platform-next/research');tool=Path('/workspace/build01-sd/kernel-work/toolchain')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Preserve real immutable source refs and tag resolution output.
source_refs={}
for name,p in {'gralloc':root/'gralloc-source','bionic':base/'rockchip-bionic','system_core':base/'rockchip-system-core','libhardware_patched':root.parent/'libhardware'}.items():
 source_refs[name]={'path':str(p),'revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=p,text=True).strip(),'tracked_diff':subprocess.check_output(['git','diff','--name-only'],cwd=p,text=True).splitlines()}
ref=subprocess.run(['git','ls-remote','https://android.googlesource.com/platform/external/libcxx','refs/tags/android-7.1.2_r6','refs/tags/android-7.1.2_r6^{}'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(root/'libcxx-tag-reference.log').write_bytes(ref.stdout)
assert ref.returncode==0 and b'd8170174bf66c98fca967b7133783c0c95292993' in ref.stdout
sources=['framebuffer_device','gralloc_module','alloc_device','rockchip_alloc_device']
records=[];all_deps=set()
for stem in sources+['framebuffer_device-before']:
 obj=root/(stem+'.o');assert obj.exists()
 d=(root/(stem+'.d')).read_text().replace('\\\n',' ')
 deps=[Path(s) for s in d.split(':',1)[1].split()]
 assert all(p.is_file() for p in deps)
 assert not any(str(p).startswith(('/usr/','/lib/')) for p in deps)
 assert root.parent/'libhardware/include/hardware/rk_fh.h' in deps if stem=='framebuffer_device' else True
 all_deps.update(deps)
 readelf=subprocess.check_output([str(tool/'bin/arm-linux-gnueabihf-readelf'),'-h','-A',str(obj)])
 (root/(stem+'.elf.txt')).write_bytes(readelf)
 assert b'ELF32' in readelf and b'ARM' in readelf and b'REL (Relocatable file)' in readelf
 dis=subprocess.check_output([str(tool/'bin/arm-linux-gnueabihf-objdump'),'-dr',str(obj)])
 (root/(stem+'.disassembly.txt')).write_bytes(dis)
 rec={'source_file':stem+'.cpp' if not stem.endswith('-before') else 'framebuffer_device.cpp (originalheaderbaseline)','object':obj.name,'bytes':obj.stat().st_size,'sha256':sha(obj),'dependency_count':len(deps),'readelf':stem+'.elf.txt','disassembly':stem+'.disassembly.txt'}
 if stem.startswith('framebuffer_device'):
  size=904 if stem.endswith('-before') else 908
  assert ('#'+str(size)).encode() in dis
  assert b'R_ARM_THM_CALL\tmemset' in dis and b'ioctl' in dis
  rec['fb_post_memset_size_bytes']=size
 records.append(rec)
dep_records=[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(all_deps)]
(root/'all-dependencies.json').write_text(json.dumps(dep_records,indent=2)+'\n')
report={
 'schema_version':1,
 'scope':'Four real gralloc source translation units compiled independently to ARM relocatable objects with genuine Android headers. This is not an AOSP make build, linked HAL, ioctl execution, Android system or hardware test.',
 'source_refs':source_refs,
 'compiler':{'path':str(tool/'bin/arm-linux-gnueabihf-g++'),'version':subprocess.check_output([str(tool/'bin/arm-linux-gnueabihf-g++'),'--version'],text=True).splitlines()[0],'toolchain_revision':'dd4df7dff4f1df65d78939a958b760a79e3650a1'},
 'headers':{'C_library':'Pinned Rockchip bionic actual includes and generated kernel UAPI headers. -nostdinc and -nostdinc++ prevent automatic host/glibc includes.','Cxx_library':json.loads((root/'libcxx-source.json').read_text()),'GLES_KHR':json.loads((root/'acquired-headers.json').read_text()),'no_fake_headers':True,'no_system_glibc_headers_in_dependencies':True},
 'configuration':{'architecture':'ARMv7, softfp calling convention, NEON enabled','language':'GNU++11','defines':['ANDROID','__ANDROID__','__ANDROID_API__=25','GRALLOC_32_BITS','STANDARD_LINUX_SCREEN','PLATFORM_SDK_VERSION=25','LOG_TAG="gralloc"'],'MALI_600':False,'GRALLOC_ARM_UMP_MODULE':0,'GRALLOC_ARM_DMA_BUF_MODULE':1,'warnings':'No diagnostic suppression or -fpermissive flags were used. No extra -Werror was imposed; raw compiler stdout/stderr were empty for these standalone commands.'},
 'all_four_source_objects_compiled':True,
 'objects':records,
 'unique_dependencies':len(dep_records),
 'dependency_manifest_sha256':sha(root/'all-dependencies.json'),
 'source_changes':'No .cpp file or local gralloc header was modified. version.sh generated the normal version.h only in a new disposable clone. The separate libhardware header patch is the only interface source mutation.',
 'version_generation':{'command':['bash','version.sh'],'working_directory':str(root/'gralloc-source'),'script_sha256':sha(root/'gralloc-source/version.sh'),'template_sha256':sha(root/'gralloc-source/version.h.template'),'generated_header_sha256':sha(root/'gralloc-source/version.h'),'exit_code':0,'failure_note':'The first harness invocation used the parent directory and exited127 (version.sh not found). Preserved as version-generation-attempt-01.log; corrected invocation ran the unmodified source script.'},
 'baseline':'The same original framebuffer TU also compiles against the old libhardware header. Compiler success alone did not detect the ABI defect. Its actual memset size is904; the patched object passes908.',
 'limits':['No linking against libion/GLES/bionic or Android HAL installation.','No claim that a GNU/Linux-targeted compiler plus Android headers reproduces the final Android toolchain code generation or runtime ABI.','No hwcomposer TU build or prebuilt Mali private-handle interface validation.','No runtime display, ioctl, DMA-BUF, RGA, fences, writeback or hardware behavior test.','Header archive safety check initially rejected a real libcxxabi symlink; regular files were extracted without following it. That unused symlink was not replaced by a stub.'],
 'GitHub_Actions':'not_used'}
(root/'gralloc-object-build-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'objects':[{k:r[k] for k in ['object','bytes','sha256']} for r in records],'unique_dependencies':len(dep_records),'no_host_headers':True},indent=2))
