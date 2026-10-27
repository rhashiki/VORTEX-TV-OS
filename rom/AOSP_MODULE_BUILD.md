# VortexHome compilado pelo AOSP 7.1.2

O módulo `VortexHome` passou pelo mecanismo GNU make/Jack do AOSP oficial
`android-7.1.2_r6`, com `tapas arm eng VortexHome`. O experimento é separado
do APK Gradle e da plataforma Rockchip completa. Não gera sistema Android,
ramdisk ou imagem de cartão.

O [relatório da etapa](../docs/VALIDATION_2026-10-26_AOSP_BOOTLOADER.md) contém
o APK, os hashes, os testes e as limitações. A
[receita detalhada](../docs/validation/2026-10-26-aosp-bootloader/aosp-app/BUILD_RECIPE.md)
registra os caminhos concretos do experimento, versões e adaptações de host.

## Correções aplicadas à integração

`LOCAL_JACK_ENABLED := true` era rejeitado pelo parser real r6, que aceita
`full`, `incremental` ou `disabled`. O módulo usa agora `full`.
As opções aapt explicitam `versionCode=1` e `versionName=0.1.0-dev`, iguais
às do Gradle. Antes disso, a compilação AOSP herdava a versão da plataforma.
Nenhum código Java ou recurso visual mudou.

O experimento partiu de Vortex `45d626a`, com esse
[patch exato de integração](platform-reference/vortex-aosp-integration.patch).
Essa mesma correção está aplicada ao `Android.mk` atual.

## Entradas e ferramenta de host

| Entrada | Revisão ou ferramenta |
| --- | --- |
| AOSP build | `5bcb8ef25cbb92b0f6ee9a40fb05bb47b5173774` |
| AOSP prebuilts/sdk | `23f7de5ba433fc82269ba63c203fe0a3eaf4a680`, 22 arquivos oficiais selecionados |
| Java / Jack | JDK 8u504 / Jack 3.36.CANDIDATE |
| acp | Fontes C originais do build r6, compiladas para o host x86_64 |
| zipalign | Android SDK 33.0.2 x86_64, por override explícito do make |

Os arquivos SDK foram comparados com seus objetos Git oficiais. O Makefile
do topo é o `copyfile` legítimo `build/core/root.mk` do manifesto AOSP.
Não se criaram bibliotecas ou âncoras fictícias para satisfazer o build.
Python 2.7 foi extraído localmente para os scripts antigos. O make selecionou
suas regras existentes com Ninja/Soong desabilitados; não se reescreveu o
empacotamento do APK.

O diretório terminou com cerca de 129 MB. Isso comprova a viabilidade desse
módulo isolado neste host, sem estabelecer que a plataforma completa caiba
nos aproximadamente 13 GB livres. O init Android real ainda depende de
bionic, libc++, SELinux, crypto, fs_mgr e outras bibliotecas.

## Identidade e execução

O APK usa a chave de **teste de plataforma AOSP**, sem identidade de produção
ou vínculo com a chave da TV Box. Não deve ser tratado como atualização
assinada para um APK Gradle instalado anteriormente.

O smoke posterior usou Android 7.1.1/API25/x86 em AVD novo, separado das
sessões anteriores. Testou o APK r6 nessa API compatível; não inicializou uma
ROM Android 7.1.2 ou os drivers ARM/Rockchip. LAN com celular, USB físico e
privilégios de energia da futura ROM continuam fora desse smoke.
