from pathlib import Path
import urllib.request,json,hashlib,concurrent.futures
root=Path(__file__).resolve().parent
revision='00c3ec97785c0d42f801083c8fc2fc26d3ce4e2d'
rows=json.loads((root/'selected-paths.json').read_text())
def fetch(row):
 name=row['path']
 url=f'https://raw.githubusercontent.com/rockchip-android/frameworks-native/{revision}/{name}'
 with urllib.request.urlopen(url,timeout=60) as r:content=r.read()
 actual=hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()
 assert actual==row['sha'],name
 dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(content)
 return {'path':name,'url':url,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),'official_git_blob':row['sha'],'download_git_blob':actual,'verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool: records=list(pool.map(fetch,rows))
result={'scope':'Genuine selected public header files only, no stubs or compilation.','repository':'https://github.com/rockchip-android/frameworks-native.git','revision':revision,'files':records}
(root/'provenance.json').write_text(json.dumps(result,indent=2)+'\n')
(root/'headers.sha256').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in records))
print('verified',len(records),'files',sum(r['bytes'] for r in records),'bytes')
