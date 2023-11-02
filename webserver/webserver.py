#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

LOCALHOST = '127.0.0.1'
HOST_PORT = 8080
LED_INTERFACE_PORT = 4237

class LEDInterface:
    def __init__(self, port):
        self.cur_solid_color='ffffff'    # Persistence
        self.socket = socket.socket()
        self.socket.connect((LOCALHOST, port))

    def do(self, action, data):
        if action == 'rainbow':
            self.socket.sendall(b'ma')
        elif action == 'romantic':
            self.socket.sendall(b'mr')
        elif action == 'christmas':
            self.socket.sendall(b'mx')
        elif action == 'easter':
            self.socket.sendall(b'me')
        elif action == 'full':
            self.socket.sendall(b'bf')
        elif action == 'medium':
            self.socket.sendall(b'bm')
        elif action == 'dim':
            self.socket.sendall(b'bd')
        elif action == 'skylight':
            self.socket.sendall(b'ms')
        elif action == 'off':
            self.socket.sendall(b'm0')
        elif action == 'color':
            self.cur_solid_color = data['color'][-6:]
            self.socket.sendall(b'c' + bytes(self.cur_solid_color, 'ascii'))
        elif action.startswith('white'):
            self.socket.sendall(b'w' + bytes('%05d' % int(action.split('-')[1]), 'ascii'))
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
        if self.path != '/':
            html = ''
        else:
            html = '''
<html lang="en">
	<head>
		<meta name="viewport" content="width=device-width, initial-scale=1">
 		<!-- Bootstrap core CSS -->
		<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
		<meta name="theme-color" content="#1a73e8">
	</head>
	<body class="text-center">
		<h1>PartyMode 3.0</h1>
		<form action="/" method="POST" class="container">
			<div class="row pb-3">
				<div class="col">
					<button class="btn btn-lg btn-danger" type="submit" name="action" value="off">Off</button>
					<button class="btn btn-lg btn-warning" type="submit" name="action" value="dim">Dim</button>
					<button class="btn btn-lg btn-success" type="submit" name="action" value="medium">Medium</button>
					<button class="btn btn-lg btn-info" type="submit" name="action" value="full">Full</button>
				</div>
			</div>
			<div class="row pb-3">
				<div class="col">
					<input class="btn btn-lg btn-secondary" type="color" name="color" value="#{0}" onchange="document.getElementById('change-color').click();" />
					<button class="d-none" type="submit" name="action" id="change-color" value="color">Set Solid Color</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="rainbow">Rainbow</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="romantic">Romantic</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="christmas">Christmas</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="easter">Easter</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="skylight">Sky Light</button>
				</div>
			</div>
			<div class="row">
				<div class="col">
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-1900">Candle</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-2600">Tungsten (40W)</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-2850">Tungsten (100W)</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-3200">Halogen</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-5200">Carbon Arc</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-5400">High Noon Sun</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-6000">Direct Sunlight</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-7000">Overcast Sky</button>
					<button class="btn btn-lg btn-secondary" type="submit" name="action" value="white-20000">Clear Blue Sky</button>
				</div>
			</div>
		</form>
	</body>
</html>
            '''.format(self.led_interface.cur_solid_color)
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
