# Contrato framebuffer do candidato RK322x

Este patchset opt-in corrige a divergência **medida** entre o libhardware
selecionado e o kernel SDK. Não aprova os blobs Mali/OMX ou uma imagem Android.
A [continuação nativa](NATIVE_HAL_BUILD.md) compilou também HWC, ligou os dois
módulos manualmente e verificou seu carregamento no linker Android sob QEMU;
a plataforma Android completa e a execução gráfica continuam pendentes.
Aplicá-lo exige recompilar todos os
consumidores; não atualizar só o header e reutilizar HALs pré-compiladas.

## Fontes e ordem

Cada patch pertence à raiz de um repositório diferente, nos commits do
[overlay experimental](../vortex-r6-rockchip-experimental.xml). Conferir os
commits completos e aplicar com `git apply --check` antes de `git apply`,
sempre em checkouts descartáveis. O XML não aplica nenhum patch.

| Patch | Path no Android | Commit base |
| --- | --- | --- |
| [0001](patches/0001-libhardware-match-kernel-fb-contract.patch) | `hardware/libhardware` | `d0c81ba009240cb9ab38d75d7e88190055349c2a` |
| [0002](patches/0002-gralloc-select-mali400-for-rk322x.patch) | `hardware/rockchip/libgralloc` | `c92fb8cd8becd57b025149f2861a2072b092ddea` |
| [0003](patches/0003-hwc-use-selected-gralloc-header.patch) | `hardware/rockchip/hwcomposer` | `d3ec43f2f751123ca5e7bda2d07eded4c6352a35` |
| [0004](patches/0004-vendor-use-source-graphics-hals.patch) | `vendor/rockchip/rk322x`, **após** [0006 SD](../../sdcard/patches/0006-vendor-omit-bluetooth.patch) | `50c7170ecb4bd907059db37f09f4767b301f2d15` |

`0001` substitui o membro final `post_cfg`, não usado pelos dois consumidores
selecionados, por `rk_fb_wb_cfg` com os mesmos campos do kernel
`6c04d006ae881944d32c19e68b992d0bd5ab4fde`. O objeto passa de 904 para 908
bytes. Não se trata de padding: a semântica do membro também muda. Os callers
zeram `sizeof` completo; manter `ion_fd=0` e `phy_addr=0` conserva writeback
desabilitado no ramo do driver examinado. Não preencher `ion_fd=-1` como
sentinela de writeback.

`0002` seleciona o ramo Mali400 no alvo `rk322x`, mesmo com diretório
`hardware/arm` residual, e recusa outro valor de GPU nesse alvo. Outras
plataformas conservam o ramo anterior. `0003` faz o HWC desse alvo procurar o
header do gralloc selecionado, retirando fallbacks UMP/Intel. `0004` remove
somente as cópias vendor de `gralloc.default.so`, `gralloc.rk30board.so` e
`hwcomposer.rk30board.so`, que conflitavam com os módulos de fonte ou podiam
mascarar sua ausência. Os pacotes gralloc/HWC do common permanecem requeridos.

O produto precisa usar `TARGET_BOARD_PLATFORM=rk322x`,
`TARGET_BOARD_PLATFORM_GPU=mali400`, `TARGET_BOARD_HARDWARE=rk30board` e os
módulos fonte correspondentes. A ausência de bibliotecas necessárias deve
aparecer como falha de build; não reinserir as três cópias para contorná-la.
Os includes legados mencionados no Android.mk ainda precisam de resolução
no grafo real. A compilação isolada registrada resolveu suas dependências
por headers oficiais explícitos, sem demonstrar o grafo AOSP inteiro.

## Verificação e limites

Os headers reais completos, incluindo o header Linux com config e includes
gerados do kernel compilado, foram usados nas medições ARM. O contrato
corrigido coincide em 94 medidas de tamanho, alinhamento e campos. A asserção
de tamanho falha com o header anterior e passa depois. Os quatro arquivos
C++ reais do gralloc também compilaram como objetos ARM com Bionic e headers
Android. Esse ensaio inicial não fez link de `gralloc.rk30board.so` pelo Android
nem compilou HWC. Os resultados posteriores de HWC/link manual estão na
receita nativa acima, sem aprovação de execução gráfica em dispositivo.

Foram conferidos os patches nas fontes fixadas e a expansão GNUmake em
cenários limpos/residuais e outras plataformas. Esse harness desabilita
shells e registro de módulos; verifica somente seleção, não compila HALs.

Ainda faltam o build/link Android completo, inventário final sem as cópias antigas,
contrato privado dos blobs Mali/OMX, demais ioctls ION/RGA, fences e execução
real. Nem a igualdade dos layouts nem uma compilação C++ provam esses pontos.

Resultados, comandos e hashes: [relatório da etapa](../../../docs/VALIDATION_2026-10-27_GRAPHICS_MONITOR.md).
