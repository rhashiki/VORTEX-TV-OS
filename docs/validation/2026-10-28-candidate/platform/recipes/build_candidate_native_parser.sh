#!/usr/bin/env bash
set -o pipefail
cd /workspace/build01-full-next/platform/tree || exit 2
export JAVA_HOME=/workspace/android-toolchain/jdk8u504-b01
export PATH="/workspace/build01-platform-next/aosp-app/host-bin:$JAVA_HOME/bin:$PATH"
export LD_LIBRARY_PATH=/workspace/build01-product-next/native-rules/acquisition/clang-tools/host-compat/lib/x86_64-linux-gnu
export M4=/workspace/build01-platform-next/host-deps/usr/bin/m4
export USE_NINJA=false USE_SOONG=false JACK_SERVER=false
export JACK_HOME=/workspace/build01-full-next/platform/jack-home
export CLIENT_SETTING=/workspace/build01-full-next/platform/jack-client-settings
export OUT_DIR=/workspace/build01-full-next/platform/out
unset ONE_SHOT_MAKEFILE TARGET_BUILD_APPS
source build/envsetup.sh
lunch vortex_rk322x_sd_box-eng
vortex_lunch_status=$?
printf 'LUNCH_STATUS=%s\n' "$vortex_lunch_status"
if [ "$vortex_lunch_status" -ne 0 ]; then exit "$vortex_lunch_status"; fi
make -f Makefile -f /workspace/build01-full-next/platform/audit-tail.mk -j2 BISON=/workspace/build01-full-next/platform/out/host/linux-x86/bin/bison USE_CLANG_PLATFORM_BUILD=false VORTEX_REFERENCE_KERNEL_IMAGE=/workspace/build01-sd-next/kernel-sd/out/arch/arm/boot/Image droid showcommands
