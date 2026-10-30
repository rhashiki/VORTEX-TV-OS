# Bounded whole-platform attempt

These files preserve genuine Android make/envsetup/lunch evidence on an incomplete source tree. They do not establish complete platform dependency closure, a ROM, an SD boot image or board compatibility. The final make stop is recorded in checkpoint.json. All attempts are retained, including failures. The build baseline is historical Vortex ba4afebe; current main additionally needs unavailable private native APK and OEM catalog-access inputs.

The official r6 Bison i386 prebuilt could not execute on this host. An unchanged r6 external/bison Android.mk built native GNU Bison 2.7, selected through the supported BISON override. The original prebuilt remains unchanged. Genuine historical SDK stubs/ASM5 are host build inputs, not substitute target-platform library providers.

Small raw logs and metadata are here. Files exceeding 250 KiB are indexed in large-raw-files.json and retained outside Git for the component archive. Git-source-checkouts.json records materialized repositories only; reused source trees and fragments are documented in recipes/ and acquisition metadata, not asserted to be a full repo manifest. Java artifacts contain JVM classes only; no DEX/ART execution is claimed.
