# Official AOSP r6 host GCC 4.8 toolchain acquisition

The genuine x86_64-linux-glibc2.15-4.8 prebuilt was acquired at commit
73ca99196723f810dad42390d154654354f57c16. The 82,641,853-byte Gitiles
archive has SHA256 78ef70ce6a6af1b0f07cb63430bea28102aaa294075b61dcd7817f577087c541.
Its 240,883,563-byte regular payload and cached archive remain below the
400MiB task budget (323,525,416 nominal bytes together).

All 3,339 regular files match the archive in bytes and modes; all 202 symlink
strings match. Five host smoke cases pass: GCC version, C stdlib/features
compile, actual host execution, selected Clang with genuine libc++/libc++abi
headers and the supplied glibc 2.15 sysroot, and ELF inspection. These do not
constitute a complete Android build or target/hardware execution.

The upstream stdatomic.h symlink reaches the normal cross-project Bionic
path. The isolated mirror preserves that exact link and contains the exact
selected Bionic 8b2e5b9 header, checked against its Git blob. No system header
was substituted. The pinned archive also contains six self-references and
ten dangling references for optional host libraries; they are preserved and
reported. Builds needing those libraries may still fail.

Initial acquisition/extraction logs retain the strict checks that rejected
the cross-project link and then unresolved upstream library links. Final
extraction-verification.json records the completed, byte-verified result.
The frozen smoke and extraction records are authoritative for this state.

extracted-files.partNN.json contains the full per-file inventory split into
bounded text files. Compiler executables, the cached archive, sysroot/runtime
binaries, and local smoke executables are excluded from this text package.
Original source/license metadata remains attached under upstream-metadata/.
