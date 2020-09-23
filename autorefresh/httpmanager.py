import mimetypes
import os
import sys
from urllib.parse import quote, unquote

import jinja2

mimetypes.init()
PATH = os.path.realpath(os.path.dirname(sys.argv[0]))
CWD = os.getcwd()

# To add, just in case the javascript is disabled
NOSCRIPT = ''''''

JINJA_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader('autorefresh', 'assets'),
)

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

    template = JINJA_ENV.get_template('file_list.html')
    return template.render(current_path=path, listing_directories=directories, listing_files=files)


def __getMimetype__(path):
    val = "text/plain"
    try:
        val = mimetypes.types_map[os.path.splitext(path)[1]]
    except:
        pass
    return val


def handlehttp(conn, path):
    path = unquote(path)
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

                template = JINJA_ENV.get_template('js_block.html')
                javascript = template.render()

                content = content.replace("</body>", javascript + "</body>")
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
        template = JINJA_ENV.get_template('404.html')
        data = template.render(path=path)
        conn.send(b"HTTP/1.0 404 OK\r\n")
        conn.send(b"Content-Type: text/html\r\n\r\n")
        conn.send(data.encode())
    conn.close()
