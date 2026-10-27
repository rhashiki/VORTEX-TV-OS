from pathlib import Path
import json,urllib.request,concurrent.futures
root=Path('/workspace/build01-product-next/native-rules/acquisition/android-gcc-runtime');ref=json.loads((root.parent/'android-gcc-reference.json').read_text());repo=ref['repository'];rev=ref['revision']
paths=['bin','arm-linux-androideabi/bin','libexec/gcc/arm-linux-androideabi/4.9','lib/gcc/arm-linux-androideabi/4.9/include','lib/gcc/arm-linux-androideabi/4.9/include-fixed','lib64']
def run(path):
 try:
  raw=urllib.request.urlopen(repo+'/+/'+rev+'/'+path+'/?format=JSON',timeout=45).read();x=json.loads(raw[raw.index(b'\n')+1:]);(root/('listing-'+path.replace('/','-')+'.json')).write_text(json.dumps(x,indent=2)+'\n');return (path,[(e['name'],e['mode']) for e in x['entries']])
 except Exception as e:return(path,type(e).__name__)
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
 for result in pool.map(run,paths):print(json.dumps(result),flush=True)
