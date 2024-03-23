var ws = new WebSocket("ws://10.150.83.102:7648/ws");
ws.onmessage = function(event) {
    console.log("Received:", event.data);
};
ws.onopen = function(event) {
    ws.send("Hello Server!");
};
