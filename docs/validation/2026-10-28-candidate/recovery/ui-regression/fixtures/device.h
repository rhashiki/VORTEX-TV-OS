#pragma once
#include "screen_ui.h"
class Device {
 public:
 explicit Device(RecoveryUI* ui): ui_(ui) {}
 virtual ~Device() {}
 virtual RecoveryUI* GetUI() { return ui_; }
 virtual int HandleMenuKey(int,int) { return kNoAction; }
 enum BuiltinAction {
        NO_ACTION = 0,
        REBOOT = 1,
        APPLY_SDCARD = 2,
        // APPLY_CACHE was 3.
        APPLY_ADB_SIDELOAD = 4,
        WIPE_DATA = 5,
        WIPE_CACHE = 6,
        REBOOT_BOOTLOADER = 7,
        SHUTDOWN = 8,
        VIEW_RECOVERY_LOGS = 9,
        MOUNT_SYSTEM = 10,
        RUN_GRAPHICS_TEST = 11,
    };
 virtual BuiltinAction InvokeMenuItem(int) { return NO_ACTION; }
 virtual const char* const* GetMenuItems() { return nullptr; }
 static const int kNoAction=-1,kHighlightUp=-2,kHighlightDown=-3,kInvokeItem=-4;
 private: RecoveryUI* ui_;
};
