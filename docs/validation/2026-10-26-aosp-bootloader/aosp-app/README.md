# Evidências congeladas do build isolado

`BUILD_RECIPE.md` e `aosp-app-report.json` registram o momento em que o APK
foi compilado, antes da execução no emulador. As declarações de ausência de
runtime nesses arquivos se referem àquele experimento. O smoke posterior
do mesmo SHA-256 está em [runtime-result.json](../runtime/runtime-result.json)
e no [relatório consolidado](../../../VALIDATION_2026-10-26_AOSP_BOOTLOADER.md).

Os arquivos foram copiados sem reescrever a evidência. A receita original
usa a estrutura do workspace do experimento: seus caminhos `evidence/...`
correspondem aos registros reunidos neste diretório, e o patch está em
[rom/platform-reference](../../../../rom/platform-reference/vortex-aosp-integration.patch).
Os scripts de aquisição e conferência SDK também mantêm os caminhos
concretos originais; precisam ser ajustados para outro diretório de trabalho.
