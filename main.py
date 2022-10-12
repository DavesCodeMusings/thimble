# Sample hello app using Thimble.
# (Assumes network connection is already configured.)

from thimble import Thimble

app = Thimble()

@app.route('/')
def hello():
    return 'Hello!'

@app.route('/world')
def hello_cleveland():
    return 'Hello World!'

@app.route('/cleveland')
def hello_cleveland():
    return 'Hello Cleveland!'

app.run(debug=True)  # Listen on 0.0.0.0:80 by default.
