# Vortex TV OS — Roadmap oficial

**Produto:** Vortex TV OS (não existe versão Lite). **Hardware prioritário:** MXQ PRO 4K 5G / PCB R329Q_V8.0 / RK322x / 1 GB DDR3 / Android 7.1.2.

> Documento canônico para Codex e desenvolvimento. Nenhuma referência visual gerada automaticamente pode substituir os arquivos oficiais enviados pelo proprietário.

## Identidade visual APROVADA — 25/10/2026

As quatro peças a seguir são oficiais e distintas:

| Peça | Original recebido | Papel | Uso no Android | SHA-256 do original |
|---|---|---|---|---|
| **Logo oficial completo** | `1000915946.png` (JPEG real, 1536×646) | Marca "VORTEX TV OS", ondas brancas | Substituir **o texto** "VORTEX TV OS" no topo da Home por um `ImageView` contendo a marca integral; preservar proporção e brilho | `0cb93dcdc414487b0095499260a069fe5ae9dbd3cafd1fb5992a0ed02f9d0920` |
| **Ícone quadrado oficial** | `1000915968.png` (JPEG real, 1536×1536) | App launcher icon com ondas neon e moldura quadrada arredondada | `android:icon`, mipmap/drawable e atalhos quadrados | `bc20b1af97cdead54e3d12f6a4b224e7cd9860c80aaeeb685430e43e55bba7d3` |
| **Ícone/banner Android TV oficial** | `1000915967.png` (JPEG real, 1536×864, 16:9) | Banner horizontal com as mesmas ondas neon | `android:banner`, card/ícone Leanback, apresentação na TV | `fae9dca1d4da7c0f7082daeed0a67300a45e2bda663bdcdcbc9daabb089b707c` |
| **Boot animation OFICIAL** | `1000915952.mp4` (1280×720, 24 FPS, 4s, 96 quadros) | Animação da inicialização da ROM | Gerar `bootanimation.zip` Android otimizado, **substituindo a versão antiga de seis segundos** | `627b735c3709eff96f9d0bf69c38470a27f1d8ed095c82f6799c97c238ac0d9d` |

**Não confundir:** as imagens neon quadrada e horizontal são ícones do **aplicativo Launcher**; o logo branco completo com texto é a marca na **Home**. O vídeo MP4 é exclusivo do **boot da ROM**, não é o ícone do app.

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
- Permite-se apenas redimensionamento, otimização de compressão e remoção cuidadosa de fundo para criar variantes **derivadas**, preservando sempre os arquivos originais.
- Miniaturas do repositório (quando existentes) são **pré-visualizações**, não substituem fontes completas.

## Build 01 — Core / identidade / hardware

- [x] Código-fonte inicial da Home, controles, Installer e integração experimental AOSP consolidado na `main`.
- [x] Compilação de APK debug e testes parciais em emulador reportados em `docs/VALIDATION_2026-10-25_CONTINUATION.md`.
- [ ] Integração das quatro peças de marca oficiais e atualização visual.
- [ ] Compilação e regressão completas, incluindo teste de QR/USB/PackageInstaller.
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
