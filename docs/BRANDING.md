# Assets visuais oficiais — Vortex TV OS

Atualização de 25/10/2026. **Fonte de verdade:** imagens e vídeo entregues pelo proprietário neste projeto, com os SHA-256 registrados em [ROADMAP.md](../ROADMAP.md).

## Quatro assets distintos

1. **Logo completo branco, horizontal e com texto "VORTEX TV OS"**: substitui o texto atualmente escrito pelo launcher na Home; usar `ImageView`, com redimensionamento proporcional. Fonte: `1000915946.png` (JPEG 1536×646).
2. **Ícone de aplicativo quadrado**: arte neon roxa/azul em quadrado arredondado. Fonte: `1000915968.png` (JPEG 1536×1536). Destinado ao ícone Android normal.
3. **Ícone/banner de aplicativo para TV (16:9)**: arte neon horizontal. Fonte: `1000915967.png` (JPEG 1536×864). Destinado ao banner Android TV/Leanback.
4. **Boot animation do SO**: novo vídeo `1000915952.mp4`, 1280×720, 24fps, 4s. Gerar ZIP Android a 12fps com 48 frames + último frame em loop. O vídeo anterior de 6 segundos não é mais a referência oficial.

## Caminhos sugeridos de produção

- `branding/source/vortex-logo-complete.jpg` (fonte 1536×646)
- `branding/source/vortex-launcher-icon-square.jpg` (fonte 1536×1536)
- `branding/source/vortex-launcher-banner-tv.jpg` (fonte 1536×864)
- `branding/source/vortex-official-boot.mp4` (fonte 1280×720)
- `app/src/main/res/drawable-nodpi/vortex_home_logo.webp`
- `app/src/main/res/mipmap-nodpi/ic_launcher.webp`
- `app/src/main/res/drawable-nodpi/vortex_tv_banner.webp`
- `assets/bootanimation.zip` (binário de boot ROM gerado localmente; não integra o APK).

Estas são convenções para Codex, **não uma afirmação de que os binários já estejam no GitHub**. Os arquivos fonte precisam ser transferidos para o workspace através da entrega/attachment correspondente; verificar SHA-256 antes de processar. Miniaturas WebP de preview, se adicionadas, não são substitutos de fontes.

## Critérios de aceite

- Logotipo inteiro, sem cortes, substitui texto na Home sem roubar foco D-pad.
- Ícone quadrado e banner de TV recebem recursos/atributos Android distintos.
- Nem o vídeo nem o ZIP devem ser empregados como recurso visual de interface da Home.
- A boot animation preserva o conteúdo real do vídeo e é validada para 720p/12fps no RK3229.
- Nenhum asset redesenhado por IA ou substituído por placeholder como resultado final.
