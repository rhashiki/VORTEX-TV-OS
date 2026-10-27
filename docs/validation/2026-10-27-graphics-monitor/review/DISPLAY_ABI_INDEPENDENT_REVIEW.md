# Revisão independente do contrato framebuffer

Revisão somente de fontes, sem compilação nova, ioctl executado ou teste físico.
Pins e hashes dos arquivos lidos estão em `display-abi-independent-review.json`.

## Resultado

Há dois chamadores reais do contrato incompatível nas fontes selecionadas:
`gralloc/framebuffer_device.cpp:128` e
`hwcomposer/rk_hwcomposer.cpp:3715`. Ambos incluem `hardware/rk_fh.h`,
reservam `struct rk_fb_win_cfg_data` na pilha, zeram o objeto completo e o
passam ao ioctl `0x4628`. Não foi encontrada nenhuma referência a `post_cfg`
ou `wb_cfg` nas fontes C/C++/headers dos dois projetos. Portanto o membro
final atual não implementa overscan de userspace nesses chamadores.

O kernel `rk_fb.c:3048` lê e `rk_fb.c:3059` devolve `sizeof(win_data)` sem
negociar o tamanho ou codificá-lo no número do ioctl. A medição ARM já
registrada é 904 bytes no userspace e 908 no kernel, com prefixo de 888
bytes comum. O kernel pode ler quatro bytes fora do objeto da aplicação,
falhar com EFAULT quando cruzar uma página, ou sobrescrever quatro bytes
na cópia de volta. O mesmo ioctl e um prefixo igual não evitam isso.

A divergência tem semântica: os 16 bytes finais da aplicação são
`rk_lcdc_post_cfg {xpos,ypos,xsize,ysize}`, enquanto o kernel espera os
20 bytes de `rk_fb_wb_cfg`, com formato, ION fd, endereço, dimensões e
campos reservados. Adicionar padding, manter post_cfg como campo ativo ou
tratar o ioctl como write-only não corrige esse contrato.

## Estratégia mínima coerente

Substituir o membro final no header de userspace pela declaração exata
`rk_fb_wb_cfg` do kernel fixado e recompilar todos os consumidores desse
header. Não é necessário alterar o driver para aceitar um ABI inventado.
Manter o memset completo dos dois chamadores: ausência de pedido de
writeback fica representada por endereço/fd zero.

`rk_fb_set_win_config()` só usa `wb_cfg` quando a propriedade
`SUPPORT_WRITE_BACK` está habilitada; `rk_fb_set_wb_buffer()` desabilita o
writeback quando `phy_addr == 0 && ion_fd == 0`. O driver RK322x examinado
não atribui essa propriedade. Entre os drivers LCDC examinados, ela é
atribuída em `rk3368_lcdc.c`. Isso não torna a diferença de quatro bytes
inofensiva: as duas cópias completas continuam incondicionais.

A prova precisa usar os headers reais e conferir offsets/tamanhos de todos
os campos e arrays compartilhados, alinhamento, signedness/width e valor
do ioctl, em ARM. O novo nome/tipo do tail deve corresponder ao kernel,
sem campo post_cfg adicional. A compilação de declarations isoladas não
substitui o build e link das HALs.

## Seleção efetiva das fontes

O common D042 já lista `gralloc.$(TARGET_BOARD_HARDWARE)` e
`hwcomposer.$(TARGET_BOARD_HARDWARE)` em PRODUCT_PACKAGES. O board padrão
é `rk30board`. O vendor candidato copia, ao mesmo tempo,
`gralloc.rk30board.so` e `hwcomposer.rk30board.so` para os caminhos das HALs
que seriam compiladas. Além disso copia `gralloc.default.so`, que é um
fallback do loader de libhardware. Remover essas três cópias num perfil
explícito de HALs de fonte é coerente; não basta corrigir um header que a
imagem final pode nunca usar. É necessário conferir as entradas finais da
imagem e os módulos efetivamente construídos.

Há dois riscos adicionais de seleção por árvore residual:

- O HWC inclui `gralloc_priv.h` e seu Android.mk procura
  `hardware/rockchip/libgralloc_ump` antes de `hardware/rockchip/libgralloc`.
- O gralloc seleciona MALI_600 se `hardware/arm` existir, mesmo com
  `TARGET_BOARD_PLATFORM_GPU=mali400`.

Um perfil de fontes precisa rejeitar essas alternativas residuais ou provar
qual include/ramo o compilador e o make usaram. O XML sozinho não limpa
árvores de uma sincronização anterior.

## Contratos e comportamentos ainda abertos

As formas escalares examinadas de três outros ioctls coincidem: DMA-BUF
export (`0x5003`, int), VSYNC enable (`0x4629`, int) e IOMMU enabled
(`0x4632`, int). Isso não aprova seus resultados em hardware ou o pacing.
Há ainda ioctls RGA e IPP e dependências ION não comparados integralmente
nesta revisão.

O layout `private_handle_t` do gralloc contém unions de ponteiros/padding
64 bits, campos de fd, tamanho, stride, formato e estado privados. O HWC
faz casts diretos de buffer_handle_t para esse tipo. As bibliotecas
`libGLES_mali.so` e `libgralloc_priv_omx.so` continuam no vendor, com sua
própria expectativa privada não estabelecida. Compilar gralloc e HWC com
o mesmo header não demonstra compatibilidade dos blobs.

Os fds em rk_fh.h são signed short na interface dos dois lados; não os
alargar para int independentemente. O HWC só registra erro de CONFIG_DONE
e continua tratando os fences, enquanto o gralloc retorna no erro. Ciclo
de vida de fences, falhas parciais e sincronização precisam de testes
específicos quando o target completo executar.

Conclusão desta revisão: a substituição exata do tail é uma correção
justificável do contrato source-to-source desse ioctl; a plataforma gráfica
completa permanece sem aprovação de build, link, EGL/ION/RGA e execução.
