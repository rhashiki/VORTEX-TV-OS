#!/usr/bin/env bash
# Vortex TV OS: independent local checks, deliberately NO GitHub Actions.
# Run from any path after checking out the repository.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "[1/3] Python source and JVM HTTP integration tests"
command -v python3 >/dev/null || { echo "ERROR: python3 missing"; exit 2; }
command -v javac >/dev/null || { echo "ERROR: javac missing"; exit 2; }
command -v java >/dev/null || { echo "ERROR: Java missing"; exit 2; }
python3 -c 'from PIL import Image' >/dev/null 2>&1 || {
  echo "ERROR: Pillow missing. Install tools/requirements.txt before running asset checks."
  exit 2
}
python3 -m unittest discover -s tests -v

echo "[2/3] Android SDK and Gradle toolchain"
if ! command -v gradle >/dev/null; then
  echo "BLOCKED: Gradle missing. Install compatible Gradle 7.6.x, JDK 11, Android SDK 33."
  exit 3
fi
if [ -z "${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}" ]; then
  echo "BLOCKED: ANDROID_HOME / ANDROID_SDK_ROOT missing."
  exit 3
fi
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT}}"
if [ ! -f "$SDK/platforms/android-33/android.jar" ]; then
  echo "BLOCKED: Android platform 33 absent from $SDK"
  exit 3
fi

echo "[3/3] Android APK compilation and lint"
gradle --no-daemon :app:assembleDebug :app:lintDebug
APK="app/build/outputs/apk/debug/app-debug.apk"
test -s "$APK" || { echo "ERROR: APK build completed but artifact missing"; exit 4; }
command -v unzip >/dev/null && unzip -t "$APK" | tail -2
printf 'PASS: Android debug APK compiled: %s (%s bytes)\n' "$APK" "$(wc -c < "$APK")"
echo "NOTE: AOSP ROM, Rockchip drivers and hardware boot are NOT validated by this script."
