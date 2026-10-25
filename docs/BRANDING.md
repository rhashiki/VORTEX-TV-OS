# Assets visuais oficiais — Vortex TV OS

Atualização de 25/10/2026. **Fonte de verdade:** imagens e vídeo entregues pelo proprietário neste projeto, com os SHA-256 registrados em [ROADMAP.md](../ROADMAP.md).

## Correção definitiva dos ícones — 25/10/2026

**Ordem expressa do proprietário:** usar **EXATAMENTE as duas imagens originais anexadas**, sem fundo branco, sem contorno, cartão, placa ou moldura externos adicionados, sem recoloração, sem redesenho, sem geração por IA e sem substituição por imagens parecidas encontradas na internet.

- **Ícone do Launcher (quadrado, 1:1):** o anexo `1000915968.png` (1536×1536, **conteúdo JPEG RGB com fundo PRETO original**, hash `bc20b1af97cdead54e3d12f6a4b224e7cd9860c80aaeeb685430e43e55bba7d3`). Usar a arte integral e a moldura luminosa **já presente na arte**, sem criar outra. O preto que existe no original é parte da arte e deve ser preservado; não substituir por branco.
- **Ícone/banner do Launcher para TV (horizontal, 16:9):** o anexo `1000915967.png` (1536×864, **conteúdo JPEG RGB com fundo PRETO original**, hash `fae9dca1d4da7c0f7082daeed0a67300a45e2bda663bdcdcbc9daabb089b707c`). Mesma regra: imagem na proporção original, sem fundo branco, sem molduras extras, sem regeneração.
- Os nomes dos anexos terminam em `.png`, **mas os bytes recebidos são JPEG**. Se copiar os bytes originais para o repositório, salvar como `.jpg` sem reencodar; se converter para outro formato para compilar o APK, fazer isso explicitamente e validar a aparência.
- Estas peças são **ícones/banners do APP Launcher**, não são o logotipo completo branco da Home nem o vídeo de boot.
- As miniaturas em `branding/previews/` têm resolução de apenas 96 pixels; **não usar miniaturas como resources finais** nem tratá-las como arquivos-fonte. Os originais anexados prevalecem.
- Para Android: `android:icon` aponta para recurso derivado do **ícone quadrado**; `android:banner` aponta para recurso derivado do **banner 16:9**. Usar `fitCenter`/redimensionamento proporcional, sem fundo adicional. Caso o launcher de terceiros aplique máscaras automáticas, documentar essa limitação de plataforma sem modificar as imagens originais.
- Critério de teste visual: fundo visível é **preto**, nunca branco; preservar as cores roxa, azul e ciano, as duas ondas e o neon da borda sem cortes ou distorções.

**Importante:** as duas imagens completas estão anexadas à conversa. Não declarar que estão no GitHub enquanto os binários originais não tiverem sido transferidos e conferidos pelo hash.

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

Os dois ícones **não precisam nem devem receber fundo branco**: seus arquivos originais já têm fundo preto. **Não trocar o fundo para branco nem aplicar um novo retângulo atrás.** Estas são convenções para Codex, **não uma afirmação de que os binários já estejam no GitHub**. Os arquivos fonte precisam ser transferidos para o workspace através da entrega/attachment correspondente; verificar SHA-256 antes de processar. Miniaturas WebP de preview, se adicionadas, não são substitutos de fontes.

## Critérios de aceite

- Logotipo inteiro, sem cortes, substitui texto na Home sem roubar foco D-pad.
- Ícone quadrado e banner de TV recebem recursos/atributos Android distintos.
- Nem o vídeo nem o ZIP devem ser empregados como recurso visual de interface da Home.
- A boot animation preserva o conteúdo real do vídeo e é validada para 720p/12fps no RK3229.
- Nenhum asset redesenhado por IA ou substituído por placeholder como resultado final.
