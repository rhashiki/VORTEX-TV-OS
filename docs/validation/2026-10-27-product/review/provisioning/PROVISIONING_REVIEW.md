# Defaults do primeiro boot sem SetupWizard

A revisão de frameworks-base edd171fec429b9d51d9cb2da961a673ec51fcc4d confirma dois bools SettingsProvider existentes: def_device_provisioned e def_user_setup_complete. Ambos têm valor false no defaults.xml original. DatabaseHelper os consulta para inserir DEVICE_PROVISIONED global e USER_SETUP_COMPLETE seguro; loadBooleanSetting traduz true em 1. O SettingsProvider cria/migra esse banco quando os XMLs de settings ainda não existem.

A proposta em overlay-proposal/ substitui somente esses dois recursos por true, limitada ao novo produto pelo PRODUCT_PACKAGE_OVERLAYS. Isso evita acrescentar outro componente HOME Provision. Não altera bancos/settings já existentes e não habilita instalação de fontes desconhecidas.

A correspondência de tipos/nomes e os leitores de fonte foram verificados. Ainda não houve compilação do SettingsProvider com esse overlay nem primeiro boot de uma imagem resultante. O resultado é uma correção de configuração fundamentada em fonte, não um teste de execução.
