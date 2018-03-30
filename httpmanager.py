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


def __generateDirPage__(path):
    ls = os.scandir(CWD + path)
    entries = []
    for entry in ls:
        entries.append(entry.name if entry.is_file() else (entry.name + "/"))
    ls.close()

    data = HTML_BEFORE
    data += "<h1>" + path + "</h1>"
    data += "<a href=\"../\">../</a><br>"
    for entry in entries:
        data += "<a href=\"" + entry + "\">" + entry + "</a><br>"
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
            conn.send(("Content-Type: " + mimetypes.types_map[".html"] +
                       "\r\n\r\n").encode())
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
                content = content.replace("</body>", JAVASCRIPT + "</body>")
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
        conn.send(b"Content-Type: text/plain\r\n\r\n")
        conn.send(b"err 404")
    conn.close()
