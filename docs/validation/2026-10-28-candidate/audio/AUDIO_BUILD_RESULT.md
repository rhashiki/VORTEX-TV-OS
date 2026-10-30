# Actual Android.mk audio and power reference build

The genuine Rockchip Nougat GNUmake rules compiled, linked, packed/stripped and
installed four modules from source: `audio.primary.rk30board`,
`audio.usb.default`, `audio.r_submix.default` and `power.default`.
The final clean build is `attempt-08-final-clean.log`, using
`build_audio_final.sh`. It compiled **53 units across 15 source modules**:
four HALs, seven shared dependencies and four static archives. The reference
Android.mk registered 22 real API25 DSO providers, nine of which were processed
as prebuilts by this build. These platform DSOs are not source-built and are
excluded from the separate artifact directory.

All modules use the real Android Clang 3.8 toolchain, Android GCC4.9 linker and
runtime, Cortex-A7/ARMv7/NEON and the normal Android softfp calling convention.
The shared CRT objects are the prior pinned Bionic-source objects reused by
supported make variables. The loader helper separately compiles its dynamic
CRT from Bionic source using Android GCC4.9. These choices are recorded rather
than presented as a complete source-built platform.

The genuine Expat Android.mk declares an NDK API8 interface for ARM. The
small official NDK sysroot subset required by that rule was acquired at
its recorded commit/hash; its headers and link interfaces are observed
compiler inputs. It is not a fabricated platform provider, and its bytes
are excluded from the delivery. The source-built Expat DSO consequently
needs `libc.so` and `libstdc++.so`; both are resolved by the real reference
runtime during the primary HAL's loader case.

The initial genuine build exposed a source composition mismatch: AOSP r6
TinyALSA lacks `pcm_config.flag`, which the selected Rockchip audio source
initializes. The matching public Rockchip TinyALSA revision
`472b5e3fc1660660e0e9a3fa4cd5f752643920f2` declares the field and propagates it
to kernel hardware parameters. The field was not deleted or replaced by a
fabricated header. Source acquisition records preserve both candidates and
the reason for the explicit vendor override.

Patch `0001-audio-reject-unsupported-hdmi-bypass-rate.patch` fixes a real
uninitialized output-type path. With direct HDMI bitstream, bypass enabled
and an unsupported sample rate, the previous branch continued without setting
the output enum before array indexing. The correction returns `-EINVAL` via
the existing error path, freeing the temporary stream and publishing a null
output before channel-status, lock or array use.

The function-boundary regression executes the actual extracted function with
public header types and simplified private device/stream fixtures. Baseline
has one expected failure and ten passing checks; patched source passes eleven.
The explicit GCC `-ftrivial-auto-var-init=zero` instrumentation makes the old
undefined enum path deterministic for that fixture; this is not a sanitizer
result or a prediction of uninstrumented ARM behavior. Supported HDMI rates,
SPDIF, normal/deep output, busy-stream and allocation-error cases remain covered.

All eleven source-built DSOs passed static ELF32/ARM, softfp and no-TEXTREL
inspection; the four HALs export HMI. Their final bytes match the saved loader
inputs. Eight actual Android-linker/QEMU metadata cases pass: four positive
HAL loads and four negatives (missing file/HMI, wrong id and rejecting a power
module when a device-open callback is required). The power module legitimately
has no device-open callback; its hook pointers are checked but never invoked.
HAL `open`, power hooks, playback/recording and hardware operations are not
called. DSO constructors/destructors may execute under `dlopen`/`dlclose`.

Twenty-eight warnings remain in the final clean build. They include legacy
implicit declarations, pointer/type and formatting diagnostics as well as
sign comparisons and unused parameters. Their exact lines are preserved in
`evidence/warnings.json`; the stage makes no zero-warning or functional-audio
claim. The corrected unsupported-rate diagnostic is not suppressed.

`evidence/compiler-inputs.json` hashes 418 observed files from 53 genuine
compiler dependency rules. `evidence/build-rules-unmodified.json` verifies
all 1,034 build files match the pinned Rockchip build source. Independent
review records the patch, fixture and loader scope in `review/`.

There is no full Android BSP/image, recovery image, SD image, physical boot,
HDMI/SPDIF/USB audio test or power-behavior validation in this result. The
separate `artifacts/` directory contains only these source-built outputs;
SDK/vendor runtime DSOs, tool executables, signing keys and filesystem images
are not included.
