from socket import socket, getaddrinfo, AF_INET, SOCK_STREAM
from uasyncio import start_server


class Thimble:
    """
    A tiny web framework in the spirit of Flask, scaled down to run on microcontrollers
    """
    def __init__(self, default_content_type='text/plain', req_buffer_size=1024):
        self.routes = {}  # Dictionary to map method and URL path combinations to functions
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size
        self.debug = False


    server_name = 'Thimble (MicroPython)'  # Used in 'Server' response header.


    @staticmethod
    def http_response_status(status_code):
        """
        Generate an HTTP response status line based on code. Unknown codes result in a 500 Internal Server Error

        Args:
            status_code (int): Numeric HTTP status code

        Returns:
            string: The entire HTTP status line (e.g. HTTP/1.1 200 OK)
        """
        http_status_text = {
            200: "200 OK",
            400: "400 Bad Request",
            404: "404 Not Found",
            500: "500 Internal Server Error"
        }

        if (status_code not in http_status_text):
            status_code = 500

        return f'HTTP/1.1 {http_status_text[status_code]}'


    @staticmethod
    def parse_query_string(query_string):
        """
        Split a URL's query string into individual key/value pairs
        (ex: 'pet=Panda&color=Red' becomes { "pet": "panda", "color": "red"}

        Args:
            query_string (string): the query string portion of a URL (without the leading ? delimiter)
        
        Returns:
            dictionary: key/value pairs
        """
        query = {}
        query_params = query_string.split('&')
        for param in query_params:
            if (not '=' in param):  # A key with no value, like: 'red' instead of 'color=red'
                key=param
                query[key] = ''
            else:
                key, value = param.split('=')
                query[key] = value
                
        return query


    @staticmethod
    def parse_http_request(req_buffer):
        """
        Given a raw HTTP request, return a dictionary with individual elements broken out

        Args:
            req_buffer (bytes): the unprocessed HTTP request sent from the client

        Returns:
            dictionary: key/value pairs including, but not limited to method, path, query, headers, body, etc.
                or None type if parsing fails
        """
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


    @staticmethod
    def format_http_response(body, status_code, content_type):
        """
        Given a body string, HTTP response code, and content-type, add necessary headers and format the server's response

        Args:
            body (string): the html, json, or plain text that is being sent to the client
            status_code (int): the HTTP status code as defined by RFC 7231 Respone Status Codes (ex. 200)
            content_type (string): a media type as defined by the IANA (ex. 'text/plain' or 'application/json')
            
        Returns:
            string: a formatted HTTP response including status line, appropriate headers and body
        """

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


    # MicroPython does not have a built-in types module, so to avoid external dependencies this method lets
    # Thimble determine if route functions should be awaited or not by comparing their type to known async
    # and regular functions that are already part of the code.
    @staticmethod
    def is_async(func):
        """
        Determine if a function is async not by comparing its type to known async and regular functions.

        Args:
            func (object): a reference to the function being examined

        Returns:
            boolean: True if the function was defined as asynchronous, False if not, and None if unknown

        """
        if (type(func) == type(Thimble.on_connect)):
            return True  # It's an async function
        elif(type(func) == type(Thimble.run)):
            return False # It's a regular function
        else:
            return None  # It's not a function


    def route(self, url_path, methods=['GET']):
        """
        Given a path and list of zero or more HTTP methods, add the decorated function to the route table.

        Args:
            url_path (string): path portion of a URL (ex. '/path/to/thing') that will trigger a call to the function
            methods (list): a list of any HTTP methods (eg. ['GET', 'PUT']) that are used to trigger the call

        Returns:
            nothing
        """

        def add_route(func):
            for method in methods:
                self.routes[method.upper() + url_path] = func  # Methods are uppercase (see RFC 9110.)
        return add_route


    def run(self, host='0.0.0.0', port=80, debug=False):
        """
        Synchronous connection handler used to process one connection at a time.

        Args:
            host (string): IP address of the interface the listener will bind to
            port (int): TCP port number the listener will bind to
            debug (boolean): flag indicating if extra messages should be sent to the serial console

        Returns:
            nothing
        """
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
                    except Exception as ex:
                        print(f'Function call failed: {ex}')
                        res = Thimble.format_http_response('', 500, 'text/plain')
                    else:
                        if (isinstance(func_result, tuple)):  # User-defined functions can respond with a body, status code tuple or just a body.
                            res = Thimble.format_http_response(func_result[0], func_result[1], self.default_content_type)
                        else:
                            res = Thimble.format_http_response(func_result, 200, self.default_content_type)

                if (self.debug): print(f'Response:\n{res}')
                conn.send(res)
                conn.close()


    async def on_connect(self, reader, writer):
        """
        Callback function for run_async to process the HTTP request.

        Args:
            reader (stream): data sent from the client
            writer (stream): data sent to the client

        Returns:
            nothing
        """
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
                if (self.debug): print(f'Async function? {Thimble.is_async(self.routes[route_key])}')
                try:
                    if (Thimble.is_async(self.routes[route_key]) == True):
                        func_result = await self.routes[route_key](req)
                    else:
                        func_result = self.routes[route_key](req)
                except Exception as ex:
                    print(f'Function call failed: {ex}')
                    res = Thimble.format_http_response('', 500, 'text/plain')
                else:
                    if (isinstance(func_result, tuple)):  # User-defined functions can respond with a body, status code tuple or just a body.
                        res = Thimble.format_http_response(func_result[0], func_result[1], self.default_content_type)
                    else:
                        res = Thimble.format_http_response(func_result, 200, self.default_content_type)


            if (self.debug): print(f'Response:\n{res}')
            writer.write(res)
            await writer.drain()
            reader.wait_closed()
            writer.close()
            if (self.debug): print(f'Connection closed for {client_ip}')


    def run_async(self, host='0.0.0.0', port=80, loop=None, debug=False):
        """
        Asynchronous connection handler used to process multiple connections without blocking.

        Args:
            host (string): IP address of the interface the listener will bind to
            port (int): TCP port number the listener will bind to
            loop (object): a reference to the asynchronous loop that the listener will insert itself into
            debug (boolean): flag indicating if extra messages should be sent to the seria console

        Returns:
            nothing
        """
        self.debug = debug
        print(f'Starting asynchronous listener on {host}:{port}')
        server = start_server(self.on_connect, host, port, 5)
        loop.create_task(server)

