# Source and license notes

This evidence package contains text records, small build/probe/test scripts, patches and license notices. The separate final HAL output files were compiled from the exact pinned public source trees and patches listed in source-revisions.json and compiler-inputs.json. No Google SDK platform DSO, vendor blob, compiler executable, QEMU executable, CRT object, static archive, filesystem image, signing key or complete source checkout is included here.

Gralloc alloc_device.cpp and its Android.mk retain their original ARM/AOSP copyright and Apache-2.0 source header. Source excerpts in the regression retain their origin through source hashes and pinned paths; they are not a substitute for the complete upstream source.

The Rockchip HWC files have differing individual headers; several only state Copyright (C) 2015 Rockchip Electronics Co., Ltd. No uniform upstream license is inferred or assigned by this report. Public source provenance does not itself establish redistribution terms for every upstream file or a future product. The upstream source/patch references must remain attached to experimental outputs.

The genuine source-built LLVM unwind/compiler-rt archives contribute their upstream University of Illinois/NCSA/MIT notices, copied under licenses/. The linked Android GCC runtime archives are covered by their upstream GPL texts and GCC Runtime Library Exception, also copied under licenses/. AOSP Bionic source CRT provenance and its original source copyright/header are retained in the CRT evidence. These notes do not relabel third-party code.

Host compiler/relocation-packer license/provenance texts are retained for reproduction; their executable bytes are excluded. The SDK ARM32 libraries and vendor libion are excluded rather than repackaged under the project's license. Consult the exact pinned source repositories for the complete original source and per-file notices.
