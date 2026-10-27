from pathlib import Path
import urllib.request,hashlib,json
root=Path('/workspace/build01-product-next/product-graph');tree=root/'tree'
rev='00c3ec97785c0d42f801083c8fc2fc26d3ce4e2d'
names=['tablet-10in-xhdpi-2048-dalvik-heap.mk','tablet-dalvik-heap.mk','tablet-7in-hdpi-1024-dalvik-heap.mk','phone-xhdpi-1024-dalvik-heap.mk']
rows=[]
for n in names:
 path='build/'+n;url='https://raw.githubusercontent.com/rockchip-android/frameworks-native/'+rev+'/'+path
 data=urllib.request.urlopen(url,timeout=45).read();dest=tree/'frameworks/native'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 rows.append({'path':'frameworks/native/'+path,'revision':rev,'url':url,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'evidence/native-build-fragments.json').write_text(json.dumps(rows,indent=2)+'\n')
print('Fetched true build fragments:',len(rows))
