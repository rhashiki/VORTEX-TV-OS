# Buffer privado Mali/OMX: evidência delimitada

O probe inclui o header gralloc completo e os tipos Android reais, compilados
para ARMv7 softfp. Os 57 valores registrados incluem sizeof, alinhamentos,
offsets/tamanhos de campos e a constante magic. O objeto mede private_handle_t
com 104 bytes/alinhamento8, native_handle_t12, numFds1 e numInts22.
O compilador avisa sobre offsetof em classe derivada non-standard-layout;
os diagnósticos estão preservados, sem supressão.

A inspeção estática do libGLES_mali.so vendor fixado encontrou verificações
dos mesmos native_handle version12, numFds1, numInts22 e magic0x03141592,
esta última no offset16. ANativeWindowBuffer.handle é lido em60, igual ao
probe. Foram comparadas também leituras selecionadas de flags, share_fd,
fd, offset, base, size e format. O subrelatório mali/README.md delimita
endereços e evita atribuir nomes inventados aos helpers sem símbolos.

O export Rockchip_get_gralloc_private do libgralloc_priv_omx.so lê
format40, share_fd12, type48, stride44 e size28, e escreve esses valores nos
offsets0,4,8,12,16 do destino. A fonte real da ponte OMX selecionada também
foi compilada para objeto ARM; suas leituras correspondem a esses offsets.
Isso não afirma igualdade binária entre fonte compilada e blob.

private-abi-review.json reúne19 comparações de valores/campos selecionados,
com fontes fixadas e hashes. São evidências de uma parte do contrato privado,
não19 testes de renderização nem prova de compatibilidade completa.
Os blobs não foram executados nesta auditoria estática; não houve GPU, ION,
RGA, alocação, importação, cache, fence ou reprodução de mídia exercitados.

Objetos, os scripts com caminhos concretos e os registros permitem repetir
as medições, mas não formam uma ROM ou mídia inicializável. A integração
Android e a semântica completa dos buffers ainda precisam de validação.
