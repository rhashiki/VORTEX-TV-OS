# Vortex TV nativo — integração no Vortex TV OS

O `VortexHome` (launcher) e o `VortexTV` (streaming) são **aplicações
diferentes**, instaladas juntas no firmware, sem instalação manual e sem login.

O produto experimental exige ambos os módulos:

- Launcher AOSP: `os.vortex.tv`.
- Streaming app (release): `os.vortex.tv.stream`, construído a partir
  de `rhashiki/Vortex-TV`.
- `rom/prebuilt/VortexTV.apk`: APK release já compilado do aplicativo Vortex TV.
- `rom/prebuilt/catalog-access`: arquivo OEM de 20 caracteres hexadecimais,
  provisionado exclusivamente no ambiente de montagem do firmware.

A integração AOSP copia a configuração para
`/system/etc/vortex-tv/catalog-access`; o app a consulta automaticamente,
sem telas de login, pareamento, QR, seleção de fontes ou importação manual de M3U.

**Não commit** `catalog-access` ou APK com segredos. Ambos são ignorados
pelo `.gitignore`. Não publique o arquivo de acesso em releases, logs,
imagens de demonstração ou serviços de download público.

## Atualização automática

No primeiro boot do firmware, o aplicativo tenta baixar do Supabase as
fontes importadas. O servidor mantém a lista e o Media3 faz a reprodução
diretamente da origem. O app usa paginação de 500 registros e SQLite para
continuar após falhas. Em execuções seguintes, sincroniza no máximo a
cada 12 horas, preservando o catálogo local.

Isso **não** significa que os 33.601 links já foram homologados: a maioria
não passou por teste individual de vídeo e áudio.

## Montagem da imagem

Na árvore AOSP experimental, o módulo pré-instalado `VortexTV` é
definido em `rom/prebuilt/Android.mk` e o produto é selecionado pelo
`rom/vortex_product.mk`. O build deve falhar se o APK ou o arquivo
OEM não existirem: não silencie falhas deixando de instalar o aplicativo.

**Status físico:** o repositório ainda não contém imagem inicializável
homologada para R329Q_V8.0/RK3229. Incluir o APK no produto experimental
não comprova boot, Ethernet, vídeo, áudio ou controle remoto.

## Provisionamento feito no backend

A configuração OEM está provisionada no **Supabase Vault**, sob o nome
`vortex_tv_os_oem_catalog_access`. O registro de acesso correspondente
existe na tabela privada `vortex_family.device_access` e foi testado via
Edge Function com resposta HTTP 200 e 500 registros M3U.

O ambiente de montagem da ROM deve recuperar esse segredo do Vault
**somente durante o build autorizado**, escrever o arquivo ignorado
`rom/prebuilt/catalog-access` e excluí-lo de logs/commits. Nada será
solicitado ao usuário final. A montagem/flash ainda não ocorreu.

A proteção efetiva do arquivo na imagem precisa ser validada com as
permissões/SELinux da versão final; uma cópia em `/system/etc` pode ser
lida por outros aplicativos caso tenha permissões permissivas.
