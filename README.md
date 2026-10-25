# Vortex TV OS — Build 01 (starter técnico)

Sistema Android TV experimental para **MXQ PRO 4K 5G / R329Q_V8.0** (família Rockchip RK322x, ARMv7, 1 GB DDR3, Android 7.1.2, kernel 3.10.104).

> **Não é uma ROM flashável.** Nenhum APK foi compilado, emulado ou inicializado na TV Box até o momento. Este commit publica código inicial, não conclui a Build 01.

## O que há neste repositório

- Launcher Java nativo (API 25) sem AndroidX, GMS, Kotlin runtime ou WebView.
- Home escura com gradiente roxo/azul, relógio e foco via D-pad.
- Atalhos para instalador (placeholder), Configurações e Energia.
- Acesso discreto a aplicativos de usuário após a instalação.
- Fragmentos AOSP 7.1.2 em `Android.mk` e `rom/vortex_product.mk` (não fornecem kernel, HALs, DTB ou loader).
- Prévia navegável em `preview/index.html` (somente simulação visual).
- Gerador de boot animation em `tools/make_bootanimation.py`; a logo oficial de duas ondas ainda não foi incorporada.
- Testes estáticos em `tests/test_source_layout.py`.

## Compilar apenas o aplicativo

É necessário Android Studio / Android SDK (plataforma 33), Gradle compatível com Android Gradle Plugin 7.4.2 e JDK 11. Não há Gradle Wrapper incluído.

```sh
gradle :app:assembleDebug
adb install app/build/outputs/apk/debug/app-debug.apk
```

Depois, testar num emulador Android TV compatível. Reinício/desligamento privilegiado dependem de integração na ROM.

## Testes locais, sem GitHub Actions

```sh
python -m unittest discover -s tests -v
```

O teste estático **não** prova compilação Android, velocidade, funcionamento do D-pad ou compatibilidade da ROM com o MXQ.

## Alvo final

Vortex TV OS (sem Lite), duas builds completas, interface 720p minimalista; Installer local por QR Code ou pendrive, nenhum Bluetooth, nenhum Google Play Services, nenhuma App Store.

Metas **não medidas**: firmware compactado até 600 MB, sistema instalado até 800 MB e consumo em repouso até 450 MB.

## Integrar ao AOSP

Importar esta pasta numa árvore AOSP 7.1.2 verificada em `vendor/vortex/home`, integrar `rom/vortex_product.mk` e compilar. **Não tentar gravar** antes de identificar modelo/ID da flash, Wi-Fi, loader DDR, partições e procedimento de recuperação. O proprietário dispensou backup da ROM antiga.

Status técnico e fontes: [rom/HARDWARE.md](rom/HARDWARE.md).

**Não criar nem executar GitHub Actions.** Validar localmente ou em ambiente independente.
