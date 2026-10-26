# Build 01 — combinação de componentes para referência SD

Base: `dd1b91435926cb0061c84957fe618c71b84be497`.
Esta etapa continua a preparação de um teste por microSD, antes da instalação
interna. Não foi produzida uma ROM Android ou mídia inicializável e não houve
boot, gravação ou coleta física na TV Box. Não se pediram novos dados da placa.

## Incompatibilidade encontrada e corrigida nas fontes

O fstab comunitário dos três primeiros patches usa `ff500000.rksdmmc`, mas
o DTS RK3229 do kernel adquirido define o controlador SD em `30000000`.
Passar na checagem isolada do fstab não comprovava essa combinação.
O patch `0004` adapta o fstab ao controlador do SDK e foi aplicado numa nova
árvore descartável, após `0001`. O resultado mantém `/system` em `ro` e
não oferece o próprio cartão de boot ao vold.

O nome esperado `30000000.rksdmmc` tem base no código OF/MMIO que nomeia o
platformdevice, não na posição `mmcblk0`/`mmcblk1`. Foram examinados também
o parser GPT do kernel, a exportação `PARTNAME` e o ramo de ueventd que gera
links `by-name`. É uma relação estática condicionada a eventos e labels
reais; nenhum desses links foi observado na unidade. O endereçamento não
identifica a pinagem ou os demais componentes da R329Q_V8.0.

O [perfil e os comandos de conferência](../rom/sdcard/SD_REFERENCE.md)
registram os limites. O perfil comunitário antigo continua disponível, com
seu controlador original, para evitar alterar silenciosamente seu significado.
A adaptação SDK deve ser selecionada explicitamente.

## Serviços e ferramentas retirados do candidato Android

A revisão encontrou caminhos além dos removidos em `0001`–`0003`.
`0005` retira das fontes common examinadas:

- O serviço vendor automático `drmservice` e sua inclusão no produto; sua
  política permitia acesso NAND/vendor storage. Isso é distinto do DRM de
  mídia Android, que não foi desativado por esse patch.
- A cópia de `whtest.sh`, que remonta `/dev/block/mtdblock8` como `/system`
  gravável, e de `preinstall_cleanup.sh`, que remonta `/system` para limpeza.
  Não se demonstrou execução automática dessas ferramentas no boot anterior.
- O import OP-TEE deste init, sem presumir que o serviço estava presente
  no ramdisk anterior.
- Os serviços, pacotes, flags e concessões Bluetooth enumerados em init,
  ueventd e política vendor. A seleção Wi-Fi upstream foi conservada; ela
  não identifica o chip da unidade.

`0006` retira seis entradas explícitas de cópia de bibliotecas Bluetooth da
árvore vendor. Os binários permanecem upstream e não foram redistribuídos.
Aplicação real, verificação de patch, whitespace e replay byte a byte passaram.
As árvores usadas na etapa anterior permaneceram intactas.

Ainda existem referências PAN desabilitadas e grupos compartilhados com GPS.
Outras dependências podem reintroduzir pacotes/serviços. Recovery, atualização,
inventário final e política SELinux compilada continuam pendentes; não se
declarou uma imagem sem Bluetooth ou preservação física da memória interna.

## Conferência cruzada e regressão

`tools/audit_sd_boot_inputs.py` lê fstab, DTB FDT17 binário, configuração e
arquivo de cmdline, sem executar dtc, montar imagens ou abrir dispositivos.
Confere o controlador e os compatibles efetivamente usados pelos drivers,
capabilities SD/SDIO, nós NAND/eMMC/Bluetooth desabilitados, opções do kernel
e seletores de boot exatos sem duplicatas. Também exige que o `chosen/bootargs`
do DTB corresponda ao contrato proposto.

A revisão independente encontrou dois falsos positivos durante o desenvolvimento:
um nó MMC sem o compatible que faz o binding do driver e um controlador
extra com o driver genérico `snps,dw-mshc`. Ambos passaram a ser rejeitados,
com casos de regressão. O uso da configuração real encontrou ainda símbolos
Kconfig legítimos com letras minúsculas, como `CONFIG_CPU_32v6K`. O parser foi
corrigido para aceitá-los sem deixar de rejeitar duplicatas; o teste falhou
antes e passou depois da correção.

A combinação antiga de fstab, DTB e config é rejeitada. A combinação nova
passa como **`inputs_only`**: esse resultado não aprova imagem, driver,
bootloader, correspondência entre config e binário ou hardware.

A validação completa passou com **96 testes Python/JVM**, sem skips: os 69
anteriores, três casos para a seleção explícita do fstab e 24 casos do auditor
cruzado. Assemble debug e lint Android passaram. O APK continua com 69.098
bytes e SHA-256
`bedc7e95321c533e650f198f14e737f611aa765de5aebc6c46f930725fa9074b`;
o código do aplicativo não mudou. Não se repetiu a sessão de emulador, cuja
regressão anterior continua documentada separadamente.

## Kernel do perfil SD efetivamente compilado

Foi criado outro worktree e outro diretório `O=`, preservando a referência
anterior. O novo DTS inclui o SDK genérico, mas desabilita os nós NAND, eMMC
e Bluetooth. O fragmento aplicado sobre `rockchip_defconfig` mantém NAND,
MTD e Bluetooth desabilitados, MMC/GPT ativos e `HOTPLUG_CPU=y`.

A primeira compilação falhou na ligação: três consumidores ainda chamavam
`GetSNSectorInfo`/`GetParamterInfo`, fornecidas pelo driver NAND removido.
O patch adicional `kernel-sd-no-nand.patch` condiciona esses caminhos.
Com NAND `y`, os ramos originais são preservados byte a byte; com `n`, IDB
Ethernet retorna indisponibilidade, Wi-Fi mantém a validação do MAC e USB
informa ausência de tag. Não se inventaram identificadores ou sucesso de
leitura, nem se testou NAND modular. O replay dos dois patches de kernel
reproduziu exatamente os 34 arquivos alterados, além da cópia do novo DTS.

O **make normal, sem `-k`, terminou com código zero** e produziu:

| Artefato | Bytes | SHA-256 |
| --- | --- | --- |
| `Image-sd-reference` | 15.380.696 | `00ab9ab1393ac76c96ec984b73a680fc586e861d22f1c404485b6d043a6a9f52` |
| `rk3229-sdk-sd-reference.dtb` | 72.372 | `ffc55fd04b80ef2c49307d7428b6be8d7b6362410f235ad25be4c6c7f3109fb7` |

Configuração final SHA-256:
`989995cfcf9395f51c7299ffd2fd3fad91e1fad216b54e9f6eb9ea8e457f8868`.
Os arquivos DTB/config são os mesmos conferidos no auditor cruzado.
Houve seis avisos GCC permitidos pela whitelist original, nenhum proibido
e um aviso MODPOST separado. Nenhum desses avisos foi ocultado. Os símbolos
NAND citados ficaram ausentes do ELF, sem funções substitutas de sucesso.

Isso compila kernel/DTB separados, não o sistema Android, ramdisk ou mídia.
O backend `sdmmc_vendor_storage` permanece compilado por dependência MMC e
possui operações de escrita; sua guarda depende da ausência de cartão eMMC
ativo. Desabilitar o nó e examinar essa relação em fontes não comprova a
preservação física da flash, nem valida os fallbacks de MAC e a rede.

## Análise do aviso MODPOST

Foi examinada a referência `dvfs_temp_limit()` → `.cpuinit.text:cpu_up()` no
ELF anterior. `HOTPLUG_CPU=y` mantém essas seções na região permanente; os
símbolos da cadeia `cpu_up` ficam fora do intervalo de init liberável.
O worker térmico continua sendo chamado depois do init, por isso não foi
marcado como função descartável para eliminar o aviso. A análise se limita
àquela configuração e aos símbolos examinados, sem teste térmico/hotplug.
A inspeção também foi repetida no novo ELF: `cpu_up` está em `0xc0923b48`,
fora do intervalo de init liberável `0xc0d20000`–`0xc0d80400`, assim como a
cadeia examinada. O aviso permanece visível; essa prova estática não valida
execução térmica/hotplug ou hardware.

## Pesquisa da plataforma Android

Foram adquiridos seis checkouts rasos TinkerBoard, cerca de 60 MB, e registrados
28 heads críticos observados. Isso não resolve os 534 projetos nem fornece um
BSP RK3229. Apesar de condicionais `rk322x`, o gralloc força caminho DRM,
Utgard desativado e AFBC; hwcomposer força DRM e áudio injeta `TINKER_AUDIO`.
Essa base RK3288 não foi adotada automaticamente para o Mali400/UMP candidato.

O init dessa referência exige as substrings `storagemedia=sd` e
`androidboot.mode=sd` para selecionar o modo SD, sem parsing estrito de tokens.
O auditor de arquivos não modifica o init em execução. O fixup eMMC do kernel
só ocorre no ramo Rockchip de disco eMMC com `mtdparts`; o parser GPT é
consultado antes. Não se afirmou que todo boot SD recebe modo eMMC.

Continuam faltando plataforma Android compatível, loader DDR/trust, layout e
conteúdo do cartão, ramdisk completo e política compilada. Os checkouts e
compilações parciais também reduziram o espaço livre neste host de 32 GB;
não se iniciou sincronização completa AOSP sem capacidade estabelecida.

A coleta automática de logs ainda é projeto de integração: deve usar domínio
SELinux dedicado e só gravar após confirmar a identidade real da montagem
SD. O serviço vendor `abc` tem privilégios excessivos para reutilização.
Não há promessa de capturar falhas anteriores à montagem dos dados.

## Evidências de fonte

- [Regressão completa e Gradle](validation/2026-10-26-sd-profile/validation-final.log)
- [Resultado da compilação SD](validation/2026-10-26-sd-profile/kernel-sd/report.json)
- [Comandos do kernel](validation/2026-10-26-sd-profile/kernel-sd/commands.txt)
- [Log final do kernel](validation/2026-10-26-sd-profile/kernel-sd/build.log)
- [Primeira falha de link preservada](validation/2026-10-26-sd-profile/kernel-sd/first-failure-build.log)
- [Configuração final](validation/2026-10-26-sd-profile/kernel-sd/rockchip_defconfig.generated)
- [Replay dos 34 arquivos](validation/2026-10-26-sd-profile/kernel-sd/combined-patch-replay.json)
- [Verificação independente dos artefatos/entradas](validation/2026-10-26-sd-profile/kernel-sd/root-verification.json)
- [Ciclo de vida no novo ELF](validation/2026-10-26-sd-profile/kernel-sd/section-lifetime-review.json)
- [Fstab adaptado](validation/2026-10-26-sd-profile/fstab-sdk-audit.json)
- [Combinação nova de arquivos](validation/2026-10-26-sd-profile/sd-reference-cross-audit.json)
- [Combinação anterior rejeitada](validation/2026-10-26-sd-profile/old-reference-cross-audit.json)
- [Teste do símbolo Kconfig antes da correção](validation/2026-10-26-sd-profile/kconfig-symbol-before.log)
- [Mesmo teste após correção](validation/2026-10-26-sd-profile/kconfig-symbol-after.log)
- [Adaptação do controlador](validation/2026-10-26-sd-profile/patch-controller-results.json)
- [Auditoria dos caminhos restantes](validation/2026-10-26-sd-profile/ramdisk-review/ramdisk-source-review.json)
- [Aplicação e replay de 0005/0006](validation/2026-10-26-sd-profile/ramdisk-review/factory-service-patch-validation.json)
- [Análise do ciclo de vida do kernel anterior](validation/2026-10-26-sd-profile/kernel-review/section-lifetime-review.json)
- [Plataforma, bootmode e cadeia GPT/ueventd](validation/2026-10-26-sd-profile/research/PLATFORM_FINDINGS.md)
- [28 referências críticas observadas](validation/2026-10-26-sd-profile/research/platform-critical-references.json)
- [Revisão independente do patch sem NAND](validation/2026-10-26-sd-profile/research/no-nand-independent-review.json)
- [Capacidade observada no host](validation/2026-10-26-sd-profile/host-capacity.json)

Não foi usado GitHub Actions. O próximo teste físico continua condicionado a
uma imagem Android completa efetivamente construída e auditada.
