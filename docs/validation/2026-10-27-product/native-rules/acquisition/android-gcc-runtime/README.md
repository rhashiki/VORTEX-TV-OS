# Matched official Android GCC4.9 tool/runtime subset

This task acquired selected host frontends/binutils, compiler headers and ARM
runtime archives from the official android-7.1.2_r6 prebuilt repository:
https://android.googlesource.com/platform/prebuilts/gcc/linux-x86/arm/arm-linux-androideabi-4.9
commit0390252b6bcc6217966ade31d07f8b12f6f78f89.

The final 69 selected entries were compared to their official Git blob IDs
and hashed with SHA256. Genuine symlinks were preserved. GCC/G++, cc1/cc1plus,
collect2, binutils/gold, liblto_plugin and its aliases, lto-wrapper, the selected
compiler include roots and four default/Thumb/ARMv7 variants each of libgcc
and libatomic were acquired. This is not a complete compiler repository.

GCC/G++ --version, gold --version and dynamic host dependencies passed.
The tools report GCC4.9 20150123 prerelease and gold1.11/binutils2.25.51.
A real header-free ARMv7 softfp C object and minimal shared-library tool probe
compiled/linked successfully. The shared probe is a tool-readiness result,
not a HAL or a platform runtime test. No -fno-use-linker-plugin workaround
or fabricated archive alias was used.

For -march=armv7-a -mthumb -mfpu=neon -mfloat-abi=softfp, the actual driver
selects armv7-a/thumb/libgcc.a and libatomic.a. The retained readelf logs
cover 1,751 and107 ARM archive members respectively and report no hard-float
VFP calling-convention attribute. These are genuine Android softfp runtimes,
not the hard-float Linaro archive rejected by the prior link attempt.

COPYING, COPYING.LIB, COPYING.RUNTIME, COPYING3, COPYING3.LIB and NOTICE are
preserved in licenses/. Provenance includes the official source URLs and
blob hashes; binaries themselves do not need to be exported in the Vortex
firmware or evidence package. No system packages were changed. No HAL,
Android system, device driver or physical hardware was built/tested by this
acquisition subtask.

clang-resource-alias-independent.json separately verifies the genuine upstream
Clang resource symlink3.8.256229 ->3.8 against the official blob, confirming
that it is not an invented compatibility alias.
