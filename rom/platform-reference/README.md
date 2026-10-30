# Composição experimental de fontes AOSP r6 / Rockchip

Este diretório registra a composição usada nos ensaios de compilação.
O produto já passou pelo lunch real e houve tentativas de make droid, ainda
com fontes/dependências ausentes. **Não é o manifesto do fornecedor, um lock
resolvido, um BSP compatível ou uma ROM completa.**

- [aosp-r6-default.xml](aosp-r6-default.xml): bytes do manifesto oficial
  `android-7.1.2_r6`, com 541 projetos e revisão padrão em tag.
- [vortex-r6-rockchip-experimental.xml](vortex-r6-rockchip-experimental.xml):
  overlay opt-in de `.repo/local_manifests`, com 29 commits completos,
  incluindo 24 projetos Rockchip e cinco candidatos já registrados.
- [vortex-product-integration.patch](vortex-product-integration.patch): corrige
  a descoberta/duplicação do produto sobre o Vortex `1db0c91` agora fixado.
  O perfil materializado usa `device/vortex/vortex_rk322x_sd_box`.
- [vortex-aosp-integration.patch](vortex-aosp-integration.patch): registro
  histórico da correção AOSP sobre `45d626a`. Não aplicar ao novo pin, que
  já contém aquela correção de módulo. O XML não executa nenhum patch.

A composição tem 556 projetos: 14 substituições reais, sem colisões de
nomes/paths, e 527 projetos AOSP ainda em tags. Os commits
Rockchip selecionados têm árvores não vazias; isso não prova fechamento de
dependências. Não se executou `repo sync` nem `repo manifest -r` completo.

O common D042 continua no path `device/rockchip/common`, para corresponder
às revisões dos patches SD existentes. O common e o produto RK3328 da outra
fonte foram excluídos explicitamente. Não aplicar os patches D042 em outra
revisão. O kernel e o Vortex também precisam dos patches documentados;
sincronizar o XML sozinho não materializa o perfil Vortex nem aplica as
exclusões. Seguir o [perfil de produto](../product/README.md) e o plano de
patches do driver de compilação.

O build Rockchip declara `NHG47K`, como a base oficial r6. A divergência
framebuffer original de 904/908 bytes exige o patchset gráfico. O patch de
seleção também impede que um checkout residual de hardware/arm altere o
ramo Mali400 escolhido para RK322x.

O [patchset gráfico posterior](graphics/README.md) corrige o layout medido
no header, torna a seleção Mali400 explícita para RK322x e retira três
cópias vendor conflitantes. Gralloc/HWC já compilaram e passaram por link e
instalação Android.mk com bibliotecas de referência. ABI privada dos blobs,
execução gráfica e o build inteiro do Android continuam pendentes.

A compilação de áudio mostrou outra dependência obrigatória:
`rockchip-android/external-tinyalsa` no lugar da TinyALSA padrão AOSP. O
campo pcm_config.flag é usado de fato pelo driver. O novo
[patch de áudio](audio/README.md) também rejeita uma taxa HDMI não suportada
antes de usar um tipo de saída indefinido.

[Pesquisa e provas de layout ARM](../../docs/validation/2026-10-26-aosp-bootloader/platform/PLATFORM_R6_FINDINGS.md)
detalham os pins, includes, alternativas excluídas e bloqueios. A composição
foi feita nas fontes disponíveis, sem novos pedidos de diagnóstico ao dono.
