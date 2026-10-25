# Importação dos originais oficiais

Esta preparação segue [ROADMAP.md](../ROADMAP.md) e [BRANDING.md](BRANDING.md)
na revisão `cb249f2`. Os originais não estão neste workspace nem no GitHub:
há somente as três miniaturas documentais, que não entram no APK. O título
textual da Home e a ausência de ícone/banner oficiais continuam pendentes.

## Conferir e importar as três imagens

Os anexos com nome `.png` contêm JPEG RGB. O importador confere os três hashes
canônicos, o formato e as dimensões **antes de escrever qualquer arquivo**.
Ele recusa miniaturas, fontes diferentes, sobrescrita de recursos diferentes
e caminhos de saída que apontem para fora do repositório. Não há opção para
ignorar os hashes. A opção de conferência não grava nada:

```sh
python3 -m pip install -r tools/requirements.txt
python3 tools/import_official_branding.py \
  --square /caminho/1000915968.png \
  --banner /caminho/1000915967.png \
  --logo /caminho/1000915946.png \
  --check-only
```

Após conferir as fontes, repetir sem `--check-only`. A saída JSON registra
hashes, dimensões e tamanho das fontes e dos derivados. Guardar esse relatório
com os logs da build. Os JPEGs são preservados byte a byte em `branding/source/`,
com extensão `.jpg` correta; os PNGs são derivados por redução proporcional
Lanczos, sem corte, fundo adicional, moldura ou recoloração:

| Recurso | Caminho | Tamanho |
| --- | --- | --- |
| Ícone quadrado | `app/src/main/res/mipmap-nodpi/ic_launcher.png` | 192×192 |
| Banner TV | `app/src/main/res/drawable-nodpi/vortex_tv_banner.png` | 320×180 |
| Logo completo da Home | `app/src/main/res/drawable-nodpi/vortex_home_logo.png` | 480×202 |

A altura do logo é arredondada ao pixel mais próximo. Não se modifica o fundo
preto dos ícones. Os testes do importador usam fixtures sintéticas com hashes
locais apenas dentro do processo de teste; o CLI real continua recusando essas
fixtures. Eles verificam a transformação e as falhas, **não** aprovam a marca real.

O importador prepara os arquivos; **não altera o manifesto nem a Home**.
A integração deverá, com os originais presentes:

1. Definir `android:icon="@mipmap/ic_launcher"` e
   `android:banner="@drawable/vortex_tv_banner"`; retirar a exceção temporária
   `MissingTvBanner` do manifesto.
2. Substituir somente o título da Home por `ImageView` com
   `@drawable/vortex_home_logo`, `FIT_CENTER`, sem fundo e sem foco D-pad.
   Preservar hora/data, grade, margens e navegação.
3. Compilar, executar lint, conferir os três recursos no Android API 25 e
   registrar screenshot em 1280×720, memória e tempo de abertura. Conferir
   preto original, duas ondas, neon integral e proporções, sem distorção.

## Vídeo oficial de quatro segundos

```sh
python3 tools/bootanimation_from_video.py /caminho/1000915952.mp4 --official
```

O modo oficial exige o SHA-256 registrado no roadmap antes de executar ffmpeg
ou criar o destino. Exige 12 fps e verifica 48 quadros de 1280×720; o último
quadro fica em loop. O ZIP utiliza `ZIP_STORED` e só substitui o destino após
concluir a escrita. A conversão mantém a compressão visual já prevista pelo
conversor (paleta padrão de 128 cores); a aparência ainda precisa ser conferida
com o vídeo real.

Sem `--official`, o conversor permanece genérico e **não comprova origem
oficial**. Não foi gerado um novo ZIP a partir do MP4 real nesta etapa.
O antigo `tools/make_bootanimation.py`, que criava arte provisória, foi
desativado: agora apenas informa o comando oficial e termina sem gravar arquivos.
Não se promete reproduzir byte a byte o ZIP de 3,07 MB mencionado na outra
conversa, pois o resultado depende das versões de ffmpeg/Pillow e da conversão.
O ZIP pertence ao boot da ROM, não à interface da Home. A integração AOSP e
a reprodução no RK3229 continuam pendentes de fonte, BSP e hardware.
