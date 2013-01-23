"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from datetime import timedelta
from functools import wraps
from urllib import urlencode

from flask import Flask, abort, render_template, redirect, request, session, url_for
import requests

from itsdangerous_session import ItsDangerousSessionInterface

app = Flask(__name__)
app.secret_key = 'hackme'
app.session_interface = ItsDangerousSessionInterface()
app.permanent_session_lifetime = timedelta(hours=2)

cas_server_endpoint = 'https://login.case.edu/cas/'

def my_cas_endpoint(redirect_to=None):
    if redirect_to is None:
        redirect_to = request.path
    return url_for('login', redirect_to=redirect_to, _external=True)

def requires_auth(f):
    wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            return redirect(cas_server_endpoint + 'login?' + urlencode(dict(service=my_cas_endpoint(), renew='true')))
    return decorated

@app.route('/login')
def login():
    if 'ticket' in request.args and 'redirect_to' in request.args:
        ticket = request.args.get('ticket')
        redirect_to = request.args.get('redirect_to')
        r = requests.get(cas_server_endpoint + 'validate', params=dict(service=my_cas_endpoint(redirect_to), ticket=ticket), verify=True)
        if not r.status_code == requests.codes.ok:
            return abort(500)
        (answer, username) = r.text.split('\n', 1)
        if answer == 'yes':
            #set cookie and redirect
            session['username'] = username
            return redirect(redirect_to)
    return abort(401)

@app.route('/')
@requires_auth
def index():
    return session['username']

"""
Don't invoke this directly in production.  This is for development only.
Use a WSGI webserver such as Gunicorn to serve this in production.
"""
if __name__ == '__main__':
    app.run(debug=True)
