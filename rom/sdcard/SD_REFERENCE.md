# Perfil SD de referência RK3229

Este perfil aproxima os componentes de fonte já disponíveis. Continua sendo
um ensaio sobre o SDK genérico Rockchip, sem identificar a pinagem, os
reguladores, DDR, Wi-Fi ou controle remoto da R329Q_V8.0. Não é uma imagem
inicializável, uma configuração aprovada da placa ou uma instrução de gravação.

## Correspondência de controlador

O fstab comunitário usa `ff500000.rksdmmc`; o DTS do kernel RK3229 adquirido
define o SD em `rksdmmc@30000000`, eMMC em `rksdmmc@30020000` e NAND em
`nandc@30030000`. O teste anterior verificou o fstab isoladamente e não
comprovou essa correspondência. O quarto patch troca o controlador do fstab
para a referência `30000000.rksdmmc`, depois de aplicar `0001`.

Esse nome deriva do ramo OF/MMIO que forma `<endereço>.<nome do nó>`, e não
da enumeração `mmcblk0`/`mmcblk1`. Na referência de `system/core` examinada,
ueventd usa o evento da plataforma e o `PARTNAME` para criar os links
`by-name`. A configuração exige GPT no kernel, mas ainda não há tabela ou
conteúdo de partições, eventos reais ou links de dispositivo verificados.
As entradas USB herdadas continuam sem validação de hardware.

## Kernel separado para este ensaio

[rk3229-sdk-sd-reference.dts](rk3229-sdk-sd-reference.dts) inclui o DTS SDK
existente e desabilita os nós NAND, eMMC e Bluetooth. Mantém o SD habilitado.
O `chosen/bootargs` conserva `vmalloc=496M psci=enable` e acrescenta
`storagemedia=sd androidboot.mode=sd androidboot.hardware=rk30board`.
O parâmetro herdado `rockchip_jtag` foi retirado deste ensaio.
Isso não modifica parâmetros que um bootloader ainda não selecionado possa
acrescentar ou substituir em execução.

[rk3229-sdk-sd-reference.config](rk3229-sdk-sd-reference.config) é um
fragmento aplicado sobre `rockchip_defconfig`. Desabilita `RK_NAND`, `MTD` e
`BT`; conserva MMC, o controlador Rockchip, GPT e `HOTPLUG_CPU` habilitados.
Os demais ajustes genéricos do SDK não representam identificação da TV Box.
O perfil não deve ser usado para instalação interna.

O primeiro link com NAND desabilitada encontrou três consumidores de funções
IDB ainda não condicionados. O
[patch sem NAND](kernel-sd-no-nand.patch), aplicado depois do
[patch de compilação original](kernel-build-fixes.patch), guarda essas
chamadas por `CONFIG_RK_NAND`. Com `y`, os três ramos originais são mantidos;
com `n`, Ethernet retorna indisponibilidade do IDB, Wi-Fi continua a validação
existente do MAC e USB informa ausência de tag. Nenhum identificador ou
sucesso de leitura é fabricado. Configuração com NAND modular não foi testada.

Os fallbacks de endereço MAC e a disponibilidade real de rede continuam
pendentes. O backend genérico `sdmmc_vendor_storage` ainda é compilado por
MMC: a guarda de ausência de cartão eMMC foi examinada em fontes, mas a
inacessibilidade física do armazenamento interno não foi demonstrada.

O [complemento para o monitor aberto](MONITOR_REFERENCE.md) desabilita no
DTB dois consumidores de SIP incompatíveis e registra uma correção da
propagação de erro PSCI. Ele conserva o perfil e os binários anteriores;
não estabelece compatibilidade completa do monitor nem habilita console.

O aviso MODPOST de `dvfs_temp_limit()` para `cpu_up()` continua visível.
A análise estática do ELF anterior mostrou que, com `HOTPLUG_CPU=y`, as
seções `.cpuinit` são mantidas na região permanente e os símbolos examinados
ficam fora da memória de init liberável. Isso explica o aviso nessa
configuração, mas não testa hotplug, gerenciamento térmico ou hardware.
Não se marcou o worker térmico recorrente como função descartável.

O [relatório de 26/10](../../docs/VALIDATION_2026-10-26_SD_PROFILE.md)
registra a compilação bem-sucedida, os hashes e os avisos, incluindo a
inspeção de lifetime repetida no novo ELF. Os componentes continuam separados
do sistema Android e dos componentes de boot.

## Repetir a compilação dos componentes

Usar kernel e toolchain nas revisões da [referência original](KERNEL_BUILD.md),
com GNU make, compilador C do host, Python3 e `bc`. Partir de outro checkout
descartável limpo e outro diretório de saída, sem reaproveitar o ensaio anterior:

```sh
VORTEX_CHECKOUT=/caminho/VORTEX-TV-OS
KERNEL_CHECKOUT=/caminho/kernel-sd
KERNEL_OUTPUT=/caminho/kernel-sd-out
ARM_TOOLCHAIN=/caminho/linaro

git -C "$KERNEL_CHECKOUT" rev-parse HEAD
git -C "$KERNEL_CHECKOUT" apply --check "$VORTEX_CHECKOUT/rom/sdcard/kernel-build-fixes.patch"
git -C "$KERNEL_CHECKOUT" apply "$VORTEX_CHECKOUT/rom/sdcard/kernel-build-fixes.patch"
git -C "$KERNEL_CHECKOUT" apply --check "$VORTEX_CHECKOUT/rom/sdcard/kernel-sd-no-nand.patch"
git -C "$KERNEL_CHECKOUT" apply "$VORTEX_CHECKOUT/rom/sdcard/kernel-sd-no-nand.patch"
cp "$VORTEX_CHECKOUT/rom/sdcard/rk3229-sdk-sd-reference.dts" "$KERNEL_CHECKOUT/arch/arm/boot/dts/"
make -C "$KERNEL_CHECKOUT" O="$KERNEL_OUTPUT" ARCH=arm \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" \
  HOSTCFLAGS='-O2 -fcommon' rockchip_defconfig
sh "$KERNEL_CHECKOUT/scripts/kconfig/merge_config.sh" -m -O "$KERNEL_OUTPUT" \
  "$KERNEL_OUTPUT/.config" "$VORTEX_CHECKOUT/rom/sdcard/rk3229-sdk-sd-reference.config"
make -C "$KERNEL_CHECKOUT" O="$KERNEL_OUTPUT" ARCH=arm \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" \
  HOSTCFLAGS='-O2 -fcommon' olddefconfig

export KBUILD_BUILD_USER=vortex
export KBUILD_BUILD_HOST=cloud
export KBUILD_BUILD_TIMESTAMP='Mon Oct 26 12:00:00 UTC 2026'
make -C "$KERNEL_CHECKOUT" -j2 O="$KERNEL_OUTPUT" ARCH=arm \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" \
  CC="python3 $VORTEX_CHECKOUT/tools/legacy_kernel_gcc_wrapper.py $ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-gcc" \
  HOSTCFLAGS='-O2 -fcommon' Image rk3229-sdk-sd-reference.dtb
```

Usar caminhos absolutos sem espaços nesse fluxo legado. Conferir o config
resolvido, não apenas o fragmento. A receita registra o processo; não promete
identidade binária entre hosts, compatibilidade física ou cartão inicializável.

## Conferência cruzada dos arquivos

O auditor de fstab conserva o perfil comunitário antigo como padrão. Para
conferir a adaptação explicitamente:

```sh
python3 tools/audit_sd_fstab.py /caminho/fstab.rk30board.bootmode.sd \
  --profile rk3229-sdk-sd-reference --json
```

O auditor cruzado lê os quatro arquivos regulares indicados, incluindo o
DTB binário produzido, sem acessar dispositivos ou montar imagens:

```sh
python3 tools/audit_sd_boot_inputs.py \
  --fstab /caminho/fstab.rk30board.bootmode.sd \
  --dtb /caminho/rk3229-sdk-sd-reference.dtb \
  --config /caminho/kernel-out/.config \
  --cmdline rom/sdcard/sd-reference.cmdline --json
```

O resultado `inputs_only` significa somente consistência com este contrato
estático. Não valida bootloader, DTB alterado pelo loader, linha de comando
efetiva, montagem, conteúdo das partições, HALs ou ausência de escritas
internas. Um arquivo de cmdline correto não prova que o bootloader o usará.

## Integração Android ainda aberta

Na referência TinkerBoard de `system/core`, o init só seleciona `sd` quando
encontra `storagemedia=sd` e `androidboot.mode=sd`; depois escolhe o init e o
fstab pelo modo. Essa implementação usa busca por substring, não validação
estrita de tokens. O auditor deste repositório não substitui nem corrige o
init Android em execução. Essa plataforma é RK3288 e não foi selecionada
como base completa RK3229.

O parser Rockchip do kernel só acrescenta `androidboot.mode=emmc` no ramo
específico de disco eMMC com `mtdparts`, não em todo boot SD. O parser GPT
é consultado antes. Isso esclarece o código; não estabelece qual caminho
será percorrido pelo futuro bootloader e pela unidade.

Antes de preparar mídia, ainda faltam plataforma Android compatível, loader
DDR/trust, partições, ramdisk e inventário completos, exclusão efetiva de
recovery/updaters, política SELinux compilada e coleta de logs no cartão com
identidade de montagem verificada. Só depois caberá fornecer um procedimento
específico de preparo e teste físico do cartão.
