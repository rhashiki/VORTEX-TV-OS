#!/usr/bin/env bash
set -e
cd /workspace/build01-full-next/recovery/tree
export LD_LIBRARY_PATH=/workspace/build01-product-next/native-rules/acquisition/clang-tools/host-compat/lib/x86_64-linux-gnu
export JAVA_HOME=/workspace/android-toolchain/jdk8u504-b01
export PATH="/workspace/build01-platform-next/aosp-app/host-bin:$JAVA_HOME/bin:$PATH"
export USE_NINJA=false USE_SOONG=false JACK_SERVER=false
export JACK_HOME=/workspace/build01-full-next/recovery/jack-home
export CLIENT_SETTING=/workspace/build01-full-next/recovery/jack-client-settings
export OUT_DIR=/workspace/build01-full-next/recovery/out
source build/envsetup.sh
tapas arm eng "$@"
make -f Makefile -f /workspace/build01-full-next/recovery/linkmap-tail.mk -j1 LEX=/workspace/build01-platform-next/host-deps/usr/bin/flex BISON=/workspace/build01-platform-next/host-deps/usr/bin/bison BISON_PKGDATADIR=/workspace/build01-platform-next/host-deps/usr/share/bison M4=/workspace/build01-platform-next/host-deps/usr/bin/m4 TARGET_BUILD_APPS= TARGET_ARCH_VARIANT=armv7-a-neon TARGET_CPU_VARIANT=cortex-a7 TARGET_BOARD_PLATFORM=rk322x TARGET_BOARD_PLATFORM_PRODUCT=box TARGET_BOARD_HARDWARE=rk30board USE_CLANG_PLATFORM_BUILD=false ONE_SHOT_MAKEFILE="${RECOVERY_MAKEFILES}" ACP=/workspace/build01-platform-next/aosp-app/host-bin/acp "$@" showcommands
