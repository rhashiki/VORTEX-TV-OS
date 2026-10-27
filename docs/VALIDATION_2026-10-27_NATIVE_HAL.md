# Build 01 — HALs gráficas ligadas e carregadas em ARM

Base: `0928d6a1081b9fd373769e0e7fa6f9282134fdc8`.
Foram compilados os oito arquivos HWC, corrigidos defeitos nas fontes e ligados
`gralloc.rk30board.so` e `hwcomposer.rk30board.so`. Os dois módulos passaram
por carregamento/metadados no linker Android ARM sob QEMU.

**É um ensaio manual com bibliotecas de referência API25, não o build AOSP
completo. Ainda não há imagem Android/SD inicializável ou teste físico.**
O aplicativo Vortex, sua Home sem gaveta e seus recursos não foram alterados.
Não se declarou funcionamento de framebuffer, composição, GPU ou HDMI.

## HWC compilado e corrigido

O HWC foi fixado em `d3ec43f2f751123ca5e7bda2d07eded4c6352a35`, com o
patch anterior de seleção do header gralloc. A aquisição delimitada de
40 headers frameworks/native e do header uevent legado completou os includes
reais, junto de Bionic/systemcore/libc++ e librkvpu já fixados. Não se criaram
tipos Android ou bibliotecas fictícias para satisfazer o compilador.

Três defeitos foram corrigidos no [patch 0005](../rom/platform-reference/graphics/patches/0005-hwc-fix-format-policy-and-hdmi-strings.patch):

- `switch(handle && handle->format)` reduzia formatos não zero a bool1,
  aceitando RGB565/RGBX/formatos desconhecidos como RGBA na política de mix.
  Agora o código verifica handle e compara o formato real.
- O helper itoa terminava com a constante multicaractere `'\0 '`, que não
  era NUL. O terminador passou a `'\0'`.
- O diagnóstico HDMI tinha `%d` sem argumento; agora recebe o estado lido.

Quatorze testes host dos corpos reais das funções, com tipos HAL/gralloc
verdadeiros, registraram oito falhas antes e nenhuma depois. Eles cobrem
handles/listas nulos, formatos selecionados e cinco valores decimais não
negativos. Não são testes de renderização ou suspensão; não aprovam todos
os radixes, números negativos ou INT_MIN. Os corpos testados continuam byte
idênticos nos arquivos usados pela compilação final.

O [patch 0006](../rom/platform-reference/graphics/patches/0006-hwc-fix-diagnostic-formats.patch),
aplicado depois de 0005, corrige conversões e argumentos em 18 chamadas de
diagnóstico: float/double, ponteiros, flag64bit e argumento handle ausente.
O baseline de quatro TUs afetados falha com **17 erros** ao usar
`-Werror=format`. O conjunto completo de **oito TUs atuais compila** com
esse flag e zero diagnósticos de formato. **Outros 109 avisos permanecem**,
visíveis nos logs; não se afirmou build sem avisos. Os bytes legados dos
arquivos foram preservados e os patches transportam texto ASCII/UTF-8.

A primeira tentativa HWC encontrou includes ausentes; a primeira tentativa
privada da correção de formatos também não recriou o path relativo real
`../librkvpu`. Ambos os bloqueios de ambiente ficaram preservados. Nenhum
header fictício ou fonte de driver foi criado para contorná-los.

## Compilação e link das duas HALs

Os oito TUs HWC atuais usam ARMv7/softfp/NEON,
RK322X/RK322X_BOX/RK_BOX/DMA_BUF/API25, sem exceções/RTTI.
Os quatro TUs gralloc `c92fb8cd8becd57b025149f2861a2072b092ddea` também
foram recompilados com `-fno-exceptions -fno-rtti -fno-strict-aliasing`.
A variante anterior mantinha os defaults GCC de exceções; seus objetos
permanecem preservados, sem serem misturados ao conjunto novo.

O header libhardware continua com o contrato framebuffer de 908 bytes da
etapa anterior. O compilador é Linaro GNU ARM6.3.1, com includes Android reais
e `-nostdinc/-nostdinc++`. O CRT compartilhado veio das fontes Bionic reais
`8b2e5b977118ebb8447cdf429c4a6be534c4fd1b`, sem CRT glibc do host.

O link manual passou para ambos os módulos com `--no-undefined`,
`--no-allow-shlib-undefined`, `-z defs`, RELRO/NOW e SONAME próprio.
Cada módulo exporta HMI e é ELF32/ARM/EABI5/soft-float. Os imports dinâmicos
são normais em uma DSO; a verificação encontrou seus provedores no conjunto
de referência. Isso não significa que todos os símbolos sejam definidos
na própria HAL, nem que a mesma resolução esteja pronta no futuro sistema.

Foram usadas **21 bibliotecas de plataforma e o linker Android7.1.1/API25
ARM32 reais**, mais a libion Rockchip vendor fixada em `50c7170ecb4bd907059db37f09f4767b301f2d15`.
O conjunto tem 22 bibliotecas, com hashes e imports transitivos registrados.
Não se usaram substitutos vazios nem opções para ignorar imports fortes sem
resolução. O source graph Android.mk completo ainda não foi executado.

## Referência Android adquirida

A imagem oficial API25 ARM64 consultada primeiro só tinha lib64 e não forneceu
os ELFs ARM32. A negativa foi registrada. A pesquisa localizou depois o
pacote oficial SDK `system-images;android-25;google_apis;armeabi-v7a`:

- Archive `armeabi-v7a-25_r18.zip`, 952.973.150 bytes.
- SHA1 publicado e observado: `a6f7c491e3bb937523dddfa287e07d785934e8a1`.
- SHA256 observado: `0e888e3141ec4bf55494cbbb268e91fab60de7bf5163f85a40a4bab7e31032ff`.

O download inteiro foi conferido; ZipFile verificou os CRCs de system.img
e dos metadados selecionados. O filesystem foi extraído como arquivo sparse,
lido com debugfs sem montagem e removido após a extração/hashes das bibliotecas.
A extração parou ao alcançar a reserva de disco e foi retomada após remover
somente caches novos. O prefixo parcial foi conferido byte a byte; a retomada
registrou mínimo de 8.640.032.768 bytes livres. Nenhum artefato de etapa anterior
foi apagado. Uma tentativa incompleta de parser ZIP streaming foi abandonada;
a entrega usa o caminho stdlib de arquivo completo verificado.

A imagem SDK é somente uma referência deste ensaio. **Google Apps não foram
integrados ao Vortex**. Os ELF adquiridos de plataforma/vendor e a imagem
não são redistribuídos no pacote de componentes compilados desta etapa.
A referência é Android7.1.1/API25, não o BSP Rockchip7.1.2 ou o firmware original
da R329Q_V8.0. Não se propõe substituir a ROM por essa imagem SDK.

## Carregamento pelo linker Android sob QEMU

O probe C e seu CRT executável Bionic real foram ligados para ARM. QEMU7.2
user mode executou esse processo com o linker e as bibliotecas acima,
sem inicializar um sistema Android completo.

**Cinco verificações passaram**: carregamento de gralloc e HWC por
`dlopen(RTLD_NOW)`, consulta HMI e fechamento; arquivo inexistente,
biblioteca sem HMI e identificador incorreto foram recusados com os códigos
esperados. O programa verifica tag, id e ponteiros de métodos. Nome e versões
são apenas impressos, sem comparação a valores esperados.

O probe **não chama `methods->open`**. Carregamento/fechamento podem executar
construtores e destrutores; o construtor gralloc inicializa metadados, mutex
e estado local. Não se afirmou que nenhuma instrução de dependência executou
ou que todas as dependências são livres de efeitos laterais.
Não houve teste de dispositivo gráfico, alocação, importação, composição,
framebuffer, GPU, HDMI, RGA/ION, fences ou VPU.

O linker legado avisa sobre DF_1_PIE/NOW (`DT_FLAGS_1=0x8000001`) do probe
produzido por GNU ld. O aviso permanece em todos os logs; não foi suprimido.
Ele se refere ao executável de teste, e as HALs não carregam o bit PIE.

## Parte observada da ABI privada Mali/OMX

Um probe dos headers completos mediu 56 quantidades mais magic diretamente
no objeto ARM: private_handle_t104/alinhamento8, native_handle_t12,
numFds1, numInts22 e magic0x03141592 em offset16. O compilador preservou
seus avisos de offsetof em classe derivada non-standard-layout.

O ELF Mali vendor verifica esse mesmo fingerprint e usa sete offsets de
campos coincidentes. ANativeWindowBuffer.handle é lido em offset60, como
no header. O export Rockchip_get_gralloc_private do blob OMX lê
format/share_fd/type/stride/size em40/12/48/44/28, iguais ao probe e ao objeto
da ponte OMX compilado de sua fonte real. São **19 comparações estáticas
selecionadas**, sem divergência encontrada; não são testes de renderização.
A auditoria desses blobs foi estática, sem executá-los para validar GPU.

Essa evidência reduz a incerteza de fingerprint/campos examinados, mas não
aprova a ABI inteira, formatos, ownership, lifetime, cache, alocação, ION/RGA,
VPU ou fences. Helpers sem símbolos foram identificados por endereços;
não se inventaram nomes a partir dos rótulos aproximados do objdump.

## Artefatos finais

| Arquivo | Bytes | SHA256 |
| --- | --- | --- |
| `gralloc.rk30board.so` | 40.044 | `757c7bd142bf2d65330e1f4c972e8664706604018a89b1bd0963e5f91e7564a3` |
| `hwcomposer.rk30board.so` | 140.140 | `585842ade2e8bde7d2f0e8cf9cd9fca43762accf484671266efd1f4106f7241f` |
| `hal_metadata_probe` | 7.192 | `3b04317fa4259c73346b2afffa71ef0905306b1679eeff39df1606c63b68a0bc` |

São componentes de engenharia para investigação, não um pacote Android
instalável, atualização, ROM ou cartão SD. O aplicativo não foi recompilado
nem seu fluxo de Installer repetido nesta etapa; permanecem válidos como
resultados anteriores os 96 testes de regressão e as 14 verificações do
Installer registradas no relatório anterior.

Continuam necessários build Android completo e inventário final das
bibliotecas/HALs, integração init/ramdisk/SELinux e layout SD, fechamento do
monitor/console/reservas/suspensão, execução gráfica/multimídia e testes de
periféricos na TV Box. A inicialização por SD deve preceder instalação interna.
Nenhum dado adicional de placa foi solicitado ao proprietário.

## Receitas e evidências

- [Receita nativa e ordem dos patches](../rom/platform-reference/graphics/NATIVE_HAL_BUILD.md)
- [Link estrito e hashes](validation/2026-10-27-native-hal/gralloc-link/evidence/hal-link-results.json)
- [Bibliotecas reais de referência](validation/2026-10-27-native-hal/gralloc-link/evidence/platform-libraries.json)
- [Proveniência do archive ARM32](validation/2026-10-27-native-hal/gralloc-link/evidence/arm32-reference-acquisition.json)
- [Compilação HWC e 17 erros de formato corrigidos](validation/2026-10-27-native-hal/hwc-format/source-format-review.json)
- [14 testes host de comportamento](validation/2026-10-27-native-hal/hwc/evidence/behavior/behavior-results.json)
- [Cinco casos do loader](validation/2026-10-27-native-hal/loader/evidence/loader-smoke-result.json)
- [Medição do buffer privado](validation/2026-10-27-native-hal/private-abi/private-handle-layout.json)
- [Campos Mali/OMX comparados](validation/2026-10-27-native-hal/private-abi/private-abi-review.json)
- [Revisão independente de link/loader](validation/2026-10-27-native-hal/review/native-link-loader-review.json)
- [Integridade final](validation/2026-10-27-native-hal/root-verification.json)

Nenhum GitHub Actions foi consultado, criado ou executado. Não houve boot
físico ou escrita na TV Box. A Build01 permanece aberta.
