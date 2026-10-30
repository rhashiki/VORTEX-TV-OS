#!/usr/bin/env python3
"""Compile the real board UI with narrow host API fixtures and exercise its menu/key behavior."""
from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent
SOURCE=BASE/'tree/device/rockchip/common/recovery/recovery_ui.cpp'
RECOVERY=BASE/'source'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def enum(text,name):
 m=re.search(r'enum\s+'+name+r'\s*\{.*?\};',text,re.S)
 if not m:raise ValueError(name)
 return m.group(0)
fixture=ROOT/'fixtures';fixture.mkdir(exist_ok=True)
(fixture/'common.h').write_text('#pragma once\n')
(fixture/'screen_ui.h').write_text('''#pragma once
class RecoveryUI {
 public:
 '''+enum((RECOVERY/'ui.h').read_text(),'KeyAction')+'''
 virtual ~RecoveryUI() {}
 virtual KeyAction CheckKey(int key, bool long_press) { ++callback_calls;last_key=key;last_long_press=long_press;return IGNORE; }
 int callback_calls=0,last_key=-1;bool last_long_press=false;
 bool IsKeyPressed(int) { return power_held; }
 bool power_held=false;
};
class ScreenRecoveryUI: public RecoveryUI {};
''')
(fixture/'device.h').write_text('''#pragma once
#include "screen_ui.h"
class Device {
 public:
 explicit Device(RecoveryUI* ui): ui_(ui) {}
 virtual ~Device() {}
 virtual RecoveryUI* GetUI() { return ui_; }
 virtual int HandleMenuKey(int,int) { return kNoAction; }
 '''+enum((RECOVERY/'device.h').read_text(),'BuiltinAction')+'''
 virtual BuiltinAction InvokeMenuItem(int) { return NO_ACTION; }
 virtual const char* const* GetMenuItems() { return nullptr; }
 static const int kNoAction=-1,kHighlightUp=-2,kHighlightDown=-3,kInvokeItem=-4;
 private: RecoveryUI* ui_;
};
''')
harness=r'''
#include <climits>
#include <cstdio>
#include <cstring>
#include "SOURCE_INCLUDE"
static int passed=0,failed=0;
static void check(const char* name,bool ok) {printf("%s %s\n",ok?"PASS":"FAIL",name);ok?++passed:++failed;}
int main() {
 Device* d=make_device();
 const char* expected[]={"reboot system now","apply update from ADB","apply update from external storage","wipe data/factory reset","wipe cache partition"};
 Device::BuiltinAction action[]={Device::REBOOT,Device::APPLY_ADB_SIDELOAD,Device::APPLY_SDCARD,Device::WIPE_DATA,Device::WIPE_CACHE};
 const char*const* items=d->GetMenuItems();
 for(int i=0;i<5;i++) {char label[48];snprintf(label,sizeof label,"menu-%d-label-and-action",i);check(label,items[i] && strcmp(items[i],expected[i])==0 && d->InvokeMenuItem(i)==action[i]);}
 check("menu-terminated-after-five",items[5]==nullptr);
 check("negative-menu-index",d->InvokeMenuItem(-1)==Device::NO_ACTION);
 check("first-past-end-menu-index",d->InvokeMenuItem(5)==Device::NO_ACTION);
 check("large-menu-index",d->InvokeMenuItem(INT_MAX)==Device::NO_ACTION);
 check("down-key",d->HandleMenuKey(KEY_DOWN,1)==Device::kHighlightDown);
 check("volume-down-key",d->HandleMenuKey(KEY_VOLUMEDOWN,1)==Device::kHighlightDown);
 check("up-key",d->HandleMenuKey(KEY_UP,1)==Device::kHighlightUp);
 check("volume-up-key",d->HandleMenuKey(KEY_VOLUMEUP,1)==Device::kHighlightUp);
 check("enter-key",d->HandleMenuKey(KEY_ENTER,1)==Device::kInvokeItem);
 check("power-key",d->HandleMenuKey(KEY_POWER,1)==Device::kInvokeItem);
 check("unmapped-key",d->HandleMenuKey(KEY_LEFT,1)==Device::kNoAction);
 bool hidden=true;for(int key:{KEY_DOWN,KEY_UP,KEY_VOLUMEDOWN,KEY_VOLUMEUP,KEY_ENTER,KEY_POWER}) hidden &= d->HandleMenuKey(key,0)==Device::kNoAction;
 check("hidden-menu-ignores-navigation",hidden);
 RecoveryUI* ui=d->GetUI();check("base-device-stores-ui-pointer",ui!=nullptr);
 check("platform-two-argument-callback-short",ui->CheckKey(KEY_POWER,false)==RecoveryUI::IGNORE && ui->callback_calls==1 && ui->last_key==KEY_POWER && !ui->last_long_press);
 check("platform-two-argument-callback-long",ui->CheckKey(KEY_VOLUMEUP,true)==RecoveryUI::IGNORE && ui->callback_calls==2 && ui->last_key==KEY_VOLUMEUP && ui->last_long_press);
 delete ui;delete d;
 printf("RESULT passed=%d failed=%d\n",passed,failed);return failed?1:0;
}
'''
# The initializer-list loop is a fixture dependency only.
harness='#include <initializer_list>\n'+harness
results=[]
for name,source in [('baseline',BASE/'recovery_ui.baseline.cpp'),('patched',SOURCE)]:
 out=ROOT/(name+'-harness.cpp');out.write_text(harness.replace('SOURCE_INCLUDE',str(source)))
 cmd=['g++','-std=c++11','-Wall','-Wextra','-Werror','-I'+str(fixture),str(out),'-o',str(ROOT/(name+'-test'))]
 r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/(name+'-compile.log')).write_bytes(r.stdout)
 record={'label':name,'source_sha256':digest(source),'compile_command':cmd,'compile_exit_code':r.returncode}
 if name=='baseline':
  assert r.returncode!=0
  assert b'APPLY_EXT' in r.stdout and b'APPLY_CACHE' in r.stdout and b'Device::Device()' in r.stdout
  record['expected_result']='compile failure due to old Device constructor and removed action enums'
 else:
  assert r.returncode==0,r.stdout.decode()
  r=subprocess.run([str(ROOT/(name+'-test'))],stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(ROOT/(name+'-runtime.log')).write_bytes(r.stdout)
  assert r.returncode==0,r.stdout.decode()
  record.update({'runtime_exit_code':r.returncode,'runtime_result':r.stdout.decode().splitlines()[-1]})
 results.append(record)
report={'scope':'Host-only API-shape/menu/key regression of actual unmodified UI source with narrow fixtures; genuine Android object compilation logged separately. No recovery link, framebuffer, real input, flash or device execution. Fixture headers copy the real action enums and two-argument key callback shape; fixture callback markers verify pass-through but do not implement the Android key policy or UI ABI.','status':'pass','checks':results,'source_headers':{str(p.relative_to(RECOVERY)):digest(p) for p in [RECOVERY/'device.h',RECOVERY/'ui.h']}}
(ROOT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
