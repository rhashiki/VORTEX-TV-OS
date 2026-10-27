# Composição experimental de fontes AOSP r6 / Rockchip

Este diretório registra uma composição para investigação, sem download
completo ou compilação da plataforma. **Não é o manifesto do fornecedor,
um lock resolvido, um BSP compatível ou uma receita aprovada de ROM.**

- [aosp-r6-default.xml](aosp-r6-default.xml): bytes do manifesto oficial
  `android-7.1.2_r6`, com 541 projetos e revisão padrão em tag.
- [vortex-r6-rockchip-experimental.xml](vortex-r6-rockchip-experimental.xml):
  overlay opt-in de `.repo/local_manifests`, com 28 commits completos,
  incluindo 23 projetos Rockchip e cinco candidatos já registrados.
- [vortex-aosp-integration.patch](vortex-aosp-integration.patch): correção do
  módulo AOSP sobre o Vortex `45d626a` fixado no overlay. É obrigatória para
  reproduzir o módulo corrigido; o XML não executa patches.

A composição em memória tem 556 projetos: 13 substituições reais, sem
colisões de nomes/paths, e 528 projetos AOSP ainda em tags. Os commits
Rockchip selecionados têm árvores não vazias; isso não prova fechamento de
dependências. Não se executou `repo sync` nem `repo manifest -r` completo.

O common D042 continua no path `device/rockchip/common`, para corresponder
às revisões dos patches SD existentes. O common e o produto RK3328 da outra
fonte foram excluídos explicitamente. Não aplicar os patches D042 em outra
revisão. O kernel e o Vortex também precisam dos patches documentados;
sincronizar o XML sozinho não cria o produto Vortex nem exclui launchers,
Bluetooth, recovery ou atualizadores.

O build Rockchip declara `NHG47K`, como a base oficial r6. Gralloc/HWC usam
framebuffer/DMA-BUF, mas há um **bloqueio de ABI**: `rk_fb_win_cfg_data`
mede 904 bytes no userspace e 908 no kernel atual, com membro final diferente.
Não integrar esse par sem corrigir e validar a interface. A ausência de
`hardware/arm` no layout proposto também importa: um checkout residual desse
path altera o ramo gráfico escolhido por wildcard.

O [patchset gráfico posterior](graphics/README.md) corrige o layout medido
no header, torna a seleção Mali400 explícita para RK322x e retira três
cópias vendor conflitantes. Seus quatro objetos gralloc foram compilados,
mas o link Android, a ABI dos blobs e a execução continuam pendentes.

[Pesquisa e provas de layout ARM](../../docs/validation/2026-10-26-aosp-bootloader/platform/PLATFORM_R6_FINDINGS.md)
detalham os pins, includes, alternativas excluídas e bloqueios. A composição
foi feita nas fontes disponíveis, sem novos pedidos de diagnóstico ao dono.
