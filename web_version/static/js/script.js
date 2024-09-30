var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

// Dicionário para armazenar marcadores no mapa
var markers = {};

// Dicionário para armazenar itens da lista
var listaItens = {};

// Inicializar o mapa
// ... código existente de inicialização do mapa ...

// Atualizar os totais de logins
socket.on('atualizar_totais', function(data) {
    document.getElementById('total-online').textContent = data.online;
    document.getElementById('total-offline').textContent = data.offline;
});

// Atualizar a lista de clientes online
socket.on('atualizar_lista_online', function(data) {
    var listaClientes = document.getElementById('lista-clientes');
    listaClientes.innerHTML = '';  // Limpar a lista

    data.clientes_online.forEach(function(cliente) {
        var login = cliente.login;
        var conexao = cliente.conexao || 'N/A';
        var ultimaConexao = cliente.ultima_conexao_final || 'N/A';

        var listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        listItem.id = 'cliente-' + login;
        listItem.innerHTML = '<strong>Login:</strong> ' + login + '<br>' +
                             '<strong>Conexão:</strong> ' + conexao + '<br>' +
                             '<strong>Última Conexão:</strong> ' + ultimaConexao;

        listaClientes.appendChild(listItem);
        listaItens[login] = listItem;
    });
});

// Evento para quando um cliente ficar offline
socket.on('cliente_offline', function(data) {
    var login = data.login;
    var lat = parseFloat(data.latitude);
    var lon = parseFloat(data.longitude);

    // Atualizar o item na lista
    var listItem = listaItens[login];
    if (listItem) {
        listItem.classList.add('offline');
        // Mover o item para o topo da lista
        var listaClientes = document.getElementById('lista-clientes');
        listaClientes.insertBefore(listItem, listaClientes.firstChild);

        // Fazer o item piscar
        blinkListItem(listItem);
    }

    // Adicionar marcador no mapa
    if (lat && lon) {
        var marker = L.marker([lat, lon], {icon: redIcon}).addTo(map);
        marker.bindPopup("Login: " + login);
        markers[login] = marker;

        // Fazer o marcador piscar
        blinkMarker(marker);
    }
});

// Evento para quando um cliente voltar a ficar online
socket.on('cliente_online', function(data) {
    var login = data.login;

    // Atualizar o item na lista
    var listItem = listaItens[login];
    if (listItem) {
        listItem.classList.remove('offline');
        listItem.classList.remove('blinking');
    }

    // Remover marcador do mapa
    var marker = markers[login];
    if (marker) {
        map.removeLayer(marker);
        delete markers[login];
    }
});

// Função para fazer o item da lista piscar
function blinkListItem(item) {
    item.classList.add('blinking');
}

socket.on('connect', function() {
    console.log('Conectado ao servidor Socket.IO');
});

// CSS para o efeito de piscar
// Adicione o seguinte CSS no seu arquivo style.css:

/*
.offline {
    background-color: #f8d7da;
}

.blinking {
    animation: blinking 1s infinite;
}

@keyframes blinking {
    0% { background-color: #f8d7da; }
    50% { background-color: #ffffff; }
    100% { background-color: #f8d7da; }
}
*/
