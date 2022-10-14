"""
  Thimble -- A tiny web framework in the spirit of Flask, but scaled down to run on microcontrollers.
"""

from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM

class Thimble:
    def __init__(self, default_content_type='text/plain', req_buffer_size=1024):
        self.routes = {}  # Dictionary to map method and URL path combinations to functions
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size
        self.server_name = 'Thimble (MicroPython)'

    http_status_text = {
        200: "200 OK",
        400: "400 Bad Request",
        404: "404 Not Found",
        500: "500 Internal Server Error"
    }

    # Generate an HTTP response status line based on code. Unknown codes result in a 500.
    # Returns a string similar to: HTTP/1.1 200 OK
    @staticmethod
    def http_response_status(status_code):
        if (status_code not in Thimble.http_status_text):
            status_code = 500
        return f'HTTP/1.1 {Thimble.http_status_text[status_code]}\r\n'

    # Given a raw HTTP request, return a dictionary with individual elements broken out.
    # Takes a buffer containing the HTTP request sent from the client.
    # Returns a dictionary containing method, path, query, headers, body, etc. or None if parsing fails.
    @staticmethod
    def parse_http_request(req_buffer):
        req = {}
        try:
            req_buffer_lines = req_buffer.decode('utf8').split('\r\n')
            req['method'], req['target'], req['http_version'] = req_buffer_lines[0].split(' ', 2)  # Example first line: GET /page.html HTTP/1.1
            if ('?' in req['target']):
                req['path'], req['query'] = target.split('?')
                req['query'] = '?' + req['query']  # Convention is to include the question mark.
            else:
                req['path'] = req['target']
            req['headers'] = {}
            for i in range(1, len(req_buffer_lines) - 1):
                if (req_buffer_lines[i] == ''):  # Blank line signifies the end of headers.
                    break
                else:
                    name, value = req_buffer_lines[i].split(':', 1)
                    req['headers'][name.strip()] = value.strip()
            req['body'] = req_buffer_lines[len(req_buffer_lines) - 1]  # Last line is the body (or blank if no body.)
        except:
            req = None
        return req

    def route(self, url_path, methods=['GET']):
        def add_route(func):
            for method in methods:
                self.routes[method + url_path] = func
        return add_route

    def run(self, host='0.0.0.0', port=80, debug=False):
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(getaddrinfo(host, port)[0][-1])
        sock.listen()
        print(f'Listening on {host}:{port}')

        while (True):
            conn, client = sock.accept()
            if (debug): print(f'Connection from: {client}')
            req_buffer = conn.recv(self.req_buffer_size)
            req = Thimble.parse_http_request(req_buffer)
            if (debug): print(req)
            if (req):
                route_key = req['method'] + req['path']  # Example: 'GET/gpio/0'
                if (debug): print(f'Looking up route by key: {route_key}')
                if (route_key in self.routes and callable(self.routes[route_key])):  # Is it a function in the route table?
                    res = None
                    if (debug): print(f'Executing: {self.routes[route_key]}')
                    try:
                        res = self.routes[route_key](req)  # Execute function pointed to by route_key with request parameters.
                    except:
                        if (debug): print("Function call failed.")
                        res = ('', 500)
                    body = ''
                    status_code = 200
                    if (isinstance(res, tuple)):
                        body, status_code = res
                    else:
                        body = res
                    conn.send(f'{Thimble.http_response_status(status_code)}')  # Status line
                    conn.send(f'Content-Length: {len(body)}\r\n')
                    conn.send(f'Content-Type: {self.default_content_type}\r\n')
                    conn.send(f'Server: {self.server_name}\r\n')
                    conn.send('\r\n')  # Blank line denotes end of headers.
                    conn.send(f'{body}\r\n')
                else:
                    if (debug): print('No route found.')
                    conn.send(f'{Thimble.http_response_status(404)}')
            else:
                if (debug): print('HTTP request was invalid or too long')
                conn.send(f'{Thimble.http_response_status(400)}')

            conn.close()
