# Source and license provenance

This evidence package contains text logs, build definitions, small test/probe
scripts, source excerpts, patches and license notices. Separate compiled
artifacts originate from the exact pinned sources and observed inputs recorded
in the JSON evidence. SDK/platform reference DSOs, vendor blobs, toolchain
executables, CRT objects and complete external source checkouts are excluded.

The primary audio source files have differing original notices. `audio_hw.c`,
`alsa_mixer.c` and `audio_hw_hdmi.c` carry AOSP Apache-2.0 headers;
`alsa_route.c` states Rockchip copyright without a license grant in that header.
The per-file header excerpts preserve that distinction. No uniform third-party
license is inferred from public availability or assigned to the complete BSP.

The Android power/USB/submix and framework/system-media source carries its
upstream Apache-2.0 notices. TinyALSA and audio_route preserve their BSD notices;
Speex and Expat retain their original notices. These texts are under `licenses/`.

Source-built LLVM unwind/compiler-rt archives retain their upstream
University of Illinois/NCSA/MIT notices. Linked GCC runtime code retains the
upstream GPL texts and GCC Runtime Library Exception. These notices are copied
from the previously verified exact Android toolchain/source provenance rather
than relabeling the third-party outputs.

These notes do not establish redistribution rights for a future full vendor
firmware. Refer to each pinned repository and its per-file notices for complete
source and licensing details.
