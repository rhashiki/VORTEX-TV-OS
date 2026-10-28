# Native Vortex TV streaming app, separate from the VortexHome launcher.
# AOSP 7.1.2 module; the actual release APK is staged in this directory,
# never checked into source control.
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_MODULE := VortexTV
LOCAL_MODULE_TAGS := optional
LOCAL_MODULE_CLASS := APPS
LOCAL_MODULE_SUFFIX := $(COMMON_ANDROID_PACKAGE_SUFFIX)
LOCAL_SRC_FILES := VortexTV.apk
LOCAL_CERTIFICATE := platform
include $(BUILD_PREBUILT)
