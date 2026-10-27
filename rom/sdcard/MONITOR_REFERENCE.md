# Perfil complementar para o monitor aberto

Este é um complemento experimental ao [perfil SD SDK](SD_REFERENCE.md),
sem aprovação da placa R329Q_V8.0. Não é mídia inicializável nem deve ser
combinado como uma ROM pronta com os arquivos de boot anteriores.

O OP-TEE RK322x compilado não implementa os serviços SIP Rockchip usados
pelo FIQ debugger e pelo gerenciamento DDR legado do kernel 3.10. A opção
`PM_DEVFREQ=n` sozinha não retira esse gerenciamento DDR: ele tem outro
caminho de registro e worker. Retornos desconhecidos não podem ser tratados
como leituras válidas de frequência.

[rk3229-sdk-sd-monitor-gated.dts](rk3229-sdk-sd-monitor-gated.dts) inclui o DTS
SD anterior e desabilita somente `/fiq-debugger` e o clock de DVFS DDR.
O DTB foi compilado e comparado estruturalmente: apenas essas duas propriedades
`status` mudaram, em 468 nós. Nas fontes examinadas, o primeiro não registra
o dispositivo e o segundo impede o registro do worker DDR legado. As funções
SIP continuam no binário; não se afirmou ausência de qualquer chamada vendor.

Para reproduzir a compilação do DTB no build do kernel, copiar o DTS SD base
e este complemento para `arch/arm/boot/dts/`, usar a configuração e as
ferramentas da [referência SD](SD_REFERENCE.md) e pedir o alvo
`rk3229-sdk-sd-monitor-gated.dtb`. A evidência desta etapa usou o mesmo
preprocessador e dtc do build anterior, com saída isolada: recompilar o DTS
base reproduziu exatamente seu hash antes da comparação do complemento.
Não foi ligado um novo kernel completo para esse perfil.

Há uma lacuna de console: o kernel anterior não tem
`CONFIG_SERIAL_ROCKCHIP_CONSOLE`, e desabilitar FIQ não habilita um console
serial comum. UART1 está habilitada no DTS, UART2 desabilitada; as rotas
físicas continuam desconhecidas. Este complemento conserva esses estados,
sem inventar uma UART da unidade ou instrução de conexão.

## Propagação de erro de suspensão

[kernel-propagate-psci-suspend-error.patch](kernel-propagate-psci-suspend-error.patch)
pertence ao kernel `6c04d006ae881944d32c19e68b992d0bd5ab4fde`. Pode ser
aplicado depois dos patches de compilação e sem NAND já documentados; a
aplicação foi conferida na árvore correspondente. `rkpm_enter` ignorava o
retorno de `cpu_suspend`, executava o callback de finalização e retornava
sucesso. O patch mantém o callback e devolve o erro real. O monitor retorna
não suportado para CPU_SUSPEND; o patch não implementa suspensão.

O arquivo C real, antes e depois, compilou em objeto ARM usando os includes,
configuração e flags do kernel existente. **O Image anteriormente entregue
não contém esse patch.** Ainda falta compilá-lo e ligá-lo no kernel completo,
além de testar os caminhos de erro e suspend/resume em hardware.

## Limites que permanecem

Negociação de versão SIP e configuração de suspensão ainda fazem chamadas
vendor no boot, cujos retornos desconhecidos seguem fallbacks legados.
CPU_ON/OFF padronizados não aprovam o restante da interface. O DTB Linux
entregue pelo bootloader ainda precisa reservar core/SHM do OP-TEE e ter
console e seleção de mídia efetivos verificados. DDR, clocks, voltagens,
pinagem e periféricos permanecem referências genéricas.

[Relatório, comandos, inventário SIP e hashes](../../docs/VALIDATION_2026-10-27_GRAPHICS_MONITOR.md).
Não houve escrita na TV Box, boot físico ou produção de Android completo.
