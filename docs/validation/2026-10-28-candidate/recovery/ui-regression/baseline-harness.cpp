#include <initializer_list>

#include <climits>
#include <cstdio>
#include <cstring>
#include "/workspace/build01-full-next/recovery/recovery_ui.baseline.cpp"
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
