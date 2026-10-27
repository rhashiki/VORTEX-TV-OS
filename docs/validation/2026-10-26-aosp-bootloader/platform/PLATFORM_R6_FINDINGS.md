# Composição experimental AOSP r6 + fontes Rockchip — 26/10/2026

Pesquisa de fontes, sem sincronização completa, build Android, execução de
scripts BSP ou operações físicas. Os arquivos do repositório Vortex não foram
alterados nesta tarefa. Os checkouts rasos adquiridos permaneceram limpos.

## Base mais próxima encontrada

Foi localizada a organização pública `rockchip-android`, branch
`rk3328-box-7.1`, com fontes de plataforma e HALs diferentes da referência
TinkerBoard r39 examinada anteriormente.

| Projeto | Commit observado |
| --- | --- |
| build | `d2721c65c9282b31df7b79f85289ee6c4e636716` |
| system/core | `ab5f1d24b072e36ddcf02439303050c501d9dc5b` |
| bionic | `8b2e5b977118ebb8447cdf429c4a6be534c4fd1b` |
| hardware/libhardware | `d0c81ba009240cb9ab38d75d7e88190055349c2a` |
| hardware/rockchip/libgralloc | `c92fb8cd8becd57b025149f2861a2072b092ddea` |
| hardware/rockchip/hwcomposer | `d3ec43f2f751123ca5e7bda2d07eded4c6352a35` |
| hardware/rockchip/audio | `03b111b6736b48ec17ffee4906caecf59323d8c1` |

O build declara Android 7.1.2, API25, `NHG47K` e patch2017-04-05.
O `build_id.mk` oficial de `android-7.1.2_r6` também declara `NHG47K`;
o arquivo foi adquirido para comparação. Essa correspondência é uma evidência
de versão, não uma demonstração de fechamento de dependências ou ABI.

`rockchip-critical-references.json` registra 31 caminhos pesquisados, com
25 branches resolvidas. A organização listava 504 repositórios, 140 com
tamanho reportado maior que zero; não foi encontrado repositório com nome
de manifesto nessa listagem. Não se conclui inexistência universal de um
manifesto do fornecedor por essa busca.

## Overlay concreto, com limites explícitos

`aosp-r6-default.xml` contém os bytes oficiais do manifesto r6: 541 projetos,
sem includes, revision default `refs/tags/android-7.1.2_r6`. Seu SHA-256 é
`9a0ef14c94804bbdf5c90c25f24a52f6435035a54e90827ca7626ca7e696363f`.

`vortex-r6-rockchip-experimental.xml` é um overlay opt-in de
`.repo/local_manifests`, para uma árvore iniciada a partir dessa base oficial.
Não é o manifesto original de Rockchip, um lock completo ou um BSP aprovado.

- Contém 28 projetos com commits completos: 23 do subconjunto Rockchip e
  cinco candidatos já conhecidos — device/common/vendor D042, kernel Rockchip
  e Vortex fixado em `45d626a4bc508b49b8863bd67e2ce9f2f17554d5`.
- Faz 13 substituições por `remove-project` com nomes reais do manifesto AOSP.
  Preserva a cópia de `build/core/root.mk` para `Makefile` e os linkfiles de
  Soong. A composição em memória resulta em 556 projetos, sem nomes ou paths
  duplicados. Os 528 projetos AOSP não substituídos continuam em tags r6,
  sem resolução individual dos seus commits.
- Os 23 commits Rockchip selecionados têm entradas na árvore raiz; nenhum
  projeto reportado vazio foi colocado no overlay. Isso não valida seu
  conteúdo completo ou suas dependências.
- O novo common Rockchip `63ab18755e227df17790024e6f0857df88acc638` foi
  excluído: BoardConfig/device.mk diferem do D042 e o init SD não existe nessa
  revisão. Mantém-se explicitamente o common D042 alvo dos patches existentes.
  O alvo de produto RK3328 também não foi incluído no sync proposto.

O XML não executa patches, não herda automaticamente o produto Vortex, não
remove outros launchers e não exclui recovery/updaters. A composição entre
common/vendor D042 e o subconjunto de plataforma RK3328 continua experimental.
Não foi executado `repo sync` ou `repo manifest -r` nesta tarefa.

## Gráficos: DMA-BUF/framebuffer, com uma incompatibilidade real

O candidato D042 já seleciona `mali400` e `GRAPHIC_MEMORY_PROVIDER=dma_buf`.
As novas fontes gralloc/HWC usam framebuffer, ION/DMA-BUF e condicionais
RK322X/RK322X_BOX. O allocator UMP está desabilitado. Logo, a presença de
arquivos ou diretórios chamados UMP não identifica o caminho efetivamente usado.

O gralloc escolhe `MALI_600` se `hardware/arm/` existir, independentemente do
nome do GPU. A base oficial mais o overlay proposto não introduzem esse path;
o ramo legado é esperado nesse layout. Diretórios residuais/untracked ainda
podem alterar a seleção. Os includes UMP do ramo legado são condicionais ao
allocator desabilitado; paths de include inexistentes não foram apresentados
como prova de uma dependência efetiva de UMP.

Foram localizados os headers necessários `hardware/rk_fh.h` e
`hardware/rga.h` no libhardware selecionado, os formatos gráficos Rockchip em
`system/core/include/system/graphics.h` e `vpu_mem.h`/`vpu_api.h` no librkvpu.
Alguns números de ioctl coincidem, incluindo `RK_FBIOSET_CONFIG_DONE=0x4628`
e a exportação de DMA-BUF0x5003. Isso não bastou para aprovar a interface.

Foi encontrada uma diferença concreta em `rk_fb_win_cfg_data`:

| Declarações | Tamanho ARM EABI | Membro final | Offset / tamanho do final |
| --- | --- | --- | --- |
| libhardware novo, `include/hardware/rk_fh.h` | 904 bytes | `rk_lcdc_post_cfg post_cfg` | 888 / 16 bytes |
| kernel6c04d006, `include/linux/rk_fb.h` | 908 bytes | `rk_fb_wb_cfg wb_cfg` | 888 / 20 bytes |

As declarações reais foram extraídas sem reescrita e compiladas isoladamente
com o toolchain ARM existente para medir os layouts; não foi uma compilação
de HAL ou do Android. Fontes, comandos, objetos e tamanhos estão em
`framebuffer-abi-review/`. O driver `rk_fb.c:3047–3060` copia
`sizeof(win_data)` do/para userspace. Não é correto ligar esse par sem tratar
a interface e presumir compatibilidade só pelo framebuffer e ioctl.

Além disso, ambos os Android.mk gráficos executam `version.sh` durante a
expansão e geram `version.h`; esses scripts não foram executados na pesquisa.
Layout de `private_handle_t`, blobs GLES, demais ioctls ION/RGA e composição
de módulos ainda exigem revisão/build/runtime próprios.

## Bootmode e áudio da nova referência

Diferente do core TinkerBoard, este `system/core` conserva o mapa
`ro.boot.mode` → `ro.bootmode`. Com `androidboot.mode=sd` importado, o ramo
de polling eMMC/NVMe pode ser pulado e o valor SD é copiado antes de criar o
link de fstab. Não foi aplicado patch Tinker nem forçado um modo de mídia.
Isso é leitura do código, sem execução de init ou observação de montagem.

O áudio tem ramo `rk322x` e não injeta `TINKER_AUDIO` incondicionalmente.
Ainda não há correspondência comprovada de codec, mixer, HDMI ou HAL binária
com a unidade física.

## Outros candidatos e bloqueios

O device pstglia examinado foi fixado em
`4bd6219e3dc0480d6b2ca4da0de73fd2ea2d52da`. Continua com bootargs NAND,
`rockchip_jtag`, permissive e extração de vendor; também referencia módulos
Intel herdados em device.mk. Seu local manifest não fornece uma base pronta
para substituir o candidato SD. Nenhum dado adicional foi pedido ao dono.

A composição nova fornece uma referência de fontes mais concreta para os
próximos ensaios, mas continuam abertos: a interface framebuffer divergente,
fechamento de módulos e pacotes vendor, seleção do produto mínimo Vortex,
aplicação/auditoria dos patches SD, política SELinux, loader/DDR/trust,
ramdisk/layout SD e validação física. Nenhuma ROM ou cartão foi produzido.

## Arquivos principais para revisão

- `vortex-r6-rockchip-experimental.xml`: overlay opt-in, sem sync executado.
- `overlay-composition-review.json`: projetos, substituições e bloqueios.
- `aosp-r6-default.xml` e `aosp-r6-manifest-reference.json`: base oficial.
- `rockchip-critical-references.json`: 25 heads entre 31 caminhos pesquisados.
- `selected-branch-nonempty-review.json`: raízes dos 23 projetos escolhidos.
- `known-candidate-nonempty-review.json`: cinco candidatos conhecidos.
- `acquired-source-checkouts.json`: revisões/tree IDs dos checkouts locais.
- `mali-legacy/graphics-source-review.json`: comparação das fontes gráficas.
- `framebuffer-abi-review/layout-review.json`: medição ARM e limites.
- `rockchip-common-files-comparison.json`: razão da escolha explícita D042.

Não foi usado GitHub Actions e nenhum binário de fornecedor foi executado.
