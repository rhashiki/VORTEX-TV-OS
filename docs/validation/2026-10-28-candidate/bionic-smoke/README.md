# Smoke com Bionic compilado de fontes

**Resultado parcial e qualificado:** dez casos normais de metadados passam;
um caso exploratório adicional de carregamento direto de libdl falha.
O relatório original mantém a expectativa e a falha, sem reescrever o resultado.

O runtime privado de teste combina três bibliotecas Bionic novas (`libc`,
`libdl`, `libm`), sete dependências de áudio compiladas de fontes e as demais
bibliotecas API25/vendor da referência anterior. O linker Android e o probe
são os artefatos reais já adquiridos/compilados; **não foram recompilados aqui**.
As bibliotecas novas foram copiadas, fixadas por hash e comparadas aos build IDs
dos objetos LINKED do recovery. Nenhum arquivo anterior foi modificado.

As seis cargas positivas são gralloc, HWC, áudio primary/USB/submix e power.
Os quatro negativos normais são arquivo ausente, HMI ausente em libm, modo
device indevido para power e id incorreto. Usam RTLD_NOW/HMI/dlclose sob QEMU
user-mode. O probe não chama HAL open nem hooks de energia; construtores e
destrutores de DSO podem executar. Não há operação de GPU, áudio, energia,
kernel Android completo, recovery, cartão SD ou hardware físico validada.

Os traces abrem `/system/lib/libc.so` e, nas cargas gráficas, `libm.so` no
prefixo isolado. Seus bytes correspondem às bibliotecas compiladas de fontes.
Nenhum caso normal abre o arquivo libdl fornecido. A implementação Android
pode atender libdl pela tabela interna do linker; não se afirma execução
dos stubs da nova libdl.

O caso exploratório tenta abrir a nova libdl por caminho absoluto e termina
com `DLOPEN_FAILED`, exit2, por `__cxa_finalize` não resolvido, antes de consultar
HMI. A expectativa inicial era exit3 e permanece registrada. Dois diagnósticos
posteriores reproduzem essa falha usando a libdl de referência, inclusive com
o runtime de referência inteiro inalterado. Esse contexto não apaga a falha
nem comprova uma integração completa do novo linker/libdl. A fonte Bionic
fixada também documenta que libdl é um conjunto de stubs com símbolos indefinidos
permitidos e implementações fornecidas pelo linker dinâmico.

`evidence/bionic-smoke-summary.json` é o resumo qualificado. O arquivo
`mixed-bionic-smoke-result.json` conserva o experimento original com status
fail. `runtime-integrity-and-trace-verification.json` confirma hashes/build IDs
e os caminhos observados. Todos os logs brutos, inclusive a falha e seus
diagnósticos posteriores, permanecem nas evidências.

`run_smoke.py` não compila nem baixa arquivos. Ele cria um prefixo novo e recusa
sobrescrever um prefixo existente. Seus caminhos são os desta sessão concreta;
não é um instalador de runtime ou firmware. O diretório `reference/` contém
insumos privados de teste e fica fora do pacote textual/de firmware: SDK,
vendor e ferramentas não são redistribuídos.
