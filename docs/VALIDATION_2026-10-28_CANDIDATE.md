# Build 01 — tentativa de plataforma e componentes candidatos

Execução iniciada em 27/10, retomada em 28/10 e consolidada em 30/10/2026.
Base Vortex do ensaio completo:
`ba4afebe58e9c9cb8fd2a05dc88d142ce1b5e8fe`. A consolidação preserva as
sete atualizações posteriores até `1db0c914fda74419be097b36c1e753296bcc2bbc`,
incluindo VortexTV na Home. O overlay para a próxima execução fixa esse novo pin.

**O lunch real do produto passou; make droid foi executado e ainda não
produziu uma ROM completa.** Foram compilados novos módulos de áudio/energia,
o Java central core-all e um componente Linux de diagnóstico. O recovery
Rockchip também foi ligado como executável estático. Não há imagem SD
inicializável validada.

O proprietário autorizou construir um candidato com as fontes públicas
disponíveis para a família RK322x. Isso permite avançar sem novos pedidos de
identificação da placa; não transforma correspondência de nome/chip em
compatibilidade física comprovada. Não houve operação na TV Box.

## Tentativa real do Android completo

Foi criada outra árvore de trabalho, sem alterar as saídas dos experimentos
anteriores. Ela usa o build Rockchip
`d2721c65c9282b31df7b79f85289ee6c4e636716`, JDK8 e o produto
`vortex_rk322x_sd_box-eng`. Não registra os 22 DSOs SDK de referência como
substitutos das bibliotecas da plataforma nesta tentativa. Os experimentos
de HALs que os utilizam continuam identificados separadamente.

A execução encontrou duas falhas que a inspeção anterior de listas não
alcançava:

- O diretório device/vortex/rk322x_sd_box não correspondia ao PRODUCT_DEVICE
  vortex_rk322x_sd_box. O envsetup real não encontrava o BoardConfig. O destino
  foi corrigido para device/vortex/vortex_rk322x_sd_box.
- O checkout Vortex dentro de vendor também continha AndroidProducts.mk do
  template. Ele registrava o mesmo produto duas vezes. O guard agora registra
  somente o perfil materializado no destino device correto.

Após as correções, lunch passou e make droid avançou pelo registro dos módulos
e até a compilação Java de libcore. Foram adquiridos fontes reais LLVM,
libcore, ICU, frameworks/base, frameworks/native, JUnit, Conscrypt, JarJar,
OkHttp, BouncyCastle, libphonenumber, AIDL, Bison e gtest, além de
stubs SDK oficiais necessários aos makefiles. Não se usaram JARs vazios ou
aliases entre versões de SDK para contornar as verificações.

A primeira aquisição esparsa de frameworks/native não podia ser clonada
localmente sem os objetos promisor. Um checkout real do commit selecionado
substituiu essa tentativa. Projetos com referências ../ entre diretórios
foram materializados na hierarquia BSP; symlinks para projetos externos podem
mudar a resolução desses caminhos. Os logs preservam essas falhas de preparo.

O make real gerou core-all/classes-full-debug.jar a partir de libcore
`e0874054acea0e164c4464d3bb82302df50e8e5c` e ICU
`18c86be3562ecbfaffd4a42b4fcc702874acf605`:

- 7.895.697 bytes; SHA-256
  `d48d5bb865dc86eb02722c97cc20d7fdae1fae78e6001b99a2bbcc4a930a96ee`.
- 4.770 entradas ZIP, incluindo 4.559 classes; CRC conferido.
- Headers de String, Object e Normalizer conferidos como classes Java8.

É um JAR intermediário compilado, sem dex/boot.art, execução no ART ou sistema
Android resultante. A verificação estrutural não é um teste de comportamento
das classes. Os avisos de APIs deprecated e operações unchecked permanecem.

A sequência chegou à tentativa 27. O Bison i386 oficial não executou neste
host; o Android.mk original compilou o GNU Bison2.7 de fonte para o host64,
selecionado pelo override BISON suportado. Foram produzidos 592 objetos host;
neste ensaio completo ainda não há objetos nativos target nem AIDL ligado.
Os componentes ARM de áudio/recovery pertencem aos ensaios separados abaixo.

Também foram gerados core-oj e core-libart, com CRC válido e classes Java8:

| JAR intermediário | Bytes | SHA-256 |
| --- | ---: | --- |
| core-oj | 4.254.727 | `09c6239ae60e7e9a816582109b4d6eb89db685bdd3f6068accdda03b27da4c30` |
| core-libart | 3.633.367 | `3f561b45779aa4ee8e0f7a72c55a4c542519ef19b32c914668e37894c80186fb` |

A última parada registrada é uma fonte ausente:
`system/netd/server/binder/android/net/INetd.aidl`. Fechar esse arquivo isolado
não demonstraria fechamento de todas as dependências; o checkout continua
incompleto. O inventário final real do Make contém 1.569 nomes de módulo,
416 entradas de pacote e 15 de cópia. O auditor das entradas retornou apenas
product_inputs_only, sem resolver dependências transitivas. As
[evidências completas do ensaio](validation/2026-10-28-candidate/platform/README.md)
preservam comandos, 27 tentativas, aquisições e snapshot final. Não houve
system.img, boot.img, dex/boot.art ou inicialização Android resultante.

O snapshot independente da tentativa 05 registrava 901 nomes de módulo,
416 entradas de pacote/412 únicas e somente 45 nomes selecionados presentes
naquela árvore fina. Esses números são históricos desse snapshot; não medem
a resolução transitiva nem a árvore ampliada depois. As listas posteriores
continuam vinculadas ao seu comando/tentativa, sem afirmar fechamento.

## APK atual da Home

A Home foi recompilada a partir dos 17 arquivos de módulo/app do commit
1db0c91, sem alterações locais, em saída isolada pelas regras AOSP/Jack reais.
O make terminou com sucesso. O APK inclui a alteração que permite mostrar
os.vortex.tv.stream junto dos demais apps na Home, sem gaveta.

- APK: VortexHome-main-1db0c91-aosp-r6.apk, 44.410 bytes.
- SHA-256: `37581d89ae8fda9cc42c9d0d2e1771c5962e76f5cdc91d9bc866ee5c36844c41`.
- ZIP/CRC, alinhamento, assinatura v2, pacote os.vortex.tv e min/target API25
  conferidos. Usa a chave pública de teste da plataforma AOSP.
- Os 22 inputs SDK históricos foram novamente conferidos por hash.

A conferência inicial esperava DEX035; o Jack produziu DEX037, válido em API25.
O erro do verificador foi preservado e corrigido, sem modificar o APK. Esta
nova versão não foi executada no emulador ou na TV Box. A presença do marcador
no DEX não testa o grid em execução. Não se compilou o aplicativo de streaming.
As [evidências da Home](validation/2026-10-28-candidate/latest-home/README.md)
registram fonte, comando, verificação e a diferença em relação ao APK anterior.

## Áudio e energia

Pelas regras Android.mk genuínas, com Clang Android e link GCC Android4.9,
compilaram 53 unidades de 15 módulos: quatro HALs, sete dependências
compartilhadas e quatro archives. As HALs são audio.primary.rk30board,
audio.usb.default, audio.r_submix.default e power.default.

O teste registra 22 provedores DSO de referência reais; nove alvos prebuilt
foram processados. Esses arquivos SDK/vendor não foram compilados por esta
etapa e ficam fora da entrega. A base Expat também exige seu subconjunto NDK
API8 original, registrado como insumo. Não se declara um BSP inteiro de fonte.

A TinyALSA padrão AOSP não contém pcm_config.flag usado pelo áudio Rockchip.
A composição passou a fixar a fonte Rockchip
`472b5e3fc1660660e0e9a3fa4cd5f752643920f2`, que declara e utiliza esse campo.
O [patch de áudio](../rom/platform-reference/audio/README.md) rejeita uma
taxa não suportada no ramo HDMI bypass antes de usar outputtype indefinido.

A regressão executa a função real extraída com tipos públicos e fronteiras
privadas simplificadas: baseline tem uma falha esperada, correção passa nas
11 verificações. O baseline usa instrumentação explícita de inicialização
zero para tornar o caminho indefinido determinístico; não é medição de
sanitizer nem previsão do comportamento ARM sem instrumentação.

Os onze DSOs de fonte passaram pelas verificações ELF32/ARM, softfp e
ausência de TEXTREL. Oito casos de metadados passaram no linker Android real
sob QEMU. O módulo power não exige callback open; seus hooks foram conferidos
como ponteiros, sem execução. Nenhum método HAL, áudio ou energia foi chamado;
construtores/destrutores podem executar ao carregar/descarregar os DSOs.

Permanecem 28 avisos de compilação, incluindo declarações implícitas, tipos,
ponteiros e formatos. Reprodução/captura, HDMI/SPDIF/USB, mixer e energia na
TV Box não foram validados. Hashes e detalhes estão nas
[evidências de áudio](validation/2026-10-28-candidate/audio/AUDIO_BUILD_RESULT.md).

## Recovery e bibliotecas Bionic

O experimento separado usa recovery Rockchip/AOSP Nougat de revisão
`4e64764f19db25238c296691ef0d950603eae33b`. O alvo aosp_arm compila sua UI
padrão. A UI comunitária corrigida é outro archive, compilado e testado
separadamente; ela não foi implicitamente incorporada ao executável baseline.

O build Android.mk chegou ao link, pack/strip e instalação de um recovery
estático ELF32/ARM, sem interpretador dinâmico:

- Executável instalado: 956.040 bytes; SHA-256
  `5e2c3639b15a51728b24f8400dd2539c2ace87647fca41527698129ce543928c`.
- O ELF intermediário com símbolos tem 15.993.164 bytes.
- Foram observadas 1.582 regras de compilação com objeto correspondente,
  54 módulos archive de fonte, três DSOs Bionic e 16 objetos principais.
  Esse inventário é da árvore do experimento, sem equiparar cada regra a um
  arquivo-fonte único ou todas as bibliotecas a contribuições retidas no ELF.
- Não foi executado, nem mesmo com --help. Não se gerou recovery.img, boot.img
  ou cartão a partir desse resultado.

A interface comunitária usava um construtor e enums antigos. Também ocultava
CheckKey(int,bool) ao definir uma função de um argumento. A adaptação usa o
construtor Nougat, mapeia as ações válidas e conserva a política de teclado da
classe base. Sua compilação ARM e 20 verificações host passaram. Isso não
comprova que o controle remoto físico ou a saída HDMI estejam funcionando.

O link inclui código de fontes e archives vendor Rockchip pré-compilados.
O mapa identifica seções retidas de librkupdate, libext2_uuid e libcrc32.
librkrsa aparece na linha de link, sem membros retidos identificados. Não é
um executável inteiramente compilado de fontes disponíveis. Os inputs e suas
origens são registrados; os quatro archives vendor não são entregues como
arquivos separados. O binário resultante continua contendo as contribuições
efetivamente ligadas, sem relabelar seu código como licença do projeto.

O upstream contém caminhos sdboot/fw_update e atualização de IDBlock que
precisam de revisão antes de qualquer uso como instalador. A compilação desse
programa não aprova seu comportamento de gravação. O perfil SD existente
continua com TARGET_NO_RECOVERY=true e não foi convertido em instalador.

As regras reais também produziram libc.so, libdl.so e libm.so de fontes
Bionic selecionadas, além dos componentes estáticos; não são cópias SDK.
O ensaio suplementar usa libc/libm novas em um prefixo isolado, mantendo o
linker Android de referência e outras bibliotecas API25/vendor identificadas.
Dez casos normais passaram: seis HALs e quatro negativos, sem chamar métodos
de dispositivo ou hooks de energia. Construtores/destrutores podem executar.

Um caso exploratório adicional, dlopen direto do arquivo libdl novo, falhou
com __cxa_finalize não resolvido. A mesma operação falhou com libdl/runtime de
referência inalterados. A falha original permanece registrada e não foi
reclassificada como aprovação. O linker pode fornecer libdl internamente;
esses resultados não provam execução dos stubs do novo arquivo libdl.
O resultado agregado desse ensaio é parcial/qualificado, não todos-passaram.

O comportamento do Android completo, do recovery e do kernel na placa segue
sem execução. Fontes, traces e hashes estão nas
[evidências do recovery](validation/2026-10-28-candidate/recovery/README.md) e
[do runtime Bionic misto](validation/2026-10-28-candidate/bionic-smoke/README.md).

## Componente inicial de diagnóstico

O [código novo](../rom/installer-diagnostic/README.md) compila um /init ARM32
estático com musl1.2.5 de fonte e o toolchain Linaro fixado, e gera newc/gzip.
O build registrado exige Python3.12+ para a extração com filtro de arquivos.

Como PID1, ele exige RAMFS/TMPFS antes de criar diretórios e montar somente
proc/sysfs. Lê metadados limitados, emite JSON por stdout e aguarda. Não contém
shell, formatação, gravação, seleção de destino ou coleta de FlashID. SD/eMMC/
MTD são classificados apenas como candidatos não verificados. O cartão de
boot e o armazenamento interno não foram identificados na unidade.

O binário passou em 24 casos reais ARM sob QEMU com fixtures locais. A revisão
final conferiu a fixação do inode por O_PATH antes da leitura e a guarda de
tipo do filesystem raiz. Uma recompilação no mesmo ambiente produziu o mesmo
binário; um parser independente validou o arquivo newc/gzip e seu payload.

| Componente | Bytes | SHA-256 |
| --- | ---: | --- |
| init ARM estático | 27.436 | `34c3e9afb616e5802508e2be7b0e7b0d98267d70e42bdcaff1efafa1a742a950` |
| initramfs gzip | 19.392 | `39d116db80486916a8c29001b03af832da2a38f4e15fbd3f61813a46c39cd046` |

PID1, montagens, kernel3.10, console/HDMI, bootloader e boot na placa não
foram executados. Este componente não é um recovery, instalador funcional,
ROM ou cartão SD; não habilita NAND/eMMC no perfil que os mantém desabilitados.

## Driver para continuar o build completo

O [driver de plataforma](../rom/product/FULL_PLATFORM_BUILD.md) verifica os
29 pins críticos do overlay e seus estados exatos de patch. O modo padrão
confere entradas; somente --run aplica os patches validados e chama o
envsetup/lunch/make droid reais. O kernel é um insumo separado, com hash;
nenhum arquivo vazio substitui uma imagem ausente.

A revisão independente encontrou e corrigiu falhas de tipos de arquivo,
colisão de diretórios e execução indireta por configuração Git. O driver
confere bytes/modes contra objetos Git, desabilita fsmonitor/hooks e refs de
substituição e não usa diff do worktree que possa executar clean filters.
Os testes incluem reproducers desses defeitos, aplicação/retomada de patches
e recusa antes de modificar fontes. São fixtures de orquestração, sem prova
de compilação Android. As ferramentas de host e o checkout de controle são
insumos confiados; o script não é um sandbox contra alterações concorrentes.

Os 36 testes do driver passaram. A suíte da base ba4 passou com 166 testes,
sem skips, incluindo os testes HTTP/JVM anteriores. Após integrar a main
1db0c91, a primeira execução de 170 testes encontrou um contrato antigo que
proibia toda PRODUCT_COPY_FILES no fragmento Vortex: a nova configuração OEM
é uma cópia legítima. O teste foi ajustado para permitir somente esse par de
origem/destino e continuar rejeitando outras cópias de firmware. O log da falha
inicial foi preservado. A execução final passou com **170 testes, sem skips**,
registrados em regression-tests-current-main.log.

Esta etapa não editou o código da Home. Preservou a alteração upstream que
inclui os.vortex.tv.stream no grid. Os ensaios antigos do APK/API25 pertencem
aos seus respectivos commits; não aprovam automaticamente o APK atualizado.
Não foram usados assets substitutos para a marca.

## Capacidade e pendências

O ambiente tem 31,45 GiB de disco, limite efetivo de 8 GiB RAM e duas CPUs,
sem swap ou volume persistente adicional. Começou com cerca de 10 GiB livres
e passou a aproximadamente 5 GiB depois das aquisições e compilações. As referências AOSP
históricas arquivadas indicavam espaços muito maiores; não são um mínimo
medido do produto reduzido. A reserva configurável de 10 GiB do driver também
não é uma promessa de capacidade para AOSP.

Não houve sync completo dos 556 projetos ou lock repo manifest -r de todos
eles. Os 29 pins críticos são explícitos; os outros 527 ainda herdam a tag.
As fontes e dependências faltantes continuam aparecendo no make real.

O produto atual também exige VortexTV.apk e catalog-access, fora do Git.
Esses dois arquivos não estão presentes nesta execução. Sua ausência não foi
contornada retirando o app do produto ou criando arquivos fictícios. O ensaio
completo histórico ba4 não contém essa integração e não aprova o produto novo.
A obtenção do APK release e o provisionamento OEM precisam ocorrer em uma
etapa própria, sem expor o acesso no Git ou nos logs.

Precisamos fechar o build e gerar/inspecionar imagens, integrar ramdisk,
permissões/SELinux e drivers, tratar os caminhos de montagem/BCB, resolver USB/
vold e interfaces kernel/monitor/bootloader, e finalmente testar na unidade.

Os registros estão no [diretório da etapa](validation/2026-10-28-candidate/README.md).
Os artefatos de componentes ficam no pacote local, sem runtime SDK/vendor ou
toolchains. Não houve escrita de mídia, instalação de recovery, flash ou boot
físico, nem criação, execução ou consulta de GitHub Actions.
