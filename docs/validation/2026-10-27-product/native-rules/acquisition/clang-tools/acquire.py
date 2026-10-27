from pathlib import Path
import urllib.request,json,base64,hashlib,os,shutil,concurrent.futures
root=Path('/workspace/build01-product-next/native-rules/acquisition/clang-tools')
acq=root.parent
info=json.loads((acq/'clang-reference.json').read_text());repo=info['repository'];revision=info['revision']
dest=Path('/workspace/build01-product-next/native-rules/tree/prebuilts/clang/host/linux-x86/clang-2690385');dest.mkdir(parents=True,exist_ok=True)
records=[]
listingbin=json.loads((acq/'clang-listing-bin-.json').read_text())
listinglib=json.loads((acq/'clang-listing-lib64-.json').read_text())
listingheaders=json.loads((acq/'clang-listing-lib64-clang-3.8-include-.json').read_text())
def git_blob_sha(p):
 h=hashlib.sha1();h.update(b'blob '+str(p.stat().st_size).encode()+b'\0')
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def acquire(entry,path):
 p=dest/path;p.parent.mkdir(parents=True,exist_ok=True)
 url=repo+'/+/'+revision+'/clang-2690385/'+path+'?format=TEXT'
 if not p.exists() or git_blob_sha(p)!=entry['id']:
  tmp=p.with_suffix(p.suffix+'.part')
  with urllib.request.urlopen(url,timeout=60) as res,tmp.open('wb') as out:
   pending=b''
   while True:
    chunk=res.read(4*1024*1024)
    if not chunk:break
    pending+=chunk
    n=len(pending)//4*4
    if n:out.write(base64.b64decode(pending[:n]));pending=pending[n:]
    if shutil.disk_usage(dest).free<8*1024**3:raise RuntimeError('Disk reserve reached')
   if pending:out.write(base64.b64decode(pending))
  tmp.replace(p)
 actual=git_blob_sha(p)
 assert actual==entry['id'],(path,actual,entry['id'])
 p.chmod(0o755 if entry['mode']==33261 else 0o644)
 data={'path':path,'url':url,'git_blob_sha1':actual,'mode':oct(entry['mode']),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
 return data
for name in ['clang']:
 e=next(e for e in listingbin['entries'] if e['name']==name)
 rec=acquire(e,'bin/'+name);records.append(rec);print(name,rec['bytes'],flush=True)
# Upstream clang++ is the exact same regular executable blob; retain a regular
# file via hardlink to avoid a redundant download, not a fabricated wrapper.
e=next(e for e in listingbin['entries'] if e['name']=='clang++')
assert e['id']==records[0]['git_blob_sha1']
p=dest/'bin/clang++'
if not p.exists():os.link(dest/'bin/clang',p)
records.append({**records[0],'path':'bin/clang++','url':repo+'/+/'+revision+'/clang-2690385/bin/clang++?format=TEXT','same_upstream_blob_as':'bin/clang'})
for name in ['libLLVM.so','libc++.so']:
 e=next(e for e in listinglib['entries'] if e['name']==name)
 rec=acquire(e,'lib64/'+name);records.append(rec);print(name,rec['bytes'],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 jobs=[pool.submit(acquire,e,'lib64/clang/3.8/include/'+e['name']) for e in listingheaders['entries'] if e['type']=='blob']
 for j in jobs:records.append(j.result())
result={'scope':'Narrow official AOSP r6 Clang host-tool/header acquisition only, not a platform build.','repository':repo,'revision':revision,'files':records,'decoded_total_bytes':sum(r['bytes'] for r in records),'system_package_state_changed':False}
(root/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print('Verified',len(records),'tool/header files',result['decoded_total_bytes'],flush=True)
