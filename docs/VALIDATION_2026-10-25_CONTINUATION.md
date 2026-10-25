# Build 01 — continuação: API 25 e preparação do BSP

Base: `d9992eb04c4f320f0ff00b8931667a6b2b2e9a42`. Trabalho realizado em
2026-10-25, sem GitHub Actions. O APK continua experimental; nenhuma ROM AOSP
foi compilada ou inicializada na placa RK3229.

## Mudanças e resultados

- Ícone de energia substituído por vetor Android nativo, conferido visualmente
  no emulador API 25. O desenho não depende mais de um glifo ausente na fonte.
- Manifesto solicita `android.permission.SHUTDOWN`, exigida pela Activity de
  desligamento. Solicitá-la não concede privilégios ao APK debug: o grant e as
  ações de energia continuam dependendo da assinatura/configuração da ROM.
- Após receber o APK por HTTP, InstallerActivity fecha o pareamento e mostra
  a tela inicial antes de abrir PackageInstaller. A confirmação pode ser
  translúcida e não causar `onStop()`: por isso a correção anterior de retomada
  não bastava para remover o QR consumido após cancelar a instalação.
- No emulador, o APK de teste foi enviado, a instalação foi cancelada pelo
  D-pad, o pacote permaneceu ausente e o Vortex voltou à tela inicial sem QR.
- **20 testes Python/JVM passaram, sem skips**, incluindo nove testes do novo
  pré-verificador e a integração HTTP. O script de validação compilou o APK.
- Os **13 arquivos Java** também compilaram contra as classes reais de boot
  do SDK Android API 25, com a classe R gerada pelo AGP e stubs de lambda do
  build-tools. Isso detecta referências a APIs ausentes nessa base; não executa
  Jack e não substitui a compilação do módulo dentro do AOSP.
- A seleção de um APK real pelo Storage Access Framework, no armazenamento
  emulado, chegou ao PackageInstaller. Após confirmação, o hash do APK instalado
  correspondeu ao arquivo escolhido. Isso não valida pendrive físico.

## Home sem gaveta de aplicativos

Conforme solicitado pelo proprietário, não há mais botão Meus apps nem tela
separada de aplicativos. AppsActivity foi removida do manifesto, do código e do
DEX compilado. Todos os apps de usuário com Activity lançável ficam diretamente
na Home, junto das três ações de instalação, configurações e energia.

A grade usa ícones dos aplicativos, rótulos acessíveis e rolagem vertical.
No emulador havia 18 apps lançáveis: 15 fixtures descartáveis e três apps de
teste já instalados. Todos ficaram acessíveis na Home; o D-pad alcançou a última
linha, abriu Vortex Smoke App diretamente e preservou o foco ao retornar.
As fixtures não são incluídas no APK Vortex nem na futura ROM.

A atualização da lista considera componente, rótulo e lastUpdateTime, e não
apenas a quantidade de apps. A tela evita reconstrução quando nada mudou e
restaura o foco e a posição quando a lista muda.
Uma atualização de Grid 15 para Grid 15 atualizado, mantendo a mesma lista de
pacotes, apareceu na Home após a retomada e preservou o foco no app selecionado.

Para repetir a verificação de APIs, instalar a plataforma 25 e build-tools
33.0.2 junto da cadeia APK documentada e executar:

```sh
bash tools/validate_build01.sh
bash tools/validate_android_api25.sh
```

## Artefato desta continuação

`vortex-tv-os-build01-debug.apk`: **66.519 bytes**.
SHA-256: `35160cf8e9cb0cd5956accafeb01619c9f7ba11605bb293f5a67dfd3dbe7d3b9`.
Package `os.vortex.tv`, versão `0.1.0-dev`, minSdk/targetSdk 25, assinatura debug
APK v2 verificada. Compilação com JDK 11.0.32.1, Gradle 7.6.4 e AGP 7.4.2.
O APK anterior foi preservado no pacote de evidências da tentativa anterior.

## Preparação AOSP

Foi instalado e conferido o Temurin **JDK 8u504**, separado da cadeia JDK 11
do aplicativo. O SHA-256 do arquivo de distribuição foi verificado contra os
metadados do fornecedor antes da extração. Isso prepara a seleção Java para
Nougat; não afirma que todas as dependências de host do BSP estejam prontas.

O novo `tools/aosp_preflight.py` inspeciona somente leitura um perfil da árvore
comunitária `rk322x_box`. Ele confere âncoras AOSP/device/vendor/kernel, versões,
JDK 8 e um manifesto resolvido com commits completos, e inventaria os arquivos
explícitos por SHA-256. Não executa scripts do BSP, não baixa fontes e não grava
no dispositivo. Projetos aninhados também precisam de revisões fixadas.

```sh
python3 tools/aosp_preflight.py /caminho/BSP \
  --manifest-lock /caminho/evidencias/manifest-lock.xml --json
```

Os testes usam árvores sintéticas para conferir rejeições e comportamento
somente leitura; uma fixture não representa um BSP aprovado. Mesmo `exit 0`
significa apenas `preflight_only`, nunca ROM ou hardware validados.

A execução no workspace real retornou **exit 2 / blocked**, com JDK 8 aprovado
e ausência de todas as 12 âncoras de fontes, além do manifesto resolvido. Ainda
faltam árvore AOSP 7.1.2, device/rockchip, vendor/rockchip, kernel/DTB e revisões
fixadas. Havia aproximadamente 23 GB livres antes da instalação adicional;
essa capacidade não foi validada para uma compilação AOSP completa.

O [runbook de compilação](../rom/AOSP_BUILD_RUNBOOK.md) explica como conferir um
BSP externo, integrar VortexHome e tentar primeiro o módulo do aplicativo,
antes da imagem completa. Ele não inventa um alvo `lunch` para R329Q_V8.0.

## Evidências

- [Validação completa e compilação](validation/2026-10-25-continuation/validate-build01.log)
- [Compilação contra Android 25](validation/2026-10-25-continuation/api25.log)
- [Cancelamento e retorno sem QR consumido](validation/2026-10-25-continuation/cancellation.log)
- [Seleção e cópia pelo SAF](validation/2026-10-25-continuation/saf-copy.log)
- [Home, D-pad, rolagem e abertura de app](validation/2026-10-25-continuation/home-grid.log)
- [Atualização sem alterar a quantidade de apps](validation/2026-10-25-continuation/home-update.log)
- [Pré-verificação no workspace real](validation/2026-10-25-continuation/aosp-preflight.json)
- [JDK 8](validation/2026-10-25-continuation/aosp-jdk8.log)
- [Metadados do APK](validation/2026-10-25-continuation/artifact-metadata.log)
- [Hashes dos arquivos de entrada do APK](validation/2026-10-25-continuation/build-inputs.sha256)

## O que impede fechar a ROM

Precisamos de um BSP completo com procedência e revisões identificadas e de
diagnóstico da unidade: FlashID, NAND/eMMC, geometria/partições, DDR/loader/trust,
Wi-Fi exato, IR e drivers/HALs HDMI/GPU/VPU/áudio. Não há evidência suficiente
para selecionar esses componentes somente pelo nome RK3229 ou R329Q_V8.0.
Depois de compilar, continuam obrigatórios boot físico e os testes do
[checklist da placa](../rom/BOARD_BRINGUP_CHECKLIST.md).

Celular externo e QR óptico, pendrive físico, pouco armazenamento, interrupção
de cópia e medições da TV Box ainda exigem validação. Os testes desta sessão
usam Android 7.1.1/API 25 x86 em software e não aprovam drivers Rockchip.
