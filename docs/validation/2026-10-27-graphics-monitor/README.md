# Evidências desta etapa

O Git contém os registros de texto copiados das experiências, sem reescrever
os resultados. Objetos ARM, APKs, DTB e capturas ficam no pacote de artefatos
da entrega. Os manifestos originais congelados abrangem também esses binários;
seus hashes e contagens estão em `root-verification.json`.

Scripts e comandos mantêm os caminhos concretos do workspace original e
dependem das fontes/configs indicados. Não são instaladores. O registro GNUmake
em `selection/` é apenas uma expansão diagnóstica: shells e registro Android
de módulos foram desabilitados, sem compilar ou ligar HALs nesse harness.

Os 94 valores são medidas de layout, não 94 testes de execução. Os quatro
objetos gralloc foram compilados separadamente com headers Android e GCC ARM;
isso não substitui make/link Android. A correção de erro de suspensão também
foi compilada somente como objeto; o Image anterior permanece sem ela.

[Relatório consolidado](../../VALIDATION_2026-10-27_GRAPHICS_MONITOR.md).
