# Ensaio de contrato framebuffer e compilação de fontes gralloc

O patch `libhardware-rk-fb-kernel-contract.patch` alinha o header libhardware
`d0c81ba009240cb9ab38d75d7e88190055349c2a` ao contrato de ioctl do kernel
`6c04d006ae881944d32c19e68b992d0bd5ab4fde`. Substitui o tail não usado
post_cfg pelo wb_cfg real, com908 bytes e sem alterar o kernel.
Não aprova toda a ABI gráfica, um BSP, uma ROM ou o hardware R329Q_V8.0.

A investigação dos dois consumidores fixados, tipos, tamanhos e inicialização
está em `CALLSITE_REVIEW.md` e `evidence/callsite-review.json`. O writeback deve
permanecer zerado: neste kernel ambos ion_fd e phy_addr iguais a zero o desativam.
Todos os consumidores precisam recompilar; prebuilts antigos não são corrigidos.

## Headers completos, não declarações copiadas

`probe_contract.py` inclui os headers completos e reais do kernel e do
userspace, compila com GCC ARM6.3.1 e compara94 quantidades (tamanhos,
alinhamentos e offsets/tamanhos de cada membro). O programa reutiliza somente
os includes/config gerados do kernel SD já construído; não escreve nesses
arquivos ou nos artefatos antigos. A cópia libhardware descartável fica aqui.
A baseline é obtida por git show do commit fixado, sem reescrever declarações.

Resultado em `evidence/header-contract-review.json`:

- Antes: estrutura userspace904 bytes, kernel908; prefixos compatíveis.
- Depois: todas as94 medidas iguais, incluindo writeback20 bytes em offset888.
- A asserção de contrato contra o header antigo falha; contra o novo passa.
  A falha negativa é dessa asserção, não uma alegação de erro de compilação
  das fontes antigas do gralloc.
- `evidence/patch-replay.json` registra git apply --check e replay byte a byte
  em outro clone limpo da revisão fixada.

O script usa caminhos concretos deste workspace e precisa dos checkouts e
config gerado anteriores para reprodução. As fontes probes e os valores
medidos estão em contract_measure.c, contract_assert.c e
expected-kernel-contract.h; não formam drivers ou substitutos de headers.

## Quatro fontes reais gralloc compiladas para ARM

`hal-build/gralloc-object-build-report.json` registra quatro compilações
independentes de arquivos completos do gralloc
`c92fb8cd8becd57b025149f2861a2072b092ddea`:
framebuffer_device.cpp, gralloc_module.cpp, alloc_device.cpp e
rockchip_alloc_device.cpp. Todos produziram objetos relocáveis ARM, sem
alterar os .cpp e usando Bionic/systemcore/GLES/KHR reais e libc++ oficial r6.
-nostdinc/-nostdinc++ evitam headers automáticos do host. Foram registrados
155 arquivos de dependência com hashes; não se usaram stubs ou -fpermissive.

O TU framebuffer também compila com o header antigo. A comparação dos
objetos reais mostra memset904 antes e908 depois, no caminho que envia o
ioctl0x4628. Isso mostra a alteração efetiva no consumidor compilado,
além das medidas de header. Não demonstra execução do ioctl.

version.sh foi executado sem alterações somente num novo clone descartável
para gerar version.h. A primeira invocação do harness estava no diretório
errado e falhou127; a tentativa e a correção foram preservadas. A primeira
extração dos headers libc++ rejeitou um symlink; foram extraídos apenas os
arquivos regulares, sem substituir o symlink por header fictício. Nenhum
TU compilado precisou dele.

## Limites e artefatos

GCC Linux ARM6.3.1 mais headers Android não substitui uma compilação pela
cadeia Android final. Não houve make AOSP, link contra bionic/libion/GLES,
HAL instalada, build HWC, teste de private_handle_t Mali, DMA-BUF/RGA/fences,
writeback, HDMI físico, imagem Android/SD ou execução de TV Box. O resultado
fecha a divergência dessa declaração para estas fontes, sem encerrar esses
outros contratos. Não houve GitHub Actions.

Os objetos estão em hal-build e evidence; logs, comandos, disassemblies e
hashes permitem conferir a comparação. O manifesto hal-build-evidence.sha256
congela45 arquivos desse experimento. graphics-evidence.sha256 registra os
arquivos de resultado/prova desta tarefa, sem incluir clones ou toolchains.
