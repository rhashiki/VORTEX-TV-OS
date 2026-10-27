# Verificação independente do export OMX

O export Thumb `Rockchip_get_gralloc_private` tem32bytes e código entre
0x750 e0x770. Seus cinco loads de32bits em offsets40/12/48/44/28 coincidem
com format/share_fd/type/stride/size medidos no header gralloc real. Os stores
preenchem cinco ints consecutivos do resultado, em offsets0/4/8/12/16.

A fonte C++ real, byte idêntica ao Git fixado, usa esses cinco campos. Seu
objeto ARM existente confere no hash e reproduz os mesmos acessos; não foi
recompilado ou executado nesta revisão. O output ponteiro nulo retorna-1;
o handle de entrada não é validado por essa função.

Isto corrobora somente os campos observados nesse export. Não aprova toda a
ABI OMX/Mali, ownership, ION/RGA/fences, vídeo/GPU ou hardware. Não houve
carregamento de biblioteca, ioctl ou boot físico.
