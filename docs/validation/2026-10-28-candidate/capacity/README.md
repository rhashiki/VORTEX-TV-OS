# Capacidade observada para a tentativa Android completa

Levantamento somente de leitura em 27/10/2026. Não foi executado `repo sync`
completo, não houve configuração de armazenamento e nada das etapas anteriores
foi removido. Não é teste de firmware ou de placa.

## Limites reais do executor

`capacity.json` e `host-command-results.json` registram a medição:

- Disco persistente: 33.770.192.896 bytes no total (31,45 GiB), cerca de
  10.352.336.896 bytes livres (9,64 GiB) no snapshot.
- Memória limitada por cgroup: 8.589.934.592 bytes (8 GiB). O `free` do host
  mostra aproximadamente 9,7 GiB, mas esse não é o limite do processo.
- CPU: quota `200000/100000`, equivalente a 2 CPUs, embora 3 processadores
  sejam visíveis por `getconf`.
- Não há dispositivo swap ativo. O limite de swap permitir `max` não cria
  swap; `memory.swap.current=0` e `/proc/swaps` está vazio.
- `/tmp` e `/dev/shm` são tmpfs de aproximadamente 4,87 GiB cada, apoiados na
  mesma RAM limitada. Não são dois discos adicionais utilizáveis para um
  checkout/build grande.
- `findmnt` não mostra outro filesystem persistente gravável. Discos em
  `lsblk` não equivalem a volumes novos disponíveis; nenhum deles foi aberto,
  formatado, montado ou alterado.
- O Docker existente usa driver `vfs` e `/var/lib/docker`, no mesmo volume
  overlay de 32 GiB. Seu daemon exibe a memória/CPUs do host, sem afastar os
  limites cgroup desta sessão. Criar containers não fornece outro disco;
  nenhuma imagem/container foi criada ou executada para este levantamento.

O runtime gerenciado está conectado e em execução, mas sem capabilities,
identidades de saída ou credenciais configuradas. As ferramentas de ambiente
disponíveis expõem status/diagnóstico, não uma operação para anexar um disco
maior ou criar outra VM. Não foi iniciada aprovação de configuração.

## Referências históricas oficiais

Foram adquiridos arquivos pequenos, sem baixar toolchains ou AOSP completo:

1. A documentação AOSP no commit `0385c482894d09ec34b9320883a598a77f7894e9`
   (06/04/2015) recomenda 50 GB de checkout, 100 GB para um build e 16 GB de
   RAM/swap em VM.
2. No commit `7a4e60bdebfa9c7ebf0a953770da06c29488d1ef` (26/02/2018), a
   recomendação é 100 GB para checkout mais 150 GB para build, e 16 GB de
   RAM/swap em VM. O mesmo documento indica OpenJDK 8 para Android 7/8.

Essas são recomendações históricas gerais do AOSP, não medições de bytes
mínimos para o Vortex Nougat personalizado. Não se afirma que um produto
reduzido necessariamente ocupa o mesmo espaço. Elas demonstram por que um
sync/build convencional completo não é uma estratégia compatível com este
disco de 32 GiB e aproximadamente 10 GiB livres.

URLs, hashes e metadados de commit estão em `official-source-provenance.json`
e nos arquivos `official-*`. Uma consulta posterior ao histórico Gitiles
retornou HTTP 401; nenhum bypass ou acesso autenticado foi tentado. Não foi
necessária para a evidência acima.

## O manifesto ainda não é uma árvore pronta

O manifesto AOSP tem 541 projetos. O overlay remove 13 e acrescenta 28,
totalizando 556, dos quais somente os 28 do overlay usam commits completos;
528 ainda herdam a tag r6. Não existe `repo manifest -r` resolvido nesta
tentativa. `manifest-selected-projects.json` descreve a composição declarada.

Mesmo uma seleção equivalente a `default,-darwin` só exclui 24 projetos,
restando 532. Isso não fecha dependências do produto, não elimina todos os
projetos de teste e não constitui um tamanho calculado da árvore.

O produto mínimo atual também seleciona `webview` e 134 entradas de fontes.
Os `.mk` disponíveis não contêm todos esses payloads. A ausência de WebView
no APK Vortex não elimina automaticamente o módulo WebView do produto
Android. Remover entradas ou fornecer bibliotecas de referência para passar
um ensaio de módulos não equivale a compilar a ROM inteira.

## Estratégia executável neste ambiente

1. Reutilizar projetos/toolchains fixados já presentes por worktree ou links
   de diretórios, preservando as árvores originais e os artefatos anteriores.
2. Executar o produto com regras reais e registrar a primeira dependência
   efetivamente ausente. Adquirir fontes por projeto/commit e somente os
   insumos necessários ao ensaio, com orçamento explícito de espaço.
3. Se usar Git, clones shallow/partial/sparse podem reduzir histórico ou
   projetos não usados; os arquivos demandados pelos compiladores ainda
   precisam ser materializados. Um grupo de manifesto reduzido não é uma
   resolução de módulos. Não inventar providers ou DSOs vazios.
4. Compilar módulos independentes com `-j1` ou `-j2` e heap Jack compatível
   com o limite de 8 GiB. A memória disponível é compartilhada com os demais
   agentes/processos; medições devem ser refeitas antes de trabalhos grandes.
5. Não começar um sync ilimitado que encha o volume. Uma compilação de imagem
   completa exige capacidade adicional real ou uma árvore reduzida cujo
   fechamento e tamanho sejam demonstrados; nenhum dos dois existe ainda.

Para reproduzir um sync convencional em um futuro host com espaço suficiente,
usar o manifesto r6, overlay e patches documentados, com `--depth=1`,
`repo sync -c --no-tags --no-clone-bundle -j2` e posteriormente
`repo manifest -r`. Esses comandos não foram executados nesta medição e não
resolvem por si sós a compatibilidade entre fontes Rockchip/AOSP ou hardware.

O próximo resultado útil aqui pode ser uma compilação real de mais módulos
ou um ambiente instalador pequeno. Isso deve ser nomeado como tal; nenhum
desses componentes sozinho encerra o build completo do Android.
