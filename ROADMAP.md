# Vortex TV OS — Roadmap oficial

**Produto:** Vortex TV OS (não existe versão Lite). **Hardware prioritário:** MXQ PRO 4K 5G / PCB R329Q_V8.0 / RK322x / 1 GB DDR3 / Android 7.1.2.

> Documento canônico para Codex e desenvolvimento. Nenhuma referência visual gerada automaticamente pode substituir os arquivos oficiais enviados pelo proprietário.

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

## Identidade visual APROVADA — 25/10/2026

As quatro peças a seguir são oficiais e distintas:

| Peça | Original recebido | Papel | Uso no Android | SHA-256 do original |
|---|---|---|---|---|
| **Logo oficial completo** | `1000915946.png` (JPEG real, 1536×646) | Marca "VORTEX TV OS", ondas brancas | Substituir **o texto** "VORTEX TV OS" no topo da Home por um `ImageView` contendo a marca integral; preservar proporção e brilho | `0cb93dcdc414487b0095499260a069fe5ae9dbd3cafd1fb5992a0ed02f9d0920` |
| **Ícone quadrado oficial** | `1000915968.png` (JPEG real, 1536×1536) | App launcher icon com ondas neon e moldura quadrada arredondada | `android:icon`, mipmap/drawable e atalhos quadrados | `bc20b1af97cdead54e3d12f6a4b224e7cd9860c80aaeeb685430e43e55bba7d3` |
| **Ícone/banner Android TV oficial** | `1000915967.png` (JPEG real, 1536×864, 16:9) | Banner horizontal com as mesmas ondas neon | `android:banner`, card/ícone Leanback, apresentação na TV | `fae9dca1d4da7c0f7082daeed0a67300a45e2bda663bdcdcbc9daabb089b707c` |
| **Boot animation OFICIAL** | `1000915952.mp4` (1280×720, 24 FPS, 4s, 96 quadros) | Animação da inicialização da ROM | Gerar `bootanimation.zip` Android otimizado, **substituindo a versão antiga de seis segundos** | `627b735c3709eff96f9d0bf69c38470a27f1d8ed095c82f6799c97c238ac0d9d` |

**Não confundir:** as imagens neon quadrada e horizontal são ícones do **aplicativo Launcher**; o logo branco completo com texto é a marca na **Home**. O vídeo MP4 é exclusivo do **boot da ROM**, não é o ícone do app.

### Pré-visualizações já versionadas

Os arquivos abaixo foram reduzidos somente para **prévia documental** (não usar como masters da marca nem publicar no APK final sem as fontes em resolução adequada):

- [Ícone quadrado do Launcher](branding/previews/launcher-icon-square.webp) — 96×96
- [Ícone horizontal para Android TV](branding/previews/launcher-banner-tv.webp) — 96×54
- [Logo completo da Home](branding/previews/home-logo-complete.webp) — 96×40

Os **originais** 1536px, identificados por hashes acima, são obrigatórios para gerar os recursos definitivos. O vídeo MP4 e `bootanimation.zip` oficial continuam disponíveis nos artefatos desta conversa e **não estão versionados no repositório**.

### Boot animation preparada a partir do MP4 oficial

- Arquivo gerado no ambiente de artefatos: `Vortex_TV_OS_bootanimation_official.zip`
- 1280×720, 12 FPS, 48 quadros no segmento único `part0`, último quadro mantido em loop `part1`, ZIP sem compressão dos quadros.
- Cerca de **3,07 MB**; SHA-256 `8b76829b7d9255ccc42ca6e7f0b98ac7696beccb10822ea5feebc0e0b6b02c86`.
- **Importante:** esta anotação documenta o arquivo produzido na conversa; não presume que MP4 e ZIP já estejam versionados no GitHub. Codex deverá adicionar o binário recebido no workspace ou regenerar a partir do MP4 original usando `tools/bootanimation_from_video.py`; validar o resultado com vídeo real, não criar animação alternativa.
- A boot animation final do Android não executa arquivos MP4 diretamente: o `bootanimation.zip` contém PNGs e `desc.txt`. Confirmar localização no firmware AOSP.

### Tarefas aprovadas para a Home (Build 01)

- [ ] Registrar os arquivos originais de marca como assets de build e preservar seus hashes.
- [ ] Substituir **somente o título textual superior** no `HomeActivity.java` por `ImageView` com o logo completo.
- [ ] Manter hora/data, foco por controle IR/D-pad, cards de apps e o desempenho 720p.
- [ ] Configurar no `AndroidManifest.xml` o ícone quadrado `android:icon` e o banner 16:9 `android:banner`; gerar resoluções adaptadas sem distorção.
- [ ] Assegurar que a imagem da Home não seja confundida com ícone do aplicativo.
- [ ] Atualizar screenshot e prévia visual, conferindo contraste e margens em 1280×720.
- [ ] Testar APK em Android API25; medir memória, tempo de abertura e footprint dos assets.
- [ ] Integrar o `bootanimation.zip` otimizado na árvore AOSP; validar o player de boot real no RK3229.

### Regras de integridade visual

- **Nunca redesenhar, simplificar, regenerar ou trocar** as duas ondas do logotipo.
- Preservar as duas opções de ícone entregues pelo usuário; manter suas proporções originais.
- Não aplicar fontes inventadas, overlays ou estilos não autorizados às imagens oficiais.
- Permite-se somente redimensionamento proporcional e compressão dos recursos derivados. **Não remover nem substituir o fundo preto original dos ícones. Não adicionar fundo branco ou placas de apresentação.** Preservar os originais.
- Miniaturas do repositório (quando existentes) são **pré-visualizações**, não substituem fontes completas.

## Build 01 — Core / identidade / hardware

**Estratégia de teste definida pelo proprietário:** priorizar boot por microSD,
validar o Vortex na TV Box e só depois preparar a instalação definitiva.
Pendrive é alternativa condicionada ao bootloader. Seguir
[rom/EXTERNAL_BOOT_PLAN.md](rom/EXTERNAL_BOOT_PLAN.md); a imagem externa ainda
não foi compilada nem testada. Preservar a memória interna durante essa etapa
é um critério a demonstrar, não uma garantia já estabelecida.

- [x] Código-fonte inicial da Home, controles, Installer e integração experimental AOSP consolidado na `main`.
- [x] Compilação de APK debug e testes parciais em emulador reportados em `docs/VALIDATION_2026-10-25_CONTINUATION.md`.
- [x] Adquirir candidatos device/common/vendor em revisões fixas e verificar os patches de montagem SD em fontes reais; [resultados](docs/VALIDATION_2026-10-25_SD.md). Isso não comprova uma imagem inicializável.
- [x] Compilar kernel/DTB SDK com restrições SD, retirar caminhos vendor/fábrica conhecidos e conferir DTB/fstab/config/cmdline; [resultados](docs/VALIDATION_2026-10-26_SD_PROFILE.md). Continua sem sistema Android ou mídia de boot completos.
- [x] Compilar VortexHome pelo make/Jack AOSP r6 e validar o APK em API25; compilar TPL/SPL/U-Boot/OP-TEE em ensaio separado, com [resultados e bloqueios de ABI](docs/VALIDATION_2026-10-26_AOSP_BOOTLOADER.md). Isso não conclui a imagem Android ou o boot físico.
- [x] Corrigir o contrato framebuffer nas fontes fixadas, compilar quatro objetos gralloc e concluir upload/confirmar/cancelar/abrir app pela Home no emulador; [resultados e limites](docs/VALIDATION_2026-10-27_GRAPHICS_MONITOR.md). Ainda sem link HAL, Android completo ou validação física.
- [ ] Integração das quatro peças de marca oficiais e atualização visual.
- [ ] Compilação e regressão completas, incluindo teste de QR/USB/PackageInstaller.
- [ ] Compilar uma imagem de teste microSD e demonstrar boot externo com a instalação interna preservada.
- [ ] Confirmar flash ID exato, NAND, Wi-Fi, DDR loader, DTB, áudio/HDMI, GPU/VPU e controle IR da **unidade R329Q_V8.0**.
- [ ] AOSP/firmware flashável e **boot físico real** testados; não declarar ROM pronta antes disso.
- [ ] Medir metas: firmware compactado ≤ 600MB, sistema ≤ 800MB e RAM em repouso ≤ 450MB (metas, não resultados garantidos).

## Build 02 — Final / estabilidade

- [ ] Regressão completa do Installer por QR, segurança de sessão e pendrive, acesso a apps e recuperação de Home.
- [ ] Otimização de RAM/CPU, zRAM sob medição, boot/reinício seguro; Wi-Fi/Ethernet sem Bluetooth.
- [ ] Pacote de gravação e procedimento de recuperação específicos da placa, testados.

### Regras operacionais para Codex

- Trabalhar no repositório `rhashiki/VORTEX-TV-OS` em commits consolidados, evitando perda de alterações.
- **Nunca executar, criar, consultar ou depender de GitHub Actions.**
- Validar usando ambiente Linux/Android SDK/Gradle e testes locais; testes de emulador não provam suporte RK3229.
- Não fazer flash sem identificação de memória flash, bootloader e caminho de recuperação.
- Documentar separadamente: código implementado, artefatos efetivamente compilados e testes físicos pendentes.

Consulte também [docs/BRANDING.md](docs/BRANDING.md) e [docs/WORK_MODE_HANDOFF.md](docs/WORK_MODE_HANDOFF.md).
