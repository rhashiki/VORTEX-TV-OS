# Vortex App Installer — protocolo local (experimental)

O código Java implementa duas rotas na tela única de instalador:

1. **Celular:** detecta IPv4 Wi-Fi/Ethernet, cria um servidor HTTP apenas enquanto a tela estiver aberta, gera QR Code com segredo aleatório de 128 bits, expira após 15 minutos e aceita no máximo um upload de 512 MB. Transferência em streaming para cache local com cálculo de SHA-256, cabeçalho limitado e checagem de espaço para a cópia da sessão Android.
2. **Pendrive:** ACTION_OPEN_DOCUMENT seleciona arquivo local (depende de DocumentsUI/Storage Access Framework no firmware). Faz cópia limitada para cache privado.

Depois, **PackageInstaller Session API25** valida e apresenta confirmação Android; nenhum root, instalação silenciosa, GMS ou nuvem é usado. Depois de instalar, o app fica em Home > Meus apps.

## Considerações de segurança e compatibilidade

- O HTTP é sem TLS: restrito a **rede local confiável**; não usar rede pública. O token QR é de uso único, com validade curta. Requisições de outra Origin são rejeitadas.
- A checagem SHA-256 assegura integridade do arquivo recebido; **não garante ausência de malware**.
- A segurança do APK e de sua assinatura é decidida pelo gerenciador de pacotes Android.
- Fontes desconhecidas podem requerer habilitação para instalação. PackageInstaller sempre terá confirmação.
- Android 7.1.2 e kernel 3.10.104 são obsoletos e não são apropriados para operações sensíveis.
- APKs divididos (.apks, .xapk), streaming com progresso percentual, IPs IPv6, protocolos criptografados e instalação silenciosa **não estão no escopo da V1**.
- QR Code: projeto MIT Nayuki (copyright e licença preservados nos quatro arquivos vendorizados).
- Primeiro teste de transporte real pode ser executado com `python -m unittest discover -s tests -v` (JDK instalado). Emulador e placa RK3229 exigem testes separados.
- Sem GitHub Actions.

**Estado:** implementação experimental; compilação, permissões e hardware ainda não validados. Não é uma ROM instalável.
