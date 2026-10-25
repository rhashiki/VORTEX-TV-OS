# Compilação Android — Build 01

O código da branch `build/01-core-starter` **não é um firmware Android/ROM**. Para compilar apenas o aplicativo é necessário um computador com Android SDK e JDK apropriados.

## APK de desenvolvimento

- Android Studio ou Android SDK cmdline-tools, com SDK Platform 33 e build-tools.
- JDK 11 e Gradle compatível com Android Gradle Plugin 7.4.2.
- Sem dependência de Google Play Services, AndroidX ou Kotlin.
- O projeto não contém Gradle Wrapper, pois seus binários não foram auditados/incluídos.

Com Gradle instalado:

```sh
gradle :app:assembleDebug
```

O APK de teste não recebe automaticamente as permissões de sistema (reiniciar/desligar). Teste no Android Emulator API25 quando houver imagem compatível ou num Android 7.1.2 de teste.

## Testar transporte no computador

```sh
python -m unittest discover -s tests -v
```

JDK é necessário para executar o teste HTTP; ele inicia uma instância local e verifica origem, token, rejeição de arquivos inválidos, upload e SHA-256. **Isso não valida instalação Android**, QR via celular, hardware, nem a execução do firmware.

## Primeira ROM física

Requer firmware-base, loader DDR, tipo e FlashID NAND/eMMC, Device Tree, módulos Wi-Fi, áudio e gráficos compatíveis com R329Q_V8.0. Não presumir que firmwares V8.1 servem na V8.0.

O proprietário dispensou o backup original, mas permanece necessário confirmar como entrar em Loader/MaskROM e recuperar uma gravação mal-sucedida.

## Primeiro diagnóstico USB em Linux

```sh
bash tools/rk322x_readonly_probe.sh
```

O script só realiza consultas e não altera a flash.

**Jamais usar GitHub Actions**: testes locais/emulador/dispositivo físico.
