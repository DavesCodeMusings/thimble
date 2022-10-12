"""
  Thimble -- A tiny web framework in the spirit of Flask, but scaled down to run on microcontrollers.
"""

from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM

class Thimble:
    def __init__(self, default_content_type='text/plain', req_buffer_size=1024):
        self.routes = {}
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size

    def route(self, path):
        def add_route(func):
            self.routes[path] = func
        return add_route

    def run(self, host='0.0.0.0', port=80, debug=False):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(getaddrinfo(host, port)[0][-1])
        sock.listen()
        print(f'Listening on {host}:{port}')

        while (True):
            conn, client = sock.accept()
            if (debug): print(f'Connection from: {client}')
            req = { 'is_valid': True }
            try:
                req_buffer = conn.recv(self.req_buffer_size).decode('utf8').split('\r\n')
                if (debug): print(req_buffer)
                req_length = len(req_buffer)  # Number of lines.
                req['method'], req['url'], req['http_version'] = req_buffer[0].split(' ', 2)  # Example first line: GET /page.html HTTP/1.1
                req['header'] = {}
                for i in range(1, req_length - 1):
                    if (req_buffer[i] == ''):  # Blank line signifies the end of headers.
                        break
                    else:
                        name, value = req_buffer[i].split(':', 1)
                        req['header'][name.strip()] = value.strip()
                req['body'] = req_buffer[req_length - 1]  # Last line is the body (or blank if no body.)

            except:
                req['is_valid'] = False

            if (req['is_valid']):
                if (req['url'] in self.routes and callable(self.routes[req['url']])):  # Is it a function in the route table?
                    conn.send('HTTP/1.0 200 OK\r\n')
                    conn.send(f'Content-type: {self.default_content_type}\r\n')  # TODO: Make response headers user definable
                    conn.send('\r\n')
                    conn.send(f'{self.routes[req['url']]()}\r\n')  # Send the return value from function as the response body.
                else:
                    conn.send('HTTP/1.0 404 Not Found\r\n\r\n')
            else:
                conn.send('HTTP/1.0 400 Bad Request\r\n\r\n')

            conn.close()
