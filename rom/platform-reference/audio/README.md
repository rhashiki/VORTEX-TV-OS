# Áudio RK322x por Android.mk

O ramo tinyalsa_hal de `hardware/rockchip/audio` é a fonte usada pelo candidato
Nougat. O audio_policy.rk30board do ramo legacy não é um módulo desse fluxo.

A composição exige a TinyALSA Rockchip de revisão
`472b5e3fc1660660e0e9a3fa4cd5f752643920f2`, no path `external/tinyalsa`.
O áudio selecionado inicializa `pcm_config.flag`; a versão AOSP r6 não tem
esse campo. A fonte Rockchip o declara e o propaga para os parâmetros PCM.
Retirar o membro para forçar a compilação alteraria esse contrato.

Aplicar [0001](patches/0001-audio-reject-unsupported-hdmi-bypass-rate.patch)
na raiz de `hardware/rockchip/audio`, revisão
`03b111b6736b48ec17ffee4906caecf59323d8c1`. Antes, uma taxa não reconhecida no
ramo HDMI bypass deixava outputtype indefinido e podia usá-lo como índice.
A correção encerra a abertura com -EINVAL pelo caminho de limpeza existente.
Não estabelece uma taxa ou um dispositivo físico substituto.

O ensaio real Android.mk compila quatro HALs e suas dependências fonte com
Clang da base selecionada. Ainda utiliza bibliotecas de plataforma API25 de
referência, não um Android inteiro compilado de fonte. Testes de função host
e carregamento de metadados no linker Android não comprovam reprodução,
captura, HDMI/SPDIF/USB, mixer ou comportamento da R329Q_V8.0.

Os avisos legados restantes ficam nos logs. Este diretório contém somente a
correção e a documentação, sem blobs vendor, bibliotecas SDK ou firmware.
