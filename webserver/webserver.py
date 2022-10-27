#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

LOCALHOST = '127.0.0.1'
HOST_PORT = 8080
LED_INTERFACE_PORT = 4237

class LEDInterface:
    def __init__(self, port):
        self.socket = socket.socket()
        self.socket.connect((LOCALHOST, port))

    def do(self, action, data):
        if action == 'rainbow':
            self.socket.sendall(b'ma')
        elif action == 'christmas':
            self.socket.sendall(b'mx')
        elif action == 'full':
            self.socket.sendall(b'mf')
        elif action == 'dim':
            self.socket.sendall(b'md')
        elif action == 'off':
            self.socket.sendall(b'm0')
        elif action == 'color':
            self.socket.sendall(b'c' + bytes(data['color'][-6:], 'ascii'))
        else:
            print("Skipping unknown action %s" % action)

class Partymode3Server:
    def __init__(self, led_interface):
        def handler(*args):
            Partymode3Handler(led_interface, *args)
        http_server = HTTPServer(('', HOST_PORT), handler)
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            http_server.server_close()

class Partymode3Handler(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHandler for
        controlling PartyMode3 LED strips
    """
    def __init__(self, led_interface, *args):
        self.led_interface = led_interface
        BaseHTTPRequestHandler.__init__(self, *args)

    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command 
            'curl -I http://server-ip-address:port' 
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()

    def do_GET(self):
        """ do_GET() can be tested using curl command 
            'curl http://server-ip-address:port' 
        """
        html = '''
            <html>
            <body style="width:960px; margin: 20px auto;">
            <h1>Welcome to my Raspberry Pi</h1>
            <form action="/" method="POST">
                Mode:
                <button type="submit" name="action" value="rainbow">Rainbow</button>
                <button type="submit" name="action" value="christmas">Christmas</button>
                <button type="submit" name="action" value="dim">Dim</button>
                <button type="submit" name="action" value="full">Full</button>
                <input type="color" name="color" />
                <button type="submit" name="action" value="color">Set Solid Color</button>
                <button type="submit" name="action" value="off">Off</button>
            </form>
            </body>
            </html>
        '''
        self.do_HEAD()
        self.wfile.write(html.encode("utf-8"))

    def do_POST(self):
        """ do_POST() can be tested using curl command 
            'curl -d "submit=On" http://server-ip-address:port' 
        """
        content_length = int(self.headers['Content-Length'])    # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")   # Get the data
        post_data = {k: v for k, v in [row.split('=') for row in post_data.split('&')]}
        if 'action' in post_data:
            self.led_interface.do(post_data['action'], post_data)
        
        self._redirect('/')    # Redirect back to the root url

def main():
    Partymode3Server(LEDInterface(LED_INTERFACE_PORT))

if __name__ == '__main__':
    main()
