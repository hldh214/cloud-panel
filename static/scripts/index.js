window.onload = function () {
    ws.send('refresh');
};

let ws = new WebSocket('ws://' + window.location.hostname + ':' + window.location.port + '/ws');

ws.onmessage = function (event) {
    console.log(event);
};
