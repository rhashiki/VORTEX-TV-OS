# Revisão independente do HWC

Nenhum erro impeditivo foi encontrado no patch de três correções. A seleção
por formato passa a usar o valor real, com handle nulo recusado; itoa termina
com NUL; e o log HDMI recebe o inteiro correspondente ao formato.

Foram conferidos os hashes dos oito objetos ARM originais e dos três objetos
recompilados após a correção, bem como os hashes das fontes e os40headers
frameworks/native adquiridos. Os14casos de comportamento host usam os corpos
reais extraídos e os tipos Android/gralloc genuínos: antes8falhas, depoiszero.
Não se repetiu build ou teste neste trabalho de revisão.

O conjunto atual de oito objetos usa evidence/final para as três fontes
modificadas e evidence/attempt-02 para as cinco restantes. Ainda faltavam
relatório agregado e manifesto congelado próprios do HWC quando revisado.
Avisos continuam nos logs; o HWC não está aprovado como HAL ligada ou em
execução. Não houve Android completo, ioctl gráfico, HDMI ou boot físico.

Detalhes, hashes e escopo: hwc-source-review.json.
