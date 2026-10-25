# Build 01 — atualização ao vivo e cancelamento de transferências

Base sincronizada: `cb249f207f884d8fe11d21964175f7e97a8e3e9e`, em 2026-10-25.
As correções funcionais começaram sobre `b69ddff`; antes da publicação foram
incorporadas e lidas as três atualizações oficiais de marca (`5d7e9a8`,
`ce0aa03`, `cb249f2`). Nenhuma delas foi sobrescrita.
A Home continua sem gaveta: os apps de usuário lançáveis aparecem diretamente
na grade. Esta etapa melhora o aplicativo; não compila ou aprova a ROM RK3229.

## Correções

**Home atualizada enquanto está aberta.** Um receiver registrado apenas enquanto
a tela está iniciada acompanha instalação, remoção, alteração e substituição de
pacotes. Eventos próximos são agrupados por 150 ms; a remoção intermediária de
uma atualização é ignorada. A assinatura dos apps evita reconstruções sem
mudanças, e foco/rolagem são preservados. No emulador, remover, instalar e
atualizar Grid 15 via ADB atualizou a Home sem sair dela.

**Transferência cancelada de verdade.** O servidor anterior fechava só a porta
de escuta. Uma reprodução JVM demonstrou HTTP 200 e onComplete depois que close
já havia retornado. Agora o socket conectado também é fechado; as leituras
conferem cancelamento antes e depois de retornar, e o arquivo parcial é removido.
A entrega e close são serializados: se close ocorrer primeiro, não há entrega;
um callback já iniciado termina antes de close retornar.

O prazo total de pareamento usa relógio monotônico e vale também durante
cabeçalhos e corpo. Enviar bytes lentamente não renova os 15 minutos. Um
construtor interno com prazo menor permite testes de expiração sem alterar o
relógio nem esperar 15 minutos. Ele não altera o prazo do fluxo de produção.

**Ciclo de vida do instalador.** Voltar do QR retorna à tela inicial do
instalador. Ao pausar a Activity, o pareamento já é cancelado: esperar apenas
onStop deixava uma janela durante a troca de telas. Callbacks atrasados são
descartados por geração de pareamento e estado da tela, sem iniciar instalação
fora dela. Não é possível iniciar outro recebimento enquanto uma cópia está em
andamento. Erros de seleção/cópia ficam visíveis na tela, sem depender de toast.

**Identidade oficial preservada.** Ícone e banner em vetor que estavam em
preparação local foram retirados ao ler a nova orientação: eles não eram as
imagens aprovadas. Não foram publicados nem fazem parte do APK entregue.
As três miniaturas de 96 pixels continuam apenas na documentação. Os originais
JPEG e o MP4 oficial de quatro segundos não foram encontrados no workspace
nem estão versionados no GitHub. O título textual anterior da Home permanece
até ser possível integrar e conferir o logo verdadeiro; não foi criada marca
substituta. A integração visual continua pendente.

O novo [procedimento de importação](OFFICIAL_ASSET_IMPORT.md) confere os hashes
dos três JPEGs antes de criar fontes/derivados, preserva os originais e recusa
substitutos ou sobrescrita de arquivos diferentes. O conversor de boot recebeu
`--official`: exige o MP4 aprovado, 12 fps e 48 quadros 720p, com escrita atômica
do ZIP. São preparações testadas com fixtures; não houve processamento dos
originais reais nem aceite visual da marca nesta etapa.
O antigo gerador de arte provisória também foi desativado: não escreve mais
um ZIP e orienta a usar o conversor do MP4 oficial.

## Resultados

| Verificação | Resultado |
| --- | --- |
| Python/JVM | 43 testes passam, sem skips: 25 do aplicativo/protocolo e 18 das ferramentas de assets |
| Novos testes com sockets | Cancelar cabeçalho/corpo, limpar arquivo parcial, expirar tráfego lento e recuperar após cabeçalho inválido |
| Compilação APK | Passa |
| Compilação Java com API 25 real | 13 arquivos passam, com R gerada e stubs de lambda |
| Android lint | 0 erros e 7 avisos, após as exceções pontuais descritas abaixo |
| Home continuamente aberta | Instalação/remoção/substituição refletidas, com foco preservado |
| Arquivo vazio pelo SAF | Rejeitado com mensagem persistente e cache temporário removido |
| Arquivo que não é APK | Rejeitado antes da confirmação Android; cache removido |
| Upload parcial + Voltar | Conexão encerrada, sem HTTP 200 nem arquivo parcial restante |
| Upload parcial + outra tela | Mesmo resultado ao pausar; retorno à tela inicial sem confirmação atrasada |
| Upload completo de APK assinado | Confirmação explícita do PackageInstaller e cancelamento pelo D-pad; retorno sem QR antigo |

Os testes Android usam emulador AOSP 7.1.1/API 25 x86, por software, e fixtures
descartáveis. Não validam telefone em Wi-Fi real, pendrive físico ou drivers
Rockchip. O teste de tráfego lento usa prazos curtos no JVM; não foi uma espera
de 15 minutos na TV Box.

Cancelamento, upload completo e SAF foram repetidos no APK final de hash
`bedc7e95…`. A captura final da Home confirma a grade sem gaveta e o título
textual anterior. O teste de eventos com a Home continuamente aberta foi
feito antes da retirada dos vetores provisórios; os arquivos Java responsáveis
são idênticos aos da build final. Não foi repetido apenas por essa mudança de
recursos/manifesto.

Uma amostra de `am start -W` no emulador registrou ThisTime 2309 ms,
TotalTime 6491 ms e WaitTime 2447 ms; o PSS do processo foi 9615 KB.
São observações isoladas do APK com fixtures, em emulação por software;
não medem RAM ociosa do sistema, boot ou desempenho RK3229. O log
`AndroidRuntime:E` não registrou erros durante a regressão final.

## Lint e critérios de aprovação

`tools/validate_build01.sh` agora executa também `:app:lintDebug`, mantendo a
falha por erros. A primeira execução revelou ausência de banner TV e ícone.
Esses recursos continuam pendentes dos originais oficiais; não se utilizou
uma arte substituta para satisfazer a ferramenta. Não foi criada uma baseline
para esconder todos os achados.

Três exceções são deliberadas e pontuais:

- `ProtectedPermissions`, apenas nas solicitações REBOOT/SHUTDOWN do manifesto:
  são destinadas à integração como aplicativo de sistema e continuam sem grant
  no APK debug comum.
- `ExpiredTargetSdkVersion`, no Gradle: esse requisito de publicação Google Play
  não corresponde ao componente local da ROM Nougat, cujo alvo permanece API 25.
- `MissingTvBanner`, somente na aplicação do manifesto, temporária: permite
  validar o APK funcional sem publicar miniatura ou redesenho proibidos.
  Remover ao integrar o banner oficial. O APK atual não tem a identidade de TV
  completa; passar lint com essa exceção não é aceite de branding.

Os sete avisos permanecem no relatório: DefaultLocale em mensagem de erro do QR
vendorizado; OldTargetApi; duas ocorrências GradleOverrides pela declaração
duplicada necessária ao caminho AOSP; MissingApplicationIcon, pendente da fonte;
UnspecifiedImmutableFlag no callback PackageInstaller legado, que precisa ser
mutável para receber status; UsableSpace, cuja alternativa sugerida exige API 26.
Não se elevou o target nem se tornou o PendingIntent imutável apenas para
silenciar avisos e quebrar a compatibilidade/retorno da instalação.

## Artefato e evidências

APK debug: **69.098 bytes**, minSdk/targetSdk 25, assinatura v2 verificada.
SHA-256: `bedc7e95321c533e650f198f14e737f611aa765de5aebc6c46f930725fa9074b`.
JDK 11.0.32.1, Gradle 7.6.4 e AGP 7.4.2.

- [Validação e compilação](validation/2026-10-25-robustness/validation.log)
- [Lint](validation/2026-10-25-robustness/lint.txt)
- [Compilação com API 25](validation/2026-10-25-robustness/api25.log)
- [Reprodução do defeito original](validation/2026-10-25-robustness/baseline-close.log)
- [Atualização da Home](validation/2026-10-25-robustness/home-live.log)
- [Arquivos inválidos](validation/2026-10-25-robustness/invalid-files.log)
- [Cancelamento de upload no Android](validation/2026-10-25-robustness/android-upload-cancel.log)
- [Upload completo e confirmação](validation/2026-10-25-robustness/full-upload.log)
- [Conferência final da Home](validation/2026-10-25-robustness/home-current.log)
- [Amostra de abertura e memória](validation/2026-10-25-robustness/performance.log)
- [AndroidRuntime](validation/2026-10-25-robustness/android-runtime.log)
- [Metadados do APK](validation/2026-10-25-robustness/artifact-metadata.log)
- [Hashes de entrada](validation/2026-10-25-robustness/build-inputs.sha256)

## Pendências da Build 01

Continuam pendentes originais oficiais e aceite visual, BSP completo, revisões
e blobs identificados, kernel/DTB e configuração de placa, armazenamento adequado à compilação e diagnóstico da
unidade RK3229. Não houve compilação AOSP, gravação física, boot ou testes dos
drivers. Ainda faltam testes com pouco armazenamento e interrupções de USB/provider real.
Não foi usado GitHub Actions. O APK não é uma ROM flashável.
