#!/usr/bin/env python3
"""Metadata-only smoke with source-built Bionic DSOs in a copied reference prefix."""
from pathlib import Path
import hashlib,json,re,shutil,subprocess

ROOT=Path(__file__).resolve().parent
PREFIX=ROOT/'reference'
EV=ROOT/'evidence'
REFERENCE=Path('/workspace/build01-hal-next/gralloc-link/reference')
RECOVERY=Path('/workspace/build01-full-next/recovery/out/target/product/generic/obj/lib')
AUDIO=Path('/workspace/build01-full-next/audio/artifacts/system/lib')
PROBE=Path('/workspace/build01-full-next/audio/loader/hal_metadata_probe')
QEMU=Path('/workspace/build01-hal-next/loader/bin/qemu-arm-static')
OVERRIDES={
 'libc.so':'45aaba04bbeea0cd15d2809748b394e74c4248c4ad3bd479428f8d88ebef3a81',
 'libdl.so':'dd3e9269e81bcff5aac34f7237fb186950cdd9869619b8e29e746b521f35b86f',
 'libm.so':'79c2055323dedb9ac176c45f391bfffee2ff7d44358b3c5a89ced52dee35fa72',
}
def sha(data):return hashlib.sha256(data).hexdigest()
def record(path):
 data=path.read_bytes();return {'path':str(path),'size_bytes':len(data),'sha256':sha(data)}
def copied(source,destination,origin):
 data=source.read_bytes();destination.parent.mkdir(parents=True,exist_ok=True)
 destination.write_bytes(data);destination.chmod(0o444)
 return {'destination':str(destination.relative_to(PREFIX)),'origin':origin,'source':str(source),'size_bytes':len(data),'sha256':sha(data)}

def main():
 if PREFIX.exists():raise SystemExit('Reference prefix already exists; preserve it and choose a new stage for a different experiment.')
 EV.mkdir(exist_ok=True)
 records=[]
 for original in sorted((REFERENCE/'system/lib').glob('*.so')):
  source=RECOVERY/original.name if original.name in OVERRIDES else original
  data=source.read_bytes()
  if original.name in OVERRIDES:assert sha(data)==OVERRIDES[original.name],original.name
  records.append(copied(source,PREFIX/'system/lib'/original.name,'source-built Bionic from recovery actual Android.mk' if original.name in OVERRIDES else 'unchanged official API25 reference or pinned libion; not source-built here'))
 for source in sorted(AUDIO.glob('*.so')):
  assert not (PREFIX/'system/lib'/source.name).exists(),source.name
  records.append(copied(source,PREFIX/'system/lib'/source.name,'source-built audio dependency from actual Android.mk'))
 records.append(copied(REFERENCE/'system/bin/linker',PREFIX/'system/bin/linker','unchanged actual Android ARM32 reference linker'))
 (EV/'runtime-inputs.json').write_text(json.dumps({'scope':'private copied test runtime only; do not redistribute SDK/vendor DSOs','files':records,'source_bionic_revision':'8b2e5b977118ebb8447cdf429c4a6be534c4fd1b','probe':record(PROBE),'qemu':record(QEMU)},indent=2)+'\n')
 graphs=Path('/workspace/build01-product-next/native-rules/artifacts')
 cases=[
  ('missing-file','/nonexistent-vortex-hal.so','audio','device',2),
  ('missing-HMI-new-libm',str(PREFIX/'system/lib/libm.so'),'audio','device',3),
  ('missing-HMI-new-libdl',str(PREFIX/'system/lib/libdl.so'),'audio','device',3),
  ('gralloc',str(graphs/'gralloc.rk30board.so'),'gralloc','device',0),
  ('hwcomposer',str(graphs/'hwcomposer.rk30board.so'),'hwcomposer','device',0),
  ('audio-primary',str(AUDIO/'hw/audio.primary.rk30board.so'),'audio','device',0),
  ('audio-usb',str(AUDIO/'hw/audio.usb.default.so'),'audio','device',0),
  ('audio-submix',str(AUDIO/'hw/audio.r_submix.default.so'),'audio','device',0),
  ('power',str(AUDIO/'hw/power.default.so'),'power','module',0),
  ('power-not-device',str(AUDIO/'hw/power.default.so'),'power','device',4),
  ('wrong-id',str(AUDIO/'hw/audio.primary.rk30board.so'),'wrong-audio','device',4),
 ]
 checks=[]
 for name,module,expected,mode,expected_exit in cases:
  command=[str(QEMU),'-strace','-L',str(PREFIX),'-E','LD_LIBRARY_PATH=/system/lib',str(PROBE),module,expected,mode]
  p=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=25)
  (EV/(name+'.stdout.log')).write_bytes(p.stdout);(EV/(name+'.trace.log')).write_bytes(p.stderr)
  checks.append({'case':name,'command':command,'exit_code':p.returncode,'expected_exit_code':expected_exit,'status':'pass' if p.returncode==expected_exit else 'fail','module':record(Path(module)) if Path(module).exists() else {'path':module},'stdout_log':name+'.stdout.log','trace_log':name+'.trace.log'})
  print(name,p.returncode,p.stdout.decode('utf-8','replace').strip(),p.stderr.decode('utf-8','replace')[-500:] if p.returncode!=expected_exit else '')
 report={'scope':'Metadata-only RTLD_NOW/HMI/close with actual Android linker under QEMU user mode. Probe does not invoke HAL open or power hooks; constructors/destructors can execute. Isolated runtime combines three source-built Bionic DSOs, seven source-built audio dependency DSOs and remaining API25/pinned-vendor reference DSOs. No complete Android, recovery or physical hardware boot.','status':'pass' if all(c['status']=='pass' for c in checks) else 'fail','checks':checks,'runtime_input_manifest_sha256':sha((EV/'runtime-inputs.json').read_bytes()),'source_bionic_overrides':OVERRIDES,'limits':['The Android reference linker itself is not source-built here. It may implement libdl through its built-in libdl symbol table; the explicit libdl missing-HMI case loads the provided file but does not prove its stub functions execute.','QEMU user-mode uses the cloud Linux kernel, not RK322x Linux3.10. No graphics/audio/power operation or full init is tested.','Source-built Bionic bytes are copied and hash-bound before execution; original SDK/reference and recovery outputs are never modified.']}
 (EV/'mixed-bionic-smoke-result.json').write_text(json.dumps(report,indent=2)+'\n')
 raise SystemExit(0 if report['status']=='pass' else 1)
if __name__=='__main__':main()
