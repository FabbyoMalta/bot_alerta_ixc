# Monitoramento de Conexões PPPoE
##Este script Python monitora as conexões PPPoE de clientes em um servidor IXCSoft, enviando alertas via Telegram e WhatsApp (usando a API da Gupshup) quando clientes ficam offline ou voltam a ficar online. Ele também armazena logs de cada operação.

### Funcionalidades
- Monitora clientes online e offline no sistema IXCSoft.
- Envia alertas para um canal/usuário no Telegram quando um número de clientes offline excede um limite definido.
- Envia alertas para números de WhatsApp usando a API da Gupshup quando clientes ficam offline.
- Gera logs detalhados de todas as operações.

## Requisitos
 - Python 3.x

### Bibliotecas Python necessárias (listadas no requirements.txt):
- requests
- python-dotenv (se você optar por usar arquivos .env)
- urllib3
- logging

## Instalação
### Clone o repositório:

#### bash#
```
git clone https://github.com/seu_usuario/seu_repositorio.git
cd seu_repositorio
```

### Instale as dependências:
#### bash
```
pip install -r requirements.txt
```
Configure as variáveis de ambiente necessárias, seja diretamente no ambiente ou em um arquivo .env.

## Configuração
O script usa várias variáveis sensíveis (como tokens de API e senhas), que devem ser configuradas como variáveis de ambiente ou em um arquivo .env.

### Variáveis de Ambiente Necessárias
#### IXCSoft API:
- IXCSOFT_HOST: Endereço do servidor IXCSoft (exemplo: ixc.connectfibra.net).
- IXCSOFT_USUARIO: Usuário de autenticação na API.
- IXCSOFT_TOKEN: Token da API IXCSoft.

#### Gupshup (WhatsApp API):
- GUPSHUP_APP_NAME: Nome do aplicativo Gupshup.
- GUPSHUP_API_KEY: API Key da Gupshup.
- GUPSHUP_SOURCE_NUMBER: Número de origem autorizado para enviar mensagens.
- GUPSHUP_DESTINATION_NUMBERS: Números de destino (separados por vírgulas).
- GUPSHUP_TEMPLATE_ID: ID do template de mensagem pré-aprovado.

#### Telegram:
- TELEGRAM_BOT_TOKEN: Token do bot do Telegram.
- TELEGRAM_CHAT_ID: ID do chat ou grupo no Telegram.

## Contribuições
Sinta-se à vontade para fazer um fork deste projeto e enviar pull requests.

## Licença
Este projeto está licenciado sob a MIT License.
