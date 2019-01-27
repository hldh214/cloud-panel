let ws = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

ws.onopen = function () {
    ws.send('refresh');
};

ws.onmessage = function (event) {
    console.log(event);
};
