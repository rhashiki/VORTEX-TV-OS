# Build 01 — validação na nuvem em 2026-10-25

**Build 01 não concluída. Nenhum APK ou ROM foi gerado.**

Base examinada: `053b5d63acb467873ad02bce576e250dab6375fd`, branch `main`.
O clone falhou porque o proxy do terminal não aceitou conexão. Os 38 arquivos
foram recuperados pelo conector GitHub, fixados nesse commit, e cada conteúdo
foi conferido com o SHA-1 Git de seu blob antes das alterações. Não se trata
da cópia de referência citada no relatório anterior.

## Ambiente e bloqueios observados

- Linux x86_64; aproximadamente 9,7 GiB de RAM e 30 GiB de disco livre.
- OpenJDK `21.0.12.1`; comando `javac` ausente, mas módulo `jdk.compiler` presente.
- Compilador utilizável por `java -m jdk.compiler/com.sun.tools.javac.Main`.
- JDK 11, Gradle, Android SDK, ADB e emulador não estavam disponíveis.
- `/dev/kvm` ausente. Isso impede aceleração KVM; não prova impossibilidade de emulação por software.
- `git clone` e `curl` falharam com `Failed to connect to proxy port 8080`.
  Não foi possível baixar a cadeia Android. Uma tentativa de solicitar acesso
  adicional ficou pendente e foi interrompida; após a retomada do ambiente,
  a mesma falha de proxy persistiu.
- Abrir um ServerSocket em `127.0.0.1` falhou com
  `java.net.SocketException: Operation not permitted`. Portanto, o protocolo
  HTTP não pôde ser validado neste sandbox.

## Resultados reais

| Verificação | Resultado |
| --- | --- |
| Hashes dos 38 arquivos originais | Conferidos antes das alterações |
| Testes de contrato do código original | 8 passam; 1 falha por comentário contendo WebView |
| Testes de contrato após correção | 9 passam |
| Integração HTTP após correção | Falha ao abrir socket; não aprovada |
| Suite completa após correção | 10 testes, 1 falha; exit 1 |
| Compilação Java independente do Android | Passa com avisos de bootstrap e Java 8 obsoleto |
| Sintaxe Bash e Python | Passa |
| APK Android | Bloqueado por ferramentas ausentes e proxy indisponível |
| Home, D-pad, confirmação PackageInstaller, USB, ciclo de vida | Não executados no Android |
| QR via celular em LAN real | Não executado |
| Compilação AOSP e boot RK3229 | Não executados |

A compilação Java incluiu os quatro arquivos QR, LanApkServer, NetworkAddress e
o harness HTTP. Foi usada a opção `-source 8 -target 8`, com classes de saída
em `/workspace/build01-evidence/java8-classes`. Isso verifica sintaxe e geração
de bytecode, **não** disponibilidade de APIs no Android 25 ou no JDK 8.
`--release 8` não está disponível nesta instalação, que não contém os recursos
de compatibilidade necessários. As Activities e classes Android não foram compiladas.

Logs desta execução: [suite completa](validation/2026-10-25/final-validation.log),
[compilação Java](validation/2026-10-25/java8-compilation.log) e
[verificações de fonte](validation/2026-10-25/source-checks.log).

## Correções consolidadas

- O teste de dependências ignora comentários Java, preservando literais. A
  documentação de Ui mencionava a ausência de WebView e provocava falso positivo.
- O corpo de upload do teste agora começa com os quatro bytes ZIP `50 4b 03 04`.
  Antes continha barras e letras literais, que o servidor corretamente rejeitaria.
  Essa etapa do teste ainda depende de executar o servidor fora deste sandbox.
- Inicialização do harness tem espera limitada e informa stderr em caso de falha;
  os pipes são fechados também quando o processo já terminou.
- O manifesto declara minSdk/targetSdk 25 para o caminho AOSP, que não lê Gradle.
  Android.mk explicita Java 8 e Jack para lambdas/referências a métodos no Nougat.
  Esses ajustes são preparação de integração e ainda exigem compilação AOSP real.

## Próxima execução reproduzível

Em ambiente que permita downloads HTTPS e sockets de loopback, instalar JDK 11,
Gradle 7.6.x, SDK 33 e build-tools compatíveis; configurar ANDROID_HOME e executar:

```sh
bash tools/validate_build01.sh
```

Só publicar um APK como compilado após registrar o comando concluído, tamanho e
SHA-256 do arquivo. Depois, executar emulador API 25 e testar Home, foco por D-pad,
Settings, falhas de energia sem privilégios, QR, upload válido/inválido,
confirmação/cancelamento da instalação, USB, lançamento de apps e retorno às telas.
O teste HTTP não deve ser marcado como aprovado quando ignorado ou bloqueado.

## Integração AOSP 7.1.2 / R329Q_V8.0

O repositório fornece um módulo de aplicativo e um fragmento de produto; não
contém árvore AOSP, produto Rockchip completo, kernel, DTB, loader ou vendor blobs.
Não há dependências de firmware suficientes para produzir uma imagem instalável.
Não foram baixadas ou verificadas árvores BSP externas nesta sessão.

Antes de compilar a ROM, obter uma revisão identificada e licenciada do BSP
RK322x compatível com Android 7.1.2, toolchain legado/JDK 8 e espaço adicional.
Integrar o módulo em `vendor/vortex/home`, herdar `rom/vortex_product.mk` a partir
de um produto de placa validado e compilar VortexHome antes da imagem completa.
O aplicativo precisará de confirmação explícita das permissões de sistema e do
comportamento do PackageInstaller nessa ROM. O fragmento não define um alvo
`lunch` nem torna outra placa compatível.

**Dependem da TV Box física:** FlashID, NAND/eMMC e geometria, capacidade e mapa
de partições, revisão do SoC, loader DDR/trust, DTB, módulo/firmware Wi-Fi exatos,
IR e HALs HDMI/GPU/VPU/áudio. Acesso ao hardware ou dumps identificados é
necessário para conferir esses componentes; não presumir compatibilidade de V8.1.
Confirmar recuperação Loader/MaskROM antes de qualquer escrita. Após uma futura
compilação, boot e testes dos drivers continuam obrigatórios na placa real.

Nenhum GitHub Actions foi criado, consultado ou executado. Nenhuma gravação na
TV Box foi realizada. Não há medição de RAM Android, tamanho de ROM ou boot.
