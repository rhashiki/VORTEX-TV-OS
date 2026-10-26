# Candidato Android com montagem exclusiva por microSD

Este diretório contém um **patchset opt-in de fontes**, dedicado ao teste por
SD. Não é uma imagem inicializável, não cria um produto/`lunch` e não deve ser
usado como perfil de instalação interna. O Vortex padrão não aplica esses
patches automaticamente.

As alterações foram produzidas e aplicadas sobre duas árvores upstream reais,
com revisões fixadas. Nenhum script ou comando de build do BSP foi executado.
Os checkouts originais permaneceram sem alterações; a aplicação foi conferida
em worktrees de teste separados.

A ampliação de 26/10 acrescenta a árvore vendor e o
[perfil SDK SD de referência](SD_REFERENCE.md). Os três primeiros patches
preservam o controlador `ff500000` da fonte comunitária; `0004` adapta esse
fstab ao controlador `30000000` do kernel RK3229 examinado. Não combinar
automaticamente o fstab antigo com esse kernel. `0005`/`0006` retiram caminhos
vendor/fábrica e Bluetooth das listas examinadas, sem constituir uma imagem.

## Árvores e ordem de aplicação

| Patch | Árvore dentro do BSP | Fonte e revisão |
| --- | --- | --- |
| [0001-rk322x-sd-only-fstab.patch](patches/0001-rk322x-sd-only-fstab.patch) | `device/rockchip/rk322x` | [D042888-2/android_device_rockchip_rk322x](https://github.com/D042888-2/android_device_rockchip_rk322x/tree/f33a129bfab6d9cc87184ee3bf032224801fa446), `f33a129bfab6d9cc87184ee3bf032224801fa446` |
| [0002-common-sd-only-init.patch](patches/0002-common-sd-only-init.patch) | `device/rockchip/common` | [D042888-2/android_device_rockchip_common](https://github.com/D042888-2/android_device_rockchip_common/tree/3b1aa90ef43f9d34094739a211ad44bf9a2c0b74), `3b1aa90ef43f9d34094739a211ad44bf9a2c0b74` |
| [0003-common-disable-internal-provisioning.patch](patches/0003-common-disable-internal-provisioning.patch) | `device/rockchip/common`, após `0002` | Mesma revisão common `3b1aa90ef43f9d34094739a211ad44bf9a2c0b74` |
| [0004-rk3229-sdk-sd-controller.patch](patches/0004-rk3229-sdk-sd-controller.patch) | `device/rockchip/rk322x`, após `0001` | Mesma revisão device; adaptação ao DTS do kernel `6c04d006ae881944d32c19e68b992d0bd5ab4fde` |
| [0005-common-remove-sd-factory-services.patch](patches/0005-common-remove-sd-factory-services.patch) | `device/rockchip/common`, após `0002` e `0003` | Mesma revisão common |
| [0006-vendor-omit-bluetooth.patch](patches/0006-vendor-omit-bluetooth.patch) | `vendor/rockchip/rk322x` | [D042888-2/android_vendor_rockchip_rk322x](https://github.com/D042888-2/android_vendor_rockchip_rk322x/tree/50c7170ecb4bd907059db37f09f4767b301f2d15), `50c7170ecb4bd907059db37f09f4767b301f2d15` |

Os diffs preservam os avisos de licença Apache 2.0 presentes nos arquivos make.
Os arquivos fstab/init modificados não contêm um cabeçalho de licença próprio; a presença pública
do repositório não encerra a revisão de direitos de distribuição do BSP completo.

## Alterações implementadas

- O produto RK322x copia somente `fstab.rk30board.bootmode.sd`. A cópia do
  `init.box.rc` existente permanece. Não há cópia de fstab `unknown`/`emmc` por
  esse produto.
- No fstab SD após `0001`, as partições críticas continuam sob o controlador
  `ff500000.rksdmmc`; após `0004`, usam `30000000.rksdmmc`. `/system` mantém
  `ro`. Foi removida a entrada
  `voldmanaged` do próprio cartão de boot, para que ele não seja apresentado
  ao vold como mídia removível comum. Permanecem as entradas USB e zram.
- O common copia somente o init de bootmode `sd`, removendo os init de
  `emmc`, `unknown` e `nvme` desta lista. Também deixa de copiar seus fstab
  `unknown`/`emmc`.
- Os dois blocos charger que montavam eMMC ou `mtd@system`/`mtd@metadata`
  foram retirados de `init.rockchip.rc`, assim como o comando que fixava
  `ro.boot.charger.emmc=0` no evento `charger`.
- No fluxo normal de boot, `init.rk30board.rc` deixa de carregar explicitamente
  `/drmboot.ko` (módulo distribuído na pasta `nand` da árvore RK322x) e deixa de
  definir o serviço automático `rk_store_keybox`, antes pertencente à classe
  `main`. As demais cargas de módulos gráficos permanecem como estavam;
  o patch não presume compatibilidade de ABI ou comportamento dos binários.
- `0005` retira o serviço vendor `drmservice`, sua inclusão, ferramentas de
  fábrica `whtest`/`preinstall_cleanup`, import OP-TEE e os caminhos Bluetooth
  examinados em init, listas de pacotes, flags, ueventd e grants vendor SELinux.
  Wi-Fi conserva a seleção upstream, sem identificar o chip da unidade.
- `0006` retira seis cópias explícitas de bibliotecas Bluetooth do vendor.
  Os blobs continuam na árvore upstream e não são redistribuídos aqui.
  Serviços DRM de mídia Android e arquivos/flags recovery não foram alterados.

O resultado é intencionalmente limitado: um bootmode diferente de `sd` deixa
de ter os fallbacks de montagem dessas listas. Isso não transforma um boot
incorreto em um boot SD funcional. Os arquivos de origem de outros bootmodes
ainda existem no repositório upstream, mas não são copiados por essas listas
depois dos patches. Outros produtos ou dependências podem copiar arquivos
novamente; o ramdisk final terá de ser inspecionado.

## Pré-requisitos ainda pendentes

O caminho `/fstab.rk30board` é selecionado pelo init Rockchip a partir do
bootmode. O patchset não altera `system/core`, kernel, DTB, bootargs, loader
DDR/trust ou tabela de partições. Ainda é necessário confirmar, na revisão
real do BSP, a cadeia `storagemedia=sd` / `androidboot.mode=sd` → `ro.bootmode=sd`
→ init SD → fstab SD. Não se deve forçar um bootmode falso para mascarar uma
seleção de mídia incorreta.

O BSP completo, HALs e componentes de boot compatíveis ainda não estão
estabelecidos. A primeira mídia de teste deverá excluir recovery e instalação
automática. A composição dessa mídia continua pendente do BSP completo; não
foram forçados flags AOSP ou criados substitutos de recovery sem suas fontes.
Recovery, atualização e provisionamento vendor restantes ainda bloqueiam uma
afirmação de preservação da memória interna e ainda exigem o produto completo.
As referências e lacunas estão em
[EXTERNAL_BOOT_PLAN.md](../EXTERNAL_BOOT_PLAN.md) e
[AOSP_SOURCE_MAP.md](../AOSP_SOURCE_MAP.md).

Aplicar os patches não comprova ausência de gravações internas, nem suporte
físico RK3229. Não houve compilação de uma ROM, geração de mídia ou boot na
TV Box nesta validação. A instalação interna deve usar outro perfil, somente
depois da etapa externa. Não usar Jump Start, apagar flash ou instalar loader
interno como pré-condição escondida deste candidato SD.

## Conferência nas fontes

Executar somente em worktrees descartáveis das revisões indicadas. As duas
árvores são repositórios Git diferentes; cada patch deve ser aplicado à raiz
do repositório correspondente, sem executar scripts do BSP:

```sh
VORTEX_SOURCES=/caminho/absoluto/VORTEX-TV-OS
git -C device/rockchip/rk322x rev-parse HEAD
git -C device/rockchip/common rev-parse HEAD
git -C device/rockchip/rk322x apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0001-rk322x-sd-only-fstab.patch"
git -C device/rockchip/common apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0002-common-sd-only-init.patch"
git -C device/rockchip/rk322x apply "$VORTEX_SOURCES/rom/sdcard/patches/0001-rk322x-sd-only-fstab.patch"
git -C device/rockchip/common apply "$VORTEX_SOURCES/rom/sdcard/patches/0002-common-sd-only-init.patch"
git -C device/rockchip/common apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0003-common-disable-internal-provisioning.patch"
git -C device/rockchip/common apply "$VORTEX_SOURCES/rom/sdcard/patches/0003-common-disable-internal-provisioning.patch"
git -C device/rockchip/rk322x apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0004-rk3229-sdk-sd-controller.patch"
git -C device/rockchip/rk322x apply "$VORTEX_SOURCES/rom/sdcard/patches/0004-rk3229-sdk-sd-controller.patch"
git -C device/rockchip/common apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0005-common-remove-sd-factory-services.patch"
git -C device/rockchip/common apply "$VORTEX_SOURCES/rom/sdcard/patches/0005-common-remove-sd-factory-services.patch"
git -C vendor/rockchip/rk322x rev-parse HEAD
git -C vendor/rockchip/rk322x apply --check "$VORTEX_SOURCES/rom/sdcard/patches/0006-vendor-omit-bluetooth.patch"
git -C vendor/rockchip/rk322x apply "$VORTEX_SOURCES/rom/sdcard/patches/0006-vendor-omit-bluetooth.patch"
git -C device/rockchip/rk322x diff --check
git -C device/rockchip/common diff --check
git -C vendor/rockchip/rk322x diff --check
```

`git apply --check` e a aplicação real dos três patches passaram sobre as
revisões fixadas em 25/10/2026. O terceiro foi conferido após aplicar `0002`
em um novo worktree common. Esses resultados validam aplicação, não o build Android.
Logs desta execução: `/workspace/build01-sd/patch-validation/rk322x-apply.log`,
`common-apply.log`, `common-provisioning-apply.log` e `patch-results.json`.
O JSON registra hashes upstream e dos arquivos modificados. As árvores finais
aplicadas para inspeção ficam em `/workspace/build01-sd/check-rk322x` e
`check-common-stack`; `check-common` conserva a conferência isolada de `0002`.
Os incrementos de 26/10 foram conferidos em novos worktrees sob
`/workspace/build01-sd-next`; as árvores anteriores foram preservadas.

## Integridade do patchset

| Arquivo | SHA-256 |
| --- | --- |
| `0001-rk322x-sd-only-fstab.patch` | `7b1251a3ee6b0beaf99fb198070b13e54efac47af3c650728b28d0c5b59b7b82` |
| `0002-common-sd-only-init.patch` | `b8da51f8744f5a7cd2f2377d507a53ee87fe55fc9bd93785afa42227e7d4e0a4` |
| `0003-common-disable-internal-provisioning.patch` | `51bfc8d4828cff32f4918c63da3b657007f7d733c7d11193f63a7ff6983b69c4` |
| `0004-rk3229-sdk-sd-controller.patch` | `b45019dd690914c25b3959a2e155a48156e4b10eff155aac720c98a06c400e4c` |
| `0005-common-remove-sd-factory-services.patch` | `7918eb51fba32f060c1dfc69e719579ad2854342de0ad1182cc60aa2143956d5` |
| `0006-vendor-omit-bluetooth.patch` | `97025b3ee255f7342c3b9c08b2eccbc02c4957b3429cc679e8888e1f2b3ba8a5` |

Hashes SHA-256 dos cinco arquivos upstream antes da aplicação:

| Árvore / arquivo | SHA-256 |
| --- | --- |
| `rk322x/device.mk` | `12846b37a99728a52d80d4336c5cf772c5bbe465071cd63f2ffc26b31ef8921d` |
| `rk322x/fstab.rk30board.bootmode.sd` | `d9f4befeb3a769d65e269cbee51c50b0d41b5c32abff5b57c743097d4be0c9af` |
| `common/device.mk` | `19796400b2affbaa74bf5d75aa2ae10bef845c7d691e079e7630d6a3d7609209` |
| `common/init.rockchip.rc` | `90ef7927ba97e2df3db1d8461a9ed215c80252a1fcf0546e8f61dd96c3ecbfd7` |
| `common/init.rk30board.rc` | `94bd3fc0827c6d55357925dcbca482efd1c5946d4cac250ae558799cb120aa81` |

O trabalho usa os dados de placa já disponíveis. Não solicita novos arquivos,
identificadores ou diagnósticos ao proprietário e não utiliza GitHub Actions.

Evidência versionada: [aplicação e hashes dos três patches](../../docs/validation/2026-10-25-sd/patch-results.json)
e [validação do candidato SD](../../docs/VALIDATION_2026-10-25_SD.md).
