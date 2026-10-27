# Cadeia de boot RK322x em fontes abertas — revisão estática

Esta revisão examina fontes, sem compilar ou executar o bootloader. As compilações
coordenadas pelo agente principal têm relatórios próprios. Não houve acesso a
hardware, gravação de cartão ou flash nem uso de GitHub Actions. Nenhuma nova
informação foi solicitada ao proprietário.

## Revisões examinadas

| Componente | Revisão |
| --- | --- |
| U-Boot v2024.01 | `866ca972d6c3cabeaf6dbac431e8e08bb30b3c8e` |
| OP-TEE OS 4.0.0 | `2a5b1d1232f582056184367fb58a425ac7478ec6` |
| Kernel Rockchip 3.10.104 | `6c04d006ae881944d32c19e68b992d0bd5ab4fde` |

[chain-review.json](chain-review.json) contém hashes observados e URLs imutáveis
para os 38 arquivos examinados. Todos coincidem com as fontes pinadas. O checkout
U-Boot raso ocupa cerca de 214 MB; não foi preciso escolher um DDRblob rkbin para
localizar a implementação TPL RK322x.

## O caminho em fontes

1. O BootROM carrega TPL a partir de mídia que ele mesmo seleciona. Essa ROM não
   é implementada no checkout e sua prioridade na unidade não foi demonstrada.
2. `arch/arm/mach-rockchip/tpl.c:59–91` inicializa relógio/timer e pede o dispositivo
   RAM. `drivers/ram/rockchip/sdram_rk322x.c:784–819` chama a inicialização DDR
   quando `CONFIG_TPL_BUILD`; no SPL/U-Boot posterior lê a geometria registrada.
   Há código DDR3 aberto, inclusive treinamento e detecção de capacidade.
3. TPL retorna ao BootROM por `BROM_BOOT_NEXTSTAGE` (`tpl.c:93–113` e
   `bootrom.c:85–99`). O retorno manda a ROM continuar sua sequência. Não prova
   que toda falha de SD termina sem examinar mídia interna.
4. SPL determina os dispositivos a partir de `u-boot,spl-boot-order` e dos nós
   habilitados (`spl-boot-order.c:101–163`). Se não houver correspondência,
   há fallback para `spl_boot_device()`, normalmente MMC device0. Portanto o
   perfil precisa alinhar nó SD, alias, estágio SPL e ambiente; nomes MMC1/MMC2
   são enumeração de SPL, não identificação elétrica universal.
5. No RK322x, `SPL_FIT` seleciona `SPL_OPTEE_IMAGE` (`mach-rockchip/Kconfig:93–114`).
   O binman ARM32 usa OP-TEE em `0x60000000 + 0x8400000 = 0x68400000`
   (`arch/arm/dts/rockchip-u-boot.dtsi:114–128`) e U-Boot como loadable.
   SPL passa o FDT e salta ao monitor; OP-TEE retorna ao U-Boot proper.
6. O U-Boot proper depois prepara o DTB e o protocolo para o kernel. Kernel,
   ramdisk, sistema Android, conteúdo GPT e comando de boot específico ainda
   precisam de composição e auditoria próprias.

O formato `rksd` usa a entrada RK322x da ferramenta `tools/rkcommon.c:129`,
com identificador `RK32`. A descrição binman produz `idbloader.img` contendo
TPL/SPL e um contêiner de loader `u-boot-rockchip.bin`. O FIT fica no offset
relativo `CONFIG_SPL_PAD_TO=0x7f8000`; a combinação pressupõe a base de loader
Rockchip. SPL lê o próximo estágio no setor absoluto `0x4000` por padrão
(`common/spl/Kconfig:488–505`). Isso não é uma tabela GPT Android completa e
não é aqui um procedimento para gravar mídia.

## DDR e monitor

A referência EVB declara temporizações em `rk3229-evb-u-boot.dtsi:13–22`, com
`ddr_freq=300` e tipo `3` (DDR3), lidos pelas estruturas do driver. A detecção
de capacidade não transforma essas temporizações, alimentação, ODT ou pinagem
em configuração confirmada da R329Q_V8.0. A inicialização escreve registradores
e RAM; executar código DDR é uma operação física que não aconteceu aqui.

Para ARMv7 RK322x, não existe necessidade decorrente do ramo AArch64 de BL31.
O default FIT exige um monitor OP-TEE, mas ele pode ser compilado da fonte
RK322x acima. Isso é diferente de selecionar um binário trust aleatório.

O U-Boot possui infraestrutura genérica ARMv7 PSCI, mas o RK322x não seleciona
`ARCH_SUPPORT_PSCI` nem fornece as implementações de power-on/off nessa árvore.
As implementações weak em `arch/arm/cpu/armv7/psci.S:47–82` retornam Not Implemented.
Desativar FIT/OP-TEE pode produzir um caminho `u-boot.img`, mas isso não estabelece
monitor funcional para um kernel com `psci=enable`. Por esse motivo não se deve
apresentar a simples remoção do TEE como solução comprovada de inicialização.

OP-TEE RK322x força Cortex-A7, quatro cores e `CFG_PSCI_ARM32=y`. Os IDs ARM32
CPU_SUSPEND/OFF/ON `0x84000001/2/3` correspondem ao nó PSCI legado do kernel.
A implementação RK322x fornece CPU_ON/OFF e SYSTEM_SUSPEND/RESET. CPU_SUSPEND
continua no weak Not Supported. Além disso, o kernel tem chamadas Rockchip SIP
para FIQ/UART, DRAM e suspend; esses serviços vendor não se tornam compatíveis
porque os IDs PSCI padronizados coincidem. SMP, frequência, suspend, UART e
reinicialização continuam sem validação em execução.

## Reserva de memória indispensável para a composição

| Uso | Intervalo físico, final exclusivo | Tamanho |
| --- | --- | --- |
| OP-TEE core/TZDRAM | `0x68400000`–`0x68600000` | 2 MiB |
| OP-TEE shared memory reservada | `0x68600000`–`0x68700000` | 1 MiB |

Esses intervalos são o contrato da configuração de referência OP-TEE, não
novos dados da placa. Precisam ficar fora da RAM alocável pelo kernel e fora
dos buffers de carregamento/ramdisk do bootloader. O DTS Linux do ensaio
anterior não os reservava; portanto seus resultados isolados não aprovam
esta nova composição.

Há um caminho de fixup em fonte:

- OP-TEE, com DT externo válido e `CFG_DT`, acrescenta `/firmware/optee`,
  configuração PSCI e reservas `optee_core`/`optee_shm` (`boot.c:912–953`).
- `core/kernel/dt.c:656–720` cria `/reserved-memory` com cells/ranges e `no-map`.
- U-Boot chama `optee_copy_fdt_nodes()` ao preparar o FDT Linux
  (`boot/image-fdt.c:627–632`). A função copia as reservas `optee*` do FDT de
  controle (`lib/optee/optee.c:113–188`).
- **Isso exige `CONFIG_OPTEE_LIB=y`**. Sem ele, a chamada é um stub de sucesso
  que não copia nada (`include/tee/optee.h:65–75`). `SPL_OPTEE_IMAGE` sozinho
  não habilita essa biblioteca no U-Boot proper.
- Mesmo com a biblioteca, a função retorna sem ação se não houver
  `/firmware/optee` no FDT de controle ou se o FDT Linux já possuir esse nó.
  Um nó firmware estático, sozinho, não garante reservas. A rotina também
  reutiliza uma reserva já existente com faixa idêntica sem garantir que ela
  tenha todos os flags esperados (`fdtdec.c:1360–1372`). O FDT efetivamente
  entregue ao kernel precisa ser inspecionado; as opções de compilação não
  provam que o fixup rodou.

O kernel 3.10 adquirido tem `CONFIG_OF_RESERVED_MEM=y` e `CONFIG_HAVE_MEMBLOCK=y`.
`arch/arm/mm/init.c:388` faz a varredura, `drivers/of/fdt.c:389–505` lê o nó e
`no-map`, e `:802–811` remove o intervalo de memblock quando solicitado. Portanto
há suporte de fonte para o formato, desde que cells/ranges, tamanhos, DTB real
e configuração coincidam. Isso não demonstra isolamento TrustZone nem ausência
de outras sobreposições em runtime.

## Conflito UART/SD e rota alternativa em fonte

O UART2 default usa `uart2_xfer` em GPIO1_PC2/PC3 mux2, enquanto o SD de
quatro bits usa PC2/PC3/PC4/PC5 mux1 (`rk322x.dtsi:1026–1030,1273–1281`).
Habilitar ambos os defaults não é uma composição coerente. A rota alternativa
`uart21_xfer` usa GPIO1_PB2 (RX) e PB1 (TX), ambos mux2.

A seleção não depende apenas de `board_debug_uart_init()`: a tabela
`drivers/pinctrl/rockchip/pinctrl-rk322x.c:123–128` reconhece banco1/pin10/func2
e programa offset GRF `0x50` com `BIT(24)|BIT(8)` para selecionar UART2-1.
O pinctrl comum calcula a route mask e aplica o valor antes do mux
(`pinctrl-rockchip-core.c:220–242,598–605`). Com pinctrl completo presente nos
estágios usados, o estado normal seleciona a mesma rota usada pelo early UART.

Isso corrige um conflito lógico nas fontes EVB; não identifica a rota ou a
ligação serial real da R329Q_V8.0. Os DTBs efetivos TPL/SPL/proper e o config
resolvido ainda precisam confirmar que os nós e o pinctrl não foram removidos.

## Restrições necessárias ao ensaio SD

A defconfig EVB original habilita eMMC com `mmc0=&emmc`, ambiente persistente
MMC, comando GPT, UMS, fastboot OEM format e boot targets que incluem outros
meios. Ela não é um perfil externo exclusivo. O desenho precisa:

- Habilitar SD e desabilitar eMMC nos DTBs usados pelos três estágios, marcar
  os nós necessários para pré-relocação e apontar alias/ordem SPL somente ao SD.
- Usar ambiente sem backend persistente (`ENV_IS_NOWHERE`) e retirar saveenv,
  eraseenv, fastboot, UMS, GPT/flash e filesystem write. `MMC_WRITE` é separável
  (`drivers/mmc/Kconfig:14–20`); conferir também comandos de manutenção eMMC
  e o inventário de símbolos resolvido, sem presumir que uma flag elimina tudo.
- Evitar execução de scripts herdados ou autodetecção de mídias internas como
  preboot/autoboot. Um componente de loader sem sistema não deve inicializar
  qualquer Android interno como fallback implícito.
- Auditar UART/JTAG e conflito com SD, além dos valores EVB de pinos/tensão.
- Registrar que a política dos estágios abertos não controla a lógica imutável
  do BootROM nem comprova a preservação física da instalação interna.

USB RockUSB/MaskROM é protocolo de serviço entre host e SoC, não boot autônomo
por pendrive. A presença de UMS/fastboot no loader tampouco comprova boot USB.
Nenhuma dessas interfaces foi executada ou habilitada em hardware nesta revisão.

Os componentes compiláveis em fonte aberta removem a necessidade de buscar um
DDR/trust blob arbitrário para este ensaio. Ainda não demonstram boot na placa,
funcionamento dos drivers Android, imagem SD completa ou caminho de instalação
interna. Esta revisão mantém esses critérios separados.
