var ws = new WebSocket("ws://127.0.0.1:8000/ws");
ws.onmessage = function(event) {
    console.log("Received:", event.data);
};
ws.onopen = function(event) {
    ws.send("Hello Server!");
};
