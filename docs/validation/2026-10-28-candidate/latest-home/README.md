# Current VortexHome APK checkpoint

This experiment builds the exact tracked `Android.mk` and `app/src` files from
Vortex commit `1db0c914fda74419be097b36c1e753296bcc2bbc`, including the upstream
`os.vortex.tv.stream` system-app allowlist change. No app sources were modified.
The source inventory authenticates all 17 selected files against that commit.

It uses genuine AOSP7.1.2_r6 build/Jack/API25/aapt rules with `tapas arm eng
VortexHome`; this is an unbundled app build, not the Rockchip product build.
Read-only build and individually verified SDK inputs from the previous experiment
are reused, with a separate new tree and output directory. Original outputs are
preserved. The native-source `acp` and SDK33.0.2 `zipalign` make overrides remain
explicit host compatibility choices; this is not a pristine all-r6 host setup.

`evidence/result.json` records the generated APK, source revision, checks and
limits. ZIP CRC, signature, four-byte alignment and package/version/API metadata
are checked on the actual APK. The DEX package marker check establishes byte-string
presence, not behavior of the allowlist. The APK is signed with the public AOSP
platform TEST key, not a production identity or the physical TV Box key.

No updated-binary emulator/device runtime test occurred. Earlier API25 reports
remain historical and apply to their earlier APKs. No full-resolution official
branding assets or substitute thumbnails were introduced. Native VortexTV streaming
APK and OEM catalog-access inputs were not fetched or built; they are separate
required firmware inputs and are absent here. No secret, SDK/vendor runtime,
toolchain, boot/ROM/SD image, physical operation or GitHub Actions is included.

The exact commands are `run-app-build.sh` and `collect_result.py` in the evidence.
Host paths identify this workspace and must be adapted when reproducing elsewhere.
