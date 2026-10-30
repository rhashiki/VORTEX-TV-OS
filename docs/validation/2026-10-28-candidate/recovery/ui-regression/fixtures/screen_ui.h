#pragma once
class RecoveryUI {
 public:
 enum KeyAction { ENQUEUE, TOGGLE, REBOOT, IGNORE };
 virtual ~RecoveryUI() {}
 virtual KeyAction CheckKey(int key, bool long_press) { ++callback_calls;last_key=key;last_long_press=long_press;return IGNORE; }
 int callback_calls=0,last_key=-1;bool last_long_press=false;
 bool IsKeyPressed(int) { return power_held; }
 bool power_held=false;
};
class ScreenRecoveryUI: public RecoveryUI {};
