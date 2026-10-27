from pathlib import Path
import hashlib,json,re,subprocess,time,traceback,xml.etree.ElementTree as ET,zipfile
R=Path('/workspace/build01-graphics-next/installer'); E=R/'evidence';E.mkdir(exist_ok=True)
ADB='/workspace/android-toolchain/sdk/platform-tools/adb'; S='emulator-5586'
APK=Path('/workspace/build01-platform-next/aosp-app/artifacts/VortexHome-aosp-7.1.2-r6.apk')
FIXTURE=Path('/workspace/build01-retry/fixture/smoke.apk')
commands=[];checks=[];tokens=[];step='boot'
def redact(s):
 for token in tokens:s=s.replace(token,'[expired-session-token]')
 return s
def adb(*args,check=True,binary=False,timeout=60):
 command=[ADB,'-s',S,*args]
 r=subprocess.run(command,capture_output=True,timeout=timeout)
 commands.append({'argv':command,'exit_code':r.returncode,'stdout':'[binary]' if binary else r.stdout.decode(errors='replace'),'stderr':r.stderr.decode(errors='replace')})
 if check and r.returncode:raise RuntimeError('ADB failed '+str(args)+': '+r.stderr.decode(errors='replace'))
 return r.stdout if binary else r.stdout.decode(errors='replace')
def save(n,s): (E/n).write_text(redact(s))
def passed(n,d):checks.append({'check':n,'status':'pass','detail':d})
def dump(n):
 adb('shell','uiautomator','dump','/sdcard/vortex-regression.xml')
 xml=adb('exec-out','cat','/sdcard/vortex-regression.xml')
 save(n+'.xml',xml)
 return ET.fromstring(xml)
def texts(t):return [n.get('text','') for n in t.iter('node') if n.get('text')]
def screen(n):(E/(n+'.png')).write_bytes(adb('exec-out','screencap','-p',binary=True))
def key(k):adb('shell','input','keyevent',str(k));time.sleep(.7)
def tapnode(t,label):
 nodes=[n for n in t.iter('node') if n.get('text','').lower()==label.lower()]
 assert nodes,'Missing node '+label+'; '+str(texts(t))
 b=list(map(int,re.findall(r'\d+',nodes[0].get('bounds'))))
 adb('shell','input','tap',str((b[0]+b[2])//2),str((b[1]+b[3])//2));time.sleep(1)
def focus(t):
 return [str([c.get('text') for c in n.iter('node') if c.get('text')]) for n in t.iter('node') if n.get('focused')=='true']
def absent():return not adb('shell','pm','path','os.vortex.smoke',check=False).strip()
def pairing(prefix):
 t=dump(prefix+'-landing');tapnode(t,'Receber pelo celular')
 t=dump(prefix+'-pairing')
 urls=re.findall(r'http://([0-9.]+):(\d+)/p/([0-9a-f]{32})',' '.join(n.get('text','')+' '+n.get('content-desc','') for n in t.iter('node')))
 assert urls,'No pairing URL'
 ip,port,token=urls[0];tokens.append(token)
 # Rewrite captured XML after discovering and expiring tokens at completion.
 return ip,port,token
reqno=0
def request(session,body,expected,name,token=None,origin=None):
 global reqno
 ip,port,secret=session; secret=secret if token is None else token
 reqno+=1
 headers=(f'POST /upload/{secret} HTTP/1.1\r\nHost: {ip}:{port}\r\nOrigin: {origin or "http://"+ip+":"+port}\r\nContent-Type: application/vnd.android.package-archive\r\nContent-Length: {body.stat().st_size}\r\nConnection: close\r\n\r\n')
 h=R/'http-header.tmp';h.write_bytes(headers.encode())
 adb('push',str(h),'/data/local/tmp/vortex-http-header')
 adb('push',str(body),'/data/local/tmp/vortex-http-body')
 response=adb('shell',f'cat /data/local/tmp/vortex-http-header /data/local/tmp/vortex-http-body | toybox nc -w 5 {ip} {port}',check=False)
 save(name+'.http',response)
 assert response.startswith('HTTP/1.1 '+str(expected)+' '),name+': '+response
 return response
def socket_closed(session,name):
 ip,port,_=session; porthex=format(int(port),'04X')
 for table in ['tcp','tcp6']:
  result=adb('shell','cat','/proc/net/'+table);save(name+'-'+table+'.txt',result)
  assert not any(':'+porthex==row.split()[1][-5:] and row.split()[3]=='0A' for row in result.splitlines()[1:] if len(row.split())>=4)
report={'schema_version':1,'scope':'Real final AOSP APK Android API25 end-to-end installer regression; not a ROM or hardware test.','status':'running','device':{'serial':S},'apk':{'sha256':hashlib.sha256(APK.read_bytes()).hexdigest(),'size_bytes':APK.stat().st_size},'fixture':{'path':str(FIXTURE),'package':'os.vortex.smoke','sha256':hashlib.sha256(FIXTURE.read_bytes()).hexdigest(),'size_bytes':FIXTURE.stat().st_size},'checks':checks,'limits':['Android7.1.1/API25/x86 software AVD; not Android7.1.2/Rockchip firmware boot.','HTTP requests are sent inside the emulator to the selected private emulator interface; no physical phone/LAN/USB media exercised.','Unknown-sources setting is explicitly enabled in this disposable AVD for PackageInstaller testing.','Disposable fixture APK is an Activity-only test app, not part of the Vortex product.']}
try:
 assert report['apk']['sha256']=='81fc16aa89e523088ac8c7a6e334a2c670745d6a4e673a30a986ba6af04867d4'
 for i in range(240):
  try: boot=adb('shell','getprop','sys.boot_completed',check=False,timeout=10).strip()
  except subprocess.TimeoutExpired: boot=''
  if boot=='1': break
  time.sleep(2)
 else:raise RuntimeError('Boot timeout')
 for prop in ['ro.build.version.release','ro.build.version.sdk','ro.product.cpu.abi']:report['device'][prop]=adb('shell','getprop',prop).strip()
 assert report['device']['ro.build.version.sdk']=='25'
 step='install app'
 save('install-vortex.log',adb('install','-r',str(APK)))
 save('fixture-uninstall-initial.log',adb('uninstall','os.vortex.smoke',check=False))
 assert absent();passed('fixture_initially_absent','PackageManager reports no fixture package')
 old=adb('shell','settings','get','secure','install_non_market_apps').strip()
 adb('shell','settings','put','secure','install_non_market_apps','1')
 report['unknown_sources_setting']={'before':old,'during_test':adb('shell','settings','get','secure','install_non_market_apps').strip()}
 adb('logcat','-c')
 save('launch-home.log',adb('shell','am','start','-W','-n','os.vortex.tv/.HomeActivity'))
 time.sleep(2);t=dump('home-before')
 assert 'Instalar APK' in texts(t)
 tapnode(t,'Instalar APK');session=pairing('reject')
 step='negative HTTP tests'
 nonzip=R/'not-an-apk.bin';nonzip.write_bytes(b'This is not an Android package.\n')
 request(session,FIXTURE,404,'wrong-token',token='0'*32)
 passed('wrong_token_rejected','HTTP404, no PackageInstaller/session consumption')
 request(session,FIXTURE,403,'wrong-origin',origin='http://example.invalid')
 passed('wrong_origin_rejected','HTTP403')
 request(session,nonzip,415,'nonzip-rejected')
 assert absent();passed('invalid_apk_signature_rejected','Non-ZIP body HTTP415, fixture remains absent')
 step='ZIP without Android manifest'
 fake=R/'zip-without-android-manifest.apk'
 with zipfile.ZipFile(fake,'w') as z:z.writestr('README.txt','Not an APK; negative test only.')
 request(session,fake,200,'zip-without-manifest-transfer')
 time.sleep(2);t=dump('zip-without-manifest-rejected')
 assert any('Arquivo não é um APK Android válido' in s for s in texts(t)),texts(t)
 assert absent();socket_closed(session,'invalid-manifest-closed')
 passed('zip_without_manifest_rejected_by_package_parser','HTTP transport accepted ZIP; app rejected PackageManager archive metadata, no installation')
 step='valid transfer then cancel'
 session=pairing('cancel')
 request(session,FIXTURE,200,'cancel-valid-upload')
 time.sleep(2);t=dump('install-confirm-cancel')
 screen('install-confirm-cancel')
 assert any('install' in s.lower() for s in texts(t)),texts(t)
 assert any(n.get('package')=='com.android.packageinstaller' for n in t.iter('node')),texts(t)
 assert absent();socket_closed(session,'cancel-pairing-closed')
 passed('confirmation_before_install','Android PackageInstaller foreground; fixture absent until explicit decision')
 tapnode(t,'Cancel');time.sleep(1)
 assert absent();passed('cancel_keeps_package_absent','Pressed Android PackageInstaller Cancel; fixture still not installed')
 t=dump('installer-after-cancel')
 if 'Receber pelo celular' not in texts(t):
  key(4);t=dump('installer-after-cancel-back')
 assert 'Receber pelo celular' in texts(t)
 step='valid transfer then confirm'
 session=pairing('install');request(session,FIXTURE,200,'install-valid-upload')
 time.sleep(2);t=dump('install-confirm-approve')
 assert absent();tapnode(t,'Install')
 for i in range(30):
  if not absent():break
  time.sleep(1)
 assert not absent();passed('explicit_confirmation_installs_fixture','Fixture installed only after pressing Android Install confirmation')
 save('fixture-package.txt',adb('shell','dumpsys','package','os.vortex.smoke'))
 socket_closed(session,'success-pairing-closed');passed('accepted_upload_consumes_pairing','No tcp/tcp6 listening socket on accepted upload port')
 step='return Home and launch directly'
 # Back closes PackageInstaller if its success screen is still shown, then Installer.
 for i in range(4):
  t=dump('after-install-'+str(i))
  if 'Instalar APK' in texts(t):break
  key(4)
 else: raise AssertionError('Home not reached via Back')
 assert 'Vortex Smoke App' in texts(t),texts(t)
 assert 'Instalar APK' in texts(t)
 screen('home-installed-app')
 passed('installed_app_visible_directly_on_home','Vortex Smoke App tile is on the same Home as Install/Settings/Power, without drawer')
 # Explicit focus traversal using D-pad, then launch its selected tile.
 for i in range(8):
  t=dump('home-focus-'+str(i))
  if any('Vortex Smoke App' in f for f in focus(t)):break
  key(22)
 else:raise AssertionError('Could not reach fixture using D-pad')
 passed('installed_app_reachable_by_dpad','Home selected fixture via D-pad right')
 key(23);t=dump('fixture-launched');screen('fixture-launched')
 assert 'Installer smoke OK' in texts(t),texts(t)
 assert any(n.get('package')=='os.vortex.smoke' for n in t.iter('node'))
 passed('installed_app_launched_from_home','DPAD_CENTER opened actual fixture Activity; visible Installer smoke OK')
 key(4);t=dump('home-return-from-fixture')
 assert 'Vortex Smoke App' in texts(t)
 passed('return_from_fixture_to_home','Back returns to Home with installed app still listed')
 logs=adb('logcat','-d');save('logcat-regression.txt',logs)
 assert not re.search(r'FATAL EXCEPTION[\s\S]{0,500}Process: os\.vortex\.tv',logs)
 passed('no_vortex_fatal_exception','No Vortex fatal exception in cleared regression log')
 report['status']='pass'
except Exception as exc:
 report['status']='failed';report['failed_step']=step;report['error']=repr(exc)
 save('traceback.txt',traceback.format_exc())
 try:
  dump('failure-ui');screen('failure');save('logcat-failure.txt',adb('logcat','-d'))
 except Exception:pass
finally:
 report['ended_at_unix']=time.time()
 save('commands.json',json.dumps(commands,indent=2,ensure_ascii=False)+'\n')
 save('runtime-result.json',json.dumps(report,indent=2,ensure_ascii=False)+'\n')
 # Rewrite XML previously captured before its token had been extracted.
 for p in E.glob('*.xml'):p.write_text(redact(p.read_text()))
 for p in R.glob('*tmp'):p.unlink()
print(json.dumps(report,indent=2,ensure_ascii=False))
raise SystemExit(0 if report['status']=='pass' else 1)
