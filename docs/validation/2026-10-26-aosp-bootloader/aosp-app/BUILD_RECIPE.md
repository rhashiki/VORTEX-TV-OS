# VortexHome pelo mecanismo AOSP Nougat real

Resultado: o alvo `VortexHome` foi compilado pelo GNU make e Jack do AOSP
7.1.2_r6, usando `tapas arm eng VortexHome`. Não foi executado Gradle nesse
experimento. Não é uma compilação da plataforma Android ou uma ROM RK3229.

O APK final está em `artifacts/VortexHome-aosp-7.1.2-r6.apk`: 44.366 bytes,
SHA-256 `81fc16aa89e523088ac8c7a6e334a2c670745d6a4e673a30a986ba6af04867d4`.
ZIP, assinatura APKv2, alinhamento de 4 bytes e min/target SDK 25 passaram. O certificado é
**a chave pública de teste de plataforma do AOSP**, não uma identidade de
produção ou a chave da TVBox. Não houve instalação, emulador ou boot físico.

## Fontes fixadas

- `platform/build`: `5bcb8ef25cbb92b0f6ee9a40fb05bb47b5173774`, tag oficial
  `android-7.1.2_r6`, checkout Git completo e limpo (cerca de 14 MB).
- `platform/prebuilts/sdk`: `23f7de5ba433fc82269ba63c203fe0a3eaf4a680`.
  Foram adquiridos só 22 arquivos oficiais (70.061.046 bytes), incluindo o
  android.jar API 25, Jack 3.36.CANDIDATE e os executáveis necessários.
  `evidence/sdk-git-object-verification.json` compara cada Git blob SHA-1 ao
  objeto da árvore oficial fixada e registra SHA-256. Não é checkout completo.
- Vortex: commit `45d626a4bc508b49b8863bd67e2ce9f2f17554d5`, com somente o
  patch proposto `vortex-aosp-integration.patch` aplicado na cópia isolada.

O `Makefile` no topo é uma cópia byte a byte de `build/core/root.mk`, exatamente
como declara o `<copyfile>` do manifesto AOSP r6; não é uma âncora fabricada.
Não se criaram stubs ou substitutos de bibliotecas para satisfazer o make.

## Erros reais encontrados

- Python3 não interpreta `findleaves.py` dessa versão; Python 2.7.18 foi
  provisionado localmente com quatro pacotes do arquivo oficial Debian,
  sem alterar o banco de pacotes do sistema.
- O Android.mk do Vortex usava `LOCAL_JACK_ENABLED := true`. O parser r6 aceita
  `full`, `incremental` ou `disabled`. O patch usa `full`.
- A versão do app vinha apenas do Gradle. Sem ajuste, AOSP aplicava
  versionCode 25 e versionName de build do Android. O patch passa explicitamente
  `--version-code 1 --version-name 0.1.0-dev` pelas opções do aapt para conservar
  os mesmos valores do build Gradle.
- O `acp` pré-compilado oficial é i386 e retornou Exec format error neste host.
  Foi compilado para x86_64 o **acp real das fontes C não modificadas do r6**.
  `CopyFile.c` mantém `-Wall -Werror`; acp.c usa `-Wall` e conserva dois avisos
  de variáveis não usadas, sem ocultá-los. O Android.mk de acp não impõe Werror.
- `zipalign` r6 também é i386. O make recebeu um override explícito para o
  zipalign x86_64 do Android SDK 33.0.2 já instalado. Logo não é um ensaio com
  todos os prebuilts de host r6 intactos. Java, Jack, aapt, API e regras APK
  permaneceram r6. Nenhuma regra AOSP de empacotamento foi reescrita.

`attempt-01.log` registra uma falha inicial do harness com nounset, corrigida
antes da avaliação do AOSP; não é atribuída ao produto. `attempt-02` a `04`
registram os bloqueios seguintes; `attempt-05` é o primeiro sucesso e `06-final`
o sucesso após corrigir a versão do APK. A primeira saída foi preservada como
histórica e não é o artefato final.

## Repetir o experimento

Recriar o checkout build e o subconjunto SDK nos pins acima, reproduzir o
`copyfile` oficial e colocar uma cópia Vortex 45d626a sob vendor/vortex/home.
Aplicar o patch proposto **nessa cópia descartável**, conferindo revisão e
`git apply --check`; `evidence/patch-replay.json` registra o replay byte a byte.
`fetch_sdk_subset.py` e `verify_sdk_provenance.py` registram os arquivos oficiais
adquiridos; os scripts usam os caminhos concretos deste workspace.

Compilar o helper de host a partir de build r6, sem alterar suas fontes:

```sh
gcc -O2 -Wall -Werror -I tree/build/libs/host/include \
  -c tree/build/libs/host/CopyFile.c -o host-bin/CopyFile.o
gcc -O2 -Wall -I tree/build/libs/host/include \
  tree/build/tools/acp/acp.c host-bin/CopyFile.o -o host-bin/acp
```

Selecionar JDK 8 e o Python 2 local. Usar um diretório `OUT_DIR` exclusivo.
O script `run-app-build.sh` contém os caminhos exatos usados no sucesso final:

```sh
export JAVA_HOME=/workspace/android-toolchain/jdk8u504-b01
export PATH=/workspace/build01-platform-next/aosp-app/host-bin:$JAVA_HOME/bin:$PATH
export USE_NINJA=false USE_SOONG=false JACK_SERVER=false
export JACK_REPOSITORY=/workspace/build01-platform-next/aosp-app/tree/prebuilts/sdk/tools/jacks
export JACK_HOME=/workspace/build01-platform-next/aosp-app/jack-home
export CLIENT_SETTING=/workspace/build01-platform-next/aosp-app/jack-client-settings
export OUT_DIR=/workspace/build01-platform-next/aosp-app/out
cd /workspace/build01-platform-next/aosp-app/tree
source build/envsetup.sh
tapas arm eng VortexHome
make -j2 ACP=/workspace/build01-platform-next/aosp-app/host-bin/acp \
  ZIPALIGN=/workspace/android-toolchain/sdk/build-tools/33.0.2/zipalign VortexHome
```

São opções suportadas do fluxo legado. Desabilitar Ninja/Soong aqui seleciona
as regras GNU make existentes; não transforma uma tradução manual em AOSP.
Jack foi executado localmente sem daemon. A primeira execução criou o arquivo
padrão ~/.jack-settings; a receita final usa CLIENT_SETTING/JACK_HOME locais,
sem alterar HOME ou ler chaves/certificados de um servidor Jack existente.

O arquivo `evidence/aosp-app-report.json` registra versões, verificações, hashes,
proveniência e limites; `evidence/apk-*.log` contém as verificações do artefato.

## Capacidade e limite da entrega

O diretório terminou com aproximadamente 129 MB; durante a operação foi observado
cerca de 156 MB. É muito abaixo do teto de 2 GiB e manteve mais de 8 GiB livres. Não houve
limpeza de artefatos anteriores ou sincronização AOSP completa. O manifesto
oficial r6 tem 541 projetos; esse número não descreve o subconjunto do app.

Isso demonstra que **o módulo VortexHome pode ser validado pelo AOSP** neste
host, com as compatibilidades de ferramentas relatadas. Não resolve a escolha
da plataforma Rockchip, HALs, ABI dos módulos, init/ramdisk, bootloader/DDR/trust,
layout de cartão ou boot físico. O init Android real examinado depende de 20
bibliotecas estáticas, incluindo bionic, libc++, SELinux, crypto e fs_mgr; o
checkout system/core isolado não fornece esse fechamento de dependências.

Os requisitos atuais AOSP de 400 GB/64 GB se aplicam a versões modernas e não foram
usados como mínimo provado de Nougat. A documentação histórica AOSP citava
100 GB para checkout e 150 GB para um build; também não é uma medição deste BSP.
O host atual tem somente 32 GB totais e aproximadamente 13 GB livres: não se iniciou
um sync completo com base em uma expectativa não medida de caber nesse espaço.
Nenhuma imagem Android completa, mídia SD ou validação de hardware foi produzida.
Nenhum GitHub Actions foi consultado, criado ou executado.
