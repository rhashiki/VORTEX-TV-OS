# Produto Android SD de referência

O perfil `vortex_rk322x_sd_box` resolve suas entradas pelas funções reais de
`build/core/product_config.mk` do Rockchip Nougat. É uma referência experimental
de produto, **não uma imagem SD nem um BSP aprovado para R329Q_V8.0**.

O produto herda `core_minimal.mk`, fontes e o fragmento Vortex. Seleciona
VortexHome, PackageInstaller, DefaultContainerService, Settings, SystemUI,
teclado e DocumentsUI/ExternalStorageProvider. Os apps instalados continuam
na Home, sem gaveta. Não herda as grandes listas device/vendor que traziam
Launcher3, arquivos Bluetooth e ferramentas de fábrica.

O [patch do build](patches/0001-scope-minimal-packages-to-vortex-sd.patch)
condiciona quatro entradas herdadas somente ao nome deste produto:
`gralloc.default`, `recovery`, `applypatch` e `uncrypt`. Um `filter-out` no filho
não removeria entradas ainda representadas pelos marcadores de herança do
Android. As listas do produto original `rk322x_box` permaneceram idênticas
byte a byte no ensaio com as mesmas entradas.

## Compor as fontes

Usar uma árvore descartável da [composição experimental](../platform-reference/README.md),
nas revisões exatas ali indicadas. O XML ainda fixa um Vortex histórico;
aplicar sua correção de módulo AOSP documentada. Os novos arquivos abaixo
vêm deste checkout atualizado, não daquele commit histórico.

1. Aplicar os [patches SD 0001–0006](../sdcard/README.md), na ordem e nos
   repositórios indicados.
2. Aplicar os [patches gráficos](../platform-reference/graphics/README.md)
   nos respectivos projetos. A remoção de cópias gráficas vendor vem depois
   do patch SD 0006.
3. Aplicar o patch deste diretório na raiz do projeto `build` de revisão
   `d2721c65c9282b31df7b79f85289ee6c4e636716`.
4. Copiar o perfil para `device/vortex/rk322x_sd_box` dentro do BSP.

```sh
# Executar na raiz da árvore BSP, com caminho absoluto para este checkout.
VORTEX_CHECKOUT=/caminho/absoluto/VORTEX-TV-OS
git -C build apply --check "$VORTEX_CHECKOUT/rom/product/patches/0001-scope-minimal-packages-to-vortex-sd.patch"
git -C build apply "$VORTEX_CHECKOUT/rom/product/patches/0001-scope-minimal-packages-to-vortex-sd.patch"
mkdir -p device/vortex/rk322x_sd_box
cp -a "$VORTEX_CHECKOUT/rom/product/rk322x_sd_box/." device/vortex/rk322x_sd_box/
```

Com uma árvore completa, o alvo é `lunch vortex_rk322x_sd_box-eng`.
**Esse lunch e a compilação completa de imagens ainda não foram executados.**
O ensaio de produto usa um preâmbulo diagnóstico e as funções genuínas de
importação/herança; o ensaio nativo usa `tapas`, não este produto completo.
Não confundir os dois resultados.

## Escolhas e limites

- Gralloc/HWC têm provedores de fonte explícitos. A compilação nativa de
  referência usa bibliotecas API25 reais como prebuilts, fora deste produto;
  elas não são uma solução de dependências do BSP.
- Áudio seleciona `audio.primary.rk30board`, USB e remote-submix. A política
  derivada remove A2DP e dois tokens SCO; rotas HDMI/SPDIF restantes são
  genéricas. `audio_policy.rk30board` não é selecionado, pois seu provedor
  pertence ao ramo legacy excluído pelo próprio Android.mk.
- O BoardConfig neutraliza o Wi-Fi Broadcom presumido pelo common. Não há
  chip, driver ou firmware Wi-Fi identificado e validado para a unidade.
- O overlay SettingsProvider altera os recursos reais
  `def_device_provisioned` e `def_user_setup_complete` para `true`, pois não
  há SetupWizard. Não habilita fontes desconhecidas nem altera dados já
  existentes. A compilação desse recurso e o primeiro boot continuam pendentes.
- O init reduzido monta somente o fstab SD quando `ro.bootmode=sd`; não força
  o modo de boot. Ainda faltam permissões/ueventd, SELinux, serviços e integração
  dos drivers. Não equivale ao ramdisk completo da placa.
- Remover recovery/uncrypt dos pacotes **não remove o caminho de erro do
  init/fs_mgr que pode escrever BCB e pedir wipe/recovery**. Esse caminho
  permanece aberto e impede afirmar preservação da memória interna.
- Os caminhos USB `ff580000`/`ff5c`/`ff5d` herdados do fstab não foram
  demonstrados contra os controladores `3004`/`3008` etc. do kernel examinado.
  DocumentsUI incluído não comprova descoberta nem montagem de pendrive.
- As listas de fontes são reais, mas seus módulos/TTFs não foram compilados
  nesta árvore fina. Toda a resolução de dependências e o inventário final
  das imagens ainda precisam passar pelo build completo.

O auditor `tools/audit_product_inputs.py` confere listas exportadas e fontes
de cópia de uma árvore concreta. Seu resultado é somente `product_inputs_only`;
não aprova boot, mídia, drivers ou instalação. Exemplos e evidências estão no
[relatório consolidado](../../docs/VALIDATION_2026-10-27_PRODUCT.md).

Os novos arquivos de configuração deste perfil são Apache-2.0. A política de
áudio é derivada do arquivo público da revisão device indicada no relatório;
o original não apresenta cabeçalho de licença próprio. A revisão de direitos
do BSP completo permanece aberta. Nenhum blob vendor ou biblioteca SDK é
redistribuído neste diretório.
