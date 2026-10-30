# Evidência do componente de diagnóstico initramfs

O binário estático ARM Linux e o arquivo initramfs foram compilados como
componentes isolados. Não houve boot de kernel/PID1, Android, cartão ou TV Box.

`evidence/source-provenance-final.json` fixa o código final, os 33 inputs da
varredura de dependências e os quatro artefatos locais. Uma recompilação
isolada da fonte final produziu o mesmo hash do executável stripped. O teste
do arquivo newc/gzip foi repetido com um parser independente do produtor e
confirmou modos, UID/GID/mtime zero, console5:1 e init byte-idêntico ao binário.

`evidence/component-test-result.json` e fixture-tests/ registram 24 casos no
binário ARM real sob QEMU user-mode. O campo histórico
`trace_no_storage_io_or_write_flags` significa que as asserções do harness
não encontraram flags/syscalls mutantes e que as fixtures ficaram iguais;
não é uma autenticação de caminhos de dispositivos por trace. A ausência
de I/O de dispositivo de bloco também depende da fonte revisada e do escopo
de inputs confiáveis, finitos. Nenhum teste executou o ramo PID1/mount/wait.

`review/final-source-review.json` verifica o código final. O relatório
anterior em historical/ descreve três questões que já foram corrigidas:
pinning O_PATH de metadados regulares, guarda RAMFS/TMPFS antes de mkdir/mount,
e leitura de diretório limitada por readdir. O relatório antigo não descreve
os bytes finais. O log musl da primeira tentativa preserva a falha de ar
ausente após compilação; a receita atual inclui o binário de ar real no PATH.

`source/` contém os fontes, receitas e licenças exatamente revisados. Os
caminhos absolutos nas receitas/registros são os do workspace concreto.
As aquisições têm hash e HTTPS registrados, sem alegação de verificação de
assinatura separada. Bibliotecas de SDK/vendor, compiladores, QEMU, arquivos
de sistema e os artefatos binários não entram neste pacote textual.

`evidence.sha256` cobre todos os textos desta pasta, exceto ele próprio.
