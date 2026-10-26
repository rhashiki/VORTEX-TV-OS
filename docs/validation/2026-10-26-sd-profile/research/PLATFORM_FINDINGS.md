# Pesquisa de plataforma e caminhos SD — 2026-10-26

Escopo: comparação de fontes públicas e nomes esperados em fontes. Não houve
build da plataforma Android, montagem de mídia, execução de binários vendor,
seleção de loader ou operação na TV Box.

## Checkouts adquiridos

Todos são rasos, somente leitura durante a pesquisa, em
`/workspace/build01-sd-next/platform-reference/`.

| Diretório | Repositório TinkerBoard-Android | Commit |
| --- | --- | --- |
| manifest | rockchip-android-manifest | e4faf840083f5c88b7d789007e6707f757368f0c |
| system-core | rockchip-android-system-core | a54e58472fdeb45820fd215d45da6d8b55b27cde |
| common | rockchip-android-rk-device-rockchip-rksdk | 08a9c89bafa8e40c0ee63fbeb8975a26c962fbd2 |
| audio | rockchip-android-rk-hardware-rockchip-audio | 997bbe87ff092f54fd0e271bb8fe75fd39833237 |
| hwcomposer | rockchip-android-rk-hardware-rk29-hwcomposer_rga | 67d0889db26196e5194b9a117408e684a8839c98 |
| libgralloc | rockchip-android-rk-hardware-rk29-libgralloc_ump | 211e7d62dcaa9acc2b7f1e424607b7eef40eb57f |

O total em disco dos seis checkouts é cerca de 60 MB. Nenhum script do BSP
foi executado. `platform-critical-references.json` fixa os 28 heads críticos
observados via `git ls-remote`; o restante dos 534 projetos não foi resolvido.

## A base completa ainda não foi selecionada

O manifesto default TinkerBoard declara 528 projetos sob
`n-mr1-rk3288-tb` e inclui seis projetos AOSP `android-7.1.2_r39`. Os manifestos
de release 14.4.0.5, 14, 18, 22 e 23 também usam o include r39. O único produto
Rockchip no manifesto é `device/rockchip/rk3288`; não há produto RK3229.

A pesquisa pública do autor D042888-2 encontrou apenas os três repositórios
Rockchip já adquiridos: device RK322x, common e vendor RK322x, na branch r6.
Nenhum core/plataforma Rockchip do mesmo autor foi encontrado nessa busca.
A branch `nougat` do seu `platform_manifest` permanece no commit
843364e3e9f73044434fb07b2e8e7883a0d61c7c, referência RR/Lineage r36 já examinada,
sem lock completo do BSP r6. Isso é resultado da busca, não prova de inexistência
universal de outras fontes.

Outros manifestos localizados não resolveram essa lacuna: ADVANTECH-Rockchip
expõe branches Android 6.0.1 e 8.1; vicharak-in expõe master. Não foram adotados
como base Nougat/RK3229, nem misturados aos componentes r6.

### Por que as HALs TinkerBoard não são substituições automáticas

Há ramos `rk322x` em `hwcomposer/Android.mk:95` e
`audio/tinyalsa_hal/Android.mk:52`. Isso demonstra código condicionado ao nome
da plataforma, mas as mesmas árvores têm diferenças relevantes:

- `hwcomposer/Android.mk:14` fixa `BOARD_USES_DRM_HWCOMPOSER=true`.
- `libgralloc/Android.mk:25` força `DRM_GPU_DRIVERS := rockchip`;
  a partir de :124 usa `MALI_ARCHITECTURE_UTGARD := 0`, AFBC ativo e
  `DISABLE_FRAMEBUFFER_HAL?=1`. Não é um caminho Mali400/UMP legado validado.
- `audio/tinyalsa_hal/Android.mk:69` acrescenta `-DTINKER_AUDIO`
  incondicionalmente.

As linhas são localizadores na revisão adquirida; a compatibilidade dos
ioctls, layouts de buffers, GPUblob, VPU/HDMI/áudio continua pendente. O nome
histórico `_libgralloc_ump` do repositório não comprova o backend efetivo.

O common Tinker tem 207 arquivos compartilhados byte a byte iguais ao
common candidato D042 e 37 compartilhados diferentes; os arquivos exclusivos
estão em `common-comparison.json`. O `init.rk30board.bootmode.sd.rc` é idêntico,
mas BoardConfig.mk, device.mk, init principal e recovery.sd.fstab diferem.
Não é base para aplicar patches do common r6 indiscriminadamente no Tinker.

## Seleção real de bootmode no core TinkerBoard

Fonte: `system-core/init/init.cpp:464–539`, revisão a54e584.

1. `process_kernel_dt()` e `process_kernel_cmdline()` rodam antes da exportação
   de propriedades (`init.cpp:843–852`). Parâmetros `androidboot.*` são
   importados para `ro.boot.*`, mas a cópia direta de `ro.boot.mode` para
   `ro.bootmode` está comentada nessa árvore.
2. A exportação relê `/proc/cmdline` em até 20 tentativas de 1 s. Para declarar
   `ro.bootmode=sd`, exige as substrings `storagemedia=sd` E
   `androidboot.mode=sd`. Há ramos separados eMMC eNVMe.
3. A verificação usa `strstr`, sem limites de token nem rejeição de duplicatas
   ou valores conflitantes. Um validador externo preciso não transforma esse
   código em um parser estrito nem valida a cadeia real.
4. O `hardware` inicia como `rk30board` e pode ser sobrescrito por
   `ro.boot.hardware`. `symlink_fstab()` monta o nome
   `/fstab.<hardware>.bootmode.<ro.bootmode>` e cria `/fstab.<hardware>`;
   somente o ramo `ro.rk.soc` contendo rk3288 acrescenta um sufixo SoC.
5. `gatekeeperd/gatekeeperd.cpp:58–59` também possui tratamento sd com a
   propriedade `ro.boot.mode`; conferir ambas as propriedades na integração.

Não foi aplicado patch para forçar sd a esse core; ele continua uma referência
RK3288, não a plataforma escolhida para o Vortex.

## Relação GPT → PARTNAME → by-name

É uma cadeia de fontes condicionada a eventos reais, não uma observação de
`/dev` na TV Box.

Kernel Rockchip 6c04d006ae881944d32c19e68b992d0bd5ab4fde:

- `arch/arm/boot/dts/rk322x.dtsi:907–909`: o nó SD é
  `rksdmmc@30000000`, `reg=<0x30000000 0x10000>`. É diferente do controlador
  ff500000 usado no fstab candidato de outra referência.
- `drivers/of/platform.c:108–122`: quando o ramo MMIO traduz `reg`, chama
  `dev_set_name(dev, "%llx.%s", addr, node->name)`. Para o nó acima, o nome
  esperado nesse ramo é `30000000.rksdmmc`.
- `block/partitions/efi.c:662–670`: o parser GPT copia o nome de partição
  para `info->volname` e define `has_info=true`. Essa versão faz conversão
  UTF16LE simplificada para 7 bits, portanto usar nomes ASCII simples.
- `block/partition-generic.c:221–227`: o uevent de partição inclui
  `PARTN` e, se `volname` não vazio, `PARTNAME`.

Core TinkerBoard a54e584:

- `init/devices.cpp:276–294`: registra o platformdevice e tira os prefixos
  `/devices/` e, quando presente, `platform/` para obter seu nome.
- `:302–314`: procura o platformdevice cujo caminho é prefixo do blockdevice.
- `:399–404`: parser recebe os campos PARTN e PARTNAME do uevent.
- `:486–511`: constrói `/dev/block/platform/<nome>/by-name/<partname>`;
  `sanitize()` protege o segmento do nome antes de gerar o link.

Assim, eventos de platformdevice com caminho `/devices/30000000.rksdmmc`
ou `/devices/platform/30000000.rksdmmc` e evento de partição descendente
com `PARTNAME=system` têm um ramo de fonte que gera
`/dev/block/platform/30000000.rksdmmc/by-name/system`.
Outros prefixos/registradores, ausência de eventos, ordem de coldboot,
configuração GPT ou labels distintos podem impedir esse resultado. Não foi
executado ueventd nem apresentado esse caminho como comprovado em runtime.

## O fixup eMMC do kernel não é universal no SD

`block/partitions/check.c:73` tenta EFI antes dos parsers RK nas linhas 112–113.
`rkpart_partition()` em `rk.c:378–393` retorna 0 se a capacidade é menor que 1 GiB,
se `bd_disk->emmc_disk!=1` ou se não existe `mtdparts=`. Só o ramo que passa
nessas condições chama `rkpart_bootmode_fixup()` na linha421. Esse fixup
acrescenta `androidboot.mode=emmc` ou a flag de charger eMMC. O parser GPT não
chama esse fixup. Portanto não afirmar que qualquer bootSD recebe eMMC.

Uma busca nas fontes .c/.h do kernel fixado não encontrou `storagemedia`.
Esse valor deve vir de cmdline/firmware/loader na cadeia efetiva; nenhum foi
escolhido ou executado aqui. É preciso integrar e observar a cadeia antes de
alterar indiscriminadamente parser ou propriedades para “garantir” sd.
