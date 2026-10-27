# Cartão SD de instalação do Vortex

Objetivo esclarecido pelo proprietário: uma experiência semelhante ao disco
de instalação do Windows. O cartão inicia um instalador; após confirmação,
ele prepara as partições internas e instala o Vortex. Ao final, o cartão é
retirado e o sistema passa a iniciar da memória interna.

**Estado: arquitetura planejada. Não há instalador, imagem SD inicializável
ou ROM completa produzidos e validados.** A intenção de instalar não equivale
a uma gravação física já executada ou à aprovação de uma imagem desconhecida.

## Experiência pretendida

1. Com a TV Box desligada, inserir o cartão preparado e ligar o aparelho.
2. O boot pelo SD carrega um ambiente pequeno de instalação.
3. O instalador identifica o armazenamento interno, distingue-o do cartão e
   verifica a compatibilidade, integridade e tamanho do pacote de sistema.
4. A TV apresenta a opção **Instalar Vortex**, com aviso de remoção dos dados
   existentes e confirmação pelo controle remoto.
5. Somente depois da confirmação, prepara as partições necessárias conforme
   o layout validado, grava as imagens e verifica o resultado.
6. Informa a conclusão, orienta desligar e retirar o cartão. No próximo boot,
   a TV Box inicia o Vortex da memória interna.

Se o armazenamento ou o pacote não corresponder ao perfil suportado, o
instalador deve encerrar sem iniciar a gravação. A identificação deve ser
automática pelo software; não cria outro pedido de diagnóstico ao proprietário.
O procedimento de retomar/reparar uma instalação interrompida ainda precisa
ser projetado e testado antes de oferecer esse fluxo.

## Ambiente de instalação

Um Linux com initramfs é uma opção a investigar: pode executar o instalador
sem precisar iniciar toda a interface Android. Ainda exige bootloader/DDR,
kernel, acesso ao cartão, driver do armazenamento interno e vídeo/entrada
adequados. A escolha e a implementação desse ambiente permanecem abertas.

O cartão deverá conter a cadeia de boot, o ambiente de instalação, o pacote
Android completo e seus metadados de integridade/compatibilidade. As imagens
Android do destino continuam obrigatórias; um ambiente de instalação menor
não substitui a compilação e validação do Vortex completo.

No RK322x não há garantia de seleção automática do SD como em um PC com BIOS/
UEFI. Há referências públicas de boot externo para a família, mas a unidade
R329Q_V8.0 ainda não executou uma imagem deste projeto. Copiar arquivos ou o
APK para um cartão comum não o torna inicializável.

“Limpar partições” deve seguir o formato real do armazenamento e o layout de
instalação. Não significa apagar indiscriminadamente o chip inteiro. NAND e
eMMC podem exigir drivers, tratamento de blocos e empacotamento distintos;
loader DDR, áreas de boot e caminho de recuperação precisam de tratamento
específico. Não há receita de gravação escolhida para esta unidade.

## Relação com o perfil de teste existente

O [teste externo](EXTERNAL_BOOT_PLAN.md) continua como etapa de desenvolvimento
e validação. Não é a experiência final de instalação pedida pelo proprietário.
O [kernel SD atual](sdcard/SD_REFERENCE.md) desabilita NAND/eMMC no DTS e
RK_NAND/MTD na configuração; ele não pode servir diretamente como instalador
interno. Deve permanecer preservado, com um perfil separado para o instalador.

O [U-Boot compilado](bootloader/README.md) também não tem payload Android nem
autoboot configurados. O instalador precisará integrar o boot real do cartão;
não é necessário habilitar escrita interna no U-Boot se ela ocorrer no Linux.
Modificar o loader interno ou apagar flash para forçar o boot não deve ser
apresentado como simples inicialização independente por cartão.

## Trabalho restante

- Comprovar a cadeia de boot externa e integrar kernel/initramfs de instalação.
- Integrar e testar identificação automática e acesso correto à NAND/eMMC.
- Compilar as imagens Android e definir layout, metadados e validação do pacote.
- Implementar interface por controle remoto, confirmação, escrita, verificação
  e recuperação de falhas/interrupção, inicialmente em alvos simulados.
- Construir a mídia, inspecionar seus conteúdos e validar na TV Box antes de
  disponibilizar um procedimento de instalação definitiva.

O [relatório mais recente](../docs/VALIDATION_2026-10-27_PRODUCT.md) registra
os componentes já compilados e os bloqueios atuais. Nenhuma operação de
formatação, gravação de cartão ou flash foi executada para definir este plano.
