# AOSP 7.1.2 / RK322x: mapa de dependências

Referências consultadas por HTTPS em 2026-10-25. Nenhuma constitui uma ROM
validada para R329Q_V8.0, e nenhum loader foi escolhido ou gravado nesta sessão.

| Fonte | Evidência e limite |
| --- | --- |
| [AOSP: versões antigas](https://source.android.com/docs/setup/start/older-versions) | Android 7.0–8.0 usa OpenJDK 8. Separar essa cadeia do JDK 11 usado pelo APK. |
| [AOSP: requisitos atuais](https://source.android.com/docs/setup/start/requirements) | Referência atual de 400 GB livres e 64 GB RAM. Esses números não são um mínimo comprovado para Nougat. O ambiente desta sessão tinha apenas cerca de 30 GB livres. |
| [Kernel oficial Rockchip](https://github.com/rockchip-linux/kernel/tree/6c04d006ae881944d32c19e68b992d0bd5ab4fde) | A revisão examinada declara Linux 3.10.104 e contém DTS rk3229-box, rk3229-box-rk805, rk3229-sdk e rk3229.dtsi. Versão igual não garante módulos/HALs ou compatibilidade da placa. |
| [Device tree comunitária RK322x](https://github.com/D042888-2/android_device_rockchip_rk322x/tree/f33a129bfab6d9cc87184ee3bf032224801fa446) | Branch aosp-7.1.2_r6, produto rk322x_box, ARMv7/Cortex-A7/Mali400. Depende de vendor/rockchip/rk322x, device/rockchip/common e kernel/arch/arm/boot/Image. Não é um BSP completo. |
| [Common da mesma origem](https://github.com/D042888-2/android_device_rockchip_common/tree/3b1aa90ef43f9d34094739a211ad44bf9a2c0b74) | Dependência candidata agora adquirida e conferida localmente. Contém o init SD, mas também caminhos de charger/recovery internos e dependências de plataforma Rockchip que precisam de revisão. |
| [Vendor RK322x da mesma origem](https://github.com/D042888-2/android_vendor_rockchip_rk322x/tree/50c7170ecb4bd907059db37f09f4767b301f2d15) | Adquirido e inventariado: 299 fontes únicas de cópia presentes, HALs ARM/API25 e módulos. `rk29-ipp.ko` declara kernel 3.0.101+, enquanto os outros 12 módulos declaram 3.10.104. Presença ou versão não comprovam ABI nem suporte desta unidade. Direitos de redistribuição dos blobs ainda não estabelecidos. |
| [rkbin oficial Rockchip](https://github.com/rockchip-linux/rkbin) | Há configurações RK322XMINIALL, RK322XATMINIALL e RK322XHMINIALL. A existência de várias variantes reforça a necessidade de identificar o hardware antes de selecionar DDR/trust/loader. |
| [Plataforma TinkerBoard Nougat](https://github.com/TinkerBoard-Android/rockchip-android-manifest/tree/e4faf840083f5c88b7d789007e6707f757368f0c) | Manifesto público com 528 projetos e include de seis projetos AOSP r39; quatro referências de componentes foram conferidas. Fornece caminhos para pesquisar core/HALs Rockchip ausentes. É RK3288, não contém um alvo RK3229 e não foi combinado ao candidato r6. [Inventário de pesquisa](sdcard/platform-reference.json), sem lock completo ou compatibilidade afirmada. |

## Dependências ainda não estabelecidas

- Manifesto completo de fontes com revisões fixadas e procedência/licenças verificadas.
- Correspondência das árvores common/vendor candidatas com a plataforma completa
  e a unidade; os componentes públicos já encontrados não formam um BSP completo.
- Kernel, configuração e DTB adequados à R329Q_V8.0; módulos e firmware Wi-Fi exatos.
- HALs Android HDMI, GPU, VPU e áudio, além de IR e armazenamento compatíveis.
- Loader DDR/trust e esquema de boot/partições que correspondam à unidade física.

O fragmento `vortex_product.mk` adiciona VortexHome a um produto já existente.
Não define produto de placa ou alvo lunch. A integração do aplicativo deve ser
compilada primeiro no BSP escolhido; só então se tenta gerar a imagem completa.

## Prioridade: teste externo antes da instalação

O [plano de boot externo](EXTERNAL_BOOT_PLAN.md) registra a preferência do
proprietário e as evidências examinadas: há um fstab SD na árvore Android
comunitária, mas sua cópia não está habilitada no `device.mk` dessa revisão.
Há também uma referência Linux/Multitool para a família. Esses fatos justificam
investigar microSD primeiro; não comprovam uma imagem Vortex externa pronta.
O plano separa a fase que deve preservar a flash interna da instalação definitiva.

Há agora um [patchset SD opt-in](sdcard/README.md) aplicado às fontes reais em
worktrees separados, com [revisões dos componentes](sdcard/sources.lock.json).
O lock JSON é um inventário parcial de componentes, não um manifesto AOSP
resolvido. [Resultados e bloqueios](../docs/VALIDATION_2026-10-25_SD.md).
Também foram compilados [kernel ARM e DTB SDK de referência](sdcard/KERNEL_BUILD.md),
em ensaio separado. A configuração genérica não representa o perfil final SD
ou a placa R329Q_V8.0; esses componentes não completam o BSP Android.

Uma [composição experimental AOSP r6/Rockchip](platform-reference/README.md)
foi registrada depois, com fontes framebuffer/DMA-BUF mais próximas e um
bloqueio ABI medido (estrutura userspace 904 bytes / kernel 908 bytes).
Ela não foi sincronizada ou aprovada como BSP. Há também
[componentes U-Boot/OP-TEE compilados de fontes](bootloader/README.md), com
limites de DDR, BootROM, reservas e chamadas SIP ainda abertos.

O [perfil SDK SD posterior](sdcard/SD_REFERENCE.md) corrige a combinação de
fontes: o fstab comunitário `ff500000` não corresponde ao nó SD `30000000`
desse kernel. O perfil acrescenta restrições de configuração/DTB e conferência
cruzada, sem selecionar uma base Android completa ou identificar a placa.

## Verificações físicas obrigatórias

O proprietário já forneceu todos os dados disponíveis e não consegue obter
outros. Não solicitar novamente coleta física; seguir a restrição em
[HARDWARE.md](HARDWARE.md). Os itens abaixo permanecem critérios não comprovados.

FlashID, NAND/eMMC e geometria, capacidade e partições, revisão do SoC, DDR,
Wi-Fi e IR precisam de diagnóstico na unidade ou de evidências identificadas.
Confirmar recuperação Loader/MaskROM antes de qualquer escrita. Depois da
compilação, a aprovação continua dependendo de boot e testes HDMI/áudio,
GPU/VPU, rede, USB, controle remoto, energia, persistência e instalação de APKs.
Um emulador Android x86 não valida esses drivers ARM/Rockchip.
