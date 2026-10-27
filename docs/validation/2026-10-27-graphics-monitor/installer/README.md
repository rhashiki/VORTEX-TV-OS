# Regressão completa do Installer no APK AOSP final

Resultado: **14 verificações funcionais passaram**, além da confirmação de
identidade SHA-256 do APK efetivamente instalado. Android7.1.1/API25/x86,
1280×720, software, AVD isolado `emulator-5586`, encerrado ao final.

O fluxo real percorreu HTTP na interface privada do emulador, parser Android,
PackageInstaller, cancelamento e confirmação explícita, retorno à Home sem
gaveta e abertura do fixture por D-pad. Foram rejeitados token errado, origem
errada, corpo não ZIP e ZIP sem AndroidManifest. A chave de plataforma de teste
AOSP não dispensa a confirmação medida nesse fluxo. Nenhum código do produto
mudou. O fixture é um Activity simples e não é parte do Vortex.

A primeira tentativa de harness só movia o D-pad para a direita; apps padrão do
AVD colocaram o fixture na segunda linha. Essa suposição do teste falhou após
dez verificações. `harness-first-attempt/` conserva a tentativa. A continuação
usou D-pad baixo/esquerda e concluiu abertura e retorno, sem reinstalar/repetir
o upload. O pós-teste tentou `sha256sum`, ausente nessa API25; a tentativa também
foi preservada em `harness-host-tool-failure/`. Ler os bytes instalados com
`adb exec-out cat` e calcular SHA-256 no host resolveu a verificação final.
`commands.json` reúne as operações observadas; os dois scripts são as receitas
originais das tentativas, com seus caminhos concretos, não comandos prometidos
como portáveis ou executados integralmente sem ajustes do harness.

O APK final é `81fc16aa89e523088ac8c7a6e334a2c670745d6a4e673a30a986ba6af04867d4`.
O fixture instalado é `5461107bd1f4ae9064823cfa3699abc02be71053cd3c5751434000ed591eabbf`.
A opção Android de fontes desconhecidas foi habilitada somente neste AVD e
restaurada de1 para0 antes de encerrar. A solicitação de data partition768MiB
foi ajustada pelo emulador para arquivo lógico6GiB; a alocação física total
observada ao final foi cerca de690MiB, abaixo do orçamento de1GiB.

Isto não testa telefone/LAN física, USB real, drivers ARM/Rockchip, privilégios
de energia ou boot de ROM. Não houve operação de hardware/flash nem uso de
GitHub Actions. Nenhum AVD ou artefato anterior foi modificado.
