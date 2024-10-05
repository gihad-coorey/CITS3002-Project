from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler
import json
import re
from .routes import ROUTE_MAP

from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qsl

class WebRequest:
    def __init__(self, path: str, request_type: str, body: str, cookies: SimpleCookie):
        url = urlparse(path)
        query = dict(parse_qsl(url.query)) # will only take the last value, previous duplicate keys ignored

        self.path = url.path
        self.query = query
        self.fragment = url.fragment
        self.request_type = request_type
        self.body = body
        self.cookies = cookies
        try:
            self.json = json.loads(body)
        except:
            self.json = None

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request('GET')
    
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        self._handle_request('POST', body)

    # body is only provided by POST
    def _handle_request(self, request_type, body=''):
        cookies = SimpleCookie(self.headers.get('Cookie'))
        request = WebRequest(self.path, request_type, body, cookies)
        if request.path in ROUTE_MAP:
            content = ROUTE_MAP[request.path](request)

            body = content
            response_code = 200
            cookie = None

            # redirect
            if isinstance(content, Redirect):
                self.send_response(302)
                self.send_header('Location', content.url)
                self.end_headers()
                return
            # normal
            if type(content) is tuple:
                body = content[0]
                object = content[1]
                if 'cookies' in object:
                    cookie = SimpleCookie()
                    for key in object['cookies']:
                        cookie[key] = object['cookies'][key]

                    pass
                if 'code' in object:
                    response_code = object['code']

            self.send_response(response_code)
            self.send_header("Content-type", "text/html")
            if cookie is not None:
                for morsel in cookie.values():
                    self.send_header("Set-Cookie", morsel.OutputString())
            self.end_headers()
            if body is not None:
                self.wfile.write(bytes(body, "utf-8"))
            else:
                print ('body was None')

        elif request.path.endswith(".css"):
            self._send_file('css' + self.path, "text/css")

        elif request.path.endswith(".js"):
            self._send_file('js' + self.path, "text/javascript")

        else:
            self.send_response(404)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(bytes("404 error", "utf-8"))
        return
    
    def _send_file(self, path, content_type):
        content = open(path).read()

        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()

        self.wfile.write(bytes(content, "utf-8"))

class Redirect:
    def __init__(self, url) -> None:
        self.url = url

def redirect(url):
    return Redirect(url)

def start_server(hostName='0.0.0.0', port=80):
    webServer = HTTPServer((hostName, port), MyServer)

    if hostName=='0.0.0.0':
        print(f"Server listening on all ips")
        print(f"Access at http://localhost:%s" % (port))
    else:
        print("Server started http://%s:%s" % (hostName, port))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

if __name__ == "__main__":
    start_server('localhost', 8080)