from pathlib import Path
import hashlib,json,os,shutil,subprocess,zipfile
R=Path('/workspace/build01-full-next/latest-home');T=R/'tree';E=R/'evidence';A=R/'artifacts';A.mkdir(exist_ok=True)
old=Path('/workspace/build01-platform-next/aosp-app');sdk=Path('/workspace/android-toolchain/sdk/build-tools/33.0.2');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
installed=R/'out/target/product/generic/system/priv-app/VortexHome/VortexHome.apk';apk=A/'VortexHome-main-1db0c91-aosp-r6.apk';shutil.copyfile(installed,apk)
checks=[('apk-signature.log',[str(sdk/'apksigner'),'verify','--verbose','--print-certs',str(apk)]),('apk-alignment.log',[str(sdk/'zipalign'),'-c','-v','4',str(apk)]),('apk-badging.log',[str(T/'prebuilts/sdk/tools/linux/bin/aapt'),'dump','badging',str(apk)])]
for name,args in checks:
 p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(E/name).write_bytes(p.stdout);assert p.returncode==0,(name,p.returncode)
with zipfile.ZipFile(apk) as z:
 assert z.testzip() is None
 assert {'classes.dex','resources.arsc','AndroidManifest.xml'}.issubset(z.namelist())
 dex=z.read('classes.dex');assert dex[:8]==b'dex\n037\x00';assert b'os.vortex.tv.stream\x00' in dex
 entries=[{'path':i.filename,'bytes':i.file_size,'compressed_bytes':i.compress_size,'sha256':hashlib.sha256(z.read(i.filename)).hexdigest()} for i in z.infolist()]
(E/'apk-content-inventory.json').write_text(json.dumps(entries,indent=2)+'\n')
badging=(E/'apk-badging.log').read_text();signature=(E/'apk-signature.log').read_text()
assert "name='os.vortex.tv' versionCode='1' versionName='0.1.0-dev'" in badging
assert "sdkVersion:'25'" in badging and "targetSdkVersion:'25'" in badging
assert 'Verified using v2 scheme (APK Signature Scheme v2): true' in signature
assert 'certificate SHA-256 digest: c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8' in signature
for name in ['sdk-git-object-verification.json','sdk-subset-files.json','tool-versions.json','acp-host-build-final.log','python2-packages.json']:
 shutil.copyfile(old/'evidence'/name,E/('reused-'+name))
sdk_proof=json.loads((E/'reused-sdk-git-object-verification.json').read_text())
verified=[]
for row in sdk_proof['files']:
 p=T/'prebuilts/sdk'/row['path'];data=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 assert blob==row['official_git_blob'] and sha(p)==row['sha256']
 verified.append({'path':row['path'],'bytes':len(data),'git_blob':blob,'sha256':sha(p),'unchanged_from_verified_r6_input':True})
(E/'sdk-input-reverification.json').write_text(json.dumps({'project_revision':sdk_proof['project_revision'],'files':verified},indent=2)+'\n')
tools={}
for name,args in [('java',['/workspace/android-toolchain/jdk8u504-b01/bin/java','-version']),('javac',['/workspace/android-toolchain/jdk8u504-b01/bin/javac','-version']),('make',['make','--version']),('python2',[str(old/'host-bin/python'),'--version']),('aapt',[str(T/'prebuilts/sdk/tools/linux/bin/aapt'),'version'])]:
 proc=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True);tools[name]=proc.stdout.decode().splitlines()[0]
(E/'current-host-tools.json').write_text(json.dumps({'versions':tools,'compatibility_overrides':[{'path':str(p),'sha256':sha(p)} for p in [old/'host-bin/acp',sdk/'zipalign']]},indent=2)+'\n')
shutil.copyfile(R/'run-app-build.sh',E/'run-app-build.sh')
shutil.copyfile(R/'collect_result.py',E/'collect_result.py')
source=json.loads((E/'vortex-source.json').read_text())
assert len(source['files'])==17
for row in source['files']:
 p=T/'vendor/vortex/home'/row['path'];assert sha(p)==row['sha256']
build_rev=subprocess.check_output(['git','rev-parse','HEAD'],cwd=T/'build',text=True).strip();assert build_rev=='5bcb8ef25cbb92b0f6ee9a40fb05bb47b5173774'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=T/'build').strip()
assert (T/'Makefile').read_bytes()==(T/'build/core/root.mk').read_bytes()
files=['core/root.mk','core/configure_local_jack.mk','core/java_common.mk','core/package_internal.mk','target/product/security/platform.x509.pem']
(E/'build-inputs.json').write_text(json.dumps([{'path':'build/'+n,'sha256':sha(T/'build'/n)} for n in files],indent=2)+'\n')
report={'status':'compiled_unbundled_home_apk','scope':'VortexHome only; not streaming APK, complete Android, ROM or SD image','source_revision':source['revision'],'source_files':17,'source_changes':'none','source_byte_verification':'pass','build':{'configuration':'tapas arm eng VortexHome','make_target':'VortexHome','aosp_build_revision':build_rev,'sdk_revision':'23f7de5ba433fc82269ba63c203fe0a3eaf4a680','USE_NINJA':'false','USE_SOONG':'false','JACK_SERVER':'false','local_jack':'full','host_compatibility':'Reused genuine r6 native-source acp and explicit SDK33.0.2 zipalign override from prior experiment; remaining API25/Jack/aapt and build rules r6. Not pristine all-r6 host prebuilts.','build_sources_reused_read_only':True,'output_directory':str(R/'out')},'artifact':{'path':'artifacts/'+apk.name,'bytes':apk.stat().st_size,'sha256':sha(apk),'installed_copy_sha256':sha(installed),'package':'os.vortex.tv','version_code':1,'version_name':'0.1.0-dev','min_sdk':25,'target_sdk':25,'signature_scheme_v2':True,'signer':'Public AOSP platform TEST key; not production/device identity','certificate_sha256':'c8a2e9bccf597c2fb6dc66bee293fc13f2fc47ec77bc6b2b0d52c11f51192ab8'},'checks':{'zip_crc':'pass','alignment_4byte':'pass','signature':'pass','manifest_metadata':'pass','dex037_and_streaming_package_marker':'pass; byte-string presence only, not runtime/allowlist behavior proof'},'limitations':['No emulator/device installation or runtime validation of this updated binary. Earlier API25 results are historical, for earlier binaries.','Native VortexTV prebuilt streaming app and OEM catalog-access input were not present, fetched, built or packaged.','No user-facing app drawer or visual asset changes made. No branding previews/substitutions introduced.','No complete Android/system/recovery/boot/SD image or physical operation. No GitHub Actions used.'],'capacity':{'new_area_bytes':sum(p.stat().st_size for p in R.rglob('*') if p.is_file() and not p.is_symlink()),'budget_bytes':150*1024*1024,'free_bytes':os.statvfs(R).f_bavail*os.statvfs(R).f_frsize}}
assert report['capacity']['new_area_bytes']<report['capacity']['budget_bytes']
(E/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
