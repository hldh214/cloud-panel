let ws = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

ws.onopen = function () {
    ws.send(JSON.stringify({
        'type': 'refresh'
    }));
};

ws.onmessage = function (event) {
    let data = JSON.parse(event.data);

    switch (data.type) {
        case 'refresh':
            let tr = $('<tr></tr>');
            tr.addClass('provider-' + data.nodes[0].provider_name);
            $('.provider-' + data.nodes[0].provider_name).remove();

            data.nodes.forEach(function (each) {
                $('<td></td>').text(each.uuid).appendTo(tr);
                $('<td></td>').text(each.state).appendTo(tr);
                $('<td></td>').text(each.public_ips).appendTo(tr);
                $('<td></td>').text(each.provider_name).appendTo(tr);
                $('<td></td>').append(
                    $('<button type="button" class="btn btn-danger btn-sm">Delete</button>')
                ).appendTo(tr);
            });


            $('#tbody').append(tr);
            break;
    }
};
