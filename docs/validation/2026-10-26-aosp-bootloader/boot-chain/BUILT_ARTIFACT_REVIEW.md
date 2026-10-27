# Revisão dos artefatos U-Boot — antes e depois do pinconf

O primeiro build terminou com código zero, mas seus DTBs SPL/TPL tinham
phandles de configuração de pinos pendurados. Os grupos SD/UART estavam
presentes, porém os nós pcfg não. A função pinctrl-rockchip-core.c retorna
-ENODEV para esse caso. Isso demonstrou por que sucesso de build e nomes de
grupos não bastam para aprovar a composição.

A cópia dos três DTBs anteriores e seus hashes está em before-pinconf-fix/;
before-pinconf-review.json registra a falha. O agente principal acrescentou
bootph-all aos nós pcfg_pull_none_drv_12ma, pcfg_pull_none e pcfg_pull_up e
reconstruiu. Este revisor não alterou fontes ou saídas do build.

built-artifact-review.json registra a nova inspeção, com os nove agregados
estáticos aprovados. Os três DTBs reais agora preservam SD ativo, alias mmc0
para 30000000 e ordem SPL somente mmc0; eMMC está desabilitado e SDIO está
desabilitado ou ausente. Todos os phandles ativos SD/UART resolvem, com SD
PC2-PC5 mux1 e UART21 PB1/PB2 mux2.

A configuração resolvida e o ELF U-Boot contêm OPTEE_LIB e ambiente NOWHERE,
sem os comandos/backends de escrita enumerados. O ambiente foi extraído do
símbolo default_environment do ELF, não inferido só do arquivo-fonte: contém
apenas os sete pares explícitos, incluindo boot_targets=mmc0, bootdelay=-1 e
bootcmd de mensagem. O símbolo optee_copy_fdt_nodes está compilado; isso não
demonstra que a cópia das reservas foi executada no boot.

O FIT foi inspecionado com libfdt e dumpimage. Firmware=op-tee, loadables=u-boot;
o OP-TEE está em load/entry0x68400000 e seus bytes são exatamente os de
tee-raw.bin compilado, não um blob substituto. final-dumpimage.txt preserva a
listagem. Os DTBs SPL/TPL e o FIT são FDTv17 com last-compatible2, aceitos pelo
libfdt; o contrato estreito do auditor Linux anterior não foi ampliado para
este ensaio de bootloader.

Esses resultados verificam arquivos e símbolos estáticos. Não comprovam
execução, preservação física da memória interna, temporização DDR, elétrica,
UART da placa, serviços SIP vendor ou imagem Android/mídia inicializável.
