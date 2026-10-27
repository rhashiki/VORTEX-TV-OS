# Reprodução independente das fontes do perfil

Resultado: **PASS somente para reprodução de fontes e comparação das listas**.
Não é fechamento de módulos, build Android, validação de imagem ou boot.

`replay.py` extraiu arquivos dos commits reais com `git archive`, aplicou cada
patch somente após `git apply --check` e comparou bytes e tipos de arquivos
com a árvore usada pela inspeção do produto. Foram comparados 1.615 arquivos:

| Projeto | Base pública | Patches, em ordem | Arquivos |
| --- | --- | --- | ---: |
| build | d2721c65c9282b31df7b79f85289ee6c4e636716 | patch de seleção do produto Vortex | 1.034 |
| device/rockchip/rk322x | f33a129bfab6d9cc87184ee3bf032224801fa446 | SD 0001, 0004 | 32 |
| device/rockchip/common | 3b1aa90ef43f9d34094739a211ad44bf9a2c0b74 | SD 0002, 0003, 0005 | 245 |
| vendor/rockchip/rk322x | 50c7170ecb4bd907059db37f09f4767b301f2d15 | SD 0006, graphics 0004 | 304 |

A reprodução de common começa no commit público 3b1aa90, sem depender do
commit local 651d363. Esse commit local já incorporava SD 0002 e 0003; o
working tree acrescentava SD 0005. A comparação final confirmou o mesmo
resultado partindo da base pública e dos três patches. O diff do commit local
foi preservado em `common-local-base.patch` apenas como explicação de origem.

A primeira comparação encontrou seis links simbólicos de releasetools
convertidos em arquivos regulares por `copytree` sem `symlinks=True`. Seus
conteúdos resolvidos coincidiam com upstream; a diferença de tipo era real.
`build-dereferenced-symlinks.json` preserva essa observação. Os seis links foram
restaurados exatamente com os destinos upstream, e `setup_tree.py` passou a
preservar links. A segunda reprodução passou sem divergências. Essas rotinas
de releasetools não foram executadas.

As listas de packages, copy-files e properties do produto original rk322x_box
são byte a byte iguais entre baseline-05 e a execução com o patch Vortex
aplicado, usando as mesmas entradas e preâmbulo diagnóstico. Isso mede o
efeito da seleção condicionada nessas três listas; não comprova ausência de
efeito em todos os produtos nem avalia regras de construção de imagem.

`source-replay.json` registra verificações de aplicação, hashes dos patches,
arquivos alterados e comparações. Os quatro arquivos `*-files.json` registram
o inventário completo comparado. As árvores temporárias não fazem parte das
evidências a publicar.
