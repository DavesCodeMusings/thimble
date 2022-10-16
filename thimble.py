"""
  Thimble -- A tiny web framework in the spirit of Flask, but scaled down to run on microcontrollers.
"""

from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM
from uasyncio import start_server


class Thimble:
    def __init__(self, default_content_type='text/plain', req_buffer_size=1024):
        self.routes = {}  # Dictionary to map method and URL path combinations to functions
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size
        self.debug = False


    server_name = 'Thimble (MicroPython)'  # Used in 'Server' response header.


    # HTTP responses consist of a numeric code sent with a textual description, so here's a subset.
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
            
        return f'HTTP/1.1 {Thimble.http_status_text[status_code]}'


    # Given a query string, in the format key1=value1&key2=value2, return a dictionary of key/value pairs.
    @staticmethod
    def parse_query_string(query_string):
        query = {}
        query_params = query_string.split('&')
        for param in query_params:
            if (not '=' in param):  # Example: somebody sent ?on instead of ?state=on
                key=param
                query[key] = ''
            else:
                key, value = param.split('=')
                query[key] = value
                
        return query


    # Given a raw HTTP request, return a dictionary with individual elements broken out.
    # Takes a buffer containing the HTTP request sent from the client.
    # Returns a dictionary containing method, path, query, headers, body, etc. or None if parsing fails.
    @staticmethod
    def parse_http_request(req_buffer):
        req = {}
        req_buffer_lines = req_buffer.decode('utf8').split('\r\n')
        req['method'], target, req['http_version'] = req_buffer_lines[0].split(' ', 2)  # Example: GET /route/path HTTP/1.1
        if (not '?' in target):
            req['path'] = target
        else:  # target can have a query component, so /route/path could be something like /route/path?state=on&timeout=30
            req['path'], query_string = target.split('?', 1)
            req['query'] = Thimble.parse_query_string(query_string)

        req['headers'] = {}
        for i in range(1, len(req_buffer_lines) - 1):
            if (req_buffer_lines[i] == ''):  # Blank line signifies the end of headers.
                break
            else:
                name, value = req_buffer_lines[i].split(':', 1)
                req['headers'][name.strip()] = value.strip()

        req['body'] = req_buffer_lines[len(req_buffer_lines) - 1]  # Last line is the body (or blank if no body.)
        
        return req


    # Given a body string, HTTP response code, and content-type, add necessary headers and format the server's response.
    @staticmethod
    def format_http_response(body, status_code, content_type):
        if (isinstance(body, str) == False):
            body = str(body)
        res_lines = []  # Build response as individual lines and worry about line-endings later.
        res_lines.append(Thimble.http_response_status(status_code))
        res_lines.append(f'Content-Length: {len(body)}')
        res_lines.append(f'Content-Type: {content_type}')
        res_lines.append(f'Server: {Thimble.server_name}')
        res_lines.append('Connection: close')
        res_lines.append('')
        res_lines.append(f'{body}')

        return '\r\n'.join(res_lines)


    # Given a path and list of zero or more HTTP methods, add the decorated function to the route table. 
    def route(self, url_path, methods=['GET']):
        def add_route(func):
            for method in methods:
                self.routes[method.upper() + url_path] = func  # Methods are uppercase (see RFC 9110.)
        return add_route


    # Synchronous connection handler (one connection at a time.)
    def run(self, host='0.0.0.0', port=80, debug=False):
        self.debug = debug
        print(f'Starting listener on {host}:{port}')
        sock = socket(AF_INET, SOCK_STREAM)
        sock.bind(getaddrinfo(host, port)[0][-1])
        sock.listen()

        while (True):
            conn, client = sock.accept()
            client_ip = client[0]
            if (self.debug): print(f'Connection from: {client_ip}')
            try:
                req_buffer = conn.recv(self.req_buffer_size)
                req = Thimble.parse_http_request(req_buffer)
            except Exception as ex:
                print(f'Unable to parse request: {ex}')
                res = Thimble.format_http_response('', 400, 'text/plain')
            else:
                route_key = req['method'] + req['path']
                if (not route_key in self.routes):  # No function in the route table?
                    print(f'No route found for: {route_key}')
                    res = Thimble.format_http_response('', 404, 'text/plain')
                else:
                    try:
                        func_result = self.routes[route_key](req)  # Execute function in routing table, passing request parameters.
                        if (self.debug): print(f'Function result: {func_result}')
                        if (isinstance(func_result, tuple)):  # User-defined functions can respond with a body, status code tuple or just a body.
                            res = Thimble.format_http_response(func_result[0], func_result[1], self.default_content_type)
                        else:
                            res = Thimble.format_http_response(func_result, 200, self.default_content_type)
                    except Exception as ex:
                        print(f'Function call failed: {ex}')
                        res = Thimble.format_http_response('', 500, 'text/plain')

                conn.send(res)
                conn.close()


    # Callback for run_async
    async def on_connect(self, reader, writer):
        if (self.debug):
            client_ip = writer.get_extra_info('peername')[0]  # Get just the IP address portion of the tuple.
            print(f'Connection from client: {client_ip}')
        try:
            req_buffer = await reader.read(self.req_buffer_size)
            req = Thimble.parse_http_request(req_buffer)
        except Exception as ex:
            print(f'Unable to parse request: {ex}')
            res = Thimble.format_http_response('', 400, 'text/plain')
        else:
            route_key = req['method'] + req['path']
            if (not route_key in self.routes):  # No function in the route table?
                res = Thimble.format_http_response(f'No route found for: {route_key}', 404, 'text/plain')
            else:
                try:
                    func_result = self.routes[route_key](req)  # Execute function in routing table, passing request parameters.
                    if (self.debug): print(f'Function result: {func_result}')
                    if (isinstance(func_result, tuple)):  # User-defined functions can respond with a body, status code tuple or just a body.
                        res = Thimble.format_http_response(func_result[0], func_result[1], self.default_content_type)
                    else:
                        res = Thimble.format_http_response(func_result, 200, self.default_content_type)
                except Exception as ex:
                    print(f'Function call failed: {ex}')
                    res = Thimble.format_http_response('', 500, 'text/plain')

            if (self.debug): print(res)
            writer.write(res)
            await writer.drain()
            reader.wait_closed()
            writer.close()
            if (self.debug): print(f'Connection closed for {client_ip}')


    # Asynchronous connection handler (multiple simultaneous connections.)
    def run_async(self, host='0.0.0.0', port=80, loop=None, debug=False):
        self.debug = debug
        print(f'Starting asynchronous listener on {host}:{port}')
        server = start_server(self.on_connect, host, port, 5)
        loop.create_task(server)

