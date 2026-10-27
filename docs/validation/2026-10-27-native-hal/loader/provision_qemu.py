from pathlib import Path
import urllib.request,hashlib,subprocess,tarfile,json
root=Path('/workspace/build01-hal-next/loader');downloads=root/'downloads';downloads.mkdir(exist_ok=True)
name='qemu-user-static_7.2+dfsg-7+deb12u18+b3_amd64.deb'
url='https://deb.debian.org/debian/pool/main/q/qemu/'+name
p=downloads/name
with urllib.request.urlopen(url,timeout=60) as r,p.open('wb') as out:
 while True:
  chunk=r.read(1024*1024)
  if not chunk:break
  out.write(chunk)
assert p.stat().st_size<100*1024*1024
members=subprocess.check_output(['ar','t',str(p)],text=True).splitlines()
member=next(n for n in members if n.startswith('data.tar.'))
process=subprocess.Popen(['ar','p',str(p),member],stdout=subprocess.PIPE)
selected=[]
with tarfile.open(fileobj=process.stdout,mode='r|*') as archive:
 for item in archive:
  if item.name not in ['./usr/bin/qemu-arm-static','./usr/share/doc/qemu-user-static/copyright']:continue
  assert item.isfile()
  dest=root/('bin/qemu-arm-static' if item.name.endswith('qemu-arm-static') else 'evidence/qemu-copyright')
  dest.parent.mkdir(exist_ok=True,parents=True)
  data=archive.extractfile(item).read();dest.write_bytes(data)
  if '/bin/' in str(dest):dest.chmod(0o755)
  selected.append({'archive_path':item.name,'path':str(dest),'size_bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
assert process.wait()==0
assert (root/'bin/qemu-arm-static').is_file()
result={'source_url':url,'download_size_bytes':p.stat().st_size,'download_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selected_files':selected,'system_package_state_changed':False}
(root/'evidence/qemu-provision.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
