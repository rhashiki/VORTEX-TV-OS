# Contrato framebuffer: revisão dos consumidores fixados

Kernel: `6c04d006ae881944d32c19e68b992d0bd5ab4fde`.
libhardware: `d0c81ba009240cb9ab38d75d7e88190055349c2a`.
Gralloc: `c92fb8cd8becd57b025149f2861a2072b092ddea`.
HWC: `d3ec43f2f751123ca5e7bda2d07eded4c6352a35`.

## Por que o patch muda o contrato, sem apenas preencher espaço

Os prefixes das declarações têm os mesmos campos, ordem e tipos escalares;
cinco janelas, quatro áreas e onze fences. Não há pointers/longs ou atributo
packing na struct do ioctl. O antigo membro final `rk_lcdc_post_cfg post_cfg`
não é usado pelas fontes gralloc/HWC selecionadas. O kernel, porém, espera
`rk_fb_wb_cfg wb_cfg` e copia todos os 908 bytes nos dois sentidos.

O patch adiciona a declaração real de writeback (`data_format`, `ion_fd`,
`phy_addr`, `xsize`, `ysize`, `reserved0`, `reversed1`) e substitui o membro
final. Conserva o tipo post_cfg não usado para evitar remoção lateral de API.
Não introduz padding sem significado nem altera o tamanho esperado no kernel.

Dois consumidores do ioctl foram encontrados nas árvores selecionadas:

- Gralloc `framebuffer_device.cpp:109–128`: objeto local e memset completo
  em110, preenchimento dos campos e `RK_FBIOSET_CONFIG_DONE`.
- HWC `rk_hwcomposer.cpp:3194`, memset completo3211, fences explicitamente
  inicializados e ioctl3715. Helpers/sort usam `sizeof` do tipo, sem buffer
  hardcoded de904 bytes.

Esses consumidores não populam writeback; o novo tail permanece zero.
`rk_fb.c:2232–2234` desabilita writeback apenas quando **ion_fd e phy_addr
são ambos zero**. Usar−1 no ion_fd desse tail não é um sentinel de disable:
seria tratado como pedido de importação. A leitura de wb_cfg ocorre sob
`SUPPORT_WRITE_BACK` em2656–2658. RK322x LCDC não seta esse feature; uma
ativação explícita foi encontrada em RK3368. Isso não remove o defeito do
copy completo em3048–3060, independentemente da ativação do writeback.

## Verificação de compilação

O programa contract_measure.c inclui os headers completos e reais. O kernel
usa os includes gerados do perfil SD já compilado; o userspace inclui
hardware/rk_fh.h, sem copiar/reescrever suas declarações. GCC ARM6.3.1 mede
94 quantidades (tamanhos, alinhamentos, offsets/tamanhos de membros): todas
idênticas após o patch. Antes, a struct de envio media904, contra908 no
kernel. As quantidades do prefix eram idênticas.

contract_assert.c inclui o header real e exige os valores medidos do kernel.
A compilação negativa contra o header antigo falha; a positiva passa. Essa
negativa é de uma asserção do contrato: o gralloc antigo em si ainda pode
compilar normalmente e continuar contendo o defeito de ABI.

## Limites

Todos os consumidores precisam recompilar contra o header corrigido.
Binários antigos/prebuilts desconhecidos continuam fora da correção. A busca
cobre somente as árvores identificadas, não a totalidade de um BSP não
sincronizado. Nada aqui aprova private_handle_t do Mali proprietário, ION/RGA,
fechamento de módulos, composição visual, execução do ioctl ou HDMI físico.
Não houve imagem Android/SD, execução de TV Box ou GitHub Actions.
