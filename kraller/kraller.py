"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from flask import Flask

app = Flask(__name__)


@app.route('/')
def index():
    return 'Hello from ACM@CWRU'


if __name__ == '__main__':
    app.run()
