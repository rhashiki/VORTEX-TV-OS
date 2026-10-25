# R329Q_V8.0 / RK3229 — mandatory physical bring-up gates

### Owner information is exhausted
The owner has provided all available information and cannot obtain additional
board details. Do not request these identifiers, photos, firmware or diagnostics
again. The checks below describe validation we cannot currently establish;
they are not another data-collection task for the owner. Continue cloud/app and
public-source work using [HARDWARE.md](HARDWARE.md), preserving unknown values.

### Known from photographed device and AIDA64
- PCB R329Q_V8.0; Rockchip RK322x family (reported RK3229), ARMv7.
- 1 GiB-class DDR3 from four 2 Gbit Samsung components; kernel 3.10.104; Android API25.
- Advertised Android 10.1 and 4GB/32GB are firmware claims, not trustworthy.

### Unknown — DO NOT GUESS
- Flash package exact marking and JEDEC/FlashID, NAND/eMMC controller mode, actual capacity and partition map.
- Wi-Fi exact chip variant (SV6256P probable; SSV6051P also documented), matching driver module and firmware.
- RK322x silicon revision, trust/DDR loader, Device Tree, IR key map, HDMI/GPU/VPU/audio proprietary HAL blobs.

### Read-only discovery
- Inspect markings under good light before flashing.
- Confirm USB OTG on exact board before USB-A-to-A connection. Use matched cable and documented Rockchip loader interface.
- Loader/MaskROM: `rkdeveloptool ld`, `rci`, `rid`, `rfi`, as supported. `tools/rk322x_readonly_probe.sh` runs only queries.
- If microSD boots RK322x Multitool, use it as a diagnostic, not blindly as a universal firmware installer.
- User explicitly waived saving original Android backup, but did not waive validating recovery path.

### Before irreversible flashing
1. Identify exact chip and ROM-compatible DDR loader; match NAND driver / flash geometry.
2. Know a recovery path if Android, kernel or U-Boot fails.
3. Inspect firmware source/rights and verify hashes, kernel/DTB/partition layout.
4. Test power supply and USB detection, then make first write only with confirmed loader.
5. Post-flash: verify HDMI video/audio, Wi-Fi, Ethernet, USB storage, IR remote, clock, power/reboot, persistent data and APK install.

### ROM vs app
The repo's Gradle build produces a launcher/installer APK, **not** a flashable Android AOSP ROM. The AOSP integration fragment is experimental until toolchain, source dependencies, kernel/HALs and boot layout are validated.
