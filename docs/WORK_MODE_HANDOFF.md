# Build 01 — reproducible validation in ChatGPT Work

**Project:** https://github.com/rhashiki/VORTEX-TV-OS
**Default branch:** main
**Strict restriction:** NEVER create, run, inspect, or depend on GitHub Actions. No deployment/flash/merge is permitted on the basis of source checks alone.

## Working goal

Use a cloud computer terminal (if available) to clone main and compile the native Vortex Android APK, run complete local automated checks and an Android emulator for functional tests. Investigate available AOSP 7.1.2 / Rockchip RK322x build dependencies and produce an honest report on whether a complete ROM is feasible on the available compute.

## Required tooling

- Linux x86_64, Python 3, JDK 11, Gradle 7.6.x, Android SDK platform 33, build-tools 33.0.2+, ADB and Android Emulator.
- For optional AOSP ROM compilation: separate, substantially larger Linux environment with a compatible legacy JDK 8 toolchain, kernel and vendor binaries; do not claim a complete ROM from an APK build.
- For QR network tests, run phone/browser on a reachable LAN to a test Android TV device. Emulator networking alone does not prove phone-to-device reachability.
- User video for boot animation must be provided as source media in Work; do not substitute the image/animation with generated art.

## Runbook

```sh
git clone https://github.com/rhashiki/VORTEX-TV-OS.git
cd VORTEX-TV-OS
git rev-parse HEAD
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
