# Experimental AOSP 7.1.2 integration; NOT a flashable ROM.
LOCAL_PATH := $(call my-dir)
include $(CLEAR_VARS)
LOCAL_PACKAGE_NAME := VortexHome
LOCAL_MODULE_TAGS := optional
LOCAL_SRC_FILES := $(call all-java-files-under, app/src/main/java)
LOCAL_MANIFEST_FILE := app/src/main/AndroidManifest.xml
LOCAL_RESOURCE_DIR := $(LOCAL_PATH)/app/src/main/res
LOCAL_CERTIFICATE := platform
LOCAL_PRIVILEGED_MODULE := true
LOCAL_SDK_VERSION := 25
# AOSP Nougat uses Jack for the Java 8 lambdas and method references in this app.
LOCAL_JAVA_LANGUAGE_VERSION := 1.8
LOCAL_JACK_ENABLED := full
# Keep the app version identical in the Gradle and AOSP builds.
LOCAL_AAPT_FLAGS += --version-code 1 --version-name 0.1.0-dev
include $(BUILD_PACKAGE)
