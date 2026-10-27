# Build 01 — módulos pelo Android.mk e produto SD

Data: 27/10/2026. Base Vortex: `1fef3a1c62de4e24ff22cb62ff8dcca812ce0a84`.
**As HALs agora compilam, ligam e são instaladas pelas regras reais do Android.
O perfil SD resolve suas entradas. Ainda não existe ROM ou imagem SD inicializável.**

## Resultado nativo

O ensaio anterior fazia link manual. Nesta etapa o Rockchip build
`d2721c65c9282b31df7b79f85289ee6c4e636716` executou suas regras genuínas de
`BUILD_SHARED_LIBRARY`, link, pack/strip e instalação para
`gralloc.rk30board` e `hwcomposer.rk30board`. A receita usa GNUmake,
`tapas arm eng`, ARMv7-A/NEON/Cortex-A7, sem Ninja/Soong e sem GitHub Actions.

Uma saída inicialmente vazia compilou os quatro C++ do gralloc e oito do HWC,
além dos módulos reais `libunwind_llvm` e `libcompiler_rt-extras`. Não foram
criados arquivos vazios para satisfazer dependências. O suporte LLVM foi
compilado com Clang oficial; as HALs, com GCC Android 4.9 oficial.

Os ensaios preservam as falhas anteriores: exports ausentes, dependências
LLVM, diretório de recursos do Clang, runtime GNU/Linux hard-float incompatível
e arquivos faltantes do subconjunto GCC. A solução final usa os arquivos reais
da ferramenta Android, incluindo `liblto_plugin.so`, sem mascarar a divergência
de ABI ou desligar esse diagnóstico. O toolchain Linux usado no kernel não
foi tratado como substituto da ferramenta Android.

O grafo deste ensaio registra 22 bibliotecas compartilhadas reais como
`BUILD_PREBUILT`: 21 do runtime oficial ARM32 API25 e `libion` da referência
vendor fixada. Usa CRT Bionic previamente compilado. **Essas dependências
não foram recompiladas pelo BSP e não entram no perfil de produto nem no
pacote entregue.** Portanto o resultado é build real dos módulos, com uma
plataforma de referência, e não build completo da plataforma.

O compilador também expôs um defeito real: o formato não suportado
`HAL_PIXEL_FORMAT_YCrCb_NV12_VIDEO` podia chegar ao alocador com `size` e
`stride` indefinidos. O novo [patch 0007](../rom/platform-reference/graphics/patches/0007-gralloc-reject-unsupported-nv12-video.patch)
retorna `-EINVAL` antes da alocação. O teste executa a função real extraída
com fronteiras de alocação instrumentadas: a versão anterior falha em três
verificações negativas; a corrigida passa nas 14, incluindo formatos vizinhos
e rotas framebuffer/buffer. É um teste host de função, com tipos substitutos,
sem prova de ABI Android, overflow ARM32 ou alocação física.

Após o patch, o Android.mk recompilou o objeto afetado e voltou a ligar e
instalar o gralloc; o script de versão também recompilou consumidores do HWC.
Permanecem avisos de parâmetros não usados e redefinição
de LOG_TAG; não se declara build sem avisos. O registro limpo anterior à
correção e o incremental final estão separados nas evidências.

| Artefato final | Bytes | SHA-256 |
| --- | ---: | --- |
| gralloc.rk30board.so | 30.368 | `ad9df6102d59dc1e0f91fabff5dd6a0357a5b531285842e4a7ec351a1492c9ed` |
| hwcomposer.rk30board.so | 83.736 | `f6c6651d4b31a1400289117c017a1e45cee389bb6a060375783817e726f32fbf` |

Os dois artefatos finais passaram por `dlopen(RTLD_NOW)`, consulta de HMI e
`dlclose` no linker Android ARM real sob QEMU user-mode. Três negativos
(arquivo ausente, HMI ausente e id incorreto) também tiveram o resultado
esperado: cinco casos. O probe verifica tag/id/ponteiros e imprime versões;
não chama o método HAL `open`. Construtores/destrutores de DSO podem executar.
O aviso legado DF_1_PIE/NOW do probe permanece registrado. Isso não executa
SurfaceFlinger, GPU, HDMI nem o Android completo.

## Produto SD

O [perfil novo](../rom/product/README.md) foi importado pelas funções reais
de `product_config.mk`, com preâmbulo diagnóstico explícito. Não se usou um
parser próprio para simular herança e não se executou o grafo completo de
imagens. O produto Vortex herda `core_minimal`, o fragmento Home, fontes e
parâmetros de heap para a classe de 1 GiB.

O resultado tem 416 entradas de pacote, 412 únicas; 134 entradas são fontes,
não aplicativos. VortexHome é o único launcher selecionado. Inclui instalação
de APK, Settings/SystemUI, teclado e DocumentsUI/ExternalStorageProvider.
Não seleciona Launcher3, Bluetooth, GApps, SetupWizard/Provision, recovery,
applypatch, uncrypt ou gralloc.default. A ausência de GApps se refere às
listas examinadas, sem inventário de uma imagem final ainda inexistente.

O patch em três makefiles do build condiciona quatro entradas ao produto
Vortex. As listas packages/copy-files/properties do `rk322x_box` original são
byte a byte iguais ao baseline sem patch, com os mesmos fragmentos e
preâmbulo. Essa regressão cobre esse produto e essas listas, não todos os
produtos ou regras possíveis.

As 13 cópias declaradas têm fontes regulares presentes, hashes e destinos
relativos únicos. O auditor novo passa com status `product_inputs_only`;
não autentica quem gerou listas nem resolve dependências transitivas.
Seus testes negativos cobrem entradas incompletas, conflitos, aliases,
arquivos especiais, symlinks e seleções/copias proibidas, inclusive XML Google
codificado e blobs renomeados. Overlays/propriedades e comportamento de init
ficam fora do contrato desse auditor.

Uma revisão independente conferiu os seis arquivos recursivos do perfil e o
overlay SettingsProvider. Os bools `def_device_provisioned` e
`def_user_setup_complete` existem e são lidos na revisão real
`edd171fec429b9d51d9cb2da961a673ec51fcc4d`. Ambos passam a true somente neste
produto sem SetupWizard, para dados novos. Isso não habilita fontes
desconhecidas. O SettingsProvider com o overlay e o primeiro boot ainda não
foram compilados/executados.

Outra reprodução extraiu commits públicos, aplicou patches e comparou 1.615
arquivos de build/device/common/vendor em bytes e tipo. O common foi
reproduzido de `3b1aa90` + SD 0002/0003/0005, sem depender do commit local
intermediário. Seis symlinks de releasetools inicialmente dereferenciados na
cópia diagnóstica foram restaurados; a preparação agora preserva links.

## Validação e entrega

A suíte completa passou com **130 testes, sem skips**, usando o JDK instalado;
34 exercitam o contrato do novo auditor. O log inclui os testes HTTP/JVM.
Separadamente, passaram as 14 verificações da função gralloc corrigida, os
cinco casos do linker Android e a reprodução/comparação das fontes do produto.

O APK e a UI não mudaram nesta etapa. Permanecem os resultados anteriores de
[AOSP/Jack e emulador API25](VALIDATION_2026-10-26_AOSP_BOOTLOADER.md) e
[Installer completo](VALIDATION_2026-10-27_GRAPHICS_MONITOR.md); não são novos
testes em uma ROM Vortex. O APK anterior pode ser encontrado no pacote da
etapa anterior. Os originais da marca continuam fora do workspace.

As [evidências desta etapa](validation/2026-10-27-product/README.md) incluem
logs de build/falhas, hashes, regras, testes, listas, fontes de revisão e
reprodução. O pacote local reúne o snapshot do repositório e as duas HALs
compiladas. Não inclui runtime SDK, blobs vendor, toolchains, cartões ou
imagens Android. Os manifestos permitem verificar os arquivos concretos.

## O que impede o teste por SD e a conclusão

1. Fechar e compilar todo o Android: framework, fontes/TTFs, áudio, demais
   HALs e dependências. O espaço livre local de aproximadamente 11 GiB não é
   uma capacidade demonstrada para o checkout/build completo do AOSP.
2. Integrar o ramdisk, permissões de ion/mali/framebuffer, ueventd, SELinux,
   serviços e cadeia real de montagem. O init reduzido não os implementa.
3. Tratar e testar os caminhos de falha de montagem. O init real ainda pode
   chamar `wipe_data_via_recovery` em `FS_MGR_MNTALL_DEV_NEEDS_RECOVERY`,
   escrever BCB e solicitar wipe/recovery. Remover os pacotes de recovery
   não remove esse código; não se afirma preservação da memória interna.
4. Resolver a correspondência USB/vold: o fstab conserva controladores
   `ff580000`/`ff5c0000`/`ff5d0000`, enquanto o DTS examinado usa endereços
   `30040000`/`30080000` e outros. Não se inventaram caminhos substitutos.
5. Fechar monitor/console/reservas, suspend e integração kernel/DTB/bootloader,
   além dos contratos privados Mali/OMX, ION/RGA/fences e mídia VPU.
6. Produzir e inspecionar uma imagem externa real; depois testar boot,
   HDMI/áudio, controle remoto, Ethernet/Wi-Fi, USB, persistência e Installer
   na TV Box. Só então preparar instalação interna e recuperação.

Nenhum novo diagnóstico foi solicitado ao proprietário. Não houve gravação
de mídia, flash, boot físico ou execução/consulta de GitHub Actions.
