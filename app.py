import logging
import requests
import base64
import json
import time
import urllib3
import uuid 

# Desabilitar avisos de requisições inseguras (se necessário)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
telegram_bot_token = '6644963671:AAHgK96UoirMdoExb4EzPsbaJLmWQyi76gU'  # Substitua pelo token do seu bot
telegram_chat_id = '-4593383369'  # Substitua pelo ID do chat ou grupo

# Parâmetros de configuração
MAX_CLIENTS_IN_MESSAGE = 50       # Máximo de clientes a listar na mensagem
THRESHOLD_OFFLINE_CLIENTS = 3    # Número mínimo de novos clientes offline para enviar alerta

def obter_clientes_offline():
    url = f"https://{host}/webservice/v1/radusuarios"
    headers['ixcsoft'] = 'listar'

    clientes_offline = []
    page = 1
    rp = 1000  # Registros por página

    # Construir o grid_param com os filtros desejados
    grid_param = json.dumps([
        {"TB": "radusuarios.ativo", "OP": "=", "P": "S"},
        {"TB": "radusuarios.online", "OP": "=", "P": "N"}
    ])

    while True:
        payload = {
            'grid_param': grid_param,
            'page': str(page),
            'rp': str(rp),
            'sortname': 'radusuarios.id',
            'sortorder': 'asc'
        }

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()

            if 'type' in data and data['type'] == 'error':
                logging.error(f"Erro ao obter clientes offline: {data.get('message', '')}")
                break

            registros = data.get('registros', [])
            total_registros = int(data.get('total', 0))

            # Extrair os campos desejados de cada registro
            for registro in registros:
                cliente_info = {
                    'login': registro.get('login'),
                    'conexao': registro.get('conexao'),
                    'ultima_conexao_final': registro.get('ultima_conexao_final')
                }
                clientes_offline.append(cliente_info)

            logging.info(f"Página {page}: Obtidos {len(registros)} registros de clientes offline.")

            if len(clientes_offline) >= total_registros or len(registros) == 0:
                # Todos os registros foram obtidos
                break
            else:
                # Próxima página
                page += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição à API IXCSoft: {e}")
            break

    logging.info(f"Total de clientes offline obtidos: {len(clientes_offline)}")
    return clientes_offline

def obter_clientes_online():
    url = f"https://{host}/webservice/v1/radusuarios"
    headers['ixcsoft'] = 'listar'

    clientes_online = []
    page = 1
    rp = 1000  # Registros por página

    # Construir o grid_param com os filtros desejados
    grid_param = json.dumps([
        {"TB": "radusuarios.ativo", "OP": "=", "P": "S"},
        {"TB": "radusuarios.online", "OP": "=", "P": "S"}
    ])

    while True:
        payload = {
            'grid_param': grid_param,
            'page': str(page),
            'rp': str(rp),
            'sortname': 'radusuarios.id',
            'sortorder': 'asc'
        }

        try:
            response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()

            if 'type' in data and data['type'] == 'error':
                logging.error(f"Erro ao obter clientes online: {data.get('message', '')}")
                break

            registros = data.get('registros', [])
            total_registros = int(data.get('total', 0))

            # Extrair os campos desejados de cada registro
            for registro in registros:
                    cliente_info = {
                        'login': registro.get('login'),
                        'conexao': registro.get('conexao'),
                        'ultima_conexao_final': registro.get('ultima_conexao_final')
                    }
                    clientes_online.append(cliente_info)

            logging.info(f"Página {page}: Obtidos {len(registros)} registros de clientes online.")

            if len(clientes_online) >= total_registros or len(registros) == 0:
                # Todos os registros foram obtidos
                break
            else:
                # Próxima página
                page += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição à API IXCSoft: {e}")
            break

    logging.info(f"Total de clientes online obtidos: {len(clientes_online)}")
    return clientes_online

def enviar_alerta_telegram(clientes, status, conexao, mensagem_personalizada=None):
    total_clientes = len(clientes)
    if total_clientes == 0:
        return

    if mensagem_personalizada:
        mensagem = mensagem_personalizada + "\n"
    elif status == 'offline':
        mensagem = f"🚨 *Alerta: {total_clientes} clientes offline detectados na conexão {conexao}.*\n"
    elif status == 'online':
        mensagem = f"✅ *Alerta: Todos os clientes voltaram a ficar online na conexão {conexao}.*\n"
    else:
        mensagem = f"*Alerta: {total_clientes} clientes com status desconhecido na conexão {conexao}.*\n"

    # Listar até MAX_CLIENTS_IN_MESSAGE clientes
    if total_clientes <= MAX_CLIENTS_IN_MESSAGE:
        for cliente in clientes:
            login = cliente.get('login', 'N/A')
            ultima_conexao_final = cliente.get('ultima_conexao_final', 'N/A')
            mensagem += f"- *Login:* `{login}`\n"
            mensagem += f"  *Última conexão:* {ultima_conexao_final}\n"
    else:
        mensagem += "Listando alguns clientes:\n"
        for cliente in clientes[:MAX_CLIENTS_IN_MESSAGE]:
            login = cliente.get('login', 'N/A')
            ultima_conexao_final = cliente.get('ultima_conexao_final', 'N/A')
            mensagem += f"- *Login:* `{login}`\n"
            mensagem += f"  *Última conexão:* {ultima_conexao_final}\n"
        mensagem += f"... e mais {total_clientes - MAX_CLIENTS_IN_MESSAGE} clientes."

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
    clientes_info_offline_anterior = {}
    eventos_ativos = []  # Lista de eventos ativos
    try:
        while True:
            logging.info("Iniciando verificação de clientes.")

            # Obter clientes offline atuais
            clientes_offline = obter_clientes_offline()
            clientes_offline_atual = set()
            clientes_info_offline_atual = {}

            for cliente in clientes_offline:
                login = cliente.get('login')
                clientes_offline_atual.add(login)
                clientes_info_offline_atual[login] = cliente  # Armazena as informações completas

            # Obter clientes online atuais
            clientes_online = obter_clientes_online()
            clientes_online_atual = set()
            clientes_info_online_atual = {}

            for cliente in clientes_online:
                login = cliente.get('login')
                clientes_online_atual.add(login)
                clientes_info_online_atual[login] = cliente  # Armazena as informações completas

            if clientes_offline_anterior:
                # Identifica novos clientes offline
                novos_offlines = clientes_offline_atual - clientes_offline_anterior

                # Identifica clientes que voltaram a ficar online
                clientes_reconectados = clientes_offline_anterior - clientes_offline_atual

                # Processar novos clientes offline
                if novos_offlines:
                    logging.warning(f"Detectados {len(novos_offlines)} novos clientes offline.")

                    # Agrupar novos offlines por 'conexao'
                    conexoes_novos_offlines = {}
                    for login in novos_offlines:
                        cliente = clientes_info_offline_atual[login]
                        conexao = cliente.get('conexao', 'Desconhecida')
                        if conexao not in conexoes_novos_offlines:
                            conexoes_novos_offlines[conexao] = []
                        conexoes_novos_offlines[conexao].append(cliente)

                    # Criar eventos separados para cada 'conexao' que atendem ao threshold
                    for conexao, clientes in conexoes_novos_offlines.items():
                        if len(clientes) >= THRESHOLD_OFFLINE_CLIENTS:
                            # Criar novo evento
                            evento = {
                                'id': str(uuid.uuid4()),
                                'conexao': conexao,
                                'logins_offline': set(cliente['login'] for cliente in clientes),
                                'logins_restantes': set(cliente['login'] for cliente in clientes),
                                'timestamp': time.time()
                            }
                            eventos_ativos.append(evento)
                            logging.info(f"Criado novo evento {evento['id']} para conexão {conexao} com {len(clientes)} logins offline.")
                            enviar_alerta_telegram(clientes, status='offline', conexao=conexao)
                        else:
                            logging.info(f"Número de novos clientes offline na conexão {conexao} ({len(clientes)}) abaixo do limite de alerta.")
                else:
                    logging.info("Nenhum novo cliente offline detectado.")

                # Processar clientes que reconectaram
                if clientes_reconectados:
                    logging.info(f"Detectados {len(clientes_reconectados)} clientes que voltaram a ficar online.")
                    for login in clientes_reconectados:
                        # Encontrar eventos que incluem este login
                        eventos_para_remover = []
                        for evento in eventos_ativos:
                            if login in evento['logins_restantes']:
                                evento['logins_restantes'].remove(login)
                                logging.info(f"Login {login} reconectado no evento {evento['id']}.")

                                # Verificar se todos os logins do evento reconectaram
                                if not evento['logins_restantes']:
                                    logging.info(f"Todos os logins do evento {evento['id']} reconectaram.")
                                    # Enviar alerta
                                    clientes_evento = [clientes_info_online_atual.get(l, {'login': l}) for l in evento['logins_offline']]
                                    enviar_alerta_telegram(clientes_evento, status='online', conexao=evento['conexao'])
                                    eventos_para_remover.append(evento)
                        # Remover eventos concluídos
                        for evento in eventos_para_remover:
                            eventos_ativos.remove(evento)
                else:
                    logging.info("Nenhum cliente reconectado detectado.")

            else:
                logging.info("Primeira execução: inicializando listas de clientes.")

            clientes_offline_anterior = clientes_offline_atual
            clientes_info_offline_anterior = clientes_info_offline_atual

            # Aguarda 5 minutos antes da próxima execução
            logging.info("Aguardando 5 minutos para a próxima verificação.")
            time.sleep(300)

    except KeyboardInterrupt:
        logging.info("Interrupção solicitada pelo usuário. Encerrando o monitoramento de conexões.")
        # Realize qualquer limpeza necessária aqui
        pass

def salvar_saida_api():
    url = f"https://{host}/webservice/v1/radusuarios"
    headers['ixcsoft'] = 'listar'

    # Construir o grid_param com os filtros desejados
    grid_param = json.dumps([
        {"TB": "radusuarios.ativo", "OP": "=", "P": "S"},
        {"TB": "radusuarios.online", "OP": "=", "P": "N"}
    ])

    payload = {
        'grid_param': grid_param,
        'page': '1',
        'rp': '1000',  # Ajuste se necessário
        'sortname': 'radusuarios.id',
        'sortorder': 'asc'
    }

    try:
        response = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
        response.raise_for_status()
        data = response.json()

        if 'type' in data and data['type'] == 'error':
            logging.error(f"Erro ao obter dados da API: {data.get('message', '')}")
            return

        # Salvar a resposta em um arquivo JSON
        with open('saida_api_debug.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info("Saída da API salva em 'saida_api_debug.json'.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Erro na requisição à API IXCSoft: {e}")

if __name__ == '__main__':
    logging.info("Iniciando o monitoramento de conexões.")

    # Defina como True para salvar a saída da API, False caso contrário
    SALVAR_SAIDA_API = False  # Altere para True quando quiser salvar a saída da API

    try:
        if SALVAR_SAIDA_API:
            salvar_saida_api()
        else:
            monitorar_conexoes()
    except KeyboardInterrupt:
        logging.info("Interrupção solicitada pelo usuário. Encerrando o script.")
        # Realize qualquer limpeza necessária aqui
        pass