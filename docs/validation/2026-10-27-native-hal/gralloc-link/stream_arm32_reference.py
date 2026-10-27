from pathlib import Path
import urllib.request,struct,zlib,hashlib,json,shutil
root=Path(__file__).resolve().parent;ev=root/'evidence'
url='https://dl.google.com/android/repository/sys-img/google_apis/armeabi-v7a-25_r18.zip'
expected_size=952973150;expected_sha1='a6f7c491e3bb937523dddfa287e07d785934e8a1'
image=root/'reference-arm32-system.sparse-host.img'
h1=hashlib.sha1();h256=hashlib.sha256();read_count=0;entries=[]
with urllib.request.urlopen(url,timeout=60) as stream:
 def read(n):
  global read_count
  b=stream.read(n)
  h1.update(b);h256.update(b);read_count+=len(b)
  return b
 def exact(n):
  b=b''
  while len(b)<n:
   chunk=read(n-len(b))
   if not chunk:raise RuntimeError('truncated ZIP')
   b+=chunk
  return b
 def sparse_write(out,data):
  for i in range(0,len(data),4096):
   b=data[i:i+4096]
   if b.strip(b'\0'):out.write(b)
   else:out.seek(len(b),1)
 while True:
  sig=exact(4)
  if sig!=b'PK\x03\x04':
   assert sig in [b'PK\x01\x02',b'PK\x05\x06'],sig
   while read(1024*1024):pass
   break
  ver,flags,method,mtime,mdate,crc,compressed_size,size,namelen,extralen=struct.unpack('<HHHHHIIIHH',exact(26))
  name=exact(namelen).decode();extra=exact(extralen)
  assert not(flags & 8),'ZIP uses data descriptor: '+name
  assert compressed_size!=0xffffffff and size!=0xffffffff,'ZIP64 entry'
  keep=name=='armeabi-v7a/system.img'
  small=name in ['armeabi-v7a/NOTICE.txt','armeabi-v7a/source.properties','armeabi-v7a/build.prop']
  out=image.open('wb') if keep else None
  rawsmall=bytearray();decoder=zlib.decompressobj(-15) if method==8 and (keep or small) else None
  crccheck=0;unc=0;rawhash=hashlib.sha256();remaining=compressed_size
  def process(data):
   global crccheck,unc
   if keep:sparse_write(out,data)
   elif small:rawsmall.extend(data)
   crccheck=zlib.crc32(data,crccheck);unc+=len(data);rawhash.update(data)
  while remaining:
   b=exact(min(256*1024,remaining));remaining-=len(b)
   if not (keep or small):continue
   if method==8:
    while True:
     data=decoder.decompress(b,1024*1024);process(data)
     b=decoder.unconsumed_tail
     if not b:break
   elif method==0:process(b)
   else:raise ValueError('unsupported compression '+str(method))
   assert shutil.disk_usage(root).free>=8*1024**3,'disk reserve'
  entry={'name':name,'flags':flags,'compression_method':method,'compressed_bytes':compressed_size,'bytes':size,'crc32':f'{crc:08x}'}
  if keep or small:
   if decoder:process(decoder.flush());assert decoder.eof
   assert unc==size and crccheck==crc,(name,unc,size,crccheck,crc)
   entry['extracted_sha256']=rawhash.hexdigest()
   if keep:out.truncate(size);out.close();image.chmod(0o400)
   else:(ev/('arm32-'+Path(name).name)).write_bytes(rawsmall)
  entries.append(entry)
assert read_count==expected_size,(read_count,expected_size)
assert h1.hexdigest()==expected_sha1,(h1.hexdigest(),expected_sha1)
result={'source_url':url,'package':'system-images;android-25;google_apis;armeabi-v7a','archive_bytes':read_count,'published_sha1':expected_sha1,'observed_sha1':h1.hexdigest(),'observed_sha256':h256.hexdigest(),'archive_streamed_without_saving':True,'only_system_image_and_metadata_extracted':True,'Google_apps_not_used_or_integrated':True,'temporary_image_logical_bytes':image.stat().st_size,'temporary_image_allocated_bytes':image.stat().st_blocks*512,'entries':entries}
(ev/'arm32-image-stream-result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='entries'},indent=2))
