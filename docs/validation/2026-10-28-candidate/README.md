# Evidências da tentativa candidata — 27 a 30/10/2026

O [relatório da etapa](../../VALIDATION_2026-10-28_CANDIDATE.md) descreve os
resultados e o ponto de parada. A base do ensaio completo é ba4afeb; a
consolidação preserva também os commits posteriores até 1db0c91. Os logs de
cada componente identificam seus próprios fontes, ferramentas e saídas.

| Diretório | Evidência e limite |
| --- | --- |
| platform/ | 27 tentativas de make droid, três JARs Java e última dependência ausente; sem imagens Android |
| latest-home/ | APK da Home no commit 1db0c91, compilado e inspecionado; sem nova execução Android |
| audio/ | 53 unidades, quatro HALs e dependências; metadados sob linker Android/QEMU, sem métodos de dispositivo |
| recovery/ | Link e instalação do ELF estático, 54 archives de fonte, três DSOs Bionic, UI separada e contribuições vendor |
| bionic-smoke/ | Runtime misto: dez casos normais passaram; dlopen exploratório de libdl falhou e foi preservado |
| installer/ | /init ARM e newc/gzip, 24 casos em QEMU; sem boot, PID1 ou gravação |
| build-driver/ | Revisão e 36 fixtures de orquestração; sem compilação Android nesses fixtures |
| host-toolchain/ | Toolchain oficial GCC4.8, bytes/modos conferidos e cinco smokes host |
| capacity/ | Recursos observados, sem presumir capacidade para AOSP completo |
| review/ | Replay de patches e inventário histórico da tentativa 05 |

Os pacotes congelados usam evidence.sha256 ou sha256.json. Os handoffs ao lado dos diretórios
registram hashes de artefatos e limites dos ensaios. Caminhos absolutos são os
locais originais da execução, não dependências de execução do produto.

Logs/mapas grandes ficam no ZIP de componentes e são identificados pelos
índices de logs dos respectivos pacotes. O ZIP inclui código do commit
consolidado, artefatos compilados e licenças; exclui runtimes SDK de referência,
toolchains, configuração OEM e archives vendor separados. O recovery ligado
continua contendo as contribuições vendor descritas no seu mapa.

Não houve operação de flash, montagem de mídia, instalação de recovery ou boot
na TV Box. Nenhum resultado desta pasta constitui ROM ou instalador SD pronto.
