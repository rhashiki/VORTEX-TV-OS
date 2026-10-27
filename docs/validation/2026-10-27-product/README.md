# Evidências: produto SD e regras nativas

[Relatório consolidado](../../VALIDATION_2026-10-27_PRODUCT.md).

- `native-rules/`: 200 arquivos de texto, incluindo manifesto, logs brutos,
  receitas, revisão/fontes de dependências, licenças, regressão gralloc e
  smoke no linker Android. O resumo é
  [NATIVE_RULES_RESULT.md](native-rules/NATIVE_RULES_RESULT.md).
- `product-graph/`: preâmbulo diagnóstico, comandos, proveniência, listas
  resultantes e falhas corrigidas. As funções de importação/herança são as
  fontes reais do Android, não reimplementações. `baseline-05` é a comparação
  válida com os mesmos fragmentos e prefixos do resultado final.
- `source-replay/`: reprodução independente dos quatro projetos a partir de
  commits públicos, patches e hashes, incluindo tipos/symlinks.
- `review/`: revisão independente final, inventário do produto herdado e
  fontes reais que fundamentam o overlay SettingsProvider. O inventário
  herdado inicial tinha menos fragmentos que o baseline final; suas contagens
  não são apresentadas como uma comparação idêntica de tamanho.
- `auditor/`: 34 testes do contrato e revisão independente do auditor.
  `product-input-audit.json` é a execução final pelo script do repositório.
- `regression-tests.log`: suíte completa, 130 testes sem skips, com JDK.

Os caminhos `/workspace/...` são os caminhos concretos desta execução. As
receitas dependem dos pins e insumos registrados; não são instaladores.
As cópias de scripts conservam seus caminhos/nomes originais nas evidências.
Os manifestos específicos de cada ensaio referem-se ao escopo ali declarado;
`evidence.sha256` na raiz cobre todos os textos atuais deste diretório,
exceto ele próprio. `inputs.sha256` cobre os arquivos novos/alterados do
produto, auditor, testes, patches e documentação relacionados.

As duas HALs finais estão no pacote local de artefatos, fora do Git. Os
objetos/CRT, bibliotecas SDK/vendor, executáveis de ferramentas e sistemas
de arquivos não são redistribuídos. O pacote não contém ROM, imagem SD ou
aprovação para gravar mídia. Permanecem os bloqueios descritos no relatório.
