# AutoRefresh
AutoRefresh is a simple brackets-like auto refresher for your local website.

Unlike bracket's solution, it supports any browser (with websockets support), so you can use it with Firefox!

AutoRefresh currently only works with Linux. Support for other platforms is planned.

It is similar to [logankoester's autorefresh](https://github.com/logankoester/autorefresh), but based on python3 and it should automagically detect files to detect changes to.

The modifications are detected using pyinotify, and the http/websocket server is implemented by hand using sockets.

This is quite early stage, there is no simple way to install this at the time, but it should work.

