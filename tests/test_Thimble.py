import unittest
from uasyncio import get_event_loop
from thimble import Thimble

class TestThimble(unittest.TestCase):
    def __init__(self):
        self.loop = get_event_loop()
        self.app = Thimble()

    def test_parse_query_string(self):
        query_string = 'pet=panda&color=red'
        result = Thimble.parse_query_string(query_string)
        expected = {'pet': 'panda', 'color': 'red'}
        self.assertEqual(expected, result)

    def test_parse_http_request(self):
        async def run_test_parse_http_request():
            req_buffer = b'PUT /gpio/2 HTTP/1.1\r\nHost: 192.168.4.1\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0\r\nAccept: */*\r\nAccept-Language: en-US,en;q=0.5\r\nAccept-Encoding: gzip, deflate\r\nContent-Type: text/plain;charset=UTF-8\r\nContent-Length: 2\r\nOrigin: moz-extension://ae025f41-75b0-4072-9e03-59d403ee21b7\r\nDNT: 1\r\nConnection: keep-alive\r\n\r\non'
            expected = {'path': '/gpio/2', 'headers': {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:105.0) Gecko/20100101 Firefox/105.0', 'Accept': '*/*', 'Accept-Language': 'en-US,en;q=0.5', 'Origin': 'moz-extension://ae025f41-75b0-4072-9e03-59d403ee21b7', 'Content-Length': '2', 'Content-Type': 'text/plain;charset=UTF-8', 'Accept-Encoding': 'gzip, deflate', 'Host': '192.168.4.1', 'DNT': '1', 'Connection': 'keep-alive'}, 'method': 'PUT', 'http_version': 'HTTP/1.1', 'body': 'on'}
            self.assertEqual(await Thimble.parse_http_request(req_buffer), expected)
        self.loop.run_until_complete(run_test_parse_http_request())

    def test_http_status_line(self):
        async def run_test_http_status_line():
            self.assertEqual(await Thimble.http_status_line(0), 'HTTP/1.1 500 Internal Server Error\r\n')
            self.assertEqual(await Thimble.http_status_line(200), 'HTTP/1.1 200 OK\r\n')
            self.assertEqual(await Thimble.http_status_line(400), 'HTTP/1.1 400 Bad Request\r\n')
            self.assertEqual(await Thimble.http_status_line(404), 'HTTP/1.1 404 Not Found\r\n')
            self.assertEqual(await Thimble.http_status_line(500), 'HTTP/1.1 500 Internal Server Error\r\n')
        self.loop.run_until_complete(run_test_http_status_line())

    def test_http_headers(self):
        async def run_test_http_headers():
            expected = 'Connection: close\r\nContent-Length: 0\r\nContent-Type: text/plain\r\nServer: Thimble (MicroPython)\r\n\r\n'
            self.assertEqual(await Thimble.http_headers(), expected)
            expected = 'Connection: close\r\nContent-Length: 99\r\nContent-Type: text/html\r\nServer: Thimble (MicroPython)\r\n\r\n'
            self.assertEqual(await Thimble.http_headers(content_length=99, content_type='text/html'), expected)

        self.loop.run_until_complete(run_test_http_headers())

    def test_file_type(self):
        async def run_test_file_type():
            self.assertEqual(await Thimble.file_type('css'), 'text/css')
            self.assertEqual(await Thimble.file_type('html'), 'text/html')
            self.assertEqual(await Thimble.file_type('js'), 'application/javascript')
            self.assertEqual(await Thimble.file_type('json'), 'application/json')
            self.assertEqual(await Thimble.file_type('svg'), 'image/svg+xml')
        self.loop.run_until_complete(run_test_file_type())

    def test_route(self):
        @self.app.route('/test')
        def get_test(req):
            return req
        self.assertTrue('GET/test' in self.app.routes)
        self.assertTrue(callable(self.app.routes['GET/test']))

    def test_resolve_route(self):
        @self.app.route('/test', methods=['PUT'])
        def put_test(req):
            return req
        func = self.app.resolve_route('PUT/test')
        result = func('Testing')
        self.assertEqual(result, 'Testing')


if __name__ == '__main__':
    unittest.main()


