# Evidências do ensaio nativo

Este diretório contém os registros de texto, copiados sem reescrever as
saídas dos experimentos. Objetos, módulos compilados e o probe executável
ficam no pacote de artefatos. Arquivos de plataforma/vendor adquiridos,
imagens SDK, ferramentas e Google Apps não entram na entrega de firmware.
Os manifestos originais abrangem também binários/metadata de aquisição;
seus hashes e contagens estão em root-verification.json.

As receitas registram os caminhos concretos do workspace e dependem das
fontes e bibliotecas fixadas. Não são instaladores. Os testes de funções
HWC são host-only; os cinco casos de loader executam o linker Android ARM
sob QEMU, sem chamar o método open das HALs. Construtores/destrutores podem
executar. As versões dos módulos são impressas, não comparadas a valores
esperados pelo probe.

[Relatório consolidado](../../VALIDATION_2026-10-27_NATIVE_HAL.md).
