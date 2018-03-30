let towatch = []
// all elements
let nodes = document.getElementsByTagName("*");
for (let i = 0; i < nodes.length; i++)
    if (nodes[i].src != null && nodes[i].src != "")
        towatch.push(nodes[i].src);

// head elements (src are already checked during the all elements section)
nodes = document.head.childNodes
for (let i = 0; i < nodes.length; i++)
    if (nodes[i].href != null && nodes[i].href != "")
        towatch.push(nodes[i].href);

let data = JSON.stringify(towatch);
let sock = new WebSocket("ws://" + window.location.host + "/__websocket");
sock.addEventListener('open', function (event)
	{
		console.log(data)
		sock.send(data);
	});

