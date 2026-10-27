# Genuine Clang host subset for the native-rules experiment

The tool files come from official AOSP prebuilts/clang/host/linux-x86 at
45562a53b2a5eb7c6e8f400413d19a12c660d7b1, the android-7.1.2_r6 revision.
The selected clang-2690385 binary reports Android clang3.8.256229.

78 selected regular tool/header files were compared to their official Git
blob IDs and hashed with SHA256. clang and clang++ are identical upstream
regular executable blobs; a local hardlink preserves identical bytes and
both driver names without a redundant download. The resource-header root
contains the genuine selected direct files. This is a narrow tool subset,
not a complete prebuilt compiler repository or Android platform source tree.

The first clang --version attempt failed because the current host lacked
libncurses.so.5 and libtinfo.so.5. Genuine Debian libncurses5/libtinfo5 6.4-4
packages were extracted into host-compat, without changing system packages
or replacing ABI5 with an ABI6 symlink. With that command-local library path,
clang --version and ldd pass. The original failure remains in the logs.

Use only for this command or its process tree:
LD_LIBRARY_PATH=/workspace/build01-product-next/native-rules/acquisition/clang-tools/host-compat/lib/x86_64-linux-gnu

The official NOTICE/license markers and tool repo.prop/AndroidVersion files
are preserved with independent blob/SHA256 provenance. No tool binaries need
be exported in the Vortex firmware or evidence ZIP; metadata and acquisition
recipes suffice. This task did not compile or validate a HAL or a ROM.
