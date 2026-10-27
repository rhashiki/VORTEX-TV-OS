# Revisão independente do probe de loader

O fonte usa dlopen com RTLD_NOW/RTLD_LOCAL, dlsym de HMI, confere tag/ID e
presença de methods/open, depois fecha o handle. O ponteiro open é lido,
sem chamada; o helper não contém operação explícita de GPU, framebuffer ou
ioctl. As versões são impressas, não comparadas com uma versão esperada.

Os cinco registros e logs são coerentes: dois positivos (gralloc/HWC) saem
com0; arquivo ausente com2; HMI ausente em libm com3; ID errado com4. Os
hashes do helper e do fonte compilado correspondem aos registros.

O aviso PIE DT_FLAGS_1=0x8000001 nomeia o helper e permanece visível em todos
os casos, que prosseguem até o resultado esperado. Não foi ocultado.

Isto valida apenas o caminho registrado de carregamento/metadados/fechamento.
Dlopen/dlclose podem executar construtores/destrutores; não se afirmou que
todas as dependências são isentas de efeitos. Nenhuma operação gráfica,
Android completo ou hardware foi validado por esta revisão.
