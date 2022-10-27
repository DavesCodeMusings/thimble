# This test script simulates client requests. Here's how to use it:
#
# On the microcontroller
# 1. Copy thimble.py and mock_api.py to the flash filesytem
# 2. Supply a boot.py that will connect to wifi
# 3. Run mock_api.py
#
# On the client machine
# 1. Set the environment variable TESTED_HOST to the IP of the microcontroller
# 2. Run this file (e.g. python3 test_api.py)
# 3. Note the results

import unittest
from os import environ
import requests
from json import loads as parse


class TestThimble(unittest.TestCase):
    TESTED_HOST = '127.0.0.1'

    def test_static_text_file(self):
      """ Fetching static file: /testing.txt """
      url = f'http://{TestThimble.TESTED_HOST}/testing.txt'
      response = requests.get(url)
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.headers['Content-Type'], 'text/plain')
      self.assertEqual(response.text, 'Testing 1 2 3')

    def test_static_text_file(self):
      """ Fetching non-existent file: /bogus.txt """
      url = f'http://{TestThimble.TESTED_HOST}/bogus.txt'
      response = requests.get(url)
      self.assertEqual(response.status_code, 404)

    def test_index_html(self):
      """ Fetching static file: /index.html """
      url = f'http://{TestThimble.TESTED_HOST}/index.html'
      response = requests.get(url)
      self.assertEqual(response.status_code, 200)
      self.assertTrue('<title>Testing</title>' in response.text)
      self.assertTrue('<p>Testing 1 2 3</p>' in response.text)

    def test_index_html(self):
      """ Fetching URL root: / """
      url = f'http://{TestThimble.TESTED_HOST}/'
      response = requests.get(url)
      self.assertEqual(response.status_code, 200)
      self.assertTrue('<title>Testing</title>' in response.text)
      self.assertTrue('<p>Testing 1 2 3</p>' in response.text)

    def test_api_get(self):
      """ Requesting API route: GET /get/plain """
      url = f'http://{TestThimble.TESTED_HOST}/get/plain'
      response = requests.get(url)
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.text, 'Testing 1 2 3')
      error_response = requests.put(url)
      self.assertEqual(error_response.status_code, 404)
      error_response = requests.post(url)
      self.assertEqual(error_response.status_code, 404)
      error_response = requests.delete(url)
      self.assertEqual(error_response.status_code, 404)

    def test_api_get(self):
      """ Requesting API route: GET /get/json """
      url = f'http://{TestThimble.TESTED_HOST}/get/json'
      response = requests.get(url)
      self.assertEqual(response.status_code, 200)
      self.assertEqual(response.json()['msg'], 'Testing 1 2 3')
      error_response = requests.put(url)
      self.assertEqual(error_response.status_code, 404)
      error_response = requests.post(url)
      self.assertEqual(error_response.status_code, 404)
      error_response = requests.delete(url)
      self.assertEqual(error_response.status_code, 404)


if (__name__ == '__main__'):
    TestThimble.TESTED_HOST = environ.get('TESTED_HOST', TestThimble.TESTED_HOST)
    print(f'Testing device at IP address: {TestThimble.TESTED_HOST}')
    unittest.main()
