# Componente de diagnóstico para um futuro instalador SD

Este código produz um pequeno `/init` Linux ARM32 estático e um initramfs
`newc`/gzip. **Não é um recovery, instalador funcional, ROM ou cartão
inicializável.** Não há backend de formatação/gravação, shell interativo,
seleção de destino ou integração de bootloader/kernel neste componente.

Como PID1, o programa exige que `/` seja RAMFS/TMPFS antes de criar diretórios
e montar somente proc/sysfs com flags read-only/nosuid/nodev/noexec. Depois
enumera metadados limitados em sysfs, imprime JSON em stdout e permanece
aguardando. Não monta armazenamento de bloco nem grava logs no cartão.

As classificações SD/eMMC/MTD são candidatos não verificados. O nome
`mmcblk0` não aprova um cartão de boot; `MMC`/removable tampouco aprova o
destino interno. Nenhum FlashID, mapa de partições ou recuperação física foi
obtido por esta compilação. As configurações existentes que desabilitam NAND/
eMMC continuam separadas e não ganham acesso interno por usar este initramfs.

## Compilação registrada

Linux ARMv7-A, hard-float/VFPv3-D16, Linaro GCC6.3.1 de revisão
`dd4df7dff4f1df65d78939a958b760a79e3650a1`, com musl1.2.5 compilado do
arquivo oficial fixado por SHA-256. Não usa libc do Android nem contém um
runtime SDK/vendor. A configuração e os headers do kernel continuam sendo
insumos de integração externos.

```sh
VORTEX_ARM_TOOLCHAIN=/caminho/linaro bash build_component.sh
```

O script faz o build de musl, compila o programa e empacota o componente;
não prepara mídia nem abre dispositivos. Os caminhos de ferramentas nos
logs são os caminhos concretos do ensaio. `test_component.py` usa por padrão
o QEMU ARM já adquirido naquele workspace; a constante QEMU deve apontar
para uma instalação equivalente em outro host.

## Validação e limites

O binário ARM real passou em 24 testes sob QEMU user-mode com fixtures locais
finitas. Os testes verificam classificação não aprovada, limites de metadados,
overflow, symlinks/FIFO/diretórios, argumentos e enumeração. Conferem snapshots
imutados e ausência de flags/syscalls mutantes no trace. A análise de fonte
também verifica que O_PATH fixa um inode regular antes de qualquer open de
I/O. As fixtures não são um sandbox contra árvores arbitrárias de arquivos.

A execução PID1, as montagens, o kernel Linux3.10 e o hardware não foram
executados nesse conjunto. A presença do fallback ENOSYS em musl não substitui
um teste real com o kernel. Ainda faltam console/HDMI/entrada e integração
com a cadeia de boot. O arquivo comprimido não deve ser usado como imagem
de flash ou como procedimento de instalação na TV Box.

`package_initramfs.py` constrói o arquivo em memória: diretórios dev/proc/sys,
um registro de console5:1 e o executável init. O nó de console é somente
metadado codificado no arquivo; nenhum mknod ou mount é executado no host.
UID/GID/mtime são zero e a ordem é fixa. A mesma entrada gera bytes idênticos
no mesmo processo/ferramenta; não se promete reprodução entre toolchains.

Licenças: código novo Apache-2.0, musl com seu COPYRIGHT original e código
do runtime GCC com a exceção de biblioteca de runtime. Os textos estão em
`licenses/`; executáveis do compilador/QEMU e arquivos de runtime SDK/vendor
ficam fora da entrega.
