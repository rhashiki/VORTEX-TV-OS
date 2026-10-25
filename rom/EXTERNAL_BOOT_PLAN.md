# Testar por microSD antes da instalação interna

Estratégia proposta pelo proprietário em 25/10/2026: iniciar o Vortex por
cartão SD ou pendrive, testar na TV Box e só depois preparar a instalação
definitiva. **Prioridade de investigação: microSD.** Pendrive fica condicionado
ao suporte do bootloader. Não há imagem Vortex de boot externo pronta ou
testada nesta etapa; o artefato compilado existente continua sendo o APK.

Usar os dados já enviados e as fontes públicas. O proprietário não consegue
obter novas informações da placa; seguir [HARDWARE.md](HARDWARE.md), sem
repetir pedidos de identificação ou diagnósticos.

## Evidência encontrada

| Fonte examinada | Evidência | Limite |
| --- | --- | --- |
| [fstab SD do Android RK322x](https://github.com/D042888-2/android_device_rockchip_rk322x/blob/f33a129bfab6d9cc87184ee3bf032224801fa446/fstab.rk30board.bootmode.sd) | `/system`, `/cache`, `/metadata`, `/data` e `/misc` apontam para partições sob `ff500000.rksdmmc`. Existe configuração candidata para colocar o sistema no SD. | Arquivo de configuração não comprova boot da placa nem fornece loader/kernel/HALs completos. Os endereços pertencem a essa referência, não são identificação confirmada da unidade. |
| [device.mk da mesma revisão](https://github.com/D042888-2/android_device_rockchip_rk322x/blob/f33a129bfab6d9cc87184ee3bf032224801fa446/device.mk) | Copia os fstab `unknown` e `emmc`; não copia o fstab `sd`. | O fluxo SD não está integrado por esse trecho. É necessário auditar o restante do BSP, a seleção de bootmode e o ramdisk antes de ativá-lo. |
| [Multitool: extlinux RK322x](https://github.com/paolosabatino/multitool/blob/d7dc392fe33850f5975aa466538fd889629c430c/sources/rk322x/extlinux.conf) | Carrega kernel/DTB e seleciona a raiz por PARTUUID do meio de boot. É uma referência concreta de boot Linux externo para a família. | Multitool/Armbian não executam o Android Vortex. Iniciar Linux não comprova HALs Android, aceleração gráfica ou suporte desta unidade. |
| [Multitool: Jump Start](https://github.com/paolosabatino/multitool/blob/d7dc392fe33850f5975aa466538fd889629c430c/sources/multistrap/multitool.sh#L28) | O aviso informa que grava um U-Boot alternativo na NAND e impede o boot do firmware existente. A função [do_install_jump_start](https://github.com/paolosabatino/multitool/blob/d7dc392fe33850f5975aa466538fd889629c430c/sources/multistrap/multitool.sh#L1044) grava U-Boot/TEE em `/dev/rknand0`. | Não usar essa operação para uma etapa que deve preservar a instalação interna. Também ficam fora dessa etapa apagar flash ou instalar loader interno para forçar boot externo. |
| [Multitool: init](https://github.com/paolosabatino/multitool/blob/d7dc392fe33850f5975aa466538fd889629c430c/sources/multistrap/init#L39) | Pode expandir a partição do próprio cartão e gravar logs nele. | Boot externo não significa ausência de toda escrita. A meta do teste Vortex é manter as escritas no meio externo e preservar a memória interna. Isso depende de auditoria da imagem final. |

Referências verificadas em 25/10/2026, com revisões fixadas nos links. Nenhuma
imagem foi gravada, nenhum bootloader foi escolhido e não houve teste físico.

## Etapa 1: imagem de teste externa

O próximo artefato de firmware desejado é uma imagem microSD do Android Vortex,
com cadeia de boot, kernel, ramdisk, sistema e dados preparados para esse meio.
Ela ainda exige as fontes completas e compatíveis descritas em
[AOSP_SOURCE_MAP.md](AOSP_SOURCE_MAP.md). Copiar o APK para um cartão não produz
essa imagem. O boot por SD pode reduzir a dependência dos drivers da flash
interna nessa etapa, mas continuam necessários DDR, DTB e drivers/HALs da placa.

Na preparação do BSP candidato:

1. Auditar o caminho de boot SD e seus componentes, incluindo escolha do
   bootmode, partições, kernel e drivers necessários já no início do boot.
   A presença de um fstab SD isolado não encerra essa tarefa.
2. Criar um perfil específico de teste externo. Conferir que sistema, cache,
   metadata, dados e misc sejam resolvidos para o cartão. Auditar também init,
   recovery, serviços de atualização e montagem automática para que não façam
   alterações na flash interna.
3. Compilar o módulo VortexHome e a imagem externa, registrar revisões, logs,
   layout e hashes. A mídia de teste não deve oferecer instalação automática
   nem alteração de loader interno como pré-condição escondida.
4. Preparar coleta automática de logs no cartão quando o sistema iniciar,
   sem depender de novos levantamentos manuais do proprietário. Essa coleta
   ainda é uma tarefa de integração, não um recurso já implementado.

Só uma imagem construída e auditada permitirá fornecer um procedimento de
preparo da mídia específico. Esta página não é uma instrução para gravar uma
imagem genérica ou usar as operações de instalação do Multitool.

## Etapa 2: teste na TV Box

Se a unidade iniciar a imagem externa, testar Home sem gaveta, D-pad/IR,
HDMI/áudio, GPU/VPU, rede, portas USB, Installer por celular e pendrive,
persistência no cartão e reinicialização. Registrar os resultados reais.

Retirar o cartão deve permitir retornar ao estado anterior **se a memória
interna tiver sido preservada e o bootloader original continuar funcional**.
Isso é um critério do teste, não uma garantia estabelecida para esta unidade.
Se o boot externo depender de modificar a flash interna, registrar a limitação
em vez de apresentar esse caminho como teste independente da instalação.

## Etapa 3: instalação definitiva

Preparar a instalação interna somente depois do teste externo satisfatório.
Ela precisa de empacotamento próprio para o armazenamento da unidade e de um
caminho de recuperação; não é uma cópia byte a byte do cartão para NAND/eMMC.
Um boot por SD bem-sucedido ainda não comprova o driver, a geometria ou o
layout de gravação da memória interna. Os critérios de
[BOARD_BRINGUP_CHECKLIST.md](BOARD_BRINGUP_CHECKLIST.md) continuam aplicáveis.

## Pendrive e USB de serviço

Pendrive só será uma alternativa quando o bootloader em uso suportar iniciar
por USB e o kernel conseguir montar o sistema nele. A configuração de U-Boot
do [Multitool](https://github.com/paolosabatino/multitool/blob/d7dc392fe33850f5975aa466538fd889629c430c/sources/rk322x/assets/stepnand-patches/u-boot-2001-rk322x-box-add-defconfig.patch#L37)
habilita USB/storage em uma variante, o que não comprova suporte no bootloader
atualmente instalado na TV Box.

O protocolo [RockUSB/MaskROM usado por rkdeveloptool](https://github.com/rockchip-linux/rkdeveloptool/blob/304f073752fd25c854e1bcf05d8e7f925b1f4e14/main.cpp#L1763)
conecta um computador à TV Box; é diferente de iniciar autonomamente por um
pendrive. Essas duas rotas não devem ser tratadas como equivalentes.
