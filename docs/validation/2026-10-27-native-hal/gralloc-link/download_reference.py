from pathlib import Path
import hashlib,json,urllib.request,os,zipfile,datetime
root=Path(__file__).resolve().parent
info=json.loads((root/'official-image-reference.json').read_text())
out=root/'arm64-v8a-25_r02.zip'
sha1=hashlib.sha1();sha256=hashlib.sha256();n=0
with urllib.request.urlopen(info['archive_url'],timeout=90) as r,out.open('wb') as f:
 while True:
  b=r.read(1024*1024)
  if not b:break
  n+=len(b)
  if n>info['archive_size_bytes']:raise RuntimeError('Archive too large')
  if os.statvfs(root).f_bavail*os.statvfs(root).f_frsize<8*1024**3:raise RuntimeError('Disk reserve')
  f.write(b);sha1.update(b);sha256.update(b)
  if n%(64*1024*1024)==0:print('Downloaded',n,flush=True)
assert n==info['archive_size_bytes'] and sha1.hexdigest()==info['archive_checksum']
info.update({'observed_size_bytes':n,'observed_sha1':sha1.hexdigest(),'sha256':sha256.hexdigest(),'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
with zipfile.ZipFile(out) as z:
 info['zip_entries']=[{'name':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size} for i in z.infolist()]
(root/'download-reference-result.json').write_text(json.dumps(info,indent=2)+'\n')
print(json.dumps(info,indent=2))
