# RK322x — contrato do monitor legado e bloqueios remanescentes

Foi auditada a combinação kernel Rockchip `6c04d006ae881944d32c19e68b992d0bd5ab4fde`
+ OP-TEE `2a5b1d1232f582056184367fb58a425ac7478ec6`, usando os configs e os
ELFs realmente compilados na etapa anterior. **Não houve boot, execução de SMC,
acesso a hardware nem rebuild completo do kernel nesta etapa.** Os 32 arquivos
examinados coincidem byte a byte com seus objetos Git pinados; hashes e URLs
imutáveis estão em `monitor-call-inventory.json`. O inventário delimita nove
serviços/caminhos, não aprova toda a ABI ou todos os drivers do kernel.

## O que efetivamente está compilado

O kernel usa ARM_PSCI, SMP, HOTPLUG_CPU, SUSPEND, PM_AUTOSLEEP e DVFS. Apesar
de PM_DEVFREQ estar desabilitado, ARM_TRUSTZONE também está desabilitado:
a regra mach-rockchip/Makefile ainda inclui o driver legado `ddr_freq.o`.
O vmlinux contém `ddrfreq_init`, `ddrfreq_task`, `clk_ddr_set_rate`,
`rkpm_enter`, as chamadas PSCI e os wrappers FIQ/SIP examinados.

O ELF OP-TEE contém CPU_ON/OFF fortes; `psci_cpu_suspend` é weak e sua
instrução real é `mov r0,0xffffffff; bx lr` (disassembly preservado).
O monitor não habilita um `SM_PLATFORM_HANDLER`; os SIP vendor nomeados
`0x82000001`–`0x8200000c` não estão no dispatcher de fastcalls e retornam
unknown `0xffffffff`. O suporte PSCI padronizado não implementa esses serviços.

| Serviço | Caminho nas fontes e consequência |
| --- | --- |
| `0x8200000a` versão SIP | arch_initcall consulta quando há cpu_on no DT. Unknown escolhe SIP v1; o registro de v1 não prova suporte do monitor. |
| `0x82000003` controle de suspend | `rk322x_suspend_init` lê ctrbits e envia o SMC no init_late. Descarta o retorno e apenas imprime a configuração. Continua no perfil suplementar. |
| `0x82000008` DDR | O worker legado usa callbacks instalados por RK322x. `clk_ddr_set_rate` trata o retorno bruto u32 como MHz e devolve sucesso; unknown não vira errno. |
| `0x82000005` FIQ/UART | O SDK ativa o debugger, que tenta a ABI vendor. O helper detecta unknown, mas a montagem ARM_PSCI do debugger ignora seu erro. Não é uma console aprovada. |
| `0x84000003/2` CPU_ON/OFF | IDs e argumentos básicos são coerentes com PSCI ARM32; existem implementações fortes no monitor. SMP/hotplug físicos continuam sem teste. |
| `0x84000001` CPU_SUSPEND | O kernel instala o ponteiro pela presença da propriedade DT, sem consulta de feature. O monitor retorna -1; o wrapper converte para -EOPNOTSUPP. A função RK322x superior descartava o erro. |
| `0x8200000b` remote | O nó PWM atual não tem remote_support_psci e sai antes do SMC. Mesmo em outro DT, o driver trata erro inicial e mantém o parser PWM; isso não valida mapa IR. |
| `0x8200000c` VPU reset | Caminho condicional de recuperação do codec, após falha de idle request; retorno do SMC ignorado. Mídia/reset continua pendente. |

Não há `suspend_set_debug_enable` nesse kernel pinado. O controle efetivo é
`rk322x_suspend_init` acima. CPU_IDLE=y também não demonstra uso de
CPU_SUSPEND em idle: o driver local examinado é WFI de Cortex-A9, e retorna
-ENODEV no Cortex-A7. O suspend de sistema é o caminho separado de rockchip_pm.

## DTB suplementar com dois consumidores desabilitados

`rk3229-sdk-sd-monitor-gated.dts` inclui o perfil SD existente e altera apenas:

- `/fiq-debugger`: status de okay para disabled.
- `/dvfs/vd_logic/pd_ddr/clk_ddr`: status de okay para disabled.

Foram usados os mesmos flags CPP e o mesmo dtc do kernel, com novos caminhos
de saída externos às árvores antigas. Primeiro, o fonte base reproduziu
byte a byte o DTB anterior. O DTB novo tem **72.380 bytes**, SHA-256
`cfa9110af88ad776fd2cd528152920acdbef9a1d32a9a124fdd0381695b1e167`.

A comparação estrutural dos 468 nós verificou que somente essas duas
propriedades mudaram. Sete checks passaram, incluindo preservação de PSCI,
suspend, SD e nós internos. Nas fontes examinadas, o FIQ init consulta
of_device_is_available antes de registrar/inicializar o debugger; o DVFS
percorre somente filhos disponíveis, então não registra clk_ddr. O init
legado de DDR retorna -EINVAL antes de criar seu worker quando esse nó falta.
Isso é evidência de gating por DT, não execução dos initcalls ou prova de
remoção de todos os chamadores SIP no binário.

Desabilitar FIQ deixa uma **lacuna de console**: SERIAL_ROCKCHIP=y, mas
SERIAL_ROCKCHIP_CONSOLE=n; CMDLINE está vazio e o chosen não declara console.
UART1 está habilitado como dispositivo serial, UART2 está desabilitado.
O DTS de UART2 já referencia UART21 PB1/PB2, mas este ensaio não habilita outra
console ou presume a ligação física. Alterar status sozinho não compila suporte
de console. Não se introduziram novos pinos no perfil.

O controle vendor de suspend e a negociação de versão ainda são enviados.
As reservas OP-TEE core/SHM não foram acrescentadas por este suplemento.
CPU_SUSPEND, ABI SIP, DDR, console, reservas e comportamento físico continuam
requerendo fechamento antes de uma composição de boot Android.

## Correção pequena de erro de suspend, compilada como objeto ARM

`kernel-propagate-psci-suspend-error.patch` muda apenas o ramo PSCI de
`rkpm_enter`: guarda o retorno de `cpu_suspend`, executa o callback finish
existente e devolve o retorno real, em vez de zero incondicional.
Assim um erro não é relatado como sucesso. **Não implementa suspend no
monitor nem transforma CPU_SUSPEND em serviço suportado.**

`git apply --check` passou na fonte pinada. Os fontes C original e modificado
foram compilados como as traduções reais completas `rockchip_pm.c`, usando
o comando e o config ARM do kernel já compilado. Os dois compiles terminaram
com zero, sem novos avisos; não houve stubs ou tradução manual da função.
`suspend-error-fix-build.json` conserva comandos, hashes e escopo. A árvore e
o kernel anteriores permanecem intactos. O objeto novo não foi linkado em
um kernel completo e não foi executado em suspend/resume.

Patch SHA-256: `1014597d6a89fa50b976b019075babd58ea7b10acc1c8c797e36cd4f031c8ed8`.

Receitas de repetição: `compile_monitor_dtb.py`, `review_monitor_dtb.py`,
`compile_suspend_error_fix.py` e `collect_monitor_inventory.py`. Usam os
caminhos concretos deste workspace; não são instaladores ou instruções de flash.
Os artefatos desta revisão são componentes/objetos de referência, não uma
ROM nem uma imagem de cartão. Nenhum GitHub Actions foi consultado ou executado.
