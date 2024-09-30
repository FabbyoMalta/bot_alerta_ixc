import logging
import requests
import base64
import json
import time

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("monitoramento.log"),
        logging.StreamHandler()
    ]
)

# Configurações da API IXCSoft
host = 'ixc.connectfibra.net'  # Substitua pelo IP do seu servidor IXCSoft
usuario = '100'  # Seu usuário na API
token = '20e92d6321793317e3d43dab04feba4d46664a78512e9b030e2186e15e8803ed'  # Seu token de autenticação
token_usuario = f"{usuario}:{token}"
token_bytes = token_usuario.encode('utf-8')
token_base64 = base64.b64encode(token_bytes).decode('utf-8')


headers = {
    'Authorization': f'Basic {token_base64}',
    'Content-Type': 'application/json'
}

# Configurações do Telegram
telegram_bot_token = 'SEU_TELEGRAM_BOT_TOKEN'  # Substitua pelo token do seu bot
telegram_chat_id = 'SEU_CHAT_ID'  # Substitua pelo ID do chat ou grupo

def obter_clientes_ativos():
    url = f"https://{host}/webservice/v1/radusuarios"
    payload = {
        'qtype': 'radusuarios.ativo',
        'query': 'S',
        'oper': '=',
        'page': '1',
        'rp': '1000',  # Ajuste conforme necessário
        'sortname': 'radusuarios.id',
        'sortorder': 'asc'
    }
    headers['ixcsoft'] = 'listar'

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        if 'type' in data and data['type'] == 'error':
            logging.error(f"Erro ao obter clientes ativos: {data.get('message', '')}")
            return []

        logging.info(f"Obteve {len(data.get('registros', []))} clientes ativos.")
        return data.get('registros', [])
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na requisição à API IXCSoft: {e}")
        return []

def enviar_alerta_telegram(clientes_offline):
    mensagem = "🚨 *Alerta: Novos clientes offline detectados:*\n"
    for login, endereco in clientes_offline:
        mensagem += f"- *Login:* `{login}`, *Endereço:* {endereco}\n"

    url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    payload = {
        'chat_id': telegram_chat_id,
        'text': mensagem,
        'parse_mode': 'Markdown'
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        logging.info("Alerta enviado com sucesso no Telegram.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Falha ao enviar mensagem no Telegram: {e}")

def monitorar_conexoes():
    clientes_offline_anterior = set()
    while True:
        logging.info("Iniciando verificação de clientes offline.")
        clientes = obter_clientes_ativos()
        clientes_offline_atual = set()

        for cliente in clientes:
            login = cliente.get('login')
            online = cliente.get('online')  # Confirme o campo correto
            endereco = cliente.get('endereco', '')  # Ajuste se necessário

            if online != 'S':  # Ajuste conforme o indicador de status online/offline
                clientes_offline_atual.add((login, endereco))

        if len(clientes_offline_atual) > len(clientes_offline_anterior):
            novos_offlines = clientes_offline_atual - clientes_offline_anterior
            if novos_offlines:
                logging.warning(f"Detectados {len(novos_offlines)} novos clientes offline.")
                enviar_alerta_telegram(novos_offlines)
        else:
            logging.info("Nenhum novo cliente offline detectado.")

        clientes_offline_anterior = clientes_offline_atual

        # Aguarda 5 minutos antes da próxima execução
        logging.info("Aguardando 5 minutos para a próxima verificação.")
        time.sleep(300)

if __name__ == '__main__':
    logging.info("Iniciando o monitoramento de conexões.")
    monitorar_conexoes()
