from pathlib import Path
import concurrent.futures, hashlib, json, subprocess, xml.etree.ElementTree as ET
base=Path('/workspace/build01-sd-next/platform-reference')
root=ET.parse(base/'manifest/default.xml').getroot()
default=root.find('default').attrib
prefixes=['build','bionic','bootable/recovery','hardware/libhardware','hardware/rockchip','external/wlan_loader','system/core','device/rockchip','vendor/rockchip','kernel','u-boot','prebuilts/gcc/linux-x86/arm/arm-eabi-4.8']
projects=[dict(p.attrib) for p in root.findall('project') if any(p.attrib.get('path',p.attrib['name'])==k or p.attrib.get('path',p.attrib['name']).startswith(k+'/') for k in prefixes)]
def resolve(p):
 p=dict(p);p['repository']='https://github.com/'+p['name']+'.git';p['requested_revision']=p.get('revision',default['revision'])
 ref=p['requested_revision']
 if not ref.startswith('refs/'):ref='refs/heads/'+ref
 r=subprocess.run(['git','ls-remote','--exit-code',p['repository'],ref],capture_output=True,text=True,timeout=90)
 p['lookup_exit_code']=r.returncode
 lines=r.stdout.splitlines()
 if r.returncode==0 and len(lines)==1:p['observed_commit']=lines[0].split()[0]
 else:p['lookup_error']=r.stderr.strip()[-1000:]
 return p
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:resolved=list(pool.map(resolve,projects))
report={'schema_version':1,'scope':'critical_source_reference_subset_only','recorded_date':'2026-10-26','compatible_rk3229_bsp_selected':False,'complete_resolved_manifest':False,'manifest':{'repository':'https://github.com/TinkerBoard-Android/rockchip-android-manifest.git','revision':'e4faf840083f5c88b7d789007e6707f757368f0c','default_file_sha256':hashlib.sha256((base/'manifest/default.xml').read_bytes()).hexdigest(),'default_project_count':len(root.findall('project')),'included_project_count':6,'default_revision':default['revision'],'target_board':'RK3288 / TinkerBoard'},'observed_critical_projects':resolved,'limits':['These branch tips were read on the recorded date; they form a research subset, not a full AOSP source lock.','No RK3229 Android product is present in this manifest; the only Rockchip product path is device/rockchip/rk3288.','Not combined with D042888-2 r6 candidate components.','No bootloader/DDR/trust binaries selected or executed, and no vendor binary licensing inference.','No full sync, full platform compilation, SD image generation or hardware validation was performed.']}
Path('/workspace/build01-sd-next/research/platform-critical-references.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'projects':len(resolved),'resolved':sum('observed_commit'in p for p in resolved),'file':'/workspace/build01-sd-next/research/platform-critical-references.json'}))
for p in resolved:print(p['path'],p.get('observed_commit',p.get('lookup_error')))
