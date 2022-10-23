# Example of using Thimble as an api for an ESP configured as an access point
# (boot.py is needed to configure any access point parameters.)
from thimble import Thimble
from ubinascii import hexlify
from ujson import dumps as stringify

api = Thimble() 

@api.route('/clients')
def clients(req):
    client_list = []
    total_clients = len(wlan.status('stations'))
    i = 0
    for client in wlan.status('stations'):
        mac = hexlify(client[0], '-').decode('utf-8').upper()
        i += 1
        client_list.append(mac)
    print(stringify(client_list))
    
    return stringify(client_list), 200, 'application/json'

api.run(debug=True)
