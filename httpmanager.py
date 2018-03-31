import os
import mimetypes
import sys

HTML_BEFORE = """<!DOCTYPE HTML>
<html>
 <head>
  <meta charset="utf8">
  <title>RefresHTML</title>
 </head>
 <body>"""

HTML_AFTER = """ </body>
</html>"""

mimetypes.init()
PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
CWD = os.getcwd()

# Javascript to be included at the end of each html documents
_js_source = open(PATH + "/included.js", "r")
JAVASCRIPT = "<script>" + _js_source.read() + "</script>"
_js_source.close()

# To add, just in case the javascript is disabled
NOSCRIPT = '''<noscript><div style="width: 100vw; height: 100vh; position: fixed; top: 0; left: 0; padding: 0; margin: 0; line-height: 100vh; font-size: 3rem; background: #fff; text-align: center;">PLEASE ENABLE JAVASCRIPT FOR AUTOREFRESH TO WORK</div></noscript>'''


def __generateDirPage__(path):
    ls = os.scandir(CWD + path)
    directories = ["../"]
    files = []
    for entry in ls:
        if entry.is_file():
            files.append(entry.name)
        else:
            directories.append(entry.name + "/")
    files.sort(key=lambda s: s.lower())
    directories.sort(key=lambda s: s.lower())

    data = HTML_BEFORE
    data += "<h1>" + path + "</h1>"
    for e in directories:
        data += "<a href=\"" + e + "\">📁 - " + e + "</a><br>"
    for e in files:
        data += "<a href=\"" + e + "\">📄 - " + e + "</a><br>"
    data += HTML_AFTER
    return data


def __getMimetype__(path):
    val = "text/plain"
    try:
        val = mimetypes.types_map[os.path.splitext(path)[1]]
    except:
        pass
    return val


def handlehttp(conn, path):
    if os.path.exists(CWD + path):
        conn.send(b"HTTP/1.0 200 OK\r\n")
        # Directory
        if path.endswith("/"):
            conn.send(b"Content-Type: text/html\r\n\r\n")
            data = __generateDirPage__(path)
            conn.send(data.encode())
        # File
        else:
            mime = __getMimetype__(path)
            # HTML -> insert custom JS
            if mime == "text/html":
                data = open(CWD + path, mode="r")
                content = data.read()
                data.close()
                content = content.replace("</body>",
                                          JAVASCRIPT + NOSCRIPT + "</body>")
                conn.send(("Content-Type: " + mime + "\r\n\r\n").encode())
                conn.send(content.encode())
            # Send file as-is
            else:
                data = open(CWD + path, mode="rb")
                conn.send(("Content-Type: " + mime + "\r\n\r\n").encode())
                conn.send(data.read())
                data.close()
    # 404
    else:
        conn.send(b"HTTP/1.0 404 OK\r\n")
        conn.send(b"Content-Type: text/html\r\n\r\n")
        data = HTML_BEFORE
        data += "<h1>404 - page not found</h1>"
        data += "<a href=\"../\">Go to parent directory</a>"
        data += HTML_AFTER
        conn.send(data.encode())
    conn.close()
