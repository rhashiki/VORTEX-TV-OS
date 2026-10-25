#!/usr/bin/env bash
# Read-only diagnostic. Does NOT install, write, erase, unlock, or back up the TV Box.
set -uo pipefail
if ! command -v rkdeveloptool >/dev/null 2>&1; then
  echo "ERRO: rkdeveloptool não encontrado. Instale-o no notebook Linux."; exit 2
fi
echo "Vortex TV OS · RK322x · diagnóstico somente leitura"
echo "Conecte a porta USB OTG confirmada e coloque a placa em Loader/MaskROM."
echo "Não execute comandos de escrita (wl, ef, db, ul, etc.)."
for cmd in ld rci rid rfi; do
  echo
  echo ">> rkdeveloptool $cmd"
  if command -v timeout >/dev/null 2>&1; then
    timeout 12 rkdeveloptool "$cmd" || echo "Comando indisponível neste modo. Nenhum dado foi gravado."
  else
    rkdeveloptool "$cmd" || echo "Comando indisponível neste modo. Nenhum dado foi gravado."
  fi
done
echo
echo "Identificadores devem ser conferidos antes de qualquer imagem de firmware."
