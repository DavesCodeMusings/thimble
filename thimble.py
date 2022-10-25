from uasyncio import get_event_loop, start_server
from os import stat
from re import match

class Thimble:
    """
    A tiny web framework in the spirit of Flask, scaled down to run on microcontrollers
    """
    def __init__(self, default_content_type='text/plain', req_buffer_size=1024):
        self.routes = {}  # Dictionary to map method and URL path combinations to functions
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size
        self.static_folder = '/static'
        self.directory_index = 'index.html'
 
    server_name = 'Thimble (MicroPython)'  # Used in 'Server' response header.

    http_status_message = {
        200: "200 OK",
        302: "302 Found",
        400: "400 Bad Request",
        404: "404 Not Found",
        500: "500 Internal Server Error"
    }

    media_types = {
        'css': 'text/css',
        'html': 'text/html',
        'js': 'application/javascript',
        'json': 'application/json',
        'svg': 'image/svg+xml',
        'txt': 'text/plain'
    }


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
    async def parse_http_request(req_buffer):
        """
        Given a raw HTTP request, return a dictionary with individual elements broken out

        Args:
            req_buffer (bytes): the unprocessed HTTP request sent from the client

        Raises:
            exception: when the request buffer is empty

        Returns:
            dictionary: key/value pairs including, but not limited to method, path, query, headers, body, etc.
                or None type if parsing fails
        """
        assert (req_buffer != b''), 'Empty request buffer.'

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
    async def file_type(file_path):
        """
        Return a standard media type / subtype based on file extension
        
        Args:
            file_path (string): file name or full path

        Returns:
            string: media type as registered with the Internet Assigned Numbers Authority (IANA)
        """
        file_ext = file_path.split('.')[-1]
        if (file_ext not in Thimble.media_types):
            return 'text/plain'
        else:
            return Thimble.media_types[file_ext]


    @staticmethod
    async def http_status_line(status_code):
        """
        Given an HTTP status code (e.g. 200, 404, etc.), format the server response status line

        Args:
            status_code (int): the HTTP status code as defined by RFC 7231 Respone Status Codes (ex. 200)
            
        Returns:
            string: HTTP status line with protocol version, numeric status code, and corresponding status text
        """
        if (status_code == None or status_code not in Thimble.http_status_message):
            status_code = 500
            
        return f'HTTP/1.1 {Thimble.http_status_message[status_code]}\r\n'


    @staticmethod
    async def http_headers(content_length=0, content_type='text/plain'):
        """
        Generate appropriate HTTP response headers based on content properties
        
        Args:
            content_length (int): length of body, used for Content-Length header
            content_type (string): media-type of body, used for Content-Type header

        Returns:
            string: HTTP headers separated by \r\n
        """
        headers = 'Connection: close\r\n'
        headers += f'Content-Length: {content_length}\r\n'
        headers += f'Content-Type: {content_type}\r\n'
        headers += f'Server: {Thimble.server_name}\r\n'
        headers += '\r\n'  # blank line signifies end of headers

        return headers


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
        Given a URL path and list of zero or more HTTP methods, add the decorated function to the route table.

        Args:
            url_path (string): path portion of a URL (ex. '/path/to/thing') that will trigger a call to the function
            methods (list): a list of any HTTP methods (eg. ['GET', 'PUT']) that are used to trigger the call

        Returns:
            object: wrapper function
        """

        def add_route(func):
            for method in methods:
                self.routes[method.upper() + url_path] = func  # Methods are uppercase (see RFC 9110)

        return add_route


    def resolve_route(self, route_pattern):
        """
        Given a route pattern (METHOD + url_path), look up the corresponding function.
        
        Args:
            route_pattern (string): An uppercase HTTP method concatenated with a URL path wich may contain regex (ex: GET/gpio/([0-9+])$)

        Returns:
            object: reference to function (for non-regex URLs) or tuple with function and regex capture (for regex URLs)
        """
        result = None
        if (route_pattern in self.routes):  # pattern is a fixed string, like: 'GET/gpio/2'
            result = self.routes[route_pattern]
        else:  # pattern contains regex, like 'GET/gpio/([0-9]+)'
            for key in self.routes.keys():
                regex_match = match(key, route_pattern)
                if (regex_match):
                    func = self.routes[key]
                    wildcard_value = regex_match.group(1)
                    result = func, wildcard_value

        return result


    @staticmethod
    async def send_function_results(func, req, url_wildcard, writer):
        """
        Execute the given function with the HTTP reqest parameters as an argument and send the results as an HTTP reply
        
        Args:
            func (object): reference to the function to be executed or a tuple of function and URL wildcard
            req (dictionary): HTTP request parameters
            url_wildcard (various types): regex-matched portion of the url_path (or None for non-regex routes)
            writer (object): the uasyncio Stream object to which the results should be sent

        Returns:
            nothing
        """
        try:
            if (Thimble.is_async(func) == True):  # await the async function
                if (url_wildcard != None):
                    func_result = await func(req, url_wildcard)
                else:
                    func_result = await func(req)
            else:  # no awaiting required for non-async
                if (url_wildcard != None):
                    func_result = func(req, url_wildcard)
                else:
                    func_result = func(req)

        except Exception as ex:
            print(f'Function call failed: {ex}')
            writer.write(await Thimble.http_status_line(500))
            writer.write(await Thimble.http_headers())
            writer.write('Function call failed\r\n')

        else:
            if (isinstance(func_result, tuple) and len(func_result) == 3):
                body, status_code, content_type = func_result
            elif (isinstance(func_result, tuple) and len(func_result) == 2):
                body, status_code = func_result
                content_type = 'text/plain'
            else:
                body = func_result
                status_code = 200
                content_type = 'text/plain'

            if (not isinstance(body, str)):
                body = str(body)
            writer.write(await Thimble.http_status_line(status_code))
            writer.write(await Thimble.http_headers(content_length=len(body), content_type=content_type))
            await writer.drain()
            writer.write(body)
            await writer.drain()


    @staticmethod
    async def file_size(file_path):
        """
        Given a path to a file, return the file's size or None if there's an exception when checking.
        
        Args:
            file_path (string): a fully-qualified path to the location of the file

        Returns:
            file size in bytes or None if there was a problem obtaining the size (e.g. file does not exist)
        """

        try:
            size = stat(file_path)[6]
        except Exception as ex:
            print(f'Error reading properties of {file_path}: {ex}')
            size = None

        return size


    @staticmethod
    def read_file_chunk(file):
        """
        Given a file handle, read the file in small chunks to avoid large buffer requirements.

        Args:
            file (object): the file handle returned by open()

        Returns:
            bytes: a chunk of the file until the file ends, then nothing
        """
        while True:
            chunk = file.read(64)  # small chunks to avoid out of memory errors
            if chunk:
                yield chunk
            else: # empty chunk means end of the file
                return


    @staticmethod
    async def send_file_contents(file_path, writer):
        """
        Given a file path and an output stream, send HTTP status, headers, and file contents as body
        
        Args:
            file_path (string): fully-qualified path to file
            writer (object): the uasyncio Stream object to which the file should be sent

        Returns:
            nothing
        """
        file_size = await Thimble.file_size(file_path)
        file_type = await Thimble.file_type(file_path)
        if (file_size == None):  # None means there was an error, most likely the file doesn't exist
            writer.write(await Thimble.http_status_line(404))
            writer.write(await Thimble.http_headers())
            writer.write('File not found\r\n')
        else:
            writer.write(await Thimble.http_status_line(200))
            writer.write(await Thimble.http_headers(content_length=file_size, content_type=file_type))
            with open(file_path, 'rb') as file:
                for chunk in Thimble.read_file_chunk(file):
                    writer.write(chunk)
                    await writer.drain()  # drain immediately after write to avoid memory allocation errors


    async def on_connect(self, reader, writer):
        """
        Connection handler for new client requests.
        
        Args:
            reader (stream): input received from the client
            writer (stream): output to be sent to the client

        Returns:
            nothing
        """
        client_ip = writer.get_extra_info('peername')[0]
        if (self.debug): print(f'Connection from client: {client_ip}')

        try:
            req_buffer = await reader.read(self.req_buffer_size)
            req = await Thimble.parse_http_request(req_buffer)
            if (self.debug): print(f'Request: {req}')
        except Exception as ex:
            print(f'Unable to parse request: {ex}')
            writer.write(await Thimble.http_status_line(400))
            writer.write(await Thimble.http_headers())
            writer.write('Bad request\r\n')
        else:
            route_value = self.resolve_route(req['method'] + req['path'])
            if (isinstance(route_value, tuple)): # a function and URL wildcard value were returned
                await Thimble.send_function_results(route_value[0], req, route_value[1], writer)
            elif (route_value != None):  # just a function was returned
                await Thimble.send_function_results(route_value, req, None, writer)
            else:  # nothing returned, try delivering static content instead
                file_path = self.static_folder + req['path']
                if (file_path.endswith('/')):
                    file_path = f'{file_path}/{self.directory_index}'  # requests for '/path/to' become '/path/to/index.html'
                await Thimble.send_file_contents(file_path, writer)
            
        await writer.drain()
        writer.close()
        await writer.wait_closed()
        reader.close()
        await reader.wait_closed()
        if (self.debug): print(f'Connection closed for {client_ip}')


    def run(self, host='0.0.0.0', port=80, loop=None, debug=False):
        """
        Start an asynchronous listener for HTTP requests.
        
        Args:
            host (string): the IP address of the interface on which to listen
            port (int): the TCP port on which to listen
            loop (object): a uasyncio loop that the server should insert itself into
            debug (boolean): a flag to indicate verbose logging is desired

        Returns:
            object: the same loop object given as a parameter or a new one if no existing loop was passed
        """
        self.debug = debug
        print(f'Listening on {host}:{port}')

        if (loop == None):
            loop = get_event_loop()
            server = start_server(self.on_connect, host, port, 5)
            loop.create_task(server)
            loop.run_forever()
        else:
            server = start_server(self.on_connect, host, port, 5)
            loop.create_task(server)

        return loop


