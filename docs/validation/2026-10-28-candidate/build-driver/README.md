# Driver do produto Android completo

`tools/build_full_platform.py` prepara os patches revisados e executa o alvo
real `droid` somente quando chamado com `--run`. Sem essa opção, executa uma
conferência das entradas e não altera a árvore BSP, não inicia seus scripts
nem compila. Git e os executáveis de host JDK/Python indicados são consultados.

Ele exige Linux, Python 3.9+, Git, Bash, GNUmake, JDK 8, Python 2.7 e uma árvore
completa já sincronizada da composição AOSP 7.1.2/Rockchip. Não baixa fontes,
instala pacotes, monta imagens ou acessa a TV Box. Não invoca scripts vendor
de fábrica nem GitHub Actions.

## Entradas e execução

Usar o manifesto AOSP `android-7.1.2_r6` e o overlay experimental atualizado
`rom/platform-reference/vortex-r6-rockchip-experimental.xml`. O overlay fixa
29 projetos críticos; os demais projetos AOSP continuam herdados da tag. A
sincronização completa e o espaço para fontes/saída são trabalho separado.
As receitas Android legadas devem usar caminhos absolutos simples, sem espaços
ou caracteres de interpretação de shell/make. O teste com espaços cobre só
a passagem de argumentos do wrapper, não o suporte do build Android inteiro.
O driver não converte essa composição em um lock resolvido ou BSP compatível.

Manter este checkout Vortex atualizado **fora** da árvore BSP. A cópia Vortex
dentro do BSP fica no commit fixado pelo overlay e recebe o patch de integração
correspondente a esse commit. `rom/product/full-platform-patches.json` descreve
os patches de device/common/vendor, gráficos, áudio, build e produto. O patch
AOSP antigo para Vortex 45d626a não é usado no pin novo ba4afeb.

O kernel é compilado separadamente pela receita SD existente; não se modificam
fontes kernel que este driver não compila. Fornecer `--kernel-image` com um
Image real conferido, ou manter a imagem no caminho exigido pelo BoardConfig.
Não há criação de placeholder. O hash do override entra no marcador de saída.
Isso identifica bytes, sem aprovar kernel/DTB ou o aparelho físico.

Exemplo de conferência, em uma máquina com a árvore completa e espaço suficiente:

```sh
python3 tools/build_full_platform.py \
  --bsp-root /work/android-nougat \
  --vortex-root /work/VORTEX-TV-OS \
  --jdk-home /opt/jdk8 \
  --python2 /opt/python2/bin/python2.7 \
  --kernel-image /work/kernel-out/arch/arm/boot/Image \
  --out-dir /work/android-out \
  --jobs 2 --min-free-gib 10
```

Repetir o mesmo comando com `--run` para aplicar somente os patches validados,
materializar `device/vortex/vortex_rk322x_sd_box`, executar `lunch` e `make droid`.
O prefixo e o guard do AndroidProducts.mk evitam as duas falhas reais de descoberta
encontradas no ensaio anterior. O template continua em
`rom/product/rk322x_sd_box`; o destino BSP usa PRODUCT_DEVICE no último componente.

`--jobs` aceita 1 ou 2. `--min-free-gib` é uma reserva operacional configurável;
10 GiB não é um mínimo comprovado para compilar AOSP. O build real pode exigir
muito mais espaço. O driver usa uma saída nova ou uma saída com o mesmo marcador
de commits/patches/perfil/kernel/ferramentas. Saídas de experimentos anteriores
sem esse marcador não são reutilizadas. Usar outro `--log-dir` em uma retomada.

## Contrato de fontes

- Cada projeto crítico precisa ser seu próprio worktree Git, no HEAD exato
  do overlay. Symlinks de projeto que escapem do BSP são rejeitados.
- Os arquivos de cada stack precisam coincidir com a base ou com um prefixo
  exato dos patches. Edições parciais e alterações fora do plano são rejeitadas.
  Arquivos rastreados fora dos patches são comparados por bytes/modo com os
  objetos Git, sem diff de worktree ou execução de filtros clean. As chamadas
  Git desabilitam fsmonitor, hooks, substituição local de objetos, conversão
  textconv/diff externo e locks opcionais de atualização de índice.
- Mudanças staged, assume-unchanged, skip-worktree e arquivos não rastreados
  visíveis ao Git fora das exceções são rejeitados. Uma definição de build
  ignorada pelo Git também bloqueia. Outros artefatos ignorados não são
  autenticados por esse contrato.
- Os únicos headers gerados declarados são `version.h` dos dois projetos
  gráficos. Seus bytes são inventariados; essa exceção não autentica a origem
  de uma geração anterior. Nenhuma exceção aceita definições de build.
- Um perfil de destino já existente só é aceito se vazio ou idêntico; ele não
  é substituído se contiver conteúdo diferente. A origem atual do template e
  os arquivos de patches são insumos explicitamente confiados pelo operador.
- Não registra DSOs SDK de referência como substitutos da plataforma de fonte.
  A antiga árvore `vendor/vortex/reference-libraries/Android.mk` bloqueia.

Os controles não são uma sandbox contra alterações concorrentes ou código
malicioso. `--run` executa os scripts de build dos fontes selecionados. O check
dos pins críticos não autentica todos os projetos AOSP, dependências transitivas
ou o ambiente inteiro de ferramentas.

## Logs e limites

Os logs registram preflight, comando, retorno, marcador de entrada e o estado
do lock. Quando existe ferramenta `repo` e `.repo`, o driver consulta o comando
real `repo manifest -r`. Se não estiver disponível ou falhar, registra isso;
não inventa um manifesto resolvido. Não é necessário fabricar um lock para
registrar uma tentativa candidata de compilação.

Retorno zero significa que a conferência ou o comando de build terminou com
sucesso, conforme o modo indicado. Não aprova uma ROM, layout, mídia SD,
compatibilidade de drivers ou boot físico. Uma saída completa deve passar
por inventário e verificações próprias antes de qualquer preparação de mídia.

`tests/test_full_platform_driver.py` tem 36 testes sobre repositórios Git
descartáveis. Os fixtures de orquestração usam Bash/GNUmake reais com um
Makefile mínimo e comandos fictícios de versão do host; não compilam Android.
O preflight executado sobre a árvore fina desta sessão ficou bloqueado, como
esperado: ela ainda não é o checkout completo exigido por este driver.
