#!/usr/bin/env bash
cd /workspace/build01-platform-next/aosp-app/tree
export JAVA_HOME=/workspace/android-toolchain/jdk8u504-b01
export PATH="/workspace/build01-platform-next/aosp-app/host-bin:$JAVA_HOME/bin:$PATH"
export USE_NINJA=false
export USE_SOONG=false
export JACK_SERVER=false
export JACK_HOME=/workspace/build01-platform-next/aosp-app/jack-home
export CLIENT_SETTING=/workspace/build01-platform-next/aosp-app/jack-client-settings
export JACK_REPOSITORY=/workspace/build01-platform-next/aosp-app/tree/prebuilts/sdk/tools/jacks
export OUT_DIR=/workspace/build01-platform-next/aosp-app/out
source build/envsetup.sh
tapas arm eng VortexHome
vortex_tapas_status=$?
printf 'TAPAS_STATUS=%s\n' "$vortex_tapas_status"
if [ "$vortex_tapas_status" -ne 0 ]; then exit "$vortex_tapas_status"; fi
make -j2 ACP=/workspace/build01-platform-next/aosp-app/host-bin/acp ZIPALIGN=/workspace/android-toolchain/sdk/build-tools/33.0.2/zipalign VortexHome
