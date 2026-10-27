# Revisão independente do handle privado

Nenhuma divergência foi encontrada no conjunto delimitado. O probe inclui os
headers completos e reais, idênticos ao Git fixado:56medidas foram conferidas
nos símbolos do objeto ARM e o magic foi lido diretamente da rodata compilada.
O resultado é native_handle12bytes, handle104/alinhamento8, numFds1,
numInts22 e magic0x03141592; ANativeWindowBuffer.handle fica em60.

O blob Mali carrega o handle do wrapper em60 e valida os mesmos quatro
valores antes das leituras privadas. Foram conferidos flags20, fd88, offset92,
base56, size28, format40 e share_fd12 em seus contextos de instrução. Muitos
símbolos locais estão removidos; não se atribuíram nomes de função de fonte
com base nos rótulos aproximados do objdump.

A revisão OMX independente confirma o export de32bytes Rockchip_get_gralloc_private:
format40/share_fd12/type48/stride44/size28, com cinco saídas int consecutivas.
A fonte C++ real e seu objeto ARM existente também foram conferidos.

Essas correspondências reduzem a incerteza nos campos examinados. Não aprovam
toda a ABI Mali/OMX, semântica de alocação/vida/coerência, ION/RGA/fences, GPU,
decode, ligação/carregamento Android ou boot físico. Não houve build repetido,
execução de blob ou acesso a hardware nesta revisão.
