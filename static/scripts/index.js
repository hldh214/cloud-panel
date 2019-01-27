window.onload = function () {
    ws.send('refresh');
};

let ws = new WebSocket('ws://localhost:8888/ws');

ws.onmessage = function (event) {
    console.log(event);
};
