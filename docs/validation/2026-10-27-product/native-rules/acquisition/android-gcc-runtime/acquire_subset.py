from pathlib import Path
import urllib.request,json,base64,hashlib,os,shutil,concurrent.futures,time
root=Path('/workspace/build01-product-next/native-rules/acquisition/android-gcc-runtime')
ref=json.loads((root.parent/'android-gcc-reference.json').read_text());repo=ref['repository'];rev=ref['revision']
dest=Path('/workspace/build01-product-next/native-rules/tree/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9');dest.mkdir(parents=True,exist_ok=True)
records=[]
def tree(path):
 p=root/('listing-'+path.replace('/','-')+'.json')
 if p.exists():return json.loads(p.read_text())
 raw=urllib.request.urlopen(repo+'/+/'+rev+'/'+path+'/?format=JSON',timeout=45).read();x=json.loads(raw[raw.index(b'\n')+1:]);p.write_text(json.dumps(x,indent=2)+'\n');return x
def blob_hash(path,link=False):
 if link:data=os.readlink(path).encode();return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 h=hashlib.sha1();h.update(b'blob '+str(path.stat().st_size).encode()+b'\0')
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def fetch(e,path):
 p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);link=e['mode']==40960
 url=repo+'/+/'+rev+'/'+path+'?format=TEXT'
 exists=p.is_symlink() if link else p.is_file()
 if not exists or blob_hash(p,link)!=e['id']:
  for attempt in range(3):
   try:
    with urllib.request.urlopen(url,timeout=45) as response:
     pending=b'';out=bytearray() if link else None
     temp=p.with_name(p.name+'.part')
     if not link:writer=temp.open('wb')
     try:
      while True:
       chunk=response.read(1024*1024)
       if not chunk:break
       pending+=b''.join(chunk.split());n=len(pending)//4*4
       if n:
        decoded=base64.b64decode(pending[:n]);pending=pending[n:]
        if link:out.extend(decoded)
        else:writer.write(decoded)
       if shutil.disk_usage(root).free<8*1024**3:raise RuntimeError('8GiB reserve reached')
      if pending:raise ValueError('Invalid base64 tail')
     finally:
      if not link:writer.close()
    if link:
     target=bytes(out).decode();assert not Path(target).is_absolute();assert (p.parent/target).resolve().is_relative_to(dest.resolve()),(path,target)
     if p.is_symlink() or p.exists():p.unlink()
     p.symlink_to(target)
    else:temp.replace(p)
    break
   except Exception:
    if attempt==2:raise
    time.sleep(1)
  assert blob_hash(p,link)==e['id'],path
 if not link:p.chmod(0o755 if e['mode']==33261 else 0o644)
 data=os.readlink(p).encode() if link else p.read_bytes()
 result={'path':path,'url':url,'mode':oct(e['mode']),'git_blob_sha1':e['id'],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
 if link:result['target']=data.decode()
 return result
selected=[]
bins=['gcc','g++','as','ar','nm','objcopy','objdump','readelf','strip','ld','ld.gold','ld.bfd','ranlib','cpp']
for e in tree('bin')['entries']:
 if e['name'] in ['arm-linux-androideabi-'+n for n in bins]:selected.append((e,'bin/'+e['name']))
for e in tree('arm-linux-androideabi/bin')['entries']:
 if e['name'] in bins:selected.append((e,'arm-linux-androideabi/bin/'+e['name']))
for e in tree('libexec/gcc/arm-linux-androideabi/4.9')['entries']:
 if e['name'] in ['cc1','cc1plus','collect2','liblto_plugin.so','liblto_plugin.so.0','liblto_plugin.so.0.0.0','lto-wrapper']:selected.append((e,'libexec/gcc/arm-linux-androideabi/4.9/'+e['name']))
def collect_headers(path):
 for e in tree(path)['entries']:
  if e['type']=='tree':collect_headers(path+'/'+e['name'])
  else:selected.append((e,path+'/'+e['name']))
collect_headers('lib/gcc/arm-linux-androideabi/4.9/include')
collect_headers('lib/gcc/arm-linux-androideabi/4.9/include-fixed')
for base,name in [('lib/gcc/arm-linux-androideabi/4.9','libgcc.a'),('arm-linux-androideabi/lib','libatomic.a')]:
 for suffix in ['','/thumb','/armv7-a','/armv7-a/thumb']:
  path=base+suffix;e=next(e for e in tree(path)['entries'] if e['name']==name);selected.append((e,path+'/'+name))
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
 jobs=[pool.submit(fetch,e,path) for e,path in selected]
 for j in jobs:
  r=j.result();records.append(r);print(r['path'],r['bytes'],flush=True)
# Keep source/notice files too, if supplied by the official root tree.
for e in tree('')['entries']:
 if e['type']=='blob' and e['name'] in ['NOTICE','MODULE_LICENSE_GPL','COPYING','COPYING.LIB','COPYING.RUNTIME','COPYING3','COPYING3.LIB','SOURCE','source.properties','repo.prop']:
  records.append(fetch(e,e['name']))
result={'scope':'Selected genuine official Android GCC4.9 frontends/binutils, compiler headers and soft-float ARM runtime archives only; not a complete toolchain repository or a platform build.','repository':repo,'revision':rev,'files':records,'decoded_total_bytes':sum(r['bytes'] for r in records),'system_packages_changed':False}
(root/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
print('VERIFIED',len(records),result['decoded_total_bytes'],flush=True)
