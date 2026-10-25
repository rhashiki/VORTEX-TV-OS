# Vortex TV OS / R329Q_V8.0 — matriz de compatibilidade

## Limite de informação confirmado pelo proprietário — 25/10/2026

O proprietário já enviou todas as informações de que dispõe e informou que
não consegue obter outros dados específicos da unidade. **Não solicitar
novamente BSP/firmware-base, FlashID, chip Wi-Fi, fotos ou diagnósticos.**
Obter uma base pública e analisar suas dependências é trabalho de desenvolvimento;
não deve ser transferido ao proprietário como condição para continuar.

Os campos não confirmados abaixo permanecem desconhecidos. Isso não impede
continuar o aplicativo nem investigar/compilar uma base candidata, se houver
fontes e ambiente suficientes. Uma imagem candidata compilada continuará sem
compatibilidade física comprovada. Os critérios de hardware são limites de
validação, não uma nova lista de informações a cobrar do proprietário.

## Confirmado por fotos e AIDA64 do dispositivo

- PCB R329Q_V8.0 (data serigrafada 2019-03-30).
- Plataforma RK322x informada como RK3229, ARMv7 / 4× Cortex-A7 / GPU Mali-400.
- Quatro chips RAM Samsung 2 Gbit cada: cerca de 1 GB DDR3.
- Android 7.1.2 / API 25; kernel Linux 3.10.104; build `akrd2.20200424.110419`.
- O Android exibe informações alteradas (10.1 / 4+32 GB).

## Hipóteses ainda não verificadas na unidade

- Wi-Fi: provável SV6256P, mas há placas R329Q V8.0 com SSV6051P.
- Flash: provável NAND de 8 GB; **modelo, fabricante e FlashID desconhecidos**.
- Loader DDR, DTB, mapeamento de IR, módulos Wi-Fi, HALs gráficos e codecs proprietários ainda não foram extraídos nem validados.

## Portas de entrada para hardware

As consultas físicas abaixo permanecem como referência técnica. Dada a
restrição acima, não fazem parte de uma nova solicitação ao proprietário.
Priorizar análise de fontes e firmwares públicos com os identificadores já
registrados: `R329Q_V8.0`, `2019-03-30`, `akrd2.20200424.110419`, API 25 e
kernel `3.10.104`. Correspondência de nomes ou versão é indício para investigar,
não aprovação de loader, partições ou drivers.

1. Inspecionar pacote de firmware legítimo específico da placa; validar procedência, licenças, assinaturas e conteúdos.
2. Ler FlashID e dados da flash por RK322x Multitool ou Rockchip Loader/MaskROM em modo de consulta.
3. Confrontar loader DDR, `parameter`, kernel/DTB, NAND e Wi-Fi antes de qualquer gravação.
4. Validar vídeo HDMI, áudio, GPU/VPU, Ethernet, USB, Wi-Fi, controle IR, reinício e desligamento.
5. Definir um procedimento de recuperação sem exigir backup integral do Android antigo.

## Referências

- https://github.com/D042888-2/android_device_rockchip_rk322x/tree/aosp-7.1.2_r6
- https://github.com/rockchip-linux/rkdeveloptool
- https://github.com/rockchip-linux/rkbin
- https://github.com/rockchip-linux/mpp
- https://github.com/paolosabatino/ssv6x5x
- https://github.com/ratfumace/Klipper-OS-RK322x-R329Q-SSV6051

Repositórios externos são **referência**, não prova de compatibilidade com esta unidade.
