# Ensaio de link nativo das HALs RK322x

`gralloc.rk30board.so` e `hwcomposer.rk30board.so` foram ligados manualmente
para ARM32, usando objetos compilados das fontes fixadas e bibliotecas Android
API25 reais. Também passaram por dlopen/consulta de metadados/dlclose no linker
Android, sob QEMU user mode. Não houve make AOSP da plataforma, inicialização
Android completa, abertura dos dispositivos HAL ou renderização.

## Entradas de fonte

Aplicar os quatro patches do [contrato gráfico](README.md) nas revisões
indicadas ali. No HWC, aplicar também, nesta ordem:

1. [0005: política de formato e strings HDMI](patches/0005-hwc-fix-format-policy-and-hdmi-strings.patch).
2. [0006: formatos dos diagnósticos](patches/0006-hwc-fix-diagnostic-formats.patch).

`0005` também aplica sobre o HWC original, mas não substitui o patch de
seleção do header no Android.mk. `0006` é incremental após `0005`. Os diffs
preservam os bytes legados das fontes; não recodificar os arquivos C++.
O XML de fontes não aplica nenhum patch automaticamente.

Oito TUs HWC compilaram com ARMv7/softfp/NEON, RK322X/RK322X_BOX/RK_BOX,
DMA_BUF, API25, `-fno-exceptions -fno-rtti` e `-Werror=format`.
Os quatro TUs gralloc foram recompilados num diretório separado, também
sem exceções/RTTI. Os objetos da etapa anterior permanecem intactos.
A cadeia é GNU ARM6.3.1 com headers Android/Bionic/libc++ reais; ela ainda
não representa a cadeia de build Android final.

## Correções do HWC

A expressão `switch(handle && handle->format)` convertia formatos não zero
em bool1, aceitando indevidamente formatos como RGB565 na política de mix.
Agora o código rejeita handle nulo e compara o formato real, mantendo apenas
RGBA/BGRA nesse ramo. O helper itoa passa a terminar em NUL, e o log de
estado HDMI recebe o argumento que seu `%d` exigia.

Os testes host usam os corpos reais das duas funções e tipos HAL/gralloc
verdadeiros: 14 casos, com oito falhas antes e nenhuma depois. Não testam
composição visual, ARM ou hardware. O itoa foi testado com entradas decimais
não negativas; não se afirmou correção geral de radix ou INT_MIN.

`0006` corrige conversões/argumentos de diagnóstico em quatro arquivos.
Os quatro TUs afetados antes falham com 17 erros ao usar `-Werror=format`;
os oito atuais passam sem diagnósticos de formato. Os outros 109 avisos
continuam visíveis nos logs. Não se afirmou build sem avisos.

## Bibliotecas e link de referência

A fonte dos binários de plataforma é o pacote oficial SDK
`system-images;android-25;google_apis;armeabi-v7a`, archive `armeabi-v7a-25_r18.zip`.
A publicação SHA1 foi comparada aos bytes completos; SHA256 e os arquivos
selecionados estão nas evidências. O pacote ARM64 consultado primeiro não
continha bibliotecas32; esse resultado negativo também foi registrado.

Foram extraídas somente 21 bibliotecas de plataforma ARM32 e o linker,
mais o libion vendor fixado em `50c7170ecb4bd907059db37f09f4767b301f2d15`.
O sistema de arquivos foi lido com debugfs sem montagem. Não se integraram
GApps ou qualquer imagem SDK ao produto Vortex. Esses ELFs são referências
de link/teste, sem aprovação para a placa ou para distribuição na ROM.

O link usa CRT compartilhado Bionic real e `--no-undefined`,
`--no-allow-shlib-undefined` e `-z defs`, com SONAME específico de cada HAL.
Não se usaram bibliotecas fictícias ou flags para aceitar símbolos sem
resolução. Imports dinâmicos continuam sendo normais no ELF resultante;
a verificação resolve-os contra o conjunto de referência fornecido.

## Carregamento ARM delimitado

O probe C foi compilado com CRT executável Bionic real, não um substituto
de libc/linker. QEMU executou o processo ARM usando o linker Android API25.
O programa chama dlopen com RTLD_NOW, consulta HMI, verifica tag/id/método
open presente e chama dlclose. **Não chama o método open da HAL.**

Os dois módulos passaram. Três negativos também passaram: arquivo ausente,
biblioteca sem HMI e id incorreto. O linker legado emite aviso sobre o bit
DF_1_PIE do executável criado pelo GNU ld; o aviso ficou preservado.
Não se ocultou nem se declarou ausência de avisos de runtime.

A consulta de metadados não valida /dev/mali, framebuffer, SurfaceFlinger,
HDMI, alocação/importação/coerência, RGA/ION, fences, VPU ou reprodução.
Os módulos ainda precisam entrar no build Android real com um inventário
coerente de bibliotecas e ser executados na TV Box.

[Relatório, hashes e receitas](../../../docs/VALIDATION_2026-10-27_NATIVE_HAL.md).
