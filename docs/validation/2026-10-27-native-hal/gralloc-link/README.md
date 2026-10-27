# Ligação manual de referência das HALs ARM

Os módulos `gralloc.rk30board.so` e `hwcomposer.rk30board.so` foram ligados
com saída zero e verificação estrita de símbolos. São ELF32/ARM, com SONAME
próprio e exportação `HMI`. Não é um build AOSP, uma ROM RK3229, um teste de
framebuffer/GPU ou uma confirmação da placa R329Q_V8.0.

## Entradas reais

- Gralloc `c92fb8cd8becd57b025149f2861a2072b092ddea`, quatro arquivos .cpp
  originais, com o patch de seleção RK322x no Android.mk e o header
  libhardware corrigido da etapa anterior. Nesta variante os objetos foram
  recompilados com `-fno-exceptions`, `-fno-rtti` e `-fno-strict-aliasing`;
  os objetos anteriores permanecem intactos. Os defaults anteriores de GCC
  geravam referências C++ de exceção que não representam os flags Android.
- HWC `d3ec43f2f751123ca5e7bda2d07eded4c6352a35`, os oito objetos coerentes
  de `../hwc-format/evidence/final`, incluindo correções funcionais e de
  formatos de log descritas na tarefa HWC. Não foi misturada uma baseline
  antiga com os três primeiros objetos corrigidos.
- CRT de shared library compilado dos fontes Bionic reais não modificados
  `8b2e5b977118ebb8447cdf429c4a6be534c4fd1b`: crtbegin_so.c, crtend_so.S e
  crtbrand.S. GCC Linaro6.3.1, ARMv7 softfp/NEON. O aviso de -nostdinc++
  passado ao compilador C foi preservado; não altera firmware nem mascara
  diagnósticos. Não foram usados CRTs GNU/glibc do host.
- Bibliotecas Android ELF32/ARM reais do SDK oficial API25/Android7.1.1
  Google APIs, mais libion.so da árvore vendor D042 fixada em
  `50c7170ecb4bd907059db37f09f4767b301f2d15`. Esta libion contém a interface
  Rockchip ion_get_phys usada pelos consumidores. Seus hashes e os imports
  transitivos estão em evidence/platform-libraries.json.

O link usa `-nostdlib`, `--no-undefined`, `--no-allow-shlib-undefined`,
`-z defs`, RELRO/NOW e hash SysV/GNU. Não foi permitido ignorar imports
fortes sem definição. As bibliotecas foram verificadas como ELF32/ARM e
os 22 arquivos de dependências foram coletados de forma recursiva. Não se
fabricaram stubs ou bibliotecas vazias. Uma DSO ligada ainda conserva
imports dinâmicos: o linker confirmou seus provedores na referência usada;
isso não significa que cada símbolo esteja definido dentro da própria HAL.

## Aquisição e armazenamento

O primeiro archive oficial API25 ARM64 foi verificado e inspecionado, mas a
imagem só continha lib64. Essa negativa foi preservada, sem afirmar que ela
fornecia ARM32. A pesquisa posterior localizou o archive oficial Google APIs
`armeabi-v7a-25_r18.zip`, 952.973.150 bytes, SHA1 publicado
`a6f7c491e3bb937523dddfa287e07d785934e8a1`, SHA256
`0e888e3141ec4bf55494cbbb268e91fab60de7bf5163f85a40a4bab7e31032ff`.
O download inteiro foi conferido antes da extração stdlib ZipFile; os CRCs
foram verificados para system.img e os metadados selecionados.

A extração parou ao alcançar a reserva de disco e foi retomada após limpeza
somente dos novos caches autorizada pelo agente principal. O prefixo parcial
foi comparado byte a byte com o ZIP; o restante do filesystem foi extraído,
seu hash conferido, e as bibliotecas foram lidas com debugfs em modo read-only,
sem montagem. O mínimo medido durante a retomada foi8.640.032.768 bytes livres,
acima da reserva8GiB. A tentativa que parou e os comandos ficaram registrados.
O filesystem temporário e os dois novos ZIPs foram removidos após os hashes
e a seleção das bibliotecas; nenhum artefato de etapa anterior foi apagado.
Uma tentativa de parser ZIP em streaming foi interrompida antes de concluir;
a entrega usa somente o caminho stdlib de arquivo completo verificado.

A imagem Google é apenas uma referência de runtime para o ensaio. Não foram
instalados ou integrados Google Apps ao produto. Os ELF de referência e o
vendor libion permanecem arquivos locais de teste; o pacote de entrega pode
conter metadados/hashes/receitas, sem redistribuir esses binários ou a imagem.

## Artefatos e limites

Os módulos próprios estão em artifacts/. Comandos, mapas de link e ELF em
evidence/hal-link-results.json e nos arquivos associados. Seus hashes:

- gralloc.rk30board.so:40.044 bytes,
  `757c7bd142bf2d65330e1f4c972e8664706604018a89b1bd0963e5f91e7564a3`.
- hwcomposer.rk30board.so:140.140 bytes,
  `585842ade2e8bde7d2f0e8cf9cd9fca43762accf484671266efd1f4106f7241f`.

A referência de bibliotecas é Android7.1.1/API25 do SDK, não o BSP Rockchip
7.1.2 completo nem os arquivos originais da unidade. Headers, flags e
bibliotecas foram fornecidos explicitamente ao compilador/linker; o grafo
Android.mk inteiro ainda não foi executado. Os resultados não aprovam a ABI
privada total dos blobs, ioctls ION/RGA, gerenciamento de fences, vídeo,
reservas do monitor, boot SD ou hardware físico. A remoção das cópias vendor
antigas ainda precisa ser confirmada na imagem Android final. Nenhum GitHub
Actions ou operação na TV Box foi usado.
