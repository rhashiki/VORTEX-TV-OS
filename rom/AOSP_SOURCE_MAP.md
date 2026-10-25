# AOSP 7.1.2 / RK322x: mapa de dependências

Referências consultadas por HTTPS em 2026-10-25. Nenhuma constitui uma ROM
validada para R329Q_V8.0, e nenhum loader foi escolhido ou gravado nesta sessão.

| Fonte | Evidência e limite |
| --- | --- |
| [AOSP: versões antigas](https://source.android.com/docs/setup/start/older-versions) | Android 7.0–8.0 usa OpenJDK 8. Separar essa cadeia do JDK 11 usado pelo APK. |
| [AOSP: requisitos atuais](https://source.android.com/docs/setup/start/requirements) | Referência atual de 400 GB livres e 64 GB RAM. Esses números não são um mínimo comprovado para Nougat. O ambiente desta sessão tinha apenas cerca de 30 GB livres. |
| [Kernel oficial Rockchip](https://github.com/rockchip-linux/kernel/tree/6c04d006ae881944d32c19e68b992d0bd5ab4fde) | A revisão examinada declara Linux 3.10.104 e contém DTS rk3229-box, rk3229-box-rk805, rk3229-sdk e rk3229.dtsi. Versão igual não garante módulos/HALs ou compatibilidade da placa. |
| [Device tree comunitária RK322x](https://github.com/D042888-2/android_device_rockchip_rk322x/tree/f33a129bfab6d9cc87184ee3bf032224801fa446) | Branch aosp-7.1.2_r6, produto rk322x_box, ARMv7/Cortex-A7/Mali400. Depende de vendor/rockchip/rk322x, device/rockchip/common e kernel/arch/arm/boot/Image. Não é um BSP completo. |
| [rkbin oficial Rockchip](https://github.com/rockchip-linux/rkbin) | Há configurações RK322XMINIALL, RK322XATMINIALL e RK322XHMINIALL. A existência de várias variantes reforça a necessidade de identificar o hardware antes de selecionar DDR/trust/loader. |

## Dependências ainda não estabelecidas

- Manifesto completo de fontes com revisões fixadas e procedência/licenças verificadas.
- Árvores device/rockchip/common e vendor/rockchip correspondentes ao produto.
- Kernel, configuração e DTB adequados à R329Q_V8.0; módulos e firmware Wi-Fi exatos.
- HALs Android HDMI, GPU, VPU e áudio, além de IR e armazenamento compatíveis.
- Loader DDR/trust e esquema de boot/partições que correspondam à unidade física.

O fragmento `vortex_product.mk` adiciona VortexHome a um produto já existente.
Não define produto de placa ou alvo lunch. A integração do aplicativo deve ser
compilada primeiro no BSP escolhido; só então se tenta gerar a imagem completa.

## Verificações físicas obrigatórias

FlashID, NAND/eMMC e geometria, capacidade e partições, revisão do SoC, DDR,
Wi-Fi e IR precisam de diagnóstico na unidade ou de evidências identificadas.
Confirmar recuperação Loader/MaskROM antes de qualquer escrita. Depois da
compilação, a aprovação continua dependendo de boot e testes HDMI/áudio,
GPU/VPU, rede, USB, controle remoto, energia, persistência e instalação de APKs.
Um emulador Android x86 não valida esses drivers ARM/Rockchip.
