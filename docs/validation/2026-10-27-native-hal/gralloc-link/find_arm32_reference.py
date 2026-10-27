from pathlib import Path
import urllib.request,xml.etree.ElementTree as E,json,hashlib,subprocess,os
root=Path(__file__).resolve().parent;ev=root/'evidence'
image=root/'reference-system.sparse-host.img'
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(root/'host-deps/root/usr/lib/x86_64-linux-gnu')
p=subprocess.run([str(root/'host-deps/root/usr/sbin/debugfs'),'-R','ls -l /',str(image)],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
(ev/'api25-arm64-root-listing.log').write_bytes(p.stdout)
image.unlink() # New temporary expanded filesystem only; original archive preserved.
entries=[]
for family in ['android','google_apis']:
 url=f'https://dl.google.com/android/repository/sys-img/{family}/sys-img2-1.xml'
 raw=urllib.request.urlopen(url,timeout=60).read()
 (ev/f'{family}-system-image-metadata.xml').write_bytes(raw)
 doc=E.fromstring(raw)
 for pkg in doc.findall('remotePackage'):
  path=pkg.attrib['path']
  if 'android-25' not in path and 'android-24' not in path:continue
  if not path.endswith(';armeabi-v7a'):continue
  for ar in pkg.findall('./archives/archive'):
   c=ar.find('complete')
   if c is None:continue
   entries.append({'path':path,'metadata_url':url,'metadata_sha256':hashlib.sha256(raw).hexdigest(),'download_base':url.rsplit('/',1)[0]+'/','archive':c.findtext('url'),'bytes':int(c.findtext('size')),'checksum_type':c.find('checksum').attrib.get('type'),'checksum':c.findtext('checksum')})
(ev/'arm32-reference-candidates.json').write_text(json.dumps(entries,indent=2)+'\n')
print(json.dumps(entries,indent=2))
