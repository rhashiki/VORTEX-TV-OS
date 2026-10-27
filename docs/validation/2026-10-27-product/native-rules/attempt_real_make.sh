#!/usr/bin/env bash
cd /workspace/build01-product-next/native-rules/tree
export JAVA_HOME=/workspace/android-toolchain/jdk8u504-b01
export PATH="/workspace/build01-platform-next/aosp-app/host-bin:$JAVA_HOME/bin:$PATH"
export USE_NINJA=false USE_SOONG=false JACK_SERVER=false
export JACK_HOME=/workspace/build01-product-next/native-rules/jack-home
export CLIENT_SETTING=/workspace/build01-product-next/native-rules/jack-client-settings
export OUT_DIR=/workspace/build01-product-next/native-rules/out
source build/envsetup.sh
tapas arm eng gralloc.rk30board hwcomposer.rk30board
vortex_tapas_status=$?
printf 'TAPAS_STATUS=%s\n' "$vortex_tapas_status"
if [ "$vortex_tapas_status" -ne 0 ]; then exit "$vortex_tapas_status"; fi
make -n -j1 TARGET_TOOLS_PREFIX=/workspace/build01-sd/kernel-work/toolchain/bin/arm-linux-gnueabihf- TARGET_BOARD_PLATFORM=rk322x TARGET_BOARD_PLATFORM_PRODUCT=box TARGET_BOARD_HARDWARE=rk30board TARGET_BOARD_PLATFORM_GPU=mali400 USE_CLANG_PLATFORM_BUILD=false ONE_SHOT_MAKEFILE='hardware/rockchip/libgralloc/Android.mk hardware/rockchip/hwcomposer/Android.mk' ACP=/workspace/build01-platform-next/aosp-app/host-bin/acp gralloc.rk30board hwcomposer.rk30board
