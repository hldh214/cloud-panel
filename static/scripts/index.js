let ws = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

ws.onopen = function () {
    ws.send('refresh');
};

ws.onmessage = function (event) {
    let data = JSON.parse(event.data);

    switch (data.type) {
        case 'refresh':
            let tr = $('<tr></tr>');
            data.nodes.forEach(function (each) {
                $('<td></td>').text(each.uuid).appendTo(tr);
                $('<td></td>').text(each.state).appendTo(tr);
                $('<td></td>').text(each.public_ips).appendTo(tr);
                $('<td></td>').text(each.provider_name).appendTo(tr);
            });
            $('#tbody').append(tr);
            break;
    }
};
