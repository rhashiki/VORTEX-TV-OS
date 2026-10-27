# Build 01 — correção do contrato gráfico e regressão do Installer

Base: `d523837a473a464313e5709c3cdab441702ca8f3`. Esta etapa acrescenta
patches opt-in para fontes Android/kernel fixadas, compila objetos ARM e um
DTB complementar, e completa o fluxo de instalação do APK no emulador.
**Ainda não há sistema Android completo, HAL ligada ou imagem SD inicializável.
Nenhuma operação foi feita na TV Box.**

## Interface gráfica: divergência estrutural corrigida nas fontes

O kernel SDK copiava 908 bytes no ioctl `RK_FBIOSET_CONFIG_DONE=0x4628`,
mas o header userspace reservava 904. A investigação confirmou dois
consumidores ativos, gralloc e HWC, que zeram a estrutura inteira e não usam
o membro final `post_cfg` do header antigo.

O patch libhardware substitui esse membro pela declaração real `rk_fb_wb_cfg`
do kernel. Não acrescenta apenas padding. O campo final tem 20 bytes no
offset 888, e o objeto passa a ter 908. Os consumidores devem ser recompilados;
um header corrigido não conserta binários antigos. O writeback deve continuar
zerado: `ion_fd=0` e `phy_addr=0` o desabilitam no caminho examinado, enquanto
`-1` nesse ion_fd não é uma sentinela de desativação.

A medição inclui os headers completos reais Linux/userspace, com includes
ARM e config gerados do kernel anterior. **94 medidas de tamanho, alinhamento
e campos coincidiram depois do patch.** A asserção de contrato falhou com o
header antigo e passou com o novo. Essa falha negativa é da asserção: as
fontes antigas do gralloc compilam e ainda assim contêm o defeito de ABI.

Os quatro arquivos C++ reais do gralloc produziram objetos ARM relocáveis:
`framebuffer_device.cpp`, `gralloc_module.cpp`, `alloc_device.cpp` e
`rockchip_alloc_device.cpp`. Usaram GCC Linaro 6.3.1, ARMv7/softfp/NEON,
Bionic/systemcore selecionados e headers GLES/KHR e libc++ r6 verdadeiros,
com `-nostdinc/-nostdinc++`. Não se criaram stubs ou headers glibc de host.
O disassembly do consumidor framebuffer mostra `memset` de 904 antes e 908
depois, no caminho que envia o ioctl. Isso não executa o ioctl.

A compilação foi manual, em unidades separadas, **sem make/link Android**,
sem produzir `gralloc.rk30board.so` e sem compilar HWC. Os 155 arquivos de
dependência foram inventariados com hashes. `version.sh` original rodou
somente numa cópia descartável para gerar `version.h`; a tentativa inicial
com cwd incorreto e a correção foram preservadas. A aquisição libc++ também
preservou uma falha inicial de extração de symlink; nenhum TU usou um
substituto fictício para esse link.

## Seleção dos módulos e aplicação do patchset

O [patchset gráfico](../rom/platform-reference/graphics/README.md) inclui
mais três ajustes necessários para que a correção não seja mascarada:

- RK322x exige Mali400 e seleciona o ramo legado mesmo se `hardware/arm`
  existir. Outras plataformas conservam a seleção anterior.
- HWC em RK322x usa o header do gralloc selecionado, sem os caminhos UMP/Intel
  que apareciam antes dele na busca de includes.
- Vendor deixa de copiar `gralloc.default.so`, `gralloc.rk30board.so` e
  `hwcomposer.rk30board.so`; os pacotes de fonte continuam requeridos.

Foram conferidos aplicação e replay byte a byte nas revisões fixadas.
A expansão diagnóstica GNUmake passou em **13 cenários**, incluindo diretório
residual, GPU incorreto e preservação de outras plataformas. Esse harness
usa shells e registro de módulos desabilitados: é teste de seleção, não
outro build de HAL. A revisão independente também confirmou as três remoções
exatas do vendor e a semântica da correção do header.

Os patches são opt-in; o manifesto XML não os aplica automaticamente. O
vendor recebe seu patch gráfico depois do patch SD `0006`. Revisões, paths
e ordem estão na receita. Não foi executado sync completo ou build Android.

## Monitor aberto: consumidores incompatíveis identificados

A auditoria comparou 32 fontes aos objetos Git fixados, além dos configs e
símbolos dos ELFs anteriores. Delimita nove famílias/caminhos de serviço,
sem alegar que toda a ABI do monitor foi auditada.

No kernel, `PM_DEVFREQ=n` não retira o driver DDR legado. Ele pode usar o
serviço SIP `0x82000008`, ausente no OP-TEE RK322x compilado. A função de
clock trata o retorno bruto como frequência e relata sucesso, de modo que
unknown não é um errno válido nesse caminho. O FIQ debugger também usa a
ABI vendor que esse monitor não implementa.

O [DTS complementar](../rom/sdcard/MONITOR_REFERENCE.md) desabilita somente
`/fiq-debugger` e `/dvfs/vd_logic/pd_ddr/clk_ddr`. Antes, o mesmo processo CPP/dtc
reproduziu o DTB base byte a byte. A comparação dos **468 nós** do DTB novo
mostrou somente as duas alterações `status`; sete verificações passaram.
As fontes conferidas deixam de registrar o debugger e o worker DDR legado
com esses nós desabilitados. O auditor cruzado DTB/fstab/config/cmdline também
passou com resultado `inputs_only`, sem transformar isso em teste de boot.

O complemento **não habilita console UART convencional**: o kernel anterior
tem SERIAL_ROCKCHIP, mas não SERIAL_ROCKCHIP_CONSOLE. UART1 está habilitada
no DTS e UART2 desabilitada; não se atribuiu uma ligação física à unidade.
Negociação de versão SIP e controle vendor de suspensão continuam presentes.
As reservas core/SHM OP-TEE também não foram adicionadas por esse DTS.

Foi corrigida ainda a propagação de erro em `rkpm_enter`: mantém os callbacks
prepare/finish e retorna o resultado de `cpu_suspend`, em vez de sucesso
incondicional. O monitor retorna CPU_SUSPEND não suportado; o patch apenas
preserva esse erro. O arquivo C real, antes e depois, compilou como objeto ARM
com as flags/config do kernel existente. Não houve link de kernel novo, e
**o Image entregue anteriormente não contém essa correção**. A revisão
independente conferiu o caminho de retorno PSCI e a retenção de finish.

## Installer: fluxo completo no emulador

O APK AOSP da etapa anterior, sem alterações, passou em **14 verificações
funcionais** num AVD isolado Android 7.1.1/API25/x86, 1280×720 em software:

- Token incorreto, origem incorreta e corpo não ZIP foram recusados; ZIP sem
  Manifest foi recusado pelo parser Android após o transporte HTTP.
- Upload válido abriu a confirmação real do PackageInstaller. Cancelar
  manteve o pacote ausente; confirmar instalou o fixture.
- O aplicativo instalado apareceu diretamente na Home, foi alcançado com
  D-pad em duas direções e aberto com DPAD_CENTER. Back voltou à Home.
- O servidor de pareamento encerrou e não houve fatal exception do Vortex.

O APK instalado foi lido de volta e seu SHA-256 coincidiu com o fixture
`os.vortex.smoke` (8.535 bytes). Ele é um app de teste, fora do produto.
As fontes desconhecidas foram habilitadas apenas nesse AVD e restauradas
para zero; somente o emulador próprio foi encerrado.

Duas falhas do harness ficaram preservadas: a primeira supunha navegação só
horizontal, embora o fixture estivesse na segunda linha; a segunda tentou
`sha256sum`, ausente nessa API25. A navegação foi corrigida no harness e a
identidade foi verificada por leitura via adb e SHA-256 no host. Não se mudou
o aplicativo nem repetiu a instalação depois de passar suas verificações.
HTTP foi exercitado na interface privada do emulador. Celular/LAN física,
USB real, privilégios de energia e drivers Rockchip continuam fora do teste.
A assinatura do Vortex continua sendo a identidade de teste AOSP.

A regressão Python/JVM existente foi repetida: **96 testes passaram**.
Não se repetiu o build APK, pois Java, recursos e Android.mk do aplicativo
permaneceram iguais aos já compilados.

## Artefatos e limites da próxima integração

| Artefato | Bytes | SHA-256 |
| --- | --- | --- |
| APK AOSP anterior usado no ensaio | 44.366 | `81fc16aa89e523088ac8c7a6e334a2c670745d6a4e673a30a986ba6af04867d4` |
| `sd-monitor-gated.dtb` | 72.380 | `cfa9110af88ad776fd2cd528152920acdbef9a1d32a9a124fdd0381695b1e167` |
| `framebuffer_device.o` corrigido | 11.376 | `97325a22a87e0617eb768e107b00f8ceefd3b06edac54f68ed866f8d3d98d603` |

Os demais objetos, hashes, comandos e logs estão nas evidências. Objetos
relocáveis e DTB são componentes de engenharia; não constituem um pacote
Android instalável, uma ROM ou mídia SD. Nenhum firmware proprietário foi
executado e nenhum dispositivo físico foi escrito ou iniciado.

Permanecem necessários link Android das HALs/HWC, contrato privado dos blobs
Mali/OMX, outros ioctls ION/RGA/fences, fechamento de módulos/produto e política
SELinux, Android completo e ramdisk/layout SD. No boot faltam integração das
reservas do monitor, console observável, fechamento de suspensão/SIP/DDR e
testes reais de periféricos. O host continua com cerca de 11 GiB livres,
sem capacidade demonstrada para sincronizar e compilar o BSP inteiro.
Não foram pedidos novos dados da placa ao proprietário. A Build 01 continua
aberta e a prioridade permanece teste externo antes de instalação interna.

## Evidências

- [Contrato dos headers completos](validation/2026-10-27-graphics-monitor/graphics/evidence/header-contract-review.json)
- [Quatro objetos gralloc reais](validation/2026-10-27-graphics-monitor/graphics/hal-build/gralloc-object-build-report.json)
- [Seleção GNUmake e replay](validation/2026-10-27-graphics-monitor/selection/source-selection-review.json)
- [Revisão gráfica independente](validation/2026-10-27-graphics-monitor/review/display-abi-independent-review.json)
- [Inventário SIP e fontes](validation/2026-10-27-graphics-monitor/monitor/monitor-call-inventory.json)
- [Comparação do DTB](validation/2026-10-27-graphics-monitor/monitor/monitor-dtb-review.json)
- [Objeto da correção de erro de suspensão](validation/2026-10-27-graphics-monitor/monitor/suspend-error-fix-build.json)
- [Conferência cruzada SD](validation/2026-10-27-graphics-monitor/monitor/sd-monitor-cross-audit.json)
- [Resultado Installer](validation/2026-10-27-graphics-monitor/installer/runtime-result.json)
- [Operações observadas no emulador](validation/2026-10-27-graphics-monitor/installer/commands.json)
- [96 testes de regressão](validation/2026-10-27-graphics-monitor/regression.log)
- [Revisão final independente](validation/2026-10-27-graphics-monitor/review/final-source-review.json)
- [Integridade final](validation/2026-10-27-graphics-monitor/root-verification.json)

Nenhum GitHub Actions foi consultado, criado ou executado.
