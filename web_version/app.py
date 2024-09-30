import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import logging
import base64
import json
from threading import Event  # Importar Event do módulo threading
import urllib3
import requests

# Inicializar o monkey patching do eventlet
#eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
socketio = SocketIO(app, async_mode='eventlet')

atualizar_event = Event()

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

def obter_clientes_online():
    url = f"https://{host}/webservice/v1/radusuarios"
    custom_headers = headers.copy()
    custom_headers['ixcsoft'] = 'listar'

    clientes_online = []
    page = 1
    rp = 1000  # Registros por página

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
            response = requests.post(url, data=json.dumps(payload), headers=custom_headers, verify=False)
            response.raise_for_status()
            data = response.json()

            if data.get('type') == 'error':
                logging.error(f"Erro ao obter clientes online: {data.get('message', '')}")
                break

            registros = data.get('registros', [])
            total_registros = int(data.get('total', 0))

            for registro in registros:
                cliente_info = {
                    'login': registro.get('login'),
                    'conexao': registro.get('conexao'),
                    'ultima_conexao_final': registro.get('ultima_conexao_final'),
                    'latitude': registro.get('latitude'),
                    'longitude': registro.get('longitude')
                }
                clientes_online.append(cliente_info)

            logging.info(f"Página {page}: Obtidos {len(registros)} registros de clientes online.")

            if len(clientes_online) >= total_registros or not registros:
                break
            else:
                page += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição à API IXCSoft: {e}")
            break

    logging.info(f"Total de clientes online obtidos: {len(clientes_online)}")
    return clientes_online


def obter_clientes_offline():
    url = f"https://{host}/webservice/v1/radusuarios"
    custom_headers = headers.copy()
    custom_headers['ixcsoft'] = 'listar'

    clientes_offline = []
    page = 1
    rp = 1000  # Registros por página

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
            response = requests.post(url, data=json.dumps(payload), headers=custom_headers, verify=False)
            response.raise_for_status()
            data = response.json()

            if data.get('type') == 'error':
                logging.error(f"Erro ao obter clientes offline: {data.get('message', '')}")
                break

            registros = data.get('registros', [])
            total_registros = int(data.get('total', 0))

            for registro in registros:
                cliente_info = {
                    'login': registro.get('login'),
                    'conexao': registro.get('conexao'),
                    'ultima_conexao_final': registro.get('ultima_conexao_final'),
                    'latitude': registro.get('latitude'),
                    'longitude': registro.get('longitude')
                }
                clientes_offline.append(cliente_info)

            logging.info(f"Página {page}: Obtidos {len(registros)} registros de clientes offline.")

            if len(clientes_offline) >= total_registros or not registros:
                break
            else:
                page += 1

        except requests.exceptions.RequestException as e:
            logging.error(f"Erro na requisição à API IXCSoft: {e}")
            break

    logging.info(f"Total de clientes offline obtidos: {len(clientes_offline)}")
    return clientes_offline

def monitorar_conexoes():
    with app.app_context():
        clientes_offline_anterior = set()
        clientes_info_offline_anterior = {}
        intervalo_atualizacao = 300  # 5 minutos
        intervalo_cheque = 1     # Intervalo de checagem (1 segundo)
        tempo_decorrido = 0

        while True:
            # Aguardar o intervalo de checagem
            eventlet.sleep(intervalo_cheque)
            tempo_decorrido += intervalo_cheque

            # Verificar se uma atualização imediata foi solicitada
            if atualizar_event.is_set():
                atualizar_event.clear()
                logging.info("Atualização manual solicitada.")
                tempo_decorrido = intervalo_atualizacao  # Forçar a atualização imediata

            if tempo_decorrido >= intervalo_atualizacao:
                tempo_decorrido = 0  # Resetar o tempo decorrido

                # Obter clientes offline atuais
                clientes_offline = obter_clientes_offline()
                clientes_offline_atual = set()
                clientes_info_offline_atual = {}

                for cliente in clientes_offline:
                    login = cliente.get('login')
                    clientes_offline_atual.add(login)
                    clientes_info_offline_atual[login] = cliente

                # Obter clientes online atuais
                clientes_online_info = obter_clientes_online()

                # Emitir os totais para o front-end
                total_online = len(clientes_online_info)
                total_offline = len(clientes_offline_atual)
                socketio.emit('atualizar_totais', {'online': total_online, 'offline': total_offline}, namespace='/')

                # Emitir a lista de clientes online
                socketio.emit('atualizar_lista_online', {'clientes_online': clientes_online_info}, namespace='/')

                # Identificar novos clientes offline
                novos_offlines = clientes_offline_atual - clientes_offline_anterior

                # Identificar clientes que voltaram a ficar online
                clientes_reconectados = clientes_offline_anterior - clientes_offline_atual

                # Emitir eventos para o front-end
                if novos_offlines:
                    logging.info(f"Detectados {len(novos_offlines)} novos clientes offline.")
                    for login in novos_offlines:
                        cliente_info = clientes_info_offline_atual[login]
                        socketio.emit('cliente_offline', cliente_info, namespace='/')

                if clientes_reconectados:
                    logging.info(f"Detectados {len(clientes_reconectados)} clientes que voltaram a ficar online.")
                    for login in clientes_reconectados:
                        socketio.emit('cliente_online', {'login': login}, namespace='/')

                clientes_offline_anterior = clientes_offline_atual
                clientes_info_offline_anterior = clientes_info_offline_atual


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('atualizar_agora')
def handle_atualizar_agora():
    atualizar_event.set()
    emit('status_update', {'message': 'Atualização solicitada pelo usuário.'})
    
if __name__ == '__main__':
    with app.app_context():
        socketio.start_background_task(monitorar_conexoes)
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
