import mimetypes
import os
from urllib.parse import unquote

import jinja2

mimetypes.init()

JINJA_ENV = jinja2.Environment(
    loader=jinja2.PackageLoader('autorefresh', 'assets'),
)

class HttpManager:
    """Handle HTTP requests and serve the expected files."""
    def __init__(self, root: str):
        self.root = root


    @staticmethod
    def _generate_dir_page(path):
        """Return a file listing for a given directory."""
        directories = ["../"]
        files = []
        for entry in os.scandir(path):
            if entry.is_file():
                files.append(entry.name)
            else:
                directories.append(entry.name + "/")
        files.sort(key=lambda s: s.lower())
        directories.sort(key=lambda s: s.lower())

        template = JINJA_ENV.get_template('file_list.html')
        return template.render(current_path=path, listing_directories=directories, listing_files=files)


    @staticmethod
    def _get_mimetype(path):
        """Return the mimetype of a given path using it's extension."""
        return mimetypes.types_map.get(os.path.splitext(path)[1], "text/plain")


    def handlehttp(self, conn, path):
        """Handle an http request."""
        print(path)
        path = os.path.join(self.root, unquote(path)[1:])
        print(path)
        print("-----")
        if os.path.exists(path):
            conn.send(b"HTTP/1.0 200 OK\r\n")
            # Directory
            if path.endswith("/"):
                conn.send(b"Content-Type: text/html\r\n\r\n")
                data = self._generate_dir_page(path)
                conn.send(data.encode())
            # File
            else:
                mime = self._get_mimetype(path)
                # HTML -> insert custom JS
                if mime == "text/html":
                    data = open(path, mode="r")
                    content = data.read()
                    data.close()

                    template = JINJA_ENV.get_template('js_block.html')
                    javascript = template.render()

                    content = content.replace("</body>", javascript + "</body>")
                    conn.send(("Content-Type: " + mime + "\r\n\r\n").encode())
                    conn.send(content.encode())
                # Send file as-is
                else:
                    data = open(path, mode="rb")
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
