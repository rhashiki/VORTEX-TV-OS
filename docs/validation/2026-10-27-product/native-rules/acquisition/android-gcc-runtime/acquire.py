from pathlib import Path
import urllib.request,json,hashlib,base64,subprocess
root=Path('/workspace/build01-product-next/native-rules/acquisition/android-gcc-runtime')
ref=json.loads((root.parent/'android-gcc-reference.json').read_text());repo=ref['repository'];rev=ref['revision']
def fetch_tree(path):
 raw=urllib.request.urlopen(repo+'/+/'+rev+'/'+path+'/?format=JSON',timeout=45).read();data=json.loads(raw[raw.index(b'\n')+1:]);(root/('listing-'+path.replace('/','-')+'.json')).write_text(json.dumps(data,indent=2)+'\n');return data
for path in ['lib/gcc/arm-linux-androideabi/4.9','arm-linux-androideabi/lib','arm-linux-androideabi/lib/armv7-a']:
 try:
  x=fetch_tree(path)
  print(path,[e['name'] for e in x['entries'] if e['name'].startswith(('libgcc','libatomic','armv7','thumb'))],flush=True)
 except Exception as e:print(path,type(e).__name__,str(e)[:120],flush=True)
