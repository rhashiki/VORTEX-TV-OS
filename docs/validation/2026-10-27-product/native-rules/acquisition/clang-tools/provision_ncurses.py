from pathlib import Path
import urllib.request,re,json,hashlib,subprocess
root=Path('/workspace/build01-product-next/native-rules/acquisition/clang-tools')
base='https://deb.debian.org/debian/pool/main/n/ncurses/'
raw=urllib.request.urlopen(base,timeout=45).read();(root/'ncurses-pool-index.html').write_bytes(raw)
rows=[];target=root/'host-compat';target.mkdir(exist_ok=True)
for prefix in ['libncurses5_','libtinfo5_']:
 names=sorted(set(re.findall(r'href="('+prefix+r'[^"]+amd64.deb)"',raw.decode())))
 assert names,prefix
 # Latest package in the retained bookworm/bullseye repository listing;
 # the selected exact URL, bytes and SHA are frozen below.
 name=names[-1];data=urllib.request.urlopen(base+name,timeout=45).read();deb=root/name;deb.write_bytes(data)
 subprocess.run(['dpkg-deb','-x',str(deb),str(target)],check=True)
 rows.append({'url':base+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'host-compat-provenance.json').write_text(json.dumps({'scope':'Real missing host ABI5 runtime packages extracted locally only. No system-package mutation or ABI-alias symlinks.','packages':rows},indent=2)+'\n')
print(json.dumps(rows,indent=2))
