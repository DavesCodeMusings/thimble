from asyncio import get_event_loop, start_server
from os import stat
from re import search

class Thimble:
    """
    A tiny web framework in the spirit of Flask, scaled down to run on microcontrollers
    """
    def __init__(self, default_content_type='application/octet-stream', req_buffer_size=1024):
        self.routes = {}  # Dictionary to map method and URL path combinations to functions
        self.default_content_type = default_content_type
        self.req_buffer_size = req_buffer_size
        self.static_folder = '/static'
        self.directory_index = 'index.html'
        self.error_text = {
            400: "400: Bad Request",
            404: "404: Not Found",
            500: "500: Internal Server Error"
        }
        self.media_types = {
            'css': 'text/css',
            'html': 'text/html',
            'ico': 'image/vnd.microsoft.icon',
            'jpg': 'image/jpeg',
            'js': 'text/javascript',
            'json': 'application/json',
            'otf': 'font/otf',
            'png': 'image/png',
            'svg': 'image/svg+xml',
            'ttf': 'font/ttf',
            'txt': 'text/plain',
            'woff': 'font/woff',
            'woff2': 'font/woff2'
        }

    server_name = 'Thimble (MicroPython)'  # Used in 'Server' response header.

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
            if '=' not in param:  # A key with no value, like: 'red' instead of 'color=red'
                key = param
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
        req_buffer_string = req_buffer.decode('utf8')
        req_buffer_lines = req_buffer_string.split('\r\n')
        del req_buffer_string  # free up for garbage collection

        req['method'], target, req['http_version'] = req_buffer_lines[0].split(
            ' ', 2)  # Example: GET /route/path HTTP/1.1
        if '?' not in target:
            req['path'] = target
        else:  # target can have a query component, so /route/path could be something like /route/path?state=on&timeout=30
            req['path'], query_string = target.split('?', 1)
            req['query'] = Thimble.parse_query_string(query_string)

        req['headers'] = {}
        for i in range(1, len(req_buffer_lines) - 1):
            # Blank line signifies the end of headers.
            if req_buffer_lines[i] == '':
                break
            else:
                name, value = req_buffer_lines[i].split(':', 1)
                req['headers'][name.strip().lower()] = value.strip()

        # Last line is the body (or blank if no body.)
        req['body'] = req_buffer_lines[len(req_buffer_lines) - 1]

        return req

    @staticmethod
    async def http_status_line(status_code):
        """
        Given an HTTP status code (e.g. 200, 404, etc.), format the server response status line

        Args:
            status_code (int): the HTTP status code as defined by RFC 7231 Respone Status Codes (ex. 200)

        Returns:
            string: HTTP status line with protocol version, numeric status code, and corresponding status text
        """
        http_status_message = {
            200: "200 OK",
            302: "302 Found",
            400: "400 Bad Request",
            404: "404 Not Found",
            500: "500 Internal Server Error"
        }

        if status_code is None or status_code not in http_status_message:
            status_code = 500

        return f'HTTP/1.1 {http_status_message[status_code]}\r\n'

    @staticmethod
    async def http_headers(content_length=0, content_type='', content_encoding=''):
        """
        Generate appropriate HTTP response headers based on content properties

        Args:
            content_length (int): length of body, used for Content-Length header
            content_type (string): media-type of body, used for Content-Type header
            content_encoding(string): compression type, used for Content-Encoding header

        Returns:
            string: HTTP headers separated by \r\n
        """
        headers = 'Connection: close\r\n'
        if content_encoding != '':
            headers += f'Content-Encoding: {content_encoding}\r\n'
        headers += f'Content-Length: {content_length}\r\n'
        if content_type != '':
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
        if type(func) == type(Thimble.on_connect):  # noqa: E721
            return True  # It's an async function
        elif type(func) == type(Thimble.run):  # noqa: E721
            return False  # It's a regular function
        else:
            return None  # It's not a function

    async def send_error(self, error_number, writer):
        """
        Given a stream and an HTTP error number, send a friendly text error message.

        Args:
            error_number (integer): HTTP status code
            writer (object): the asyncio Stream object to which the file should be sent

        Returns:
            nothing
        """
        writer.write(await Thimble.http_status_line(error_number))
        error_text = f'{self.error_text[error_number]}\r\n'
        writer.write(await Thimble.http_headers(content_type='text/plain', content_length=len(error_text)))
        writer.write(error_text)
        await writer.drain()

    async def send_function_results(self, func, req, url_wildcard, writer):
        """
        Execute the given function with the HTTP reqest parameters as an argument and send the results as an HTTP reply

        Args:
            func (object): reference to the function to be executed or a tuple of function and URL wildcard
            req (dictionary): HTTP request parameters
            url_wildcard (various types): regex-matched portion of the url_path (or None for non-regex routes)
            writer (object): the asyncio Stream object to which the results should be sent

        Returns:
            nothing
        """
        try:
            if Thimble.is_async(func) is True:  # await the async function
                if url_wildcard is not None:
                    func_result = await func(req, url_wildcard)
                else:
                    func_result = await func(req)
            else:  # no awaiting required for non-async
                if url_wildcard is not None:
                    func_result = func(req, url_wildcard)
                else:
                    func_result = func(req)

        except Exception as ex:
            await self.send_error(500, writer)
            print(f'Function call failed: {ex}')
        else:
            if isinstance(func_result, tuple) and len(func_result) == 3:
                body, status_code, content_type = func_result
            elif isinstance(func_result, tuple) and len(func_result) == 2:
                body, status_code = func_result
                content_type = 'text/plain'
            else:
                body = func_result
                status_code = 200
                content_type = 'text/plain'

            if not isinstance(body, str):
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
        except OSError:
            size = None

        return size

    async def file_type(self, file_path):
        """
        Return a standard media type / subtype based on file extension

        Args:
            file_path (string): file name or full path

        Returns:
            string: media type as registered with the Internet Assigned Numbers Authority (IANA)
        """
        file_ext = file_path.split('.')[-1]
        if file_ext not in self.media_types:
            return self.default_content_type
        else:
            return self.media_types[file_ext]

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
            chunk = file.read(512)  # small chunks to avoid out of memory errors
            if chunk:
                yield chunk
            else:  # empty chunk means end of the file
                return

    async def send_file_contents(self, file_path, req, writer):
        """
        Given a file path and an output stream, send HTTP status, headers, and file contents as body.
        If client accepts gzip encoding, and a file of the same name with a .gzip extension appended
        exists, the gzipped version will be sent. This is not so much for speeding up transfer as it
        for conserving limited flash filesystem space.

        Args:
            file_path (string): fully-qualified path to file
            writer (object): the asyncio Stream object to which the file should be sent

        Returns:
            nothing
        """
        # file_size is also used as an indicator of the file's existence
        file_gzip_size = await Thimble.file_size(file_path + '.gzip')
        file_size = await Thimble.file_size(file_path)
        file_type = await self.file_type(file_path)

        if file_gzip_size is not None and 'accept-encoding' in req['headers'] and 'gzip' in req['headers']['accept-encoding'].lower():
            writer.write(await Thimble.http_status_line(200))
            writer.write(await Thimble.http_headers(content_length=file_gzip_size, content_type=file_type, content_encoding='gzip'))
            with open(file_path + '.gzip', 'rb') as file:
                for chunk in Thimble.read_file_chunk(file):
                    writer.write(chunk)
                    await writer.drain()  # drain immediately after write to avoid memory allocation errors
        elif file_size is not None:  # a non-compressed file was found
            writer.write(await Thimble.http_status_line(200))
            writer.write(await Thimble.http_headers(content_length=file_size, content_type=file_type))
            with open(file_path, 'rb') as file:
                for chunk in Thimble.read_file_chunk(file):
                    writer.write(chunk)
                    await writer.drain()
        else:  # no file was found
            await self.send_error(404, writer)
            print(f'Error reading file: {file_path}')

    def route(self, url_path, methods=['GET']):
        """
        Given a URL path and list of zero or more HTTP methods, add the decorated function to the route table.

        Args:
            url_path (string): path portion of a URL (ex. '/path/to/thing') that will trigger a call to the function
            methods (list): a list of any HTTP methods (eg. ['GET', 'PUT']) that are used to trigger the call

        Returns:
            object: wrapper function
        """
        regex_macros = {
            '<digit>': '([0-9])',
            '<float>': '([-+]?[0-9]*\.?[0-9]+)',
            '<int>': '([0-9]+)',
            '<string>': '(.*)'
        }

        regex_match = search('(<.*>)', url_path)
        if regex_match:
            url_path = url_path.replace(regex_match.group(
                1), regex_macros[regex_match.group(1)])

        def add_route(func):
            for method in methods:
                # Methods are uppercase (see RFC 9110)
                self.routes[method.upper() + url_path] = func

        return add_route

    def resolve_route(self, route_candidate):
        """
        Given a route pattern (METHOD + url_path), look up the corresponding function.

        Args:
            route_candidate (string): An uppercase HTTP method concatenated with a URL path wich may contain regex (ex: GET/gpio/([0-9+])$)

        Returns:
            object: reference to function (for non-regex URLs) or tuple with function and regex capture (for regex URLs)
        """
        result = None
        if self.debug:
            print("Looking for a route matching:", route_candidate)
        if route_candidate in self.routes:  # pattern is a non-regex string, like: 'GET/gpio/2'
            if self.debug:
                print("Route table had an exact match. We're done!")
            result = self.routes[route_candidate]
        else:  # pattern may contain regex, like 'GET/gpio/([0-9]+)'
            if self.debug:
                print("No exact match in route table. Looking for regex matches...")
            for stored_route in self.routes.keys():
                if self.debug:
                    print("Examining this route table entry for potential match:", stored_route)
                regex_match = search("^" + stored_route + "$", route_candidate)
                if regex_match:
                    if self.debug:
                        print("Found a regex match with:", stored_route)
                    func = self.routes[stored_route]
                    wildcard_value = regex_match.group(1)
                    if self.debug:
                        print(f'Extracted wildcard value: {wildcard_value}')
                    result = func, wildcard_value
                else:
                    if self.debug:
                        print("No match.")

        return result

    async def on_connect(self, reader, writer):
        """
        Connection handler for new client requests.

        Args:
            reader (stream): input received from the client
            writer (stream): output to be sent to the client

        Returns:
            nothing
        """
        remote_addr = writer.get_extra_info('peername')[0]
        if self.debug:
            print(f'Connection from client: {remote_addr}')

        try:
            req_buffer = await reader.read(self.req_buffer_size)
            req = await Thimble.parse_http_request(req_buffer)
        except Exception as ex:
            await self.send_error(400, writer)
            print(f'Unable to parse request: {ex}')
        else:
            req['remote_addr'] = remote_addr
            if self.debug:
                print(f'Request: {req}')
            route_value = self.resolve_route(req['method'] + req['path'])
            if isinstance(route_value, tuple):  # a function and URL wildcard value were returned
                await self.send_function_results(route_value[0], req, route_value[1], writer)
            elif route_value is not None:  # just a function was returned
                await self.send_function_results(route_value, req, None, writer)
            else:  # nothing returned, try delivering static content instead
                file_path = self.static_folder + req['path']
                if file_path.endswith('/'):  # '/path/to/' becomes '/path/to/index.html'
                    file_path = file_path + self.directory_index
                await self.send_file_contents(file_path, req, writer)

        await writer.drain()
        writer.close()
        await writer.wait_closed()
        reader.close()
        await reader.wait_closed()
        if self.debug:
            print(f'Connection closed for {remote_addr}')

    def run(self, host='0.0.0.0', port=80, loop=None, debug=False):
        """
        Start an asynchronous listener for HTTP requests.

        Args:
            host (string): the IP address of the interface on which to listen
            port (int): the TCP port on which to listen
            loop (object): the asyncio loop that the server should insert itself into
            debug (boolean): a flag to indicate verbose logging is desired

        Returns:
            object: the same loop object given as a parameter or a new one if no existing loop was passed
        """
        self.debug = debug
        print(f'Listening on {host}:{port}')

        if loop is None:
            loop = get_event_loop()
            server = start_server(self.on_connect, host, port, 5)
            loop.create_task(server)
            loop.run_forever()
        else:
            server = start_server(self.on_connect, host, port, 5)
            loop.create_task(server)

        return loop
    
