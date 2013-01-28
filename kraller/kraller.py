#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Kraller

An application to allow signups for accounts on a server with a key.
"""

from functools import wraps
import logging
import os
import re
from urllib import urlencode

from flask import Flask, abort, render_template, redirect, request, session, url_for, flash, send_from_directory
from flask.ext.wtf import Form, BooleanField, TextField, TextAreaField, Required
import requests

from itsdangerous_session import ItsDangerousSessionInterface
from user_management import create_user, add_ssh_key, try_getpwnam

app = Flask(__name__)
app.config.from_envvar('KRALLER_SETTINGS')
app.session_interface = ItsDangerousSessionInterface()

username_re = "[a-z]{3}[0-9]*"
gecos_re = "[A-Za-z0-9.' ()+-]"
ssh_key_re = "[A-Za-z0-9@: .\/=+-]"

def my_cas_endpoint(redirect_to=None):
    """returns the URL that should be passed to the CAS server under the
    'service' parameter.  It's where the CAS server should redirect the user
    after it has done its job"""

    if redirect_to is None:
        redirect_to = request.path
    return url_for('login', redirect_to=redirect_to, _external=True)


def cas_login_url(redirect_to=None):
    """returns a URL for the CAS server to send the user to.  Once done,
    the CAS server will send the user back to redirect_to."""

    return app.config['CAS_SERVER_ENDPOINT'] + 'login?' + urlencode(dict(service=my_cas_endpoint(redirect_to), renew='true'))


def logged_in_url(url):
    if 'username' in session:
        return url
    else:
        return cas_login_url(url)


def requires_auth(f):
    """decorates a url handler, requiring that the user be authenticated before
    seeing it."""

    @wraps(f)
    def decorated(*args, **kwargs):
        if 'username' in session:
            return f(*args, **kwargs)
        else:
            return redirect(cas_login_url())
    return decorated


def in_blacklist(name):
    return name in map(lambda x: x.strip(), open(app.config['BLACKLIST_FILE']).readlines())


@app.route('/login')
def login():
    if not 'ticket' in request.args and 'redirect_to' in request.args:
        return abort(401)

    ticket = request.args.get('ticket')
    redirect_to = request.args.get('redirect_to')
    r = requests.get(app.config['CAS_SERVER_ENDPOINT'] + 'validate', params=dict(service=my_cas_endpoint(redirect_to), ticket=ticket), verify=True)
    if not r.status_code == requests.codes.ok:
        logging.warning('Got bad response code from CAS validate endpoint')
        return abort(500)

    response_lines = r.text.splitlines()
    if len(response_lines) != 2:
        logging.warning('Got malformed response from CAS validate endpoint')
        return abort(500)

    (answer, username) = response_lines
    if answer == 'yes':
        # set cookie and redirect
        session['username'] = username
        return redirect(redirect_to)


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/')


@app.route('/')
def index():
    return render_template('index.tmpl', signup_url=logged_in_url('/signup'))


class SignupForm(Form):
    name = TextField('Full Name', [Required()])
    phone = TextField('Phone Number (optional)', [])
    ssh_key = TextAreaField('SSH Key', [Required()])
    accept_tos = BooleanField(None, [Required()])


@app.route('/signup', methods=['GET', 'POST'])
@requires_auth
def signup():
    if request.method == 'GET':
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

    username = session['username']
    if try_getpwnam(username):
        flash('You are already registered.')
        return render_template('success.tmpl')

    form = SignupForm()
    if not form.validate_on_submit():
        flash('There was an error submitting the form!')
        return render_template('signup.tmpl', form=form)

    name = form.name.data.strip()
    phone = form.phone.data.strip()
    ssh_key = form.ssh_key.data.strip()

    # before proceeding, check that all fields are sane
    valid = {
        'username': re.match(username_re, username),
        'name' : re.match(gecos_re, name),
        'phone' : re.match(gecos_re, phone),
        'ssh_key': re.match(ssh_key_re, ssh_key)
    }

    if not all(valid.values()):
        if not valid['username']:
            flash("I don't like the look of your username.")
            logging.warning('Username failed validation.  Why is this happening?')

        if not valid['name']:
            flash("I prefer names consisting only of alphanumerics, apostrophes, and periods.")

        if not valid['phone']:
            flash("Your phone number looks weird to me.  Try sticking to the basics.")

        if not valid['ssh_key']:
            flash("Are you sure that's an SSH key? Please check the entry and dial again.")

        return render_template('signup.tmpl', form=form)

    if in_blacklist(username):
        flash('You are blacklisted.')
        logging.warning('Blacklisted user attempted to sign up')
        return render_template('signup.tmpl', form=form)

    if create_user(username, name, '', '', phone):
        flash('There was an error creating a user account for you.')
        logging.warning('Error creating user account')
        return render_template('signup.tmpl', form=form)

    if add_ssh_key(username, ssh_key):
        logging.warning('Error adding ssh key')
        flash('Something went wrong when adding your ssh key.')
        return render_template('signup.tmpl', form=form)

    # Success!
    return render_template('success.tmpl')


@app.route('/add_key', methods=['POST'])
@requires_auth
def add_key():
    pass


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')


"""
Don't invoke this directly in production.  This is for development only.
Use a WSGI webserver such as Gunicorn to serve this in production.
"""
if __name__ == '__main__':
    app.run(debug=True)
