"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello from ACM@CWRU'


"""
Don't invoke this directly in production.  This is for development only.
Use a WSGI webserver such as Gunicorn to serve this in production.
"""
if __name__ == '__main__':
    app.run(debug=True)
