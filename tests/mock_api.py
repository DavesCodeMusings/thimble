# A set of routes and files used for API testing.
# This will create a static directory with files in it as part of setup.
# (boot.py is needed to configure any access point parameters.)
from thimble import Thimble
from os import stat, mkdir
from ujson import dumps as stringify

try:
    stat('/static')
except OSError as ex:
    if (ex.errno == 2):  # Error #2 is ENOENT (file or dir not found)
        mkdir('/static')

try:
    stat('/static/testing.txt')
except OSError as ex:
    if (ex.errno == 2):
        with open('/static/testing.txt', 'w') as file:
            file.write('Testing 1 2 3')

try:
    stat('/static/index.html')
except OSError as ex:
    if (ex.errno == 2):
        with open('/static/index.html', 'w') as file:
            file.write('<!DOCTYPE html>\n')
            file.write('<html>\n')
            file.write('<head>\n')
            file.write('<title>Testing</title>\n')
            file.write('</head>\n')
            file.write('<body>\n')
            file.write('<p>Testing 1 2 3</p>\n')
            file.write('</body>\n')
            file.write('</html>\n')

api = Thimble()


@api.route('/get/plain')
def test_get(req):
    return 'Testing 1 2 3'

@api.route('/get/json')
def test_get(req):
    return stringify({ "msg": "Testing 1 2 3" }), 200, 'application/json'


api.run(debug=True)

