# Flattened product selection and file audit

Read-only selection/file audit of already flattened rk322x_box eng product lists in the supplied diagnostic tree. No conditional branch inference, BSP script execution, module dependency closure, build success, ROM approval, or hardware claims.

Missing means absent/nonregular after resolving symlinks under the supplied product-graph tree; it does not establish absence in a complete Android checkout. All input lists were consumed exactly as present.

## Counts

| Measure | Count |
|---|---:|
| package_entries | 399 |
| unique_packages | 388 |
| duplicate_package_entries_beyond_first | 11 |
| copy_entries | 342 |
| unique_copy_entry_strings | 338 |
| exact_duplicate_copy_entries_beyond_first | 4 |
| unique_literal_destinations | 332 |
| unique_normalized_destinations | 328 |
| leading_slash_destination_entries | 6 |
| literal_destinations_with_multiple_sources | 6 |
| normalized_destinations_with_multiple_literal_spellings | 4 |
| unique_copy_sources | 338 |
| regular_copy_sources_following_symlinks | 325 |
| source_symlinks_to_regular_files | 0 |
| missing_or_nonregular_unique_sources | 13 |
| missing_or_nonregular_copy_entries | 14 |
| missing_or_nonregular_literal_first_sources | 10 |
| property_tokens | 55 |
| malformed_property_tokens | 3 |

## Selected feature cases

- Launcher: `Launcher3` appears at package lines 1 and 64; no launcher COPY_FILES entries.
- Bluetooth: no `Bluetooth`, `BluetoothMidiService`, `bluetooth.default`, or `libbt-vendor` package, or Bluetooth-named permission XML is selected. `audio.a2dp.default` and `javax.obex` remain; the copy list retains the A2DP HAL, 22 `.hcd` firmware files, and 7 `lib/rtkbt` plugins. The selected generic `platform.xml` still maps BLUETOOTH/BLUETOOTH_ADMIN/BLUETOOTH_STACK permissions. `ro.rk.bt_enable=false` is selected. These facts do not prove runtime/module closure.
- Google/GApps: no named GApps package is selected. Three Google-named permission XML files remain in COPY_FILES (Maps, media effects, Widevine), and selected `features.xml` declares `com.google.android.feature.GOOGLE_BUILD` and `com.google.android.feature.GOOGLE_EXPERIENCE`. Permission/feature declarations alone do not establish the corresponding apps/libraries.
- Updater/recovery: `uncrypt`, `applypatch`, and `recovery` are selected; the vendor `librockchip_update_jni.so` is copied. No named vendor updater app is selected.
- Factory: no factory-named app/module/copy path is selected. Four `ro.factory.*` properties remain, along with generic debug/test tools recorded separately in JSON.

## Destination cases

Pinned `build/core/Makefile:29-45` keeps the first source for each literal destination after removing exact duplicate entry strings. Content hashes below distinguish duplicate selections from different file contents.

| Literal destination | Lines | Sources | Existing contents differ |
|---|---|---:|---|
| `system/usr/keylayout/ff680030_pwm.kl` | 6, 310 | 2 | True |
| `system/etc/audio_policy.conf` | 7, 317 | 2 | False |
| `system/etc/permissions/android.hardware.hdmi.cec.xml` | 258, 328 | 2 | Unknown: one source absent |
| `system/etc/permissions/android.hardware.usb.accessory.xml` | 259, 318 | 2 | Unknown: one source absent |
| `system/etc/permissions/android.software.webview.xml` | 262, 336 | 2 | Unknown: one source absent |
| `system/etc/permissions/tv_core_hardware.xml` | 273, 334 | 2 | True |

Six destinations begin with a slash. Four also have a relative spelling below: literal deduplication does not merge them, while `append-path` (`build/core/definitions.mk:847-849`) collapses the doubled slash in the generated output path:

- `system/bin/rksmbd`: lines 45, 321; spellings: `system/bin/rksmbd`, `/system/bin/rksmbd`; existing contents differ: False.
- `system/etc/smb.conf`: lines 46, 324; spellings: `system/etc/smb.conf`, `/system/etc/smb.conf`; existing contents differ: False.
- `system/etc/smbpasswd`: lines 47, 326; spellings: `system/etc/smbpasswd`, `/system/etc/smbpasswd`; existing contents differ: False.
- `system/etc/smbusers`: lines 48, 325; spellings: `system/etc/smbusers`, `/system/etc/smbusers`; existing contents differ: False.

## Missing/nonregular source cases

| Source | Lines |
|---|---|
| `system/core/rootdir/init.zygote32.rc` | 301, 337 |
| `kernel/arch/arm/boot/Image` | 302 |
| `hardware/broadcom/wlan/bcmdhd/config/wpa_supplicant_overlay.conf` | 313 |
| `hardware/broadcom/wlan/bcmdhd/config/p2p_supplicant_overlay.conf` | 314 |
| `frameworks/native/data/etc/android.hardware.usb.accessory.xml` | 318 |
| `frameworks/native/data/etc/android.hardware.hdmi.cec.xml` | 328 |
| `frameworks/av/media/libeffects/data/audio_effects.conf` | 335 |
| `frameworks/native/data/etc/android.software.webview.xml` | 336 |
| `system/core/rootdir/etc/public.libraries.android.txt` | 338 |
| `system/core/rootdir/init.usb.rc` | 339 |
| `system/core/rootdir/init.usb.configfs.rc` | 340 |
| `system/core/rootdir/ueventd.rc` | 341 |
| `system/core/rootdir/etc/hosts` | 342 |

All device/rockchip and vendor/rockchip selected sources are regular files in this tree. The 13 absent sources belong to system, kernel, hardware, or framework paths; three are later alternatives ignored by the literal first-source rule. Ten first-selected literal destinations have absent sources.

## Property token cases

Properties were serialized by whitespace splitting in inspect.mk. The three tokens from testing.mediascanner.skiplist = /mnt/shell/emulated/Android/ are individually not key=value. This audit does not evaluate later build-property normalization or final build.prop validity.

Heapstartsize, heapgrowthlimit, and heapsize appear with differing selected values. Heap target utilization/minfree/maxfree, HDMI enable, and U-disk visible also repeat; JSON records the original order and values without asserting final property resolution.

## Input SHA-256

- `packages.list`: `d3cda7185a68ba68073a1466566feb022cddadfe3ec51b7b97ca322112b0dad3`
- `copy-files.list`: `8cd2e76c5666ac89bebf04073129b82e97e59077f9047ba8098dcd3dc1fb41e1`
- `properties.list`: `727a67ae916cbcbf671c4c2828b877f32d35f39be763d2a4d99ecdf9011d94a4`

- Full case/source inventory: `inventory.json` (`c39c5749e0ac928b9208fec53fef8ec6ca6202aa7e7dfea3f3d8054ae13e4c6d`).

JSON includes every selected package/copy entry with original line numbers, SHA-256 for every existing unique source, exact duplicate strings, source status, first-source conflicts, normalized aliases, and property token anomalies.
