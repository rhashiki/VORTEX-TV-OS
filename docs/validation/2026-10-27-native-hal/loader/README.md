# Carregamento e metadados das HALs em ARM

O probe usa o linker Android ARM32 API25 real, bibliotecas de referência reais
extraídas do SDK e QEMU7.2 user mode. Não inicializa uma imagem Android ou a
TV Box. O processo C inclui hardware/hardware.h verdadeiro e foi ligado com
CRT executável Bionic original, sem substituir libc ou a interface HAL.

Cinco casos passaram: gralloc e HWC carregaram com RTLD_NOW e exportaram
HMI; arquivo inexistente, biblioteca sem HMI e id errado foram recusados
com os códigos esperados. O probe verifica tag, id e ponteiros de método,
mas apenas imprime versões e nome, sem afirmar valores esperados para eles.
Depois chama dlclose. Não chama methods->open ou qualquer operação gráfica.

dlopen/dlclose podem executar construtores/destrutores das dependências.
O construtor do gralloc inicializa metadados/mutex e o estado local; isso
faz parte deste teste de software. O ensaio não aprova possíveis efeitos
laterais de todas as dependências, não exercita GPU, framebuffer, ION/RGA,
fences, VPU ou composição e não comprova boot completo ou compatibilidade
física da R329Q_V8.0.

O linker legado avisa sobre DT_FLAGS_1=0x8000001 (DF_1_PIE/NOW) do executável
produzido pelo GNU ld. A saída foi preservada, sem supressão, e todos os
códigos de saída esperados foram observados. Não se declarou ausência de
avisos ou equivalência à cadeia Android final.

As receitas têm caminhos concretos do workspace. QEMU foi extraído localmente
de pacote oficial Debian e só o executável ARM foi selecionado; não se
instalaram pacotes no sistema. A entrega exporta a proveniência da ferramenta,
não o executável QEMU ou os ELF de plataforma/vendor usados como referência.
Nenhum GitHub Actions foi usado.
