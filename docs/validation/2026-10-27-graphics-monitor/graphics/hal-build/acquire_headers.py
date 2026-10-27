from pathlib import Path
import urllib.request,json,hashlib,subprocess,tarfile,io
root=Path('/workspace/build01-graphics-next/graphics/hal-build')
records=[]
base='https://raw.githubusercontent.com/rockchip-android/frameworks-native/00c3ec97785c0d42f801083c8fc2fc26d3ce4e2d/opengl/include/'
for rel in ['GLES/gl.h','GLES/glext.h','GLES/glplatform.h','KHR/khrplatform.h']:
 data=urllib.request.urlopen(base+rel,timeout=40).read()
 dest=root/'native-opengl-include'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
 records.append({'url':base+rel,'path':str(dest.relative_to(root)),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(root/'acquired-headers.json').write_text(json.dumps(records,indent=2)+'\n')
print(json.dumps(records))
