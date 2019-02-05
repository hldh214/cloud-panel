let ws = new ReconnectingWebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

function create() {
    let submit_data_raw = $('#create').serializeArray();

    let submit_data = {};
    for (let x in submit_data_raw) {
        submit_data[submit_data_raw[x].name] = submit_data_raw[x].value;
    }

    ws.send(JSON.stringify({
        'type': 'create',
        'data': submit_data
    }));

    $('#create-modal').modal('hide');
}

ws.onopen = function () {
    ws.send(JSON.stringify({
        'type': 'refresh'
    }));
};

ws.onmessage = function (event) {
    let data = JSON.parse(event.data);

    switch (data.type) {
        case 'refresh':
            $('.provider-' + data.provider_name).remove();

            data.nodes.forEach(function (each) {
                let tr = $('<tr></tr>');
                tr.addClass('provider-' + data.provider_name);

                $('<td></td>').text(each.ss_config).appendTo(tr);
                $('<td></td>').text(each.state).appendTo(tr);
                $('<td></td>').text(each.public_ips).appendTo(tr);
                $('<td></td>').text(data.provider_name).appendTo(tr);

                let action_td = $('<td></td>');
                if (each.state === 'running') {
                    action_td.append(
                        $('<button type="button" class="btn btn-danger btn-sm">Delete</button>')
                            .data('node_id', each.node_id)
                            .click(function () {
                                $(this).text('Deleting...');

                                ws.send(JSON.stringify({
                                    'type': 'delete',
                                    'data': {
                                        'node_id': each.node_id,
                                        'provider_name': data.provider_name
                                    }
                                }));
                            })
                    );
                }
                action_td.appendTo(tr);

                $('#tbody').append(tr);
            });
            break;
    }
};
