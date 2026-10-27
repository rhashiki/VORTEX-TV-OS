from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json
ROOT=Path('/workspace/build01-platform-next/aosp-app');PIN='23f7de5ba433fc82269ba63c203fe0a3eaf4a680'
records=json.loads((ROOT/'evidence/sdk-subset-files.json').read_text())
directories=sorted({str(Path(r['path']).parent) for r in records})

def get_tree(directory):
 suffix='' if directory=='.' else directory+'/'
 url=f'https://android.googlesource.com/platform/prebuilts/sdk/+/{PIN}/{suffix}?format=JSON'
 with urlopen(Request(url,headers={'User-Agent':'Vortex-AOSP-module-provenance'}),timeout=30) as response:data=response.read(3000000)
 obj=json.loads(data[4:]);return directory,{r['name']:r for r in obj['entries']}

trees={}
with ThreadPoolExecutor(max_workers=4) as pool:
 for f in as_completed([pool.submit(get_tree,d) for d in directories]):
  name,tree=f.result();trees[name]=tree
results=[]
for record in records:
 path=Path(record['path']);entry=trees[str(path.parent)][path.name]
 data=(ROOT/'tree/prebuilts/sdk'/path).read_bytes()
 actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 assert actual==entry['id'],str(path)
 assert entry['mode'] in [0o100644,0o100755],entry
 results.append({'path':str(path),'official_git_blob':entry['id'],'download_git_blob':actual,'sha256':hashlib.sha256(data).hexdigest(),'mode':oct(entry['mode']),'bytes':len(data),'verified':True})
(ROOT/'evidence/sdk-git-object-verification.json').write_text(json.dumps({'project_revision':PIN,'scope':'Official pinned Git tree object hashes of the selected files, not a complete SDK repository checkout.','files':results},indent=2)+'\n')
print('Verified official Git blob objects:',len(results),'bytes:',sum(r['bytes'] for r in results))
