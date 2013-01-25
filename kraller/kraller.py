#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from datetime import timedelta
from functools import wraps
import re
from urllib import urlencode

from flask import Flask, abort, render_template, redirect, request, session, url_for
from flask.ext.wtf import Form, BooleanField, TextField, TextAreaField, Required
import requests

from itsdangerous_session import ItsDangerousSessionInterface
from user_management import create_user, add_ssh_key, try_getpwnam

app = Flask(__name__)
app.secret_key = 'hackme'
app.session_interface = ItsDangerousSessionInterface()
app.permanent_session_lifetime = timedelta(hours=2)

cas_server_endpoint = 'https://login.case.edu/cas/'

username_re = "[a-z]{3}[0-9]*"
gecos_re = "[A-Za-z0-9.' ]"
ssh_key_re = "[A-Za-z0-9/-@=+ ]"

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
            # TODO: do we have logging of any sort?
            return abort(500)
        response_lines = r.text.splitlines()
        if  len(response_lines) != 2:
            return abort(500)
        (answer, username) = response_lines
        if answer == 'yes':
            # set cookie and redirect
            session['username'] = username
            return redirect(redirect_to)
    return abort(401)

class SignupForm(Form):
    name = TextField('Full Name', [Required()])
    ssh_key = TextAreaField('SSH Key', [Required()])
    accept_tos = BooleanField(None, [Required()])

@app.route('/signup', methods=['GET', 'POST'])
@requires_auth
def signup():
    username = session['username']
    if try_getpwnam(username):
        return 'You are already registered.'

    form = SignupForm()
    if form.validate_on_submit():
        name = form.name.data.strip()
        ssh_key = form.ssh_key.data.strip()

        # before proceeding, check that all fields are sane
        if all([
            re.match(username_re, username),
            re.match(gecos_re, name),
            re.match(ssh_key_re, ssh_key)
        ]):
            # TODO: blacklist certain usernames
            if create_user(username, name, '', '', ''):
                # TODO: do something when this fails.  but what?
                pass

            if add_ssh_key(username, ssh_key):
                pass

            return redirect('/signup_success')
    else:
        return render_template('register.tmpl', form=form)

"""
Don't invoke this directly in production.  This is for development only.
Use a WSGI webserver such as Gunicorn to serve this in production.
"""
if __name__ == '__main__':
    app.run(debug=True)
