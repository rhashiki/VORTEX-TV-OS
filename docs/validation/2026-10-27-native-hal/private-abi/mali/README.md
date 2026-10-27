# Mali — inspeção estática do handle privado

Foi lido o ELF público `proprietary/lib/egl/libGLES_mali.so` do vendor D042
`50c7170ecb4bd907059db37f09f4767b301f2d15`, sem executar esse código.
Os bytes coincidem com o objeto Git fixado. SHA-256:
`82f5bc8742026be1ed67db15eb50be7361b3be926d6f90a2d1711163c00ace1c`.

O blob é ARM EABI5/soft-float, com atributos VFP/NEON. Seus dez DT_NEEDED e
os símbolos dinâmicos estão preservados nos logs. Isso não comprova o
fechamento de bibliotecas ou execução no Android futuro.

## Constantes efetivamente observadas

O helper local em `0x10224` carrega o handle do buffer em `0x10264`
(`ldr r4,[fp,#60]`) e exige:

- versão de native_handle = 12 em offset 0;
- numFds = 1 em offset 4;
- numInts = 22 em offset 8;
- magic = `0x03141592` em offset 16.

Esses checks estão em `0x10278`–`0x102a8` e repetem-se em outros dois caminhos
inspecionados. A impressão de 12 + 4 × (1+22) implica 104 bytes serializados.
A igualdade com o layout de fonte deve ser conferida pelo probe ARM de
headers completos feito pelo auditor principal; não foi compilado um probe
separado nesta subauditoria.

No mesmo caminho, o blob lê flags em offset 20 e testa bits 1/2/4; no ramo
framebuffer lê fd em 88 e offset em 92. Também há leituras de base em 56,
size em 28 e format em 40. Outro helper usa a palavra em offset 12 no ramo
ION, coerente com o campo share_fd proposto. As faixas exatas e o contexto de
cada observação estão no JSON e nos seis pequenos disassemblies.

A função pública `__egl_platform_initialize_android` chama hw_get_module
com o texto `gralloc` em `0x11c2e5`. Os caminhos inspecionados chamam os
callbacks do módulo em offsets 136 e 140 com argumentos no formato lock/unlock.

## Limites

Os checks e leituras selecionados dão evidência concreta do fingerprint e de
parte do layout esperado. Não provam toda a ABI privada Mali, semântica de
alocação/importação, coerência de cache, pixel formats, uso/vida de buffers,
fences, EGL ou renderização. Nenhum ioctl ou acesso a GPU foi exercitado.

Muitos símbolos locais estão removidos: nomes que objdump imprime como
`simbolo_exportado+offset` são apenas o símbolo público mais próximo. O JSON
identifica os helpers por endereços e não atribui nomes de fonte inventados.

`collect_mali_review.py` reproduz leitura ELF/disassembly, confere os bytes do
commit e gera o JSON, usando os caminhos concretos deste workspace. O
manifesto congela somente os arquivos curados desta revisão. Dumps amplos de
exploração fora desse manifesto não são necessários para a prova entregue.
