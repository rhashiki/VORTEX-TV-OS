# Preparar a compilação AOSP 7.1.2 / RK322x

O APK VortexHome já tem uma cadeia de compilação independente. Para gerar uma
ROM, ainda é necessário um BSP Android completo e identificado para a placa.
O repositório Vortex contém um módulo de aplicativo e um fragmento de produto;
não fornece um alvo de placa, kernel, DTB, loader ou HALs validados.

As fontes públicas reunidas em [AOSP_SOURCE_MAP.md](AOSP_SOURCE_MAP.md) servem
para investigar dependências. A presença de `rk322x_box`, de um DTS RK3229 ou de
um kernel 3.10.104 não demonstra compatibilidade com a R329Q_V8.0.

## Avançar com as informações já disponíveis

O proprietário confirmou que não pode fornecer novos dados da placa.
Não repetir pedidos de firmware-base, FlashID, identificação de Wi-Fi,
fotos ou diagnósticos. A restrição e o inventário conhecido estão em
[HARDWARE.md](HARDWARE.md).

A investigação deve usar os identificadores já registrados para procurar e
auditar bases públicas. Resolver as dependências de uma base candidata e, com
fontes completas e ambiente adequado, compilar primeiro o módulo e depois
uma imagem experimental continua sendo uma tarefa possível de desenvolvimento.
O repositório atual ainda não contém esse BSP completo. Não exigir que o
proprietário o encontre para retomar os trabalhos no aplicativo e nas fontes.

Classificar cada entrega pela evidência: APK validado; base candidata auditada;
imagem compilada sem validação física; ou ROM com boot físico demonstrado.
Uma compilação genérica RK322x pode comprovar parte da cadeia de build, mas
não resolve por si só os componentes desconhecidos desta unidade. Os critérios
físicos ao fim deste documento continuam pendentes, sem virar novos pedidos de
coleta de dados ao proprietário.

## Pré-verificação sem alterar o BSP

Use Python 3.9 ou superior para o verificador. Em uma árvore BSP já disponível,
selecione o JDK 8 indicado para Android 7.x.
Mantenha essa configuração separada do JDK 11 usado para compilar o APK Gradle.
O script confere `java` e `javac` selecionados por `JAVA_HOME` ou `PATH` e recebe a raiz BSP.
Fornecer também um manifesto resolvido, com revisão completa de 40 caracteres
hexadecimais por projeto:

```sh
python3 tools/aosp_preflight.py /caminho/absoluto/para/bsp --manifest-lock /caminho/evidencias/manifest-lock.xml
python3 tools/aosp_preflight.py /caminho/absoluto/para/bsp --manifest-lock /caminho/evidencias/manifest-lock.xml --json
```

Execute o script a partir deste repositório. Para guardar o JSON, redirecione a
saída para um arquivo de evidência fora da árvore BSP. Sem `--manifest-lock`, o
resultado permanece bloqueado: `.repo/manifest.xml` sozinho não prova as revisões
resolvidas. Gerar o lock manualmente com `repo manifest -r` na árvore BSP revisada,
gravando a saída em um caminho de evidências externo; o preflight não executa
esse comando nem compara automaticamente o lock com todos os checkouts.
O script não baixa fontes, não executa os scripts de build do BSP, não compila
e não grava na TV Box.

| Resultado | Interpretação |
| --- | --- |
| Código de saída 2 | Há bloqueios no caminho, nos arquivos inspecionados ou na cadeia Java. Corrigir os itens relatados e repetir. |
| Código de saída 0 | Os pré-requisitos que o script consegue inspecionar foram encontrados. Não é uma aprovação da compilação, da ROM ou do hardware. |

A inspeção usa o perfil da árvore comunitária `rk322x_box` indicada no mapa de
fontes, não um perfil universal para qualquer BSP Rockchip. Procura:

- AOSP: `build/envsetup.sh`, `build/core/main.mk` e `build/core/version_defaults.mk`,
  com versão Android 7.1.2 e API 25.
- Device: `device/rockchip/rk322x/BoardConfig.mk`, `AndroidProducts.mk` e
  `rk322x_box.mk`; `device/rockchip/common/BoardConfig.mk` e `tv/tv_base.mk`.
- Vendor: `vendor/rockchip/rk322x/device-vendor.mk` e `Android.mk`, presentes
  na revisão candidata `50c7170`. O `BoardConfigVendor.mk` aparece apenas como
  `-include` opcional na device tree e não existe nesse vendor público; sua
  ausência não é uma falha de pré-requisito desse perfil.
- Kernel: `kernel/Makefile` e `kernel/arch/arm/boot/Image`.
- Inventário de origem: `.repo/manifest.xml` e o lock fornecido explicitamente.

Um BSP com outra organização pode exigir outro perfil de inspeção, depois de
revisar suas dependências reais. Um nome de arquivo encontrado não confirma que
seu conteúdo serve para a placa. O inventário SHA-256
usa caminhos explícitos; não varre o diretório pessoal nem arquivos de segredos.
Hashes registram o conteúdo observado, mas não comprovam procedência, licença
ou compatibilidade. O script não substitui a revisão do manifesto completo,
das revisões dos projetos e das dependências transitivas do BSP.

Os testes da ferramenta usam árvores sintéticas para verificar rejeição de
entradas ausentes ou incompletas. Uma fixture aceita é apenas um teste do
verificador, não um BSP aprovado. Para executá-los:

```sh
python3 -m unittest discover -s tests -p test_aosp_preflight.py -v
```

## Antes de tentar compilar

1. Registrar o manifesto completo do BSP com revisões fixadas, origem dos
   projetos, licenças e hashes dos blobs que serão usados. Conferir as árvores
   `device/rockchip/common`, `device/rockchip/rk322x`, `vendor/rockchip` e kernel
   correspondentes ao produto escolhido; uma árvore comunitária isolada não
   fornece todas essas dependências.
2. Conferir as dependências de host e os compiladores exigidos por essa revisão
   do BSP. Dispor de JDK 8 e dos arquivos âncora não comprova que o host está
   pronto. Planejar armazenamento de fontes, intermediários e imagens; os cerca
   de 23 GB livres nesta sessão não constituem espaço de build AOSP validado.
3. Identificar o produto Android e sua configuração real de placa. Conferir
   kernel/configuração, DTB, flash e partições, DDR/trust/loader, módulos Wi-Fi,
   IR e HALs HDMI/GPU/VPU/áudio. Não trocar esses componentes por variantes de
   outra revisão da placa só por terem nomes parecidos.

## Integrar VortexHome ao produto confirmado

Somente após revisar o BSP, colocar uma cópia do Vortex fixada em um commit
registrado em `vendor/vortex/home`. O `Android.mk` desse diretório define o
módulo `VortexHome`, API 25, Java 8/Jack e assinatura de plataforma. Esses
parâmetros continuam sujeitos à compilação real na revisão Nougat escolhida.

No produto de placa já identificado, herdar o fragmento:

```make
$(call inherit-product, vendor/vortex/home/rom/vortex_product.mk)
```

Esse fragmento adiciona o aplicativo e a propriedade de pouca RAM. Ele não cria
produto de placa, alvo `lunch`, drivers ou esquema de boot. Revisar também os
outros launchers incluídos no produto e o comportamento da Home padrão.

Preparar o ambiente com o `build/envsetup.sh` revisado do BSP e selecionar
somente o alvo `lunch` confirmado para esse produto. Primeiro compilar o módulo
`VortexHome` pelo mecanismo de build dessa árvore; no ambiente AOSP que fornece
a função `m`, o alvo é `m VortexHome`. Registrar o comando, o alvo, o status e o
caminho real do APK produzido. Depois validar o aplicativo nessa ROM, incluindo
permissões de energia e confirmação do PackageInstaller.

Só avançar para a imagem completa com o módulo e o BSP compilados e seus
resultados registrados. Usar os alvos e o empacotamento documentados pelo BSP,
sem presumir que uma imagem Android genérica tenha o formato Rockchip correto.
Guardar logs, versões e SHA-256 de cada artefato. Um APK compilado não é uma
ROM flashável; uma imagem gerada não comprova boot.

## Aprovação física continua obrigatória

Seguir [BOARD_BRINGUP_CHECKLIST.md](BOARD_BRINGUP_CHECKLIST.md): confirmar flash,
DDR/loader/trust, DTB, rede, IR e a recuperação Loader/MaskROM da unidade antes
de qualquer escrita. O proprietário dispensou o backup original. Como não há
novos dados físicos disponíveis, identificação e recuperação continuam sem
comprovação; isso não deve gerar outro pedido de diagnóstico ao proprietário.
Escrita física exige autorização
explícita e não é uma etapa deste preflight.

Após uma futura compilação, registrar o boot real e testar HDMI/áudio, GPU/VPU,
Wi-Fi/Ethernet, USB, controle remoto, energia, persistência e instalação de APKs.
Os testes na nuvem ou em Android x86 não aprovam drivers ARM/Rockchip. A Build 01
só fecha depois desses critérios na TV Box. Não usar GitHub Actions.
