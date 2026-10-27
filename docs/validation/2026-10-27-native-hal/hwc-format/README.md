# Correção incremental dos formatos de diagnóstico HWC

Este patch é aplicado **depois** de `hwc-fix-format-policy-and-hdmi-strings.patch`
sobre o HWC `d3ec43f2f751123ca5e7bda2d07eded4c6352a35`. O patch anterior de
seleção de header RK322x permanece aplicado no Android.mk. Nenhuma árvore ou
artefato da etapa anterior foi alterado.

`hwc-fix-diagnostic-formats.patch` é um diff normal ASCII/UTF-8. As edições
foram feitas em bytes, mantendo os comentários e demais bytes legados dos
quatro arquivos; não se converteu a codificação da fonte. Replay com
`git apply --check` e aplicação real em cópia separada produziu bytes idênticos.

A correção muda somente chamadas de diagnóstico:

- Escalas float promovidas para double usam `%f`.
- Handles/layers são passados como `void *` a `%p`; endereços lógicos já
  declarados `void *` também usam `%p`.
- A constante de uso protegido de 64 bits usa `%llx` com argumento
  `unsigned long long`, sem truncar o valor.
- O diagnóstico `vop_gpu` recebe o argumento handle que faltava.
- O endereço físico `RK_U32` permanece inteiro hexadecimal, em vez de `%p`.

Os quatro TUs afetados do baseline, que já contém as três correções funcionais,
falham com `-Werror=format`: 17 erros de formato. O conjunto completo de oito
TUs corrigidos compila para ARMv7/softfp/NEON com o mesmo flag, sem diagnósticos
de formato. Os outros avisos continuam visíveis: não há afirmação de build
sem avisos. São 18 chamadas editadas, incluindo três repetições da mesma
conversão fora do ramo ativo que gerava os 17 diagnósticos.

Os comandos usam os headers Android/Bionic/libc++ reais da compilação HWC
anterior e os flags RK322x/RK322X_BOX/DMA_BUF, sem exceções ou RTTI. Não se
executou make Android, link HAL ou hardware nesta tarefa. O teste estrito de
formato cobre esses flags, não todas as combinações de plataforma do upstream.

O primeiro harness privado não recriou o symlink real `../librkvpu`, requerido
pelo include relativo da fonte. A falha fica em
`evidence/attempt-harness-missing-sibling`; a correção somente refez o layout
de diretórios das fontes genuínas. O baseline negativo de formato e o sucesso
final são separados dessa falha de ambiente.

`source-format-review.json` contém fontes, flags, objetos e hashes.
`compile_hwc.py` e `compile_baseline_formats.py` registram os caminhos concretos
do workspace; não são receitas portáteis de ROM. O conjunto atual coerente de
oito objetos está em `evidence/final`, pronto para o ensaio de link separado.
