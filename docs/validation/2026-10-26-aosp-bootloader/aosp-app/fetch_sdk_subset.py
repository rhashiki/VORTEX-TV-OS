from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import base64,hashlib,json,os,threading
ROOT=Path('/workspace/build01-platform-next/aosp-app')
DEST=ROOT/'tree/prebuilts/sdk';DEST.mkdir(parents=True,exist_ok=True)
PIN='23f7de5ba433fc82269ba63c203fe0a3eaf4a680'
PATHS=['Android.mk','25/android.jar','25/framework.aidl','tools/Android.mk','tools/jack','tools/jack-admin','tools/jack_versions.mk','tools/jack_for_module.mk','tools/jack_server_setup.mk','tools/jack-launcher.jar','tools/jack-server-4.8.ALPHA.jar','tools/jacks/jack-3.36.CANDIDATE.jar','tools/linux/bin/aapt','tools/linux/bin/acp','tools/linux/bin/aidl','tools/linux/bin/zipalign','tools/linux/lib64/libc++.so','tools/linux/lib64/libconscrypt_openjdk_jni.so','tools/linux/lib/libc++.so','tools/lib/signapk.jar','tools/dx','tools/lib/dx.jar']
manifest_path=ROOT/'evidence/sdk-subset-files.json'
records=json.loads(manifest_path.read_text()) if manifest_path.exists() else []
old={x['path']:x for x in records if x.get('status')=='downloaded'}
mode_cache={};lock=threading.Lock()

def download(path):
 target=DEST/path
 if path in old and target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest()==old[path]['sha256']:
  return old[path]
 free=os.statvfs(ROOT).f_bavail*os.statvfs(ROOT).f_frsize
 if free<8*1024**3:raise RuntimeError('Free-space reserve reached')
 url=f'https://android.googlesource.com/platform/prebuilts/sdk/+/{PIN}/{path}?format=TEXT'
 try:
  with urlopen(Request(url,headers={'User-Agent':'Vortex-AOSP-module-build'}),timeout=90) as response:
   encoded=response.read(300*1024**2+1)
  if len(encoded)>300*1024**2:raise ValueError('Individual file budget exceeded')
  data=base64.b64decode(encoded,validate=True)
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes(data)
  if path.startswith('tools/linux/bin/') or path in ['tools/jack','tools/jack-admin','tools/dx']:
   target.chmod(0o755)
  return {'path':path,'url':url,'project_revision':PIN,'status':'downloaded','bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()}
 except Exception as error:
  return {'path':path,'url':url,'status':'failed','error':str(error)}

with ThreadPoolExecutor(max_workers=4) as pool:
 for future in as_completed([pool.submit(download,p) for p in PATHS]):
  record=future.result();old[record['path']]=record
  records=sorted(old.values(),key=lambda x:x['path'])
  manifest_path.write_text(json.dumps(records,indent=2)+'\n')
  print(json.dumps({k:record[k] for k in ['path','status','bytes','error'] if k in record}),flush=True)
print('Selected decoded bytes:',sum(x.get('bytes',0) for x in old.values()))
