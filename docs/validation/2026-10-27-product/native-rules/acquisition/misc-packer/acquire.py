from pathlib import Path
import urllib.request,json,base64,hashlib,subprocess
root=Path('/workspace/build01-product-next/native-rules/acquisition/misc-packer')
repo='https://android.googlesource.com/platform/prebuilts/misc';tag='android-7.1.2_r6'
def getjson(url):
 raw=urllib.request.urlopen(url,timeout=45).read();return json.loads(raw[raw.index(b'\n')+1:])
commit=getjson(repo+'/+/'+tag+'?format=JSON');rev=commit['commit']
path='linux-x86/relocation_packer'
tree=getjson(repo+'/+/'+rev+'/'+path+'/?format=JSON')
(root/'reference.json').write_text(json.dumps({'repository':repo,'tag':tag,'revision':rev,'tree':tree},indent=2)+'\n')
e=next(e for e in tree['entries'] if e['name']=='relocation_packer');assert e['mode']==33261
url=repo+'/+/'+rev+'/'+path+'/relocation_packer?format=TEXT';data=base64.b64decode(urllib.request.urlopen(url,timeout=45).read())
h=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert h==e['id']
p=Path('/workspace/build01-product-next/native-rules/tree/prebuilts/misc')/path/'relocation_packer';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o755)
record={'scope':'One genuine official host relocation packer acquired, not a HAL or platform build.','repository':repo,'tag':tag,'revision':rev,'url':url,'path':str(p),'git_blob_sha1':h,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'system_packages_changed':False}
(root/'provenance.json').write_text(json.dumps(record,indent=2)+'\n')
for name,args in [('help',[str(p),'--help']),('ldd',['ldd',str(p)])]:
 r=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(root/(name+'.log')).write_bytes(r.stdout);print(name,r.returncode,r.stdout.decode(errors='replace')[:1800],flush=True)
print(json.dumps(record,indent=2))
