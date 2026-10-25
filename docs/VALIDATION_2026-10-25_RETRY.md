# Build 01 — compilação real do APK e emulador API 25

Em 2026-10-25, após a mudança de permissões, downloads e sockets locais passaram
a funcionar. O repositório foi clonado com Git na `main`, base
`d70e93003c65f394652ea55fa5d6471400978c5d`. A correção de ciclo de vida descrita
abaixo integra o APK testado. Os hashes dos arquivos de entrada estão em
[build-inputs.sha256](validation/2026-10-25-retry/build-inputs.sha256).

**O aplicativo foi compilado e executado. A Build 01 completa continua aberta:
nenhuma ROM AOSP foi compilada ou inicializada no RK3229.**

## Ferramentas e artefato

- Temurin JDK 11.0.32.1, Gradle 7.6.4, Android Gradle Plugin 7.4.2.
- Platform SDK 33; a compilação usou build-tools 30.0.3, padrão do plugin.
  Build-tools 33.0.2 também foi instalado após uma falha de download na primeira tentativa.
- Gerenciador SDK command-line 11076708 executado com Java 21, pois exige Java 17+.
  O aplicativo foi compilado com JDK 11.
- Android Emulator 37.2.12, imagem AOSP Android 7.1.1/API 25 x86, sem Play Services.
- Emulação por software (`-accel off`), 1 GiB de RAM, tela 1280×720; sem KVM.

APK debug: `vortex-tv-os-build01-debug.apk`, **42.379 bytes**.
SHA-256: `d3a8ce49928a32a51e4ff63b0bbfefd3ef7109f8ec199b9dacbd1a334e85fde6`.
Assinatura APK v2 verificada; package `os.vortex.tv`, versão `0.1.0-dev`,
minSdk e targetSdk 25. É um APK de desenvolvimento, sem assinatura de plataforma
ou privilégios de energia. O APK e o pacote de evidências foram entregues como
artefatos do workspace; não estão versionados como uma ROM.

## Resultados

| Verificação | Resultado observado |
| --- | --- |
| Suite Python/JVM | 10 testes passam, sem skips, incluindo HTTP real |
| Negativos HTTP ampliados | MIME incorreto, comprimento ausente, chunked e tamanho acima de 512 MiB rejeitados antes do corpo |
| Sessão HTTP | Upload e SHA-256 conferidos; conexão posterior recusada enquanto o harness Java ainda está vivo |
| `:app:assembleDebug` | BUILD SUCCESSFUL; APK íntegro e assinatura verificada |
| `tools/validate_build01.sh` | Testes e compilação passam |
| Home | Abre em 1280×720, mostra data/hora e foco em Instalar APK |
| D-pad | Abre Configurações, Energia, Installer e Meus apps |
| Desligar sem privilégios | Mostra mensagem de operação não autorizada; aplicativo continua funcionando |
| Pareamento QR | Imagem e endereço exibidos, página HTTP responde no Android |
| Interromper e retomar QR | Retorna à tela inicial; novo pareamento gera outro endereço |
| Arquivo inválido no Android | Rejeitado com HTTP 415 |
| APK assinado no Android | Recebido com HTTP 200 e encaminhado ao PackageInstaller |
| Fontes desconhecidas desativadas | Bloqueio de segurança do Android observado |
| Confirmação de instalação | APK de teste ausente antes da confirmação; instalado após selecionar INSTALL pelo D-pad |
| Meus apps | Vortex Smoke App aparece e abre pelo D-pad; tela Installer smoke OK |
| Selecionar APK USB | Abre DocumentsUI; pendrive e cópia USB física não testados |

O APK de teste separado tem package `os.vortex.smoke`, rótulo Vortex Smoke App,
8.535 bytes e SHA-256
`5461107bd1f4ae9064823cfa3699abc02be71053cd3c5751434000ed591eabbf`.
A opção de fontes desconhecidas foi habilitada apenas no emulador para o teste
positivo. Não foi usada instalação silenciosa para esse APK.

O servidor escuta somente no IPv4 privado selecionado. Um encaminhamento TCP
ADB comum não alcançou esse socket porque tenta conectar ao loopback do Android.
As requisições funcionais foram feitas com `adb shell -T toybox nc`, ao IPv4 da
própria interface emulada, com cabeçalhos HTTP e corpo do APK. Isso valida o
transporte no Android e sua integração com PackageInstaller, **não** o acesso
de um celular externo ou o escaneamento óptico do QR.

## Alterações

InstallerActivity agora marca um pareamento encerrado em `onStop()` e retorna
à tela inicial em `onStart()`, sem iniciar outro servidor automaticamente.
Antes, a Activity retomada podia continuar mostrando o QR de um socket fechado.
A cópia USB em andamento é preservada. O fluxo de sair para Settings, voltar
e pedir outro QR foi exercitado no emulador.

Os testes HTTP ganharam negativos de MIME, enquadramento e limite de tamanho,
além de verificar uso único sem confundir encerramento do servidor com saída
da JVM. Nenhum código de firmware foi selecionado para gravação.

## Evidências e reprodução

- [Compilação](validation/2026-10-25-retry/assemble.log)
- [Testes](validation/2026-10-25-retry/tests.log)
- [Versões, assinatura e metadados do APK](validation/2026-10-25-retry/artifact-metadata.log)
- [Transferência no Android](validation/2026-10-25-retry/emulator-transfer.log)
- [Confirmação explícita](validation/2026-10-25-retry/installer-confirmation.log)
- [Verificações das telas capturadas](validation/2026-10-25-retry/emulator-checks.log)

Com JDK 11, Gradle 7.6.x, SDK 33 e ANDROID_HOME configurados:

```sh
bash tools/validate_build01.sh
adb install app/build/outputs/apk/debug/app-debug.apk
adb shell am start -W -n os.vortex.tv/.HomeActivity
```

No emulador, navegar usando eventos DPAD, interromper/retomar a tela QR e
enviar um APK assinado. Testar primeiro o bloqueio de fontes desconhecidas,
depois permitir essa origem no ambiente de teste e confirmar INSTALL na TV.
Não registrar apenas HTTP 200 como prova de instalação.

## Pendências

- Celular externo, leitura óptica do QR e alcance em Wi-Fi/Ethernet reais.
- Pendrive físico, remoção durante cópia, pouco armazenamento, cancelamento de
  instalação e cobertura mais ampla de interrupções e desempenho.
- O símbolo Unicode de energia não tem glifo nessa imagem Android; o rótulo e
  o menu funcionam. O acabamento visual precisa de ícone compatível.
- ROM: faltam BSP completo, manifesto de fontes fixado, kernel/config/DTB,
  HALs e blobs adequados à placa. Veja o [mapa de fontes](../rom/AOSP_SOURCE_MAP.md).
- Diagnóstico físico de flash, DDR/loader/trust, Wi-Fi, IR e recuperação;
  posterior boot e testes HDMI/áudio/GPU/VPU/rede/USB/energia no RK3229.

Não há medição válida do tamanho da ROM ou RAM ociosa da TV Box. O emulador x86
não valida os drivers ARM/Rockchip. Não houve gravação física, compilação de
ROM ou uso de GitHub Actions.
