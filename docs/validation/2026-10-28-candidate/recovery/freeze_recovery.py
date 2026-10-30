#!/usr/bin/env python3
"""Freeze a partial genuine recovery source build without running its outputs."""
from pathlib import Path
from collections import defaultdict
import base64,hashlib,json,os,shlex,shutil,struct,subprocess
R=Path(__file__).resolve().parent;T=R/'tree';O=R/'out/target/product/generic/obj';E=R/'evidence-package';A=R/'artifacts'
E.mkdir(exist_ok=True);A.mkdir(exist_ok=True)
MAX=240000

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p):return {'path':str(p),'bytes':p.stat().st_size,'sha256':digest(p)}
def write(name,value):
 p=E/name;p.parent.mkdir(parents=True,exist_ok=True);data=(json.dumps(value,indent=2)+'\n').encode();assert len(data)<=MAX,(name,len(data));p.write_bytes(data)
def copy(p,name=None):
 p=Path(p);target=E/(name or str(p.relative_to(R)));target.parent.mkdir(parents=True,exist_ok=True);assert p.stat().st_size<=MAX,(p,p.stat().st_size);shutil.copyfile(p,target)
def write_parts(prefix,rows):
 names=[];chunk=[];size=2
 for row in rows:
  encoded=json.dumps(row,indent=2).encode();delta=len(encoded)+2*len(encoded.splitlines())+4
  if chunk and size+delta>MAX-3000:
   name=f'{prefix}-{len(names):03}.json';write(name,chunk);names.append(name);chunk=[];size=2
  chunk.append(row);size+=delta
 if chunk:
  name=f'{prefix}-{len(names):03}.json';write(name,chunk);names.append(name)
 return names

def elf_info(data):
 assert data[:4]==b'\x7fELF' and data[4]==1 and data[5]==1,'ELF32 little-endian required'
 typ,machine=struct.unpack_from('<HH',data,16);assert machine==40,'ARM required'
 return {'class':'ELF32','machine':'ARM','type':typ}
def archive_info(path):
 data=path.read_bytes();assert data[:8]==b'!<arch>\n','Self-contained GNU ar required';off=8;count=0
 while off<len(data):
  h=data[off:off+60];assert len(h)==60 and h[58:]==b'`\n';size=int(h[48:58]);name=h[:16].strip();body=data[off+60:off+60+size]
  if name not in (b'/',b'//',b'/SYM64/'):
   elf_info(body);count+=1
  off+=60+size+(size%2)
 assert off==len(data);return {'format':'GNU ar','elf32_arm_members':count}

def artifact(p,relative,kind):
 target=A/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target)
 info=record(target);info['path']=relative;info['kind']=kind
 info['inspection']=archive_info(target) if target.suffix=='.a' else elf_info(target.read_bytes())
 return info

raw=[];logsummary=[]
for p in sorted(R.glob('*.log')):
 lines=p.read_text(errors='replace').splitlines();errors=[x for x in lines if ': error:' in x or 'fatal error:' in x or 'make: ***' in x]
 info=record(p);info['path']=p.name;info['zip_path']='raw-logs/recovery/'+p.name;info['last_errors']=errors[-4:]
 if p.stat().st_size<=MAX:copy(p);info['versioned_raw_log']=True
 else:
  raw.append(info);info['versioned_raw_log']=False
  excerpt='\n'.join(lines[:32]+['[middle omitted; raw log hash and ZIP path in log-index.json]']+lines[-45:])+'\n';target=E/'log-excerpts'/p.name;target.parent.mkdir(exist_ok=True);target.write_text(excerpt)
 logsummary.append(info)
for p in [R/'recovery-link.map']:
 if p.exists():
  info=record(p);info.update({'path':p.name,'zip_path':'raw-logs/recovery/'+p.name,'versioned_raw_log':False});raw.append(info)
write('log-index.json',logsummary);write('raw-log-index.json',raw)
for name in ['attempt_make.sh','attempt_source_only.sh','build_static_components.sh','linkmap-tail.mk','0001-common-recovery-match-nougat-device-api.patch','source-provenance.json','safe-iop-acquisition.json','ndk9-acquisition.json','vendor-link-map-review.json','recovery-elf.txt','freeze_recovery.py']:
 p=R/name
 if p.exists():copy(p)
for sub in ['review','ui-regression']:
 for p in sorted((R/sub).rglob('*')):
  if p.is_file() and p.suffix in ['.json','.log','.cpp','.h','.py','.sha256'] and p.stat().st_size<=MAX:copy(p)
for name in ['Android.mk','device.h','ui.h','screen_ui.h','sdboot.cpp','recovery.cpp','install.cpp']:
 copy(R/'source'/name,'review-source/'+name)
copy(T/'device/rockchip/common/recovery/recovery_ui.cpp','review-source/recovery_ui.cpp')
copy(R/'recovery_ui.baseline.cpp','review-source/recovery_ui.baseline.cpp')

units=[];inputs={};counts=defaultdict(int)
for p in sorted(O.rglob('*.P')):
 if 'WHOLE' in p.parts or not p.with_suffix('.o').is_file():continue
 obj=p.with_suffix('.o');joined=p.read_text(errors='strict').replace('\\\n',' ');line=joined.splitlines()[0];parts=line.split(':',1);deps=shlex.split(parts[1])
 module=p.relative_to(O).parts[1] if p.relative_to(O).parts[0] in ('STATIC_LIBRARIES','SHARED_LIBRARIES','EXECUTABLES') else 'crt'
 counts[module]+=1;observed=[]
 for item in deps:
  path=Path(item);path=path if path.is_absolute() else T/path;resolved=path.resolve()
  assert not any(resolved==Path(x) or Path(x) in resolved.parents for x in ['/dev','/proc','/sys'])
  key=str(resolved)
  if key not in inputs:
   inputs[key]=record(resolved) if resolved.is_file() else {'path':key,'status':'missing_after_build'}
   inputs[key]['id']=len(inputs)-1
  observed.append(inputs[key]['id'])
 units.append({'object':str(obj.relative_to(O)),'module':module,'object_sha256':digest(obj),'dependency_file_sha256':digest(p),'input_ids':observed})
parts=write_parts('compiler-inputs',list(inputs.values()));unitparts=write_parts('compile-rules',units)
write('compiler-inputs-index.json',{'scope':'Observed compiler-generated dependencies, not all theoretical source/runtime inputs','compile_rules':len(units),'unique_resolved_inputs':len(inputs),'input_reference_format':'integer IDs resolve through compiler-inputs parts','counts_by_module':counts,'input_parts':parts,'rule_parts':unitparts})

outputs=[];excluded={'librkupdate','librkrsa','libext2_uuid','libcrc32'}
for p in sorted((O/'STATIC_LIBRARIES').glob('*_intermediates/*.a')):
 module=p.parent.name.removesuffix('_intermediates')
 if module in excluded:continue
 outputs.append(artifact(p,'static/'+p.name,'source-built static module archive'))
for name in ['libc.so','libdl.so','libm.so']:
 p=O/'lib'/name
 if p.exists():outputs.append(artifact(p,'shared/'+name,'source-built Bionic shared module'))
for p in sorted((O/'EXECUTABLES/recovery_intermediates').glob('*.o')):
 outputs.append(artifact(p,'recovery-main/'+p.name,'compiled main translation unit; not linked executable'))
for p in sorted((O/'lib').glob('crt*.o')):
 outputs.append(artifact(p,'crt/'+p.name,'source-built CRT input or combined relocatable object'))
exe=R/'out/target/product/generic/recovery/root/sbin/recovery'
compiled_executable=exe.is_file()
if compiled_executable:outputs.append(artifact(exe,'recovery/recovery','compiled recovery ELF with source modules and pinned vendor static inputs; not recovery.img'))
write('artifacts.json',outputs)

registry=[]
for rel in ['build','bionic','system/core','hardware/libhardware','bootable/recovery','external/compiler-rt','external/libunwind_llvm','external/zlib','external/libpng','external/boringssl','external/jemalloc','external/libcxx','external/libcxxabi','external/libselinux','external/libdrm','external/fec','external/squashfs-tools','external/pcre','external/bzip2','system/extras','libnativehelper','system/vold']:
 p=T/rel
 if not p.exists():continue
 try:
  head=subprocess.check_output(['git','--no-replace-objects','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(p),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip();top=subprocess.check_output(['git','--no-replace-objects','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(p),'rev-parse','--show-toplevel'],text=True,stderr=subprocess.DEVNULL).strip()
  if Path(top).resolve()!=p.resolve():raise ValueError('Parent Git tree is not a project proof')
  url=subprocess.check_output(['git','--no-replace-objects','-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-C',str(p),'remote','get-url','origin'],text=True,stderr=subprocess.DEVNULL).strip();registry.append({'path':rel,'resolved':str(p.resolve()),'head':head,'url':url,'observed_compiler_input_hashes':'compiler-inputs-index.json'})
 except (subprocess.CalledProcessError,ValueError):registry.append({'path':rel,'resolved':str(p.resolve()),'status':'header/source subset; consult compiler input hashes and acquisition provenance'})
write('source-registry.json',registry)
license_paths=[T/'bionic/NOTICE',T/'bionic/libc/NOTICE',T/'bionic/libm/NOTICE',T/'system/core/NOTICE',T/'system/extras/NOTICE',T/'external/libpng/LICENSE',T/'external/boringssl/NOTICE',T/'external/jemalloc/COPYING',T/'external/libcxx/NOTICE',T/'external/libcxxabi/NOTICE',T/'external/libselinux/NOTICE',T/'external/zlib/NOTICE',T/'external/libdrm/NOTICE',T/'external/fec/NOTICE',T/'external/squashfs-tools/NOTICE',T/'external/pcre/NOTICE',T/'external/bzip2/LICENSE',T/'external/compiler-rt/LICENSE.TXT',T/'external/compiler-rt/NOTICE',T/'external/libunwind_llvm/LICENSE.TXT',R/'deps/safe-iop/NOTICE']
lic=[]
for index,p in enumerate(license_paths):
 if p.is_file():
  dest='licenses/'+str(index).zfill(2)+'-'+p.name
  data=p.read_bytes();parts=[];encoding='UTF-8 exact bytes'
  try:data.decode('utf-8')
  except UnicodeDecodeError:encoding='base64 of original legacy text bytes'
  if encoding.startswith('base64'):
   part=dest+'.base64.txt';q=E/part;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(base64.encodebytes(data));parts=[part]
  elif len(data)<=MAX:copy(p,dest);parts=[dest]
  else:
   start=0
   while start<len(data):
    end=min(start+180000,len(data))
    if end<len(data):end=data.rfind(b'\n',start,end)+1
    assert end>start
    part=dest+f'.part{len(parts):03}.txt';q=E/part;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data[start:end]);parts.append(part);start=end
  q=A/dest;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);meta=record(q);meta.update({'path':dest,'kind':'upstream source license notice','inspection':'original upstream license bytes; legacy text encodings retained'});outputs.append(meta)
  lic.append({'source':str(p),'evidence_parts_in_order':parts,'artifact_original':dest,'sha256':digest(p),'evidence_encoding':encoding,'reconstruction':'base64-decode when indicated; otherwise concatenate parts in order for byte-identical original notice'})
write('license-provenance.json',lic)
write('artifacts.json',outputs)
main_objects=[p for p in outputs if p['kind'].startswith('compiled main')];archives=[p for p in outputs if p['kind'].startswith('source-built static')]
report={'scope':'genuine Android.mk recovery/static-platform source compilation experiment','status':'compiled_recovery_executable_with_vendor_static_inputs' if compiled_executable else 'partial_source_build','counts':{'compiler_dependency_rules_with_objects':len(units),'primary_objects_including_combined_crt':sum(p.is_file() and 'WHOLE' not in p.parts for p in O.rglob('*.o')),'source_static_archive_modules':len(archives),'source_bionic_dsos':3,'vendor_archive_inputs_named_by_link':4,'recovery_main_objects':len(main_objects),'ui_host_checks':20},'ui_archive_in_full_recovery':'not selected by aosp_arm baseline; independently compiled/tested only','artifacts':outputs,'raw_logs_outside_git':raw,'recovery_executable':record(exe) if compiled_executable else 'not_built','recovery_image':'not_built','hardware_or_pid1_execution':'not_performed','vendor_prebuilt_modules_excluded':sorted(excluded),'limits':['No recovery executable or image was run; no device commands, mounts, format or flash were executed.','Raw recovery source contains writable update/format functionality, including fw_update and IDBlock paths. It is not a read-only diagnostic component.','Libraries, objects and complete recovery have static ELF inspection only; no recovery invocation, Android boot, storage driver behavior or R329Q_V8.0 compatibility is proven.','Compiler-rule counts exclude WHOLE-extracted duplicate objects; combined CRT relocatable outputs without dependency rules are not new source translation units.','Four vendor prebuilt archive files are excluded as standalone artifacts. Three have allocated contributions in the linked executable; source/right/backend closure is not established. See vendor-link-map-review.json.']}
write('recovery-build-result.json',report)
summary='''# Recovery Rockchip/Nougat: source-build checkpoint\n\nThe genuine Android.mk rules compiled the main recovery units, source libraries\nand Bionic shared/static components recorded in recovery-build-result.json.\nThe complete static recovery ELF now links/strips/installs into the build output.\nIt was never executed. This is not recovery.img, an SD card or an Android ROM.\n\nThe opt-in common UI patch fixes the Device constructor/menu API and removes\nthe obsolete one-argument key callback, retaining the platform policy. Twenty\nhost fixture assertions pass; the original source fails compilation as expected.\nThe baseline generic aosp_arm experiment still compiles default_device.cpp;\nthe corrected UI archive is tested separately and is not shown linked into\na complete recovery.\n\nThe SDK runtime DSOs were not used as static libc substitutes. Genuine Bionic\nsource CRT, libc/libdl/libm shared libraries and the listed static archives\nwere built by Android rules. The recovery link names four genuine vendor archives;\nlink-map allocated contributions are observed for librkupdate, libext2_uuid and\nlibcrc32, while librkrsa has no selected members in this build. This is a mixed\nsource/prebuilt-input executable, not fully source-built. ELF inspection is not\nruntime or physical proof.\nThe static archive count excludes WHOLE copies; source-unit counts come from\ncompiler dependency rules with matching object outputs.\n\nRaw recovery sdboot/recovery code can dispatch fw_update and update IDBlock.\nThat source is not a read-only diagnostic or an approved installer backend.\nThe four vendor prebuilt archive inputs are identified in the review and are\nexcluded from the delivered artifact directory; complete source/license/backend\nclosure is not inferred.\n\nSmall raw logs are retained verbatim here. Larger logs are indexed by exact\nbytes/SHA256 and their raw-logs/recovery ZIP paths in raw-log-index.json.\nPaths are concrete workspace paths. Recipes require the genuine pinned source\nand toolchain inputs; they do not download/flash/prepare media automatically.\nLicense notices retain their per-source origin, without assigning a uniform\nlicense to all upstream material.\n'''
(E/'README.md').write_text(summary)
files=sorted(p for p in E.rglob('*') if p.is_file() and p.name!='evidence.sha256')
for p in files:
 assert p.stat().st_size<=MAX,(p,p.stat().st_size);p.read_bytes().decode('utf-8');assert b'\x00' not in p.read_bytes()
(E/'evidence.sha256').write_text(''.join(digest(p)+'  '+str(p.relative_to(E))+'\n' for p in files))
handoff={'scope':report['scope'],'status':report['status'],'evidence_package':str(E),'artifact_directory':str(A),'counts':report['counts'],'text_files_including_manifest':len(files)+1,'evidence_manifest_sha256':digest(E/'evidence.sha256'),'artifacts':outputs,'raw_logs':raw,'last_attempt':max(R.glob('attempt-*.log'),key=lambda p:p.stat().st_mtime).name,'final_stop':'Static recovery executable build passed; no image packing, runtime or physical validation' if compiled_executable else 'See last_attempt/log-index.json errors','patch':str(R/'0001-common-recovery-match-nougat-device-api.patch')}
(R/'handoff.json').write_text(json.dumps(handoff,indent=2)+'\n')
print(json.dumps({k:v for k,v in handoff.items() if k not in ('artifacts','raw_logs')},indent=2))
