# Build 01 — perfil SD e kernel ARM de referência

Base desta etapa: `6f9dee5324a2609b183d10567856a8e70cdeed83`.
O objetivo continua sendo testar o Vortex por microSD antes da instalação
interna. O proprietário já forneceu tudo que possui sobre a placa; nenhum
novo dado, diagnóstico ou firmware foi solicitado.

## Fontes adquiridas e conferidas

As dependências deixaram de ser apenas links de referência: foram obtidos
checkouts Git rasos, nas revisões abaixo, fora do repositório Vortex.
Não se executaram scripts ou comandos de build dessas três árvores Android.

| Componente | Revisão |
| --- | --- |
| device RK322x | `f33a129bfab6d9cc87184ee3bf032224801fa446` |
| common Rockchip | `3b1aa90ef43f9d34094739a211ad44bf9a2c0b74` |
| vendor RK322x | `50c7170ecb4bd907059db37f09f4767b301f2d15` |

[sources.lock.json](../rom/sdcard/sources.lock.json) registra URLs, commits e
tree SHAs. É um lock **parcial de componentes**, não um manifesto AOSP completo.
Os originais estão em `/workspace/rk322x-sd-candidate` e permaneceram limpos;
as alterações foram aplicadas somente em worktrees de teste separados.

No vendor, há 302 referências literais de cópia para 299 arquivos únicos;
todos esses arquivos estão presentes. As bibliotecas gráficas examinadas
são ELF ARM de 32 bits para Android API25. Dos 13 módulos inventariados,
12 declaram `vermagic` 3.10.104; `rk29-ipp.ko` declara **3.0.101+**. Esse módulo
não deve ser presumido compatível com o kernel de referência 3.10.104.
Versão textual igual nos demais também não comprova ABI/configuração.
O firmware SSV6051 disponível não identifica o chip Wi-Fi da unidade.

Os binários não foram executados/carregados nem incluídos no repositório ou
pacote de evidências Vortex. A presença pública e os avisos Apache de alguns
arquivos não estabelecem licença geral para redistribuir os blobs.

## Alterações de integração

O [patchset opt-in](../rom/sdcard/README.md) é dedicado ao candidato SD;
ele não é um perfil de instalação interna e não é aplicado automaticamente.

- A device tree passa a copiar somente o fstab SD. Retira a exposição do
  próprio cartão ao vold como mídia removível/formatável.
- O common deixa de copiar os init de eMMC, NAND/unknown e NVMe, além dos
  fstab internos dessas listas. O init SD continua selecionado pelo bootmode;
  um modo incorreto não é transformado artificialmente em SD.
- São retirados os dois blocos charger que montavam partições internas,
  a carga explícita de `/drmboot.ko` e o serviço automático `rk_store_keybox`
  do caminho normal examinado. As cargas gráficas existentes permanecem.

`git apply --check`, aplicação real e `git diff --check` passaram nas fontes
pinadas. Os logs registram hashes anteriores, posteriores e dos patches.
Esses resultados comprovam aplicação de alterações de fonte; não são uma
compilação AOSP ou uma inspeção do ramdisk final. Outras dependências podem
reintroduzir arquivos e serviços. Recovery/update/provisionamento restantes
continuam em auditoria; não incluir recovery na primeira mídia sem revisão.

## Verificações e regressão

O novo `tools/audit_sd_fstab.py` lê um arquivo regular explícito, sem montar
imagens, executar comandos ou acessar dispositivos. Confere cinco partições
críticas no controlador **de referência** `ff500000.rksdmmc`, sistema em `ro`
e apenas entradas opcionais conhecidas de USB/zram. Bloqueia fontes internas,
duplicatas, flags desconhecidas e exposição do próprio SD ao vold. Esse
controlador ainda não foi comprovado na unidade física.

| Verificação | Resultado |
| --- | --- |
| Configuração SD upstream real | `blocked`: expunha o cartão de boot como mídia removível |
| Fstab real após patch | `fstab_only`: entradas conferem com o perfil estático |
| Aplicação dos patches em fontes reais | Passa |
| Suite Python/JVM completa | 69 testes passam, sem skips: 43 anteriores, 20 para fstab e 6 para o helper de compilação |
| Validação Gradle APK/lint | Passa; código Android não mudou |
| APK após regressão | 69.098 bytes, byte a byte igual à etapa anterior |
| Pré-verificação da árvore candidata com JDK8 | Bloqueada: plataforma/manifesto não resolvidos e kernel isolado não integrado nessa árvore parcial |
| Boot microSD/USB e instalação interna | Não executados |

O preflight foi corrigido para as âncoras reais do vendor público:
`device-vendor.mk` e `Android.mk`. O `BoardConfigVendor.mk` que ele exigia antes
é apenas um `-include` opcional e não existe nessa revisão. A correção elimina
essa falsa exigência, mantendo a falha pelos componentes realmente ausentes.

O novo `tools/legacy_kernel_gcc_wrapper.py` preserva a licença, a whitelist
e a expressão de reconhecimento de avisos do wrapper upstream. Além do port
Python3, corrige uma corrida herdada: drena stderr e espera o compilador sair
antes de remover o objeto e rejeitar um aviso proibido. Os seis testes usam
processos de compilador simulados, inclusive um que escreve o objeto depois
do aviso. Também garantem encaminhamento de várias linhas sem espaços
adicionais, necessário para identificar corretamente o GCC nos metadados.
O teste desse último caso falhou antes da correção e passou depois.
Eles verificam a filtragem e o ciclo de vida do helper, não o kernel.

## Kernel ARM compilado de verdade

Foi adquirido separadamente o kernel Rockchip
`6c04d006ae881944d32c19e68b992d0bd5ab4fde` e o toolchain Linaro GCC6.3.1
`dd4df7dff4f1df65d78939a958b760a79e3650a1`. O ensaio usa
`rockchip_defconfig` e DTS genérico `rk3229-sdk`, não uma configuração
identificada para R329Q_V8.0. A configuração gerada foi preservada.

O [patch de compilação](../rom/sdcard/kernel-build-fixes.patch) reúne ajustes
em 31 arquivos: caminhos de fontes/saídas `O=`, declarações não usadas,
chaves preservando os escopos reais e uma comparação comprovadamente sempre
falsa apenas quando `BCMBUSTYPE` não está definido. A revisão independente
não encontrou alteração de coeficientes, valores de registros ou pinagem.
O patch bruto conserva dez bytes CR de contextos legados e foi reconstruído
sobre o commit original, reproduzindo byte a byte os 31 arquivos modificados.
Isso verifica a reconstrução de fontes, não o comportamento físico.

Após corrigir o port Python3 e os erros de compilação, uma rodada completa
terminou com sucesso. A conferência final encontrou a identificação GCC
vazia no `compile.h` por espaços inseridos pelo port na saída multilinha.
O teste reproduziu a falha, o helper foi corrigido, e **make normal**, sem `-k`,
confirmou novamente `Image` e DTB com código zero e identificação GCC correta.
Houve **seis avisos GCC permitidos pela whitelist original e nenhum GCC
proibido**; não se ampliou a whitelist para passar. Separadamente, o MODPOST
emitiu um aviso de section mismatch: `dvfs_temp_limit()` referencia `cpu_up()`
em `.cpuinit.text`. Esse aviso continua pendente de análise antes de usar o
kernel em hardware; sucesso de compilação não comprova correção em execução.

| Componente final | Tamanho | SHA-256 |
| --- | --- | --- |
| Kernel ARM `Image-reference` | 15.725.592 bytes | `d91b62b9d7339824be27a7b9196b4ce35233490b3c87c4cdeac6205499ecf846` |
| `rk3229-sdk-reference.dtb` | 72.308 bytes | `b379ff9545cd55a559cbeb3d6993653931da77a03fb2e2e3eeb7ae16118894c4` |

O `vmlinux` produzido é ELF ARM de 32 bits, EABI5, estático. A
[receita do ensaio](../rom/sdcard/KERNEL_BUILD.md) registra fontes, ferramentas
e limites. Os componentes não incluem ramdisk ou sistema Android, loader,
trust ou layout de cartão. O perfil genérico mantém NAND e Bluetooth
habilitados; não é a configuração final Vortex nem prova preservação da flash.
Nenhum módulo do vendor foi carregado e nenhum kernel foi inicializado.

O APK continua com SHA-256
`bedc7e95321c533e650f198f14e737f611aa765de5aebc6c46f930725fa9074b`.
Não se repetiu o emulador por alterações apenas nas ferramentas/fontes de ROM;
a regressão funcional anterior está no
[relatório de robustez](VALIDATION_2026-10-25_ROBUSTNESS.md). As artes oficiais
continuam pendentes dos originais, sem uso das miniaturas no APK.

## O que ainda impede uma imagem para o cartão

Falta resolver uma plataforma Android/Rockchip completa com revisões
compatíveis. O manifesto Nougat do mesmo autor encontrado na pesquisa é
[RR/Lineage genérico](https://github.com/D042888-2/platform_manifest/tree/843364e3e9f73044434fb07b2e8e7883a0d61c7c),
base `android-7.1.2_r36`/`cm-14.1`, sem os projetos Rockchip; não fornece o lock
do BSP candidato. O common também referencia bibliotecas/configurações em
`hardware/rockchip`, `external/wlan_loader` e outras árvores ainda não resolvidas.
A alternativa [pstglia](https://github.com/pstglia/local_manifests/blob/7a745c6fcfe931a856a5020cf8a36c4838c0b730/rockchip_rk3229_lineage_manifest.xml)
não foi misturada automaticamente: seu device tem bootargs NAND e seu vendor
depende de extração de outro sistema, que não será cobrada do proprietário.

A pesquisa adicional encontrou um
[manifesto público TinkerBoard Nougat](https://github.com/TinkerBoard-Android/rockchip-android-manifest/tree/e4faf840083f5c88b7d789007e6707f757368f0c),
com 528 projetos e include de seis projetos AOSP r39. Os caminhos incluem
core, build, common e HALs Rockchip. Foram conferidas quatro revisões de
componentes, registradas em
[platform-reference.json](../rom/sdcard/platform-reference.json); o build
examinado declara Android 7.1.2/API25. É uma referência **RK3288**, com código
específico dessa placa, não um BSP RK3229 selecionado ou um lock resolvido dos
534 projetos. Não se baixou esse BSP nem se misturaram seus componentes ao
candidato RK322x. Ele fornece uma próxima fonte concreta para comparação.

É preciso conferir a cadeia real de seleção de mídia no kernel, bootloader e
`system/core`. O common importa init pelo `ro.bootmode`, mas o core Android
correspondente ainda não foi estabelecido. Na referência de kernel
[6c04d006, rk.c](https://github.com/rockchip-linux/kernel/blob/6c04d006ae881944d32c19e68b992d0bd5ab4fde/block/partitions/rk.c#L277),
o caminho `rkpart_bootmode_fixup()` acrescenta `androidboot.mode=emmc` e não
possui um ramo SD; a execução depende do parser/caminho efetivamente utilizado.
Um patch histórico de outra placa não foi aplicado como solução universal.

Continuam pendentes DTB/configuração adequados, DDR/loader/trust, ABI dos
módulos, empacotamento/layout SD, inspeção do ramdisk final e logs automáticos.
O host tinha cerca de 23 GB livres e 9,7 GiB de RAM; essa capacidade ainda não
foi validada para um build AOSP completo. Nenhum desses dados vira um novo
pedido de diagnóstico ao proprietário. Nenhum loader foi escolhido ou gravado.

## Evidências

- [Validação completa](validation/2026-10-25-sd/validation.log)
- [Pré-verificação da árvore candidata](validation/2026-10-25-sd/candidate-preflight.json)
- [Fstab original](validation/2026-10-25-sd/original-sd-fstab-audit.json)
- [Fstab após patch](validation/2026-10-25-sd/patched-sd-fstab-audit.json)
- [Aplicação e hashes dos patches](validation/2026-10-25-sd/patch-results.json)
- [Inventário de cópias vendor](validation/2026-10-25-sd/vendor-copy-inventory.json)
- [Inventário binário estático](validation/2026-10-25-sd/vendor-binary-inventory.json)
- [Hashes de entrada](validation/2026-10-25-sd/inputs.sha256)
- [Resultado do kernel e artefatos](validation/2026-10-25-sd/kernel-build-report.json)
- [Log final do kernel](validation/2026-10-25-sd/kernel-build-final.log)
- [Comandos do ensaio](validation/2026-10-25-sd/kernel-commands.txt)
- [Configuração do kernel](validation/2026-10-25-sd/kernel.config)
- [Reconstrução independente do patch](validation/2026-10-25-sd/kernel-patch-replay.json)
- [Reprodução do erro de formatação do wrapper](validation/2026-10-25-sd/wrapper-format-before.log)
- [Regressão do wrapper após correção](validation/2026-10-25-sd/wrapper-format-after.log)

Não foi usado GitHub Actions. Não houve gravação física, compilação AOSP,
geração de cartão inicializável ou boot do Vortex no RK3229 nesta etapa.
