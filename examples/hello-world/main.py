# Sample hello app using Thimble.
# (Assumes network connection is already configured.)

from thimble import Thimble

app = Thimble()

@app.route('/hello')
def hello(req):
    return 'Hello!'

@app.route('/hello/world')
def hello_world(req):
    return 'Hello World!'

@app.route('/hello/cleveland')
def hello_cleveland(req):
    return 'Hello Cleveland!'

app.run(debug=True)  # Listen on 0.0.0.0:80 by default.
