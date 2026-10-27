# Revisão independente de link e loader

Nenhum erro impeditivo foi encontrado. Os dois módulos próprios conferem em
hash/tamanho, ELF32/ARM EABI5 soft-float, SONAME, HMI global, RELRO/NOW e
DT_NEEDED. Os comandos usam -nostdlib, --no-undefined,
--no-allow-shlib-undefined e -z defs, sem supressão de imports não resolvidos.
Os12objetos de entrada e os três CRTs Bionic reais foram conferidos.

As22bibliotecas reais de referência foram verificadas em bytes/hash/ELF e
fecham os DT_NEEDED recursivos registrados. A libion coincide com o Git vendor
fixado. O checksum publicado API25ARM32 foi conferido no XML SDK retido;
o archive e o filesystem temporário já estavam limpos, portanto seus hashes
originais não foram recalculados nesta revisão.

Os cinco registros QEMU/Android-linker são coerentes: gralloc/HWC carregam,
expõem HMI e fecham com0; negativos arquivo ausente/HMI ausente/ID errado
retornam2/3/4. O probe verifica tag/ID/ponteiros; versões e nome são impressos,
não comparados a valores esperados. Não chama methods->open ou GPU/ioctl.
Carregar/fechar DSOs pode executar construtores/destrutores; não se afirmou
que todas as dependências são livres de efeitos. O aviso PIE nomeia o helper
e permanece visível, enquanto os novos módulos têm somente DF_1_NOW.

É um link manual e smoke de metadados em bibliotecas SDK7.1.1/API25/ARM,
com libion vendor. Não é build AOSP completo, composição gráfica, acesso a
GPU/HDMI, boot Android ou teste físico RK3229.
