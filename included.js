let origin = location.origin + "/"

let towatch = [location.pathname.substring(1)];
// all elements
let nodes = document.getElementsByTagName("*");
for (let i = 0; i < nodes.length; i++)
    if (nodes[i].src != null && nodes[i].src.startsWith(origin))
        towatch.push(nodes[i].src.substring(origin.length));

// head elements (src are already checked during the all elements section)
nodes = document.head.childNodes
for (let i = 0; i < nodes.length; i++)
    if (nodes[i].href != null && nodes[i].href.startsWith(origin))
        towatch.push(nodes[i].href.substring(origin.length));

let data = JSON.stringify(towatch);
let sock = new WebSocket("ws://" + window.location.host + "/__websocket");

sock.addEventListener("open", e => sock.send(data));
sock.addEventListener("message", e => {if (e.data == "reload") location.reload()});
