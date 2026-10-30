# Recovery candidato — componente compilado

O recovery Rockchip/AOSP Nougat `4e64764f19db25238c296691ef0d950603eae33b`
foi compilado por suas regras Android.mk no experimento separado `aosp_arm`.
O executável instalado tem 956.040 bytes e SHA-256
`5e2c3639b15a51728b24f8400dd2539c2ace87647fca41527698129ce543928c`.
É um ELF ARM estático; não foi executado ou empacotado como recovery.img.

O link usa fontes e archives vendor Rockchip. O mapa registra contribuições
retidas de librkupdate, libext2_uuid e libcrc32; librkrsa é nomeado no comando,
sem membros retidos identificados. Esses inputs não passam a ser código aberto
pela compilação. Os archives vendor separados ficam fora do pacote de entrega.

O [patch da UI comunitária](patches/0001-common-use-nougat-recovery-ui.patch)
adapta `recovery_ui.cpp` do common `3b1aa90ef43f9d34094739a211ad44bf9a2c0b74`
após os patches SD 0002/0003/0005. Usa o construtor e as ações Nougat e deixa
a política de teclas com a classe base. O archive ARM correspondente compilou
e 20 verificações host passaram. Essa UI é um alvo separado; o executável
baseline usa default_device.cpp, sem seleção implícita desse archive.

O patch é opt-in e fica fora de full-platform-patches.json. O produto externo
SD mantém TARGET_NO_RECOVERY=true. Os caminhos upstream sdboot/fw_update e
IDBlock precisam de revisão antes de transformar o programa em instalador.

Receitas, origens, dependências, licenças, mapa de contribuições e limites:
[evidências do recovery](../../docs/validation/2026-10-28-candidate/recovery/README.md).
Os logs grandes têm hash e caminho no ZIP no raw-log-index.json desse diretório.
Não há TWRP portado, imagem SD inicializável ou boot físico comprovado.
