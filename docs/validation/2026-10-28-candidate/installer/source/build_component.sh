#!/usr/bin/env bash
# Build one Linux ARM diagnostic component. Never touches a physical device.
set -euo pipefail
VORTEX_DIAG_ROOT="$(cd "$(dirname "$0")" && pwd)"
VORTEX_ARM_TOOLCHAIN="${VORTEX_ARM_TOOLCHAIN:-/workspace/build01-sd/kernel-work/toolchain}"
export PATH="$VORTEX_ARM_TOOLCHAIN/bin:$PATH"
export CC="$VORTEX_ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-gcc"
export CFLAGS='-Os -march=armv7-a -mfloat-abi=hard -mfpu=vfpv3-d16 -fno-unwind-tables -fno-asynchronous-unwind-tables'
export SOURCE_DATE_EPOCH=0
mkdir -p "$VORTEX_DIAG_ROOT/evidence" "$VORTEX_DIAG_ROOT/artifacts"
python3 - "$VORTEX_DIAG_ROOT" <<'PY'
from pathlib import Path
import hashlib,sys,tarfile,urllib.request
r=Path(sys.argv[1]);p=r/'acquisition/musl-1.2.5.tar.gz';p.parent.mkdir(exist_ok=True)
if not p.exists():p.write_bytes(urllib.request.urlopen('https://musl.libc.org/releases/musl-1.2.5.tar.gz',timeout=60).read())
assert hashlib.sha256(p.read_bytes()).hexdigest()=='a9a118bbe84d8764da0ea0d28b3ab3fae8477fc7e4085d90102b8596fc7c75e4'
if not (r/'acquisition/musl-1.2.5/configure').exists():
 with tarfile.open(p) as t:
  for m in t.getmembers():
   q=Path(m.name);assert not q.is_absolute() and '..' not in q.parts
  t.extractall(r/'acquisition',filter='data')
PY
cd "$VORTEX_DIAG_ROOT/acquisition/musl-1.2.5"
./configure --target=arm-linux-gnueabihf --prefix="$VORTEX_DIAG_ROOT/musl" --disable-shared > "$VORTEX_DIAG_ROOT/evidence/musl-configure.log" 2>&1
make -j1 > "$VORTEX_DIAG_ROOT/evidence/musl-build.log" 2>&1
make install > "$VORTEX_DIAG_ROOT/evidence/musl-install.log" 2>&1
"$VORTEX_DIAG_ROOT/musl/bin/musl-gcc" -Os -march=armv7-a -mfloat-abi=hard -mfpu=vfpv3-d16 \
  -ffunction-sections -fdata-sections -Wall -Wextra -Werror -static \
  -Wl,--gc-sections -Wl,--build-id=sha1 -Wl,-Map,"$VORTEX_DIAG_ROOT/evidence/diagnostic-link.map" \
  "$VORTEX_DIAG_ROOT/vortex_diagnostic_init.c" \
  -o "$VORTEX_DIAG_ROOT/artifacts/vortex-diagnostic-init.unstripped" > "$VORTEX_DIAG_ROOT/evidence/diagnostic-build.log" 2>&1
arm-linux-gnueabihf-strip --strip-all \
  -o "$VORTEX_DIAG_ROOT/artifacts/vortex-diagnostic-init" \
  "$VORTEX_DIAG_ROOT/artifacts/vortex-diagnostic-init.unstripped"
arm-linux-gnueabihf-readelf -h -l -A -d "$VORTEX_DIAG_ROOT/artifacts/vortex-diagnostic-init" \
  > "$VORTEX_DIAG_ROOT/evidence/diagnostic-elf.txt"
python3 "$VORTEX_DIAG_ROOT/package_initramfs.py"
