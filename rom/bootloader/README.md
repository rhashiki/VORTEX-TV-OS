# Componentes de boot RK3229 compilados de fontes

Ensaio sobre **EVB genérica**, sem validação para R329Q_V8.0. Os componentes
não formam uma imagem SD do Vortex e não devem ser gravados como se fossem
uma mídia pronta. Não houve execução ou escrita na TV Box.

| Componente | Fonte fixada |
| --- | --- |
| U-Boot v2024.01 | `https://github.com/u-boot/u-boot.git`, `866ca972d6c3cabeaf6dbac431e8e08bb30b3c8e` |
| OP-TEE 4.0.0 | `https://github.com/OP-TEE/optee_os.git`, `2a5b1d1232f582056184367fb58a425ac7478ec6`, plataforma `rockchip/rk322x` |
| Linaro ARM GCC | `dd4df7dff4f1df65d78939a958b760a79e3650a1`, GCC 6.3.1, a mesma referência usada no kernel |

O TPL usa o inicializador DDR3 RK322x aberto dessa fonte; não se inseriu blob
DDR/trust de outra placa. Isso não confirma que os timings/voltagens da EVB
correspondam à unidade. O caminho ARMv7 não usa BL31 AArch64.

## Perfil implementado

Aplicar [uboot-sd-reference.config](uboot-sd-reference.config) sobre
`evb-rk3229_defconfig`. Copiar os dois arquivos DTS para `arch/arm/dts/`
e [vortex-sd-reference.env](vortex-sd-reference.env) para
`board/rockchip/evb_rk3229/`, nas fontes U-Boot descartáveis.

O DTB define `mmc0` como SD em `0x30000000`, ordem SPL somente `mmc0`,
eMMC desabilitado e SDIO desabilitado. O ambiente é fornecido por arquivo
explícito, com `ENV_IS_NOWHERE`, `boot_targets=mmc0` e `bootdelay=-1`.
Não há payload Android configurado. A configuração desabilita MMC_WRITE,
SPL_MMC_WRITE, ambiente persistente, comandos MMC/saveenv/fastboot/UMS,
USB, rede e MTD neste ensaio.

UART2 no mux original PC2/PC3 conflita com o barramento SD. O perfil usa
UART21 PB1/PB2, cujo caminho de rota está implementado no pinctrl RK322x.
Isso resolve a combinação lógica, sem identificar onde a UART física da
TV Box está conectada. Os grupos e seus nós de configuração `pcfg` são
mantidos nos DTBs reduzidos SPL/TPL; a revisão verificou todos os phandles.

## Receita do ensaio

Usar dois checkouts limpos nos pins acima e diretórios `O=` separados.
Host Linux x86_64 com GCC, make, Python3, OpenSSL headers, bison, flex, m4,
bc, xxd, SWIG 4.2.1, setuptools 75.8.0, pyelftools 0.32 e pycryptodome 3.23.0.
Os pacotes do experimento foram extraídos localmente. SWIG 4.3 mudou uma API
usada pelo binding libfdt e falhou; escolheu-se uma versão compatível, sem
alterar o código de firmware ou ocultar avisos.

```sh
# Caminhos absolutos, sem espaços, para fontes/ferramentas já adquiridas.
VORTEX_CHECKOUT=/caminho/VORTEX-TV-OS
UBOOT_CHECKOUT=/caminho/u-boot-sd
UBOOT_OUTPUT=/caminho/u-boot-out
OPTEE_CHECKOUT=/caminho/optee-os
OPTEE_OUTPUT=/caminho/optee-out
ARM_TOOLCHAIN=/caminho/linaro

make -C "$OPTEE_CHECKOUT" -j2 O="$OPTEE_OUTPUT" PLATFORM=rockchip \
  PLATFORM_FLAVOR=rk322x CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-"
cp "$VORTEX_CHECKOUT"/rom/bootloader/rk3229-vortex-sd-reference.dts "$UBOOT_CHECKOUT/arch/arm/dts/"
cp "$VORTEX_CHECKOUT"/rom/bootloader/rk3229-vortex-sd-reference-u-boot.dtsi "$UBOOT_CHECKOUT/arch/arm/dts/"
cp "$VORTEX_CHECKOUT/rom/bootloader/vortex-sd-reference.env" "$UBOOT_CHECKOUT/board/rockchip/evb_rk3229/"
make -C "$UBOOT_CHECKOUT" O="$UBOOT_OUTPUT" \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" evb-rk3229_defconfig
sh "$UBOOT_CHECKOUT/scripts/kconfig/merge_config.sh" -m -O "$UBOOT_OUTPUT" \
  "$UBOOT_OUTPUT/.config" "$VORTEX_CHECKOUT/rom/bootloader/uboot-sd-reference.config"
make -C "$UBOOT_CHECKOUT" O="$UBOOT_OUTPUT" \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" olddefconfig
make -C "$UBOOT_CHECKOUT" -j2 O="$UBOOT_OUTPUT" \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" TEE="$OPTEE_OUTPUT/core/tee-raw.bin"
```

Conferir o config resolvido e os DTBs filtrados; um make com saída zero não
basta para verificar referências. A receita não promete hashes idênticos
entre hosts; timestamps também entram nos binários.

## Limites de integração

O TPL retorna ao BootROM para o próximo estágio. As restrições SD nos
estágios abertos não controlam nem provam a política de fallback da ROM.
DDR, pinagem, clocks, voltagens e periferia continuam sendo referências EVB.

OP-TEE ocupa core `0x68400000`–`0x68600000` e SHM
`0x68600000`–`0x68700000`. O perfil habilita `OPTEE_LIB` para o caminho
condicional de cópia das reservas ao DTB Linux. As reservas precisam ser
verificadas no DTB efetivamente entregue ao kernel; não houve esse boot.

Os IDs padronizados PSCI CPU_ON/OFF coincidem nas fontes examinadas, mas
CPU_SUSPEND cai num retorno não suportado nessa plataforma OP-TEE. As
chamadas Rockchip SIP do kernel legado ainda não têm ABI estabelecida com
esse monitor. Compilar OP-TEE não resolve esses serviços automaticamente.

[Relatório dos componentes](../../docs/VALIDATION_2026-10-26_AOSP_BOOTLOADER.md)
e [revisão da cadeia](../../docs/validation/2026-10-26-aosp-bootloader/boot-chain/BOOT_CHAIN_REVIEW.md)
registram hashes, falhas de host e provas. O próximo artefato de sistema
continua dependendo de Android completo, HALs coerentes, ramdisk e layout;
este diretório não fornece instruções de gravação.
