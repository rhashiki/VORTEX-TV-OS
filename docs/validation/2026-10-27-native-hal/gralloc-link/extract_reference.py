from pathlib import Path
import zipfile,hashlib,json,subprocess,os,shutil
root=Path(__file__).resolve().parent
ev=root/'evidence';ev.mkdir(exist_ok=True)
image=root/'reference-system.sparse-host.img'
archive=root/'arm64-v8a-25_r02.zip'
sha=hashlib.sha256();total=0
with zipfile.ZipFile(archive) as z:
 for n in ['NOTICE.txt','source.properties','build.prop']:
  (ev/n).write_bytes(z.read('arm64-v8a/'+n))
 with z.open('arm64-v8a/system.img') as src,image.open('wb') as out:
  while True:
   b=src.read(1024*1024)
   if not b:break
   total+=len(b);sha.update(b)
   if b.strip(b'\x00'):out.write(b)
   else:out.seek(len(b),1)
  out.truncate(total)
image.chmod(0o400)
assert shutil.disk_usage(root).free>=8*1024**3
ext=root/'host-deps/root'
env=dict(os.environ);env['LD_LIBRARY_PATH']=str(ext/'usr/lib/x86_64-linux-gnu')
debugfs=ext/'usr/sbin/debugfs'
commands=[]
def run(q,label):
 cmd=[str(debugfs),'-R',q,str(image)]
 p=subprocess.run(cmd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 (ev/(label+'.log')).write_bytes(p.stdout)
 commands.append({'command':cmd,'exit_code':p.returncode,'log':label+'.log'})
 return p.stdout.decode(errors='replace')
print(run('ls -l /lib','lib-listing'))
print(run('ls -l /bin/linker','linker-listing'))
result={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'filesystem_image_logical_bytes':total,'filesystem_image_sha256':sha.hexdigest(),'filesystem_image_allocated_bytes':image.stat().st_blocks*512,'read_only_debugfs':True,'commands':commands}
(ev/'extraction-stage.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='commands'},indent=2))
