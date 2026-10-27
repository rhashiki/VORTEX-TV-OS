# Revisão independente final do perfil SD

Revisão limitada a entradas resolvidas e fontes presentes na árvore diagnóstica. Não aprova uma imagem Android/SD nem a placa física.

Foram conferidas 416 entradas de pacote (412 únicas, incluindo 134 fontes), 13 cópias com destinos relativos únicos e 6 arquivos do perfil recursivamente idênticos à árvore materializada.

VortexHome é a única seleção de launcher HOME. Estão presentes componentes para Settings/SystemUI, instalação de APK e seleção de arquivos. Os pacotes factory launcher, Bluetooth, GApps, Provision/SetupWizard, recovery, uncrypt, applypatch e gralloc.default não são selecionados. Isso não demonstra drivers ou módulos fechados.

O overlay SettingsProvider define somente os dois bools verificados por fonte: def_device_provisioned e def_user_setup_complete. Ele se aplica a dados novos; seu primeiro boot ainda não foi executado.

As três listas brutas de rk322x_box são byte a byte iguais ao baseline-05 sem patch, usando a mesma aquisição de fragmentos e o mesmo preâmbulo. O patch afeta quatro seleções somente no TARGET_PRODUCT Vortex.

Pendências antes de qualquer aprovação de imagem/boot:

- Actual init/builtins.cpp can call wipe_data_via_recovery for FS_MGR_MNTALL_DEV_NEEDS_RECOVERY; it constructs --wipe_data, writes BCB and requests reboot. Removing recovery/uncrypt/applypatch packages does not remove this compiled init path. Current SD fstab still contains check/encryptable. Exact BCB device resolution, malformed-media behavior and internal-storage preservation need integration review/tests. No assertion that this branch was executed or wrote the physical device.
- SD fstab retains /devices/ff580000.usb*, ff5c0000, ff5d0000 and /devices/usb*, while pinned RK322x DTS USB controllers use addresses30040000,30080000,300a0000,300c0000,300e0000,30100000,30120000. Actual kernel uevent/vold matching must be traced before claiming USB media discovery; DocumentsUI packages alone do not prove it.
- Minimal board init only mounts the SD fstab when ro.bootmode=sd; vendor graphics device-node ownership, ueventd/SELinux, services and full mount ordering are not integrated.
- Diagnostic tree supplies actual font product fragments, not all font payload/module sources; parsed lists do not prove framework/audio/HAL/application dependencies or image closure.
- Pinned resource/reader checks support the dedicated SettingsProvider overlay, but no SettingsProvider build or fresh Android boot has exercised it.
- R329Q_V8.0 Wi-Fi, board wiring/DDR and monitor/kernel/DTB interfaces remain unvalidated on physical hardware.

Os resultados anteriores em historical-before-final-profile/ ficam preservados como históricos; suas observações sobre entradas ainda não adquiridas ou prefixo de fontes incompleto não descrevem este snapshot final.

JSON integral: final-profile-review.json; SHA-256 7f3fd7f617eec11e99bb41175398afb3fe837a39b91ef73d3f970a9b801f1c5c.
