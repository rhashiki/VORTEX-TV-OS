from pathlib import Path
import urllib.request,hashlib,zipfile,json,shutil,os,subprocess
root=Path(__file__).resolve().parent;ev=root/'evidence'
url='https://dl.google.com/android/repository/sys-img/google_apis/armeabi-v7a-25_r18.zip'
expected_size=952973150;expected_sha1='a6f7c491e3bb937523dddfa287e07d785934e8a1'
archive=root/'armeabi-v7a-25_r18.zip';image=root/'reference-arm32-system.sparse-host.img'
if image.exists():image.unlink() # interrupted new temporary only
h1=hashlib.sha1();h256=hashlib.sha256();total=0
with urllib.request.urlopen(url,timeout=60) as stream,archive.open('wb') as out:
 while True:
  chunk=stream.read(1024*1024)
  if not chunk:break
  out.write(chunk);h1.update(chunk);h256.update(chunk);total+=len(chunk)
  assert shutil.disk_usage(root).free>=8*1024**3,'disk reserve'
assert total==expected_size and h1.hexdigest()==expected_sha1
imagehash=hashlib.sha256();imagebytes=0
with zipfile.ZipFile(archive) as z:
 for name in ['NOTICE.txt','source.properties','build.prop']:
  (ev/('arm32-'+name)).write_bytes(z.read('armeabi-v7a/'+name))
 with z.open('armeabi-v7a/system.img') as src,image.open('wb') as out:
  while True:
   data=src.read(1024*1024)
   if not data:break
   imagebytes+=len(data);imagehash.update(data)
   for i in range(0,len(data),4096):
    b=data[i:i+4096]
    if b.strip(b'\0'):out.write(b)
    else:out.seek(len(b),1)
   assert shutil.disk_usage(root).free>=8*1024**3,'disk reserve'
  out.truncate(imagebytes)
 image.chmod(0o400)
 image_entry=z.getinfo('armeabi-v7a/system.img')
 result={'source_url':url,'package':'system-images;android-25;google_apis;armeabi-v7a','archive_bytes':total,'published_sha1':expected_sha1,'observed_sha1':h1.hexdigest(),'archive_sha256':h256.hexdigest(),'stdlib_zipfile_crc_checked_on_selected_entries':True,'Google_apps_not_used_or_integrated':True,'temporary_image_logical_bytes':imagebytes,'temporary_image_allocated_bytes':image.stat().st_blocks*512,'filesystem_image_sha256':imagehash.hexdigest(),'system_image_entry_crc32':f'{image_entry.CRC:08x}','system_image_entry_compressed_bytes':image_entry.compress_size}
(ev/'arm32-reference-acquisition.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
