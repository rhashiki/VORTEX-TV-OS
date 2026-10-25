#!/usr/bin/env bash
# Compile Java against the actual Android 25 API, independently of compileSdk 33.
# Requires the normal APK toolchain plus platforms;android-25 and build-tools;33.0.2.
set -euo pipefail
cd "$(dirname "$0")/.."
for tool in python3 javac gradle; do
  command -v "$tool" >/dev/null || { echo "BLOCKED: $tool missing"; exit 3; }
done
SDK="${ANDROID_HOME:-${ANDROID_SDK_ROOT:-}}"
if [ -z "$SDK" ] || [ ! -f "$SDK/platforms/android-25/android.jar" ]; then
  echo "BLOCKED: install platforms;android-25 and configure ANDROID_HOME."
  exit 3
fi
if [ ! -f "$SDK/build-tools/33.0.2/core-lambda-stubs.jar" ]; then
  echo "BLOCKED: build-tools;33.0.2 core-lambda-stubs.jar missing."
  exit 3
fi
export VORTEX_API25_SDK="$SDK"
# Generate real Android resource identifiers; do not invent an R class for this check.
gradle --no-daemon --console=plain :app:processDebugResources
python3 - <<'PY'
import os
from pathlib import Path
import subprocess

sdk = Path(os.environ['VORTEX_API25_SDK'])
resources = Path('app/build/intermediates/compile_and_runtime_not_namespaced_r_class_jar/debug/R.jar')
if not resources.is_file():
    raise SystemExit('BLOCKED: AGP 7.4.2 generated R.jar not found; inspect resource task output.')
output = Path('app/build/api25-compat')
output.mkdir(parents=True, exist_ok=True)
sources = sorted(Path('app/src/main/java').rglob('*.java'))
if not sources:
    raise SystemExit('ERROR: no application Java sources found.')
boot = os.pathsep.join(str(p) for p in (
    sdk / 'platforms/android-25/android.jar',
    sdk / 'build-tools/33.0.2/core-lambda-stubs.jar',
))
subprocess.run(['javac', '-encoding', 'UTF-8', '-source', '8', '-target', '8',
                '-bootclasspath', boot, '-classpath', str(resources),
                '-d', str(output), *map(str, sources)], check=True)
print(f'PASS: {len(sources)} Java sources compiled against Android API 25 boot classes.')
print('Lambda stubs support javac/desugaring; this does not run AOSP Jack or build a ROM.')
PY
