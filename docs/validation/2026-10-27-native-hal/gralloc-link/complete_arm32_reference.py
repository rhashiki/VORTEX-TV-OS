from pathlib import Path
import hashlib,zipfile,json,shutil
root=Path(__file__).resolve().parent;ev=root/'evidence'
old=root/'arm64-v8a-25_r02.zip';archive=root/'armeabi-v7a-25_r18.zip';image=root/'reference-arm32-system.sparse-host.img'
cleanup=[]
if old.exists():
 assert hashlib.sha256(old.read_bytes()).hexdigest()=='1d38666f6e64f983e0d3ad86ef5c42d213685fcd6932a0f2dfbcee0e79767cc2'
 cleanup.append({'file':old.name,'sha256':'1d38666f6e64f983e0d3ad86ef5c42d213685fcd6932a0f2dfbcee0e79767cc2','reason':'Unused current-stage ARM64 cache; negative inventory retained, root authorized cleanup.'});old.unlink()
assert archive.stat().st_size==952973150
assert hashlib.sha1(archive.read_bytes()).hexdigest()=='a6f7c491e3bb937523dddfa287e07d785934e8a1'
archivesha=hashlib.sha256(archive.read_bytes()).hexdigest()
prefix_size=image.stat().st_size;assert prefix_size%(1024*1024)==0
rawsha=hashlib.sha256();total=0;min_free=shutil.disk_usage(root).free
with zipfile.ZipFile(archive) as z:
 for name in ['NOTICE.txt','source.properties','build.prop']:(ev/('arm32-'+name)).write_bytes(z.read('armeabi-v7a/'+name))
 info=z.getinfo('armeabi-v7a/system.img')
 with z.open(info) as src,image.open('rb') as previous,image.open('r+b') as out:
  out.seek(prefix_size)
  while True:
   data=src.read(1024*1024)
   if not data:break
   rawsha.update(data)
   if total<prefix_size:
    assert previous.read(len(data))==data,'Partial prefix differs from ZIP'
   else:
    for i in range(0,len(data),4096):
     b=data[i:i+4096]
     if b.strip(b'\0'):out.write(b)
     else:out.seek(len(b),1)
   total+=len(data);min_free=min(min_free,shutil.disk_usage(root).free)
   assert min_free>=8*1024**3,'disk reserve'
  out.truncate(total)
 assert total==info.file_size
 image.chmod(0o400)
 result={'source_url':'https://dl.google.com/android/repository/sys-img/google_apis/armeabi-v7a-25_r18.zip','package':'system-images;android-25;google_apis;armeabi-v7a','archive_bytes':archive.stat().st_size,'published_sha1':'a6f7c491e3bb937523dddfa287e07d785934e8a1','observed_sha1':'a6f7c491e3bb937523dddfa287e07d785934e8a1','archive_sha256':archivesha,'stdlib_zipfile_crc_checked_on_selected_entries':True,'Google_apps_not_used_or_integrated':True,'temporary_image_logical_bytes':total,'temporary_image_allocated_bytes':image.stat().st_blocks*512,'filesystem_image_sha256':rawsha.hexdigest(),'system_image_entry_crc32':f'{info.CRC:08x}','system_image_entry_compressed_bytes':info.compress_size,'partial_prefix_verified_byte_identical':prefix_size,'minimum_free_bytes_during_resumed_extraction':min_free,'root_authorized_cache_cleanup':cleanup}
(ev/'arm32-reference-acquisition.json').write_text(json.dumps(result,indent=2)+'\n')
cleanup.append({'file':archive.name,'sha256':archivesha,'reason':'Current-stage full archive verified and expanded; release temporary cache before selective library extraction.'})
archive.unlink()
(ev/'temporary-cache-cleanup.json').write_text(json.dumps(cleanup,indent=2)+'\n')
print(json.dumps(result,indent=2))
