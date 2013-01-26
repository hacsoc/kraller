#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from functools import wraps
import re
from urllib import urlencode

from flask import Flask, abort, render_template, redirect, request, session, url_for
from flask.ext.wtf import Form, BooleanField, TextField, TextAreaField, Required
import requests

from itsdangerous_session import ItsDangerousSessionInterface
from user_management import create_user, add_ssh_key, try_getpwnam

app = Flask(__name__)
app.config.from_envvar('KRALLER_SETTINGS')
app.secret_key = app.config['SECRET_KEY']
app.session_interface = ItsDangerousSessionInterface()

username_re = "[a-z]{3}[0-9]*"
gecos_re = "[A-Za-z0-9.' ]"
ssh_key_re = "[A-Za-z0-9@: .\/=+-]"


def my_cas_endpoint(redirect_to=None):
    if redirect_to is None:
        redirect_to = request.path
    return url_for('login', redirect_to=redirect_to, _external=True)


def cas_login_url():
    return app.config['CAS_SERVER_ENDPOINT'] + 'login?' + urlencode(dict(service=my_cas_endpoint(), renew='true'))


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            return redirect(cas_login_url())
    return decorated


def in_blacklist(name):
    return name in set(map(lambda x: x.strip(), open(app.config['BLACKLIST_FILE']).readlines()))


@app.route('/login')
def login():
    if 'ticket' in request.args and 'redirect_to' in request.args:
        ticket = request.args.get('ticket')
        redirect_to = request.args.get('redirect_to')
        r = requests.get(app.config['CAS_SERVER_ENDPOINT'] + 'validate', params=dict(service=my_cas_endpoint(redirect_to), ticket=ticket), verify=True)
        if not r.status_code == requests.codes.ok:
            # TODO: do we have logging of any sort?
            return abort(500)
        response_lines = r.text.splitlines()
        if len(response_lines) != 2:
            return abort(500)
        (answer, username) = response_lines
        if answer == 'yes':
            # set cookie and redirect
            session['username'] = username
            return redirect(redirect_to)
    return abort(401)


@app.route('/')
def index():
    if 'username' in session:
        username = session['username']
        # the user is logged in
        if not try_getpwnam(username):
            # the user doesn't yet have an account
            form = SignupForm()
            return render_template('signup.tmpl', form=form)
        else:
            # the user already has an account
            return render_template('add_key.tmpl')
    else:
        # the user needs to log in
        return render_template('login.tmpl', cas_server=cas_login_url())


class SignupForm(Form):
    name = TextField('Full Name', [Required()])
    ssh_key = TextAreaField('SSH Key', [Required()])
    accept_tos = BooleanField(None, [Required()])


@app.route('/signup', methods=['POST'])
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
            if in_blacklist(username):
                return 'Error creating user: user blacklisted!'

            if create_user(username, name, '', '', ''):
                return 'Error creating user'

            if add_ssh_key(username, ssh_key):
                return 'Error adding ssh key'

            return 'Success'
    else:
        return render_template('signup.tmpl', form=form)


@app.route('/add_key', methods=['POST'])
@requires_auth
def add_key():
    pass


"""
Don't invoke this directly in production.  This is for development only.
Use a WSGI webserver such as Gunicorn to serve this in production.
"""
if __name__ == '__main__':
    app.run(debug=True)
