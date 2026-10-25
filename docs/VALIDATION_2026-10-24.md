# Validação disponível — 24/10/2026

## Executado neste ambiente

1. JDK 21 local: compilação bem-sucedida de uma **implementação local reforçada de referência** do transportador Java `LanApkServer`, usando `javac --release 8`.
2. Testes HTTP reais em localhost dessa implementação de referência: 6 testes aprovados (página, token incorreto, origem divergente, carga não ZIP, tamanho acima de limite, upload íntegro e SHA-256).
3. Testes estáticos do pacote inicial local: 7 aprovados após ajustar uma regra antiga que proibia todo servidor HTTP.
4. Boot animation otimizada derivada do vídeo enviado: arquivo ZIP verificável, 73 PNGs 1280×720, 12 FPS, parte inicial única e último frame em loop; 6.102.991 bytes (~5,82 MiB).
5. Revisão remota de arquivos da branch: leitura e atualização pelo GitHub connector.

## Não executado ou comprovado

- **Não foi executada a suíte da branch do GitHub em um checkout exato**: os arquivos do conector GitHub não são automaticamente montados no runner local sem rede. O teste local cobriu uma implementação de referência equivalente, não o SHA remoto.
- Não houve build com Android SDK: SDK e Gradle não estão instalados neste runner.
- Não houve emulador nem teste físico no RK3229 (flash, Wi-Fi, controle infravermelho, HDMI, áudio, bootloader).
- Não houve verificação de instalação de APK Android real pelo PackageInstaller.
- A boot animation foi testada estruturalmente, ainda não no boot real do MXQ.

## Política de aprovação

Nenhuma build está aprovada para merge em `main` ou gravação na TV Box até compilação/testes reais. Não criar nem executar GitHub Actions.
