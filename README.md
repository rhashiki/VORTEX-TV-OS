# Vortex TV OS

Firmware experimental minimalista para **MXQ PRO 4K 5G / R329Q_V8.0** (Rockchip RK322x, ARMv7, ~1 GB DDR3).

**Estado atual: APK debug compilado e testes funcionais parciais no emulador Android API 25. Não é uma ROM flashável nem foi validado no RK3229 físico.**

Resultados e limites: [continuação e preparação AOSP](docs/VALIDATION_2026-10-25_CONTINUATION.md) · [primeira compilação e emulador](docs/VALIDATION_2026-10-25_RETRY.md).

## Escopo do produto
- Home 720p, gradiente roxo/azul neon, data/hora, D-pad e ações de energia.
- Uma aplicação de usuário de fábrica: Home + Vortex App Installer unificados.
- Enviar APK do celular por QR Code e HTTP local temporário, ou selecionar de USB.
- Android PackageInstaller instala com confirmação na TV. Todos os apps de usuário aparecem diretamente na Home, sem gaveta.
- Boot animation baseada no vídeo fornecido pelo proprietário, sem nuvem.
- Sem Bluetooth, Google Play Services ou Vortex App Store.

## Implementações no repositório
- `app/`: Java nativo API25; sem WebView, AndroidX ou runtime Kotlin.
- `app/src/main/java/os/vortex/tv/LanApkServer.java`: upload local em streaming, segredo temporário, SHA-256, restrições de tamanho, expiração e origem.
- `app/src/main/java/os/vortex/tv/ApkInstaller.java`: instalação via PackageInstaller Session API25, confirmada na TV.
- `app/src/main/java/io/nayuki/qrcodegen/`: gerador QR puro Java (MIT), licença preservada nos arquivos.
- `tools/bootanimation_from_video.py`: converter MP4 oficial para `bootanimation.zip` compactado.
- `rom/`: fragmentos AOSP e inventário do hardware. **Não contém drivers proprietários ou bootloader!**
- `tests/`: testes estáticos e integração HTTP local independente.

## Compilar APK de desenvolvimento
Android Studio/SDK 33, JDK 11, Android Gradle Plugin 7.4.2 e Gradle compatível (não há wrapper incluído):

```sh
gradle :app:assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Na ROM final, o aplicativo deve ser integrado à imagem AOSP e o permissionamento de energia validado. APK avulso não possui privilégios de reinicialização.

## Testes independentes — sem GitHub Actions
```sh
python -m unittest discover -s tests -v
```
O teste HTTP compila `LanApkServer.java` com JDK e testa o protocolo pela interface de loopback. A compilação Android e testes parciais em API 25 passaram; **ainda faltam celular em LAN real, USB físico e hardware RK3229**. Consulte o relatório para o escopo exato.

## Recriar a boot animation do vídeo do usuário
```sh
python tools/bootanimation_from_video.py /caminho/video-vortex.mp4
```
Requer `ffmpeg` e `Pillow`. Saída ignorada pelo Git: `assets/bootanimation.zip`. O arquivo gerado separadamente nesta conversa tem 720p/12 FPS e cerca de 5,8 MiB. A arte não é recriada nem substituída.

## Metas ainda não medidas
- Firmware compactado idealmente <= 600 MB
- Sistema instalado idealmente <= 800 MB
- RAM ociosa idealmente <= 450 MB

## Riscos e pendências
A placa ainda requer confirmação do FlashID NAND/eMMC, controlador Wi-Fi, loader DDR, DTB, HALs e drivers. AOSP 7.1.2 e kernel 3.10.104 são obsoletos e não devem ser usados para operações sensíveis. O proprietário dispensou backup do Android antigo, mas **não** dispensou diagnóstico e plano de recuperação.

A integração AOSP é experimental. Não flashear `app/` ou `rom/` diretamente.

Referências: [Hardware](rom/HARDWARE.md) · [Installer](rom/INSTALLER.md).

**Nunca criar ou executar GitHub Actions.** Uma build consolidada por vez, sem merge até os testes locais e físicos.
