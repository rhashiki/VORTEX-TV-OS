# Ensaio de kernel ARM de referência

Este ensaio compila componentes Linux separadamente da plataforma Android.
O perfil é `rockchip_defconfig`, com o DTS **genérico** `rk3229-sdk.dts`.
Ele não seleciona a pinagem da R329Q_V8.0, não herda automaticamente os patches
de ramdisk SD e não é um perfil aprovado de preservação da flash.

Este documento conserva o ensaio original. O
[perfil SD posterior](SD_REFERENCE.md) usa outro DTS/config e outro diretório
de saída; seus resultados não substituem os hashes desta referência.

## Fontes e ferramentas

| Entrada | Revisão |
| --- | --- |
| [Kernel Rockchip](https://github.com/rockchip-linux/kernel/tree/6c04d006ae881944d32c19e68b992d0bd5ab4fde) | `6c04d006ae881944d32c19e68b992d0bd5ab4fde`, Linux 3.10.104 |
| [Linaro ARM GCC 6.3.1](https://github.com/pstglia/gcc-linaro-6.3.1-2017.05-x86_64_arm-linux-gnueabihf/tree/dd4df7dff4f1df65d78939a958b760a79e3650a1) | `dd4df7dff4f1df65d78939a958b760a79e3650a1` |
| Filtro de avisos do host | [legacy_kernel_gcc_wrapper.py](../../tools/legacy_kernel_gcc_wrapper.py), Python3, licença e whitelist upstream preservadas |

Os resultados, configuração, comandos e hashes estão no
[relatório de compilação](../../docs/validation/2026-10-25-sd/kernel-build-report.json)
e no [relatório da etapa](../../docs/VALIDATION_2026-10-25_SD.md).

## Correções de compilação

O [patch acumulado](kernel-build-fixes.patch) registra todas as alterações
feitas em fontes versionadas do kernel. São ajustes de caminhos de entrada e
arquivos gerados para build `O=`, atributos em declarações não usadas e chaves
que tornam explícito o escopo já definido pelo C. A tabela CIFS vazia sem
referências foi retirada. Os dados de configuração, controles e tabelas dos
demais drivers foram preservados.

O patch preserva bytes de EOL legados, inclusive CR em alguns contextos. Não
normalizar suas quebras de linha. Atributos Git mantêm esses bytes; a checagem
de whitespace é feita nas fontes aplicadas. O replay do patch sobre arquivos
do commit original reproduziu byte a byte todos os arquivos modificados.

O cabeçalho GPL do Mali já existe na fonte. Os ajustes de caminho não mudam
sua licença nem desativam GPU, gerenciamento de energia ou DMA-BUF. No UMP,
o config selecionado é copiado byte a byte para o diretório de saída, com
falha de build caso não possa ser gerado, sem tocar o header de origem.

O wrapper Python3 mantém a rejeição de avisos não permitidos. A versão
versionada também espera o compilador terminar antes de limpar um objeto
rejeitado e encaminha a saída sem alterar o começo das linhas; seis testes
independentes verificam essa política e a identificação do compilador. As tentativas
iniciais usaram um port sem essa correção de ciclo de vida e estão separadas
nos registros. Não se acrescentaram avisos à whitelist para obter sucesso.

## Repetir o ensaio em outra máquina Linux

Obter os dois repositórios nas revisões indicadas, com host C compiler, GNU
make, Python3 e `bc` disponíveis. Usar caminhos absolutos sem espaços para
esse fluxo de build legado. Aplicar o patch em um checkout descartável limpo
do kernel, nunca em uma árvore BSP sem conferir sua revisão:

```sh
VORTEX_CHECKOUT=/caminho/VORTEX-TV-OS
KERNEL_CHECKOUT=/caminho/kernel
KERNEL_OUTPUT=/caminho/kernel-out
ARM_TOOLCHAIN=/caminho/linaro

git -C "$KERNEL_CHECKOUT" rev-parse HEAD
git -C "$KERNEL_CHECKOUT" apply --check "$VORTEX_CHECKOUT/rom/sdcard/kernel-build-fixes.patch"
git -C "$KERNEL_CHECKOUT" apply "$VORTEX_CHECKOUT/rom/sdcard/kernel-build-fixes.patch"
make -C "$KERNEL_CHECKOUT" O="$KERNEL_OUTPUT" ARCH=arm \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" \
  HOSTCFLAGS='-O2 -fcommon' rockchip_defconfig

export KBUILD_BUILD_USER=vortex
export KBUILD_BUILD_HOST=cloud
export KBUILD_BUILD_TIMESTAMP='Sun Oct 25 16:15:00 UTC 2026'
make -C "$KERNEL_CHECKOUT" -j2 O="$KERNEL_OUTPUT" ARCH=arm \
  CROSS_COMPILE="$ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-" \
  CC="python3 $VORTEX_CHECKOUT/tools/legacy_kernel_gcc_wrapper.py $ARM_TOOLCHAIN/bin/arm-linux-gnueabihf-gcc" \
  HOSTCFLAGS='-O2 -fcommon' Image rk3229-sdk.dtb
```

A receita registra o processo; não promete identidade binária entre hosts.
Consultar o status de cada alvo no relatório, sem tratar um DTB bem compilado
como prova de que o alvo `Image` ou o sistema Android inteiro foi concluído.

## Limites para o teste SD

A configuração genérica mantém `CONFIG_RK_NAND=y` e Bluetooth habilitado,
entre as opções de referência. Ela não é a configuração final do produto,
que deve excluir Bluetooth, nem verifica os efeitos dos drivers sobre a unidade.
Kernel/DTB compilados não incluem loader DDR,
trust, bootloader, ramdisk Android, partições ou dados de uma mídia microSD.
O caminho de bootmode SD e o perfil da placa ainda exigem integração própria.

Os módulos do vendor candidato não foram ligados ou carregados nesse ensaio.
Não presumir sua ABI, especialmente `rk29-ipp.ko`, cujo `vermagic` é 3.0.101+.
O build também emitiu um aviso MODPOST de section mismatch entre
`dvfs_temp_limit()` e `cpu_up()` em `.cpuinit.text`; sua análise continua
pendente antes de usar o kernel em hardware. O filtro de seis avisos GCC
permitidos não abrange esse aviso do linker/MODPOST.
Nenhum binário de loader foi escolhido e nenhuma operação em hardware foi
executada. O pacote de evidências não deve ser gravado como imagem de cartão.
