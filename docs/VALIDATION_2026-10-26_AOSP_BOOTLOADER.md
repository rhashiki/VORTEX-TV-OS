# Build 01 — módulo AOSP e componentes abertos de boot

Base desta etapa: `45d626a4bc508b49b8863bd67e2ce9f2f17554d5`.
Foram compilados o módulo VortexHome pelo AOSP r6 e componentes de boot
U-Boot/OP-TEE, em árvores separadas. O Android completo, o ramdisk e a imagem
SD do Vortex continuam sem compilação. Nenhuma TV Box foi iniciada ou alterada.

## Compilação real do módulo AOSP

`tapas arm eng VortexHome` e GNU make/Jack do AOSP oficial 7.1.2_r6
produziram o APK. O experimento não chamou Gradle nem traduziu manualmente
as regras de empacotamento. Usou o build fixado em
`5bcb8ef25cbb92b0f6ee9a40fb05bb47b5173774` e 22 arquivos SDK oficiais,
comparados com os objetos Git de `23f7de5ba433fc82269ba63c203fe0a3eaf4a680`.

Dois erros da integração do Vortex foram corrigidos:

- O parser Jack real rejeitava `LOCAL_JACK_ENABLED := true`; o módulo agora
  usa `full`, opção válida nessa versão.
- A versão vinha apenas do Gradle. O aapt AOSP recebia os valores da
  plataforma, e agora recebe explicitamente `1 / 0.1.0-dev`.

O host exigiu Python 2 local e um acp x86_64 compilado das fontes originais
r6. O zipalign i386 também não executava; foi usado o zipalign x86_64 do
SDK 33.0.2, por variável suportada do make. Portanto não se afirmou usar
todos os prebuilts de host r6 intactos. Java, Jack, aapt, API e regras APK
permaneceram r6. Os avisos de host ficaram visíveis nos logs.

O experimento terminou com cerca de 129 MB, mantendo a reserva de disco.
Isso permite validar o módulo aqui, mas não demonstra espaço para o BSP
completo. A assinatura é de **teste de plataforma AOSP**, sem identidade de
produção ou vínculo com a chave da TV Box.

## Execução do APK final e regressão

O APK final passou por instalação e 11 verificações em AVD novo:
metadados, Home, D-pad direita/esquerda, abertura do Installer, QR, HTTP 200,
fechamento dos sockets IPv4/IPv6 ao voltar, retorno à Home e ausência de
fatal exception do aplicativo. A imagem instalada era Android
**7.1.1/API25/x86**, 1280×720, em software; não era uma ROM 7.1.2 compilada.

A requisição HTTP ocorreu na interface privada do emulador. Não se repetiu
a regressão completa de upload/PackageInstaller, LAN com celular, USB físico
ou privilégios de energia. A primeira tentativa do harness assumia foco
inicial de D-pad num AVD em modo de toque; foi ajustado apenas o harness,
preservando a tentativa e sem mudar o app. O AVD isolado foi encerrado.

A validação local normal também passou: **96 testes Python/JVM**, assemble
debug e lint Gradle. O APK Gradle permanece com 69.098 bytes e hash
`bedc7e95321c533e650f198f14e737f611aa765de5aebc6c46f930725fa9074b`.
Nenhum código Java, recurso visual ou comportamento de gaveta foi alterado.

## Componentes de boot efetivamente compilados

U-Boot v2024.01 `866ca972d6c3cabeaf6dbac431e8e08bb30b3c8e` e
OP-TEE 4.0.0 `2a5b1d1232f582056184367fb58a425ac7478ec6` compilaram
com GCC ARM 6.3.1, em perfis RK3229/RK322x genéricos. O inicializador DDR3
TPL vem das fontes abertas; não se escolheu blob DDR/trust de outra placa.
Isso não valida os timings, voltagens ou pinagem da R329Q_V8.0.

O perfil define `mmc0` como SD `0x30000000`, ordem SPL apenas `mmc0`, eMMC
e SDIO desativados. Desabilita escrita MMC/SPL, ambiente persistente,
comandos de gravação enumerados, USB/rede/MTD e caminhos fastboot/UMS.
O ambiente real foi extraído do ELF: sete pares explícitos, incluindo
`boot_targets=mmc0` e `bootdelay=-1`. Não há payload Android ou autoboot
configurado para ele.

Foram corrigidas duas inconsistências da combinação:

- O UART2 EVB usava PC2/PC3 compartilhados com SD. O perfil usa a rota UART21
  em PB1/PB2 existente no pinctrl, sem identificar a UART física da unidade.
- Os grupos de pinos sobreviveram ao filtro SPL/TPL, mas os nós `pcfg`
  referenciados não. A revisão encontrou phandles pendurados e o driver
  retornaria `-ENODEV`. Os três nós foram mantidos, os DTBs reconstruídos
  e todos os phandles SD/UART21 conferidos novamente.

As falhas de configuração/host foram preservadas: m4 ausente, SWIG 4.3
incompatível com o binding Python libfdt, bc fora do PATH e `pkg_resources`
ausente no setuptools recente. A versão final usa SWIG 4.2.1 e setuptools
75.8.0, sem alterar fontes de firmware para ocultar erros. O make normal
final e o OP-TEE terminaram com código zero. Os avisos permanecem nos logs;
não foi declarado build sem avisos.

Nove verificações estáticas independentes passaram nos DTBs, configuração,
símbolos, ambiente e FIT finais. O FIT contém exatamente os bytes do monitor,
U-Boot e DTB compilados, com o monitor em `0x68400000`. Isso verifica a
composição do contêiner, sem afirmar assinatura segura ou execução da cadeia.

## Artefatos finais

| Artefato | Bytes | SHA-256 |
| --- | --- | --- |
| `VortexHome-aosp-7.1.2-r6.apk` | 44.366 | `81fc16aa89e523088ac8c7a6e334a2c670745d6a4e673a30a986ba6af04867d4` |
| `tee-rk322x-reference.bin` | 329.840 | `1af5d3db3df39fae6dc977c00c4f21f47108e278ec2e4a282255060d16f8460a` |
| `idbloader-sd-reference.img` | 75.776 | `0485409c9f936c58a6b78e3fdd5aeb1d2d279c7686d5806a92c8fe98d2ba8f8e` |
| `u-boot-sd-reference.itb` | 598.528 | `35275d1e5b644b3ed2b0f87ddca395c87ae0521d93261e591c61d65ab067a63e` |
| `u-boot-rockchip-reference.bin` | 8.954.368 | `58e9f9d99f41803f4329646c15e9d7b89156a24fd3285a3a78482cf6a466817e` |

O último arquivo é um contêiner de bootloader com padding, não uma imagem
de cartão Android. Os arquivos de boot não devem ser usados como pacote de
instalação. Não há procedimento de gravação ou teste físico nesta entrega.

## O que ainda impede a imagem SD

Foi encontrada uma composição de fontes mais próxima do candidato r6:
plataforma `rockchip-android/rk3328-box-7.1`, build ID `NHG47K` e gráficos
framebuffer/DMA-BUF. O overlay experimental tem 28 commits completos e,
junto ao manifesto oficial, 556 projetos sem colisões. Mantém 528 projetos
AOSP em tags, não em lock resolvido. O common D042 foi conservado
explicitamente para corresponder aos patches existentes.

Há um bloqueio de ABI medido: `rk_fb_win_cfg_data` tem **904 bytes no
userspace e 908 no kernel**, com membro final diferente. O driver copia
`sizeof(win_data)` nos dois sentidos. O mesmo ioctl e o uso de framebuffer
não aprovam esse par HAL/kernel; essa interface precisa ser tratada e validada.
O layout privado do blob Mali e outras dependências continuam abertos.

No boot, TPL retorna ao BootROM; a política SD dos estágios abertos não
controla seu fallback. O monitor aberto exige reservas de core/SHM em
`0x68400000`–`0x68700000`, conferidas no DTB entregue efetivamente ao Linux.
`OPTEE_LIB` habilita um caminho condicional de fixup, que não foi executado
em hardware. PSCI padronizado também não resolve as chamadas Rockchip SIP
do kernel legado; CPU_SUSPEND dessa plataforma OP-TEE retorna não suportado.

Continuam necessários fechamento da plataforma, correção de ABI, integração
de init/ramdisk/SELinux, inventário final de serviços e arquivos, layout SD,
compatibilidade do monitor/DDR e os testes físicos já registrados. Nenhum
desses bloqueios virou pedido de novos dados ao proprietário. A Build 01
permanece aberta.

## Evidências e receitas

- [Módulo AOSP: receita e pins](../rom/AOSP_MODULE_BUILD.md)
- [Resultado do build AOSP](validation/2026-10-26-aosp-bootloader/aosp-app/aosp-app-report.json)
- [Log final do make AOSP](validation/2026-10-26-aosp-bootloader/aosp-app/attempt-06-final.log)
- [SDK comparado aos objetos Git oficiais](validation/2026-10-26-aosp-bootloader/aosp-app/sdk-git-object-verification.json)
- [Smoke do APK final](validation/2026-10-26-aosp-bootloader/runtime/runtime-result.json)
- [Regressão completa e Gradle](validation/2026-10-26-aosp-bootloader/validation-final.log)
- [Perfil/receita dos componentes de boot](../rom/bootloader/README.md)
- [Build e hashes do bootloader](validation/2026-10-26-aosp-bootloader/bootloader/bootloader-build-report.json)
- [Log final U-Boot](validation/2026-10-26-aosp-bootloader/bootloader/build-final.log)
- [Log OP-TEE](validation/2026-10-26-aosp-bootloader/bootloader/optee-build.log)
- [Revisão independente dos artefatos](validation/2026-10-26-aosp-bootloader/boot-chain/built-artifact-review.json)
- [Falha anterior dos pinconf](validation/2026-10-26-aosp-bootloader/boot-chain/before-pinconf-review.json)
- [Composição experimental de fontes](../rom/platform-reference/README.md)
- [Medição da ABI framebuffer](validation/2026-10-26-aosp-bootloader/platform/framebuffer-abi-review/layout-review.json)
- [Conferência final de integridade](validation/2026-10-26-aosp-bootloader/root-verification.json)
- [Hashes das entradas versionadas](validation/2026-10-26-aosp-bootloader/inputs.sha256)

Nenhum GitHub Actions foi consultado, criado ou executado.
