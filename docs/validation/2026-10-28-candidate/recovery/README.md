# Recovery Rockchip/Nougat: source-build checkpoint

The genuine Android.mk rules compiled the main recovery units, source libraries
and Bionic shared/static components recorded in recovery-build-result.json.
The complete static recovery ELF now links/strips/installs into the build output.
It was never executed. This is not recovery.img, an SD card or an Android ROM.

The opt-in common UI patch fixes the Device constructor/menu API and removes
the obsolete one-argument key callback, retaining the platform policy. Twenty
host fixture assertions pass; the original source fails compilation as expected.
The baseline generic aosp_arm experiment still compiles default_device.cpp;
the corrected UI archive is tested separately and is not shown linked into
a complete recovery.

The SDK runtime DSOs were not used as static libc substitutes. Genuine Bionic
source CRT, libc/libdl/libm shared libraries and the listed static archives
were built by Android rules. The recovery link names four genuine vendor archives;
link-map allocated contributions are observed for librkupdate, libext2_uuid and
libcrc32, while librkrsa has no selected members in this build. This is a mixed
source/prebuilt-input executable, not fully source-built. ELF inspection is not
runtime or physical proof.
The static archive count excludes WHOLE copies; source-unit counts come from
compiler dependency rules with matching object outputs.

Raw recovery sdboot/recovery code can dispatch fw_update and update IDBlock.
That source is not a read-only diagnostic or an approved installer backend.
The four vendor prebuilt archive inputs are identified in the review and are
excluded from the delivered artifact directory; complete source/license/backend
closure is not inferred.

Small raw logs are retained verbatim here. Larger logs are indexed by exact
bytes/SHA256 and their raw-logs/recovery ZIP paths in raw-log-index.json.
Paths are concrete workspace paths. Recipes require the genuine pinned source
and toolchain inputs; they do not download/flash/prepare media automatically.
License notices retain their per-source origin, without assigning a uniform
license to all upstream material.
