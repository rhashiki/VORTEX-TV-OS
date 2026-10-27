# Build 01 — reproducible validation in ChatGPT Work

**READ FIRST:** [ROADMAP.md](../ROADMAP.md) and [docs/BRANDING.md](BRANDING.md) are authoritative for the official Launcher square and 16:9 TV icons, the white complete Home logo and the newly supplied 4-second boot animation MP4. Do not reuse obsolete 6-second animation or redraw the brand. Binary originals must be mounted/transferred into the workspace and verified by SHA-256 prior to integration.


**Project:** https://github.com/rhashiki/VORTEX-TV-OS
**Default branch:** main
**Strict restriction:** NEVER create, run, inspect, or depend on GitHub Actions. No deployment/flash/merge is permitted on the basis of source checks alone.

## Owner constraint: no further board information is available

The owner has already supplied everything available and cannot obtain further
unit-specific information. Do not ask again for BSP/base firmware, FlashID,
Wi-Fi chip identification, board photos or diagnostic output. Use the inventory
and public-source investigation paths in [rom/HARDWARE.md](../rom/HARDWARE.md).
The remaining unknowns stay unknown; obtaining candidate public sources is the
developer's task, not a new prerequisite to assign to the owner.

Continue app development, source/dependency audits and candidate builds where
possible. Report APK validation, a candidate BSP and any compiled image as
separate results. Physical compatibility and boot remain unverified until
actually demonstrated; lack of extra information does not establish them.

## Working goal

The owner clarified the final delivery: a **bootable SD installer**, analogous
to a Windows installation disc. It should boot an installation environment,
identify internal storage, verify a compatible Android payload, request explicit
confirmation before removing data, install/verify the internal partitions, then
instruct removal of the card for internal boot. See
[SD installer plan](../rom/SD_INSTALLER_PLAN.md). This is a planned workflow,
not an implemented installer or a physical flashing operation already authorized
for an unknown image. Do not request more board information from the owner;
future discovery should be automatic in the installation environment.

Keep the external-test profile as a separate development/validation stage.
Its kernel disables NAND/eMMC and cannot install to internal storage. The
installer needs its own reviewed kernel/ramdisk/storage support and a complete
Android payload; a small Linux/initramfs environment is an option to investigate.
Do not promise PC-style automatic SD boot on this untested RK322x unit.

Owner's preferred hardware validation sequence: build/audit a microSD test image,
test externally on the TV Box, then prepare permanent internal installation.
USB mass-storage boot is conditional on bootloader support. Follow
[external boot plan](../rom/EXTERNAL_BOOT_PLAN.md); no external Android/Vortex
image is currently built. Do not treat NAND Jump Start, loader installation or
flash erasure as a non-invasive external test.

Source preparation now exists in [rom/sdcard/](../rom/sdcard/README.md): pinned
device/common/vendor candidates, source patches checked on real worktrees and
a narrow read-only SD fstab auditor. See [the SD validation report](VALIDATION_2026-10-25_SD.md).
Passing those source/file checks is not permission to treat a card as bootable
or internal storage as preserved.

The [SDK SD reference profile](../rom/sdcard/SD_REFERENCE.md) adds explicit
controller matching (`30000000.rksdmmc` for the examined RK3229 DTS), a separate
kernel config/DTS with internal storage nodes disabled, further vendor/factory
source exclusions and cross-checks of real DTB/fstab/config/cmdline files.
An `inputs_only` result is not a boot, media or hardware approval. Preserve
the original reference artifacts and distinguish every newly compiled profile.

The [AOSP module experiment](../rom/AOSP_MODULE_BUILD.md) now builds VortexHome
through real Nougat make/Jack and has an API25 smoke result. Its APK uses the
AOSP platform test identity. The [open boot components](../rom/bootloader/README.md)
also compile separately; they have no Android payload/autoboot configured and
are not SD media. The [experimental platform overlay](../rom/platform-reference/README.md)
has a measured framebuffer ABI mismatch and is not an approved BSP.
See [the combined report](VALIDATION_2026-10-26_AOSP_BOOTLOADER.md) before continuing.

The [27/10 continuation](VALIDATION_2026-10-27_GRAPHICS_MONITOR.md) adds opt-in
graphics patches matching the measured framebuffer declaration to the kernel,
four manually compiled ARM gralloc objects, deterministic source selection and
removal of three conflicting vendor HAL copies. It is not an Android HAL link.
The unchanged AOSP APK also passed the full upload/confirmation/Home-launch
flow in API25. A supplemental DTB disables two incompatible legacy SIP consumers;
it leaves console, monitor reservations and suspend integration open. The
suspend errno patch was compiled as an object only, absent from the old Image.

The [native HAL continuation](VALIDATION_2026-10-27_NATIVE_HAL.md) then compiled
all eight HWC TUs, corrected policy/string/diagnostic defects, and linked both
gralloc/HWC manually against real API25 ARM32 reference libraries. Both DSOs
passed RTLD_NOW/HMI/close under QEMU with the real Android linker. The probe
does not call HAL device open; DSO constructors/destructors can execute. This
supersedes the standalone-object-only limit for that reference experiment,
without establishing the AOSP build graph or graphics/physical operation.

The [product/native-rule continuation](VALIDATION_2026-10-27_PRODUCT.md)
builds both HALs using genuine Android.mk compile/link/install rules with
real reference prebuilts. It adds a separate minimal SD product whose inputs
are resolved by genuine product_config inheritance and independently audited.
The build and product experiments remain separate: neither closes the complete
BSP or produces Android/SD images. Mount-error recovery/BCB behavior, USB-vold
controller matching and device permissions remain explicit blockers.

Use a cloud computer terminal (if available) to clone main and compile the native Vortex Android APK, run complete local automated checks and an Android emulator for functional tests. Investigate available AOSP 7.1.2 / Rockchip RK322x build dependencies and produce an honest report on whether a complete ROM is feasible on the available compute.

## Required tooling

- Linux x86_64, Python 3, JDK 11, Gradle 7.6.x, Android SDK platform 33, build-tools 33.0.2+, ADB and Android Emulator.
- Official asset tooling/tests additionally need Python 3.9+ and Pillow from `tools/requirements.txt`; video conversion needs ffmpeg. Follow [official asset import](OFFICIAL_ASSET_IMPORT.md), without using documentation previews as APK resources.
- For optional AOSP ROM compilation: separate, substantially larger Linux environment with a compatible legacy JDK 8 toolchain, kernel and vendor binaries; do not claim a complete ROM from an APK build.
- For QR network tests, run phone/browser on a reachable LAN to a test Android TV device. Emulator networking alone does not prove phone-to-device reachability.
- User video for boot animation must be provided as source media in Work; do not substitute the image/animation with generated art.

## Runbook

```sh
git clone https://github.com/rhashiki/VORTEX-TV-OS.git
cd VORTEX-TV-OS
git rev-parse HEAD
python3 -m pip install -r tools/requirements.txt
bash tools/validate_build01.sh
```

If dependencies are absent, install using the Work cloud computer's permitted software/environment mechanisms and rerun. Do not use GitHub-hosted workflows, do not hide errors and do not report compiled artifacts until they exist.

For the Android virtual device (API 25 preferred; compatible alternate if unavailable), test: TV Home/D-pad focus, Settings, Power error states, QR generator, LAN HTTP pairing, APK upload rejection/acceptance, installer user confirmation, USB selection, launching installed app, activity lifecycle and resource usage.

For firmware: READ ONLY inspect Rockchip references and confirm flash ID, NAND/eMMC, DDR loader, Device Tree, IR map, Wi-Fi SSV family and kernel/HAL dependencies. An emulator does not validate physical RK3229 HDMI/GPU/VPU/IR/NAND drivers.

## Required output

- Exact Git commit SHA, tool versions, CLI logs and success/fail status.
- APK build output (if success) and sizes, minimal Android compatibility report.
- Test results including negatives and any corrections, one consolidated commit per build.
- Identify specific next steps preventing a flashable Build 01 ROM, with hardware-only tests clearly marked.
- No merge or factory flash on implied authority; user must explicitly authorize hardware flashing.

## Production claims

The current main is experimental source only, NOT a verified AOSP firmware. Previous local Java/Python tests used an alternate reference copy, not guaranteed byte-identical to the Git SHA. Full Build 01 closes only with physical RK3229 boot and core drivers tested.
