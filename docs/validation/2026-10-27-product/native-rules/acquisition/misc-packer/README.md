# Official r6 host relocation packer

The single host executable comes from platform/prebuilts/misc at official
android-7.1.2_r6 commit6287eb468c5772f5da2c468396bdf0068a4fa2d5.
Its bytes match the Git blob SHA1 and observed SHA256 recorded in provenance.
The genuine MODULE_LICENSE_BSD_LIKE marker and PREBUILT source-version record
were retained with their own Git blob hashes.

The executable is installed only into this experiment's default
prebuilts/misc/linux-x86/relocation_packer path. --help exits0, and ldd reports
no missing host dependencies. No host compatibility package or system package
change was required. No disabling of relocation packing or fake packer was used.

This task checks tool acquisition/readiness only. Actual shared-library
packing, installation and loading are evaluated by the parent experiment.
The tool executable need not be exported in the Vortex artifact package.
