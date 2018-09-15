## Import Python Modules ##
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_assets import Bundle, Environment
from flask_login import LoginManager
from flask_login import login_user, logout_user, current_user, login_required
from flask_oauthlib.client import OAuth, OAuthException
from datetime import datetime
import sqlite3
import re
import json
import libgravatar
import sys
import asyncio

import LocalSettings
import OAuthSettings

app = Flask(__name__)
app.secret_key = LocalSettings.crypt_secret_key
oauth = OAuth(app)

FACEBOOK_APP_ID = OAuthSettings.facebook_app_id
FACEBOOK_APP_SECRET = OAuthSettings.facebook_app_secret

#facebook = oauth.remote_app(
#    'facebook',
#    consumer_key=FACEBOOK_APP_ID,
#    consumer_secret=FACEBOOK_APP_SECRET,
#    request_token_params={'scope': 'email'},
#    base_url='https://graph.facebook.com',
#    request_token_url=None,
#    access_token_url='/oauth/access_token',
#    access_token_method='GET',
#    authorize_url='https://www.facebook.com/dialog/oauth'
#)

try:
    flask_port_set = int(sys.argv[1])
    print(' * 강제 포트 설정 지정됨 : {}'.format(flask_port_set))
except:
    flask_port_set = LocalSettings.flask_host_port

conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
curs = conn.cursor()


try:
    curs.execute('select * from peti_data_tb limit 1')
except:
    DATABASE_QUERY = open('tables/initial.sql', encoding='utf-8').read()
    curs.executescript(DATABASE_QUERY)
    conn.commit


## LOAD CONVERSTATIONS ##
CONVERSTATIONS_NATIVE = open('dic.json', encoding='utf-8').read()
CONVERSTATIONS_DICT = json.loads(CONVERSTATIONS_NATIVE)

## Assets Bundling ##
bundles = {
    'main_js' : Bundle(
        'js/bootstrap.min.js',
        output = 'gen/main.js'
    ),

    'main_css' : Bundle(
        'css/minty.css',
        'css/custom.css',
        output = 'gen/main.css'
    )
}

assets = Environment(app)
assets.register(bundles)

class parser():
    def anti_injection(content):
        content = content.replace('"', '""')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')


@app.route('/', methods=['GET', 'POST'])
def flask_main():
    body_content = ''
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)


@app.route('/a/', methods=['GET', 'POST'])
def flask_a():
    body_content = ''
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/a/<article_id>/', methods=['GET', 'POST'])
def flask_a_article_id():
    body_content = ''
    template = open('templates/a.html', encoding='utf-8').read()
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/a/write/', methods=['GET', 'POST'])
def flask_a_write():
    body_content = ''
    template = open('templates/a_write.html', encoding='utf-8').read()
    if request.method = 'POST':
        #content
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/a/<article_id>/delete/', methods=['GET', 'POST'])
def flask_a_article_id_delete():
    body_content = ''
    template = open('templates/a_delete.html', encoding='utf-8').read()
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)


@app.route('/img/<assets>/')
def serve_pictures(assets):
    return static_file(assets, root='views/img')
@app.errorhandler(404)
def error_404(self):
    body_content = '<h1>Oops!</h1><h2>404 NOT FOUND</h2><p>존재하지 않는 페이지입니다.</p>'
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

app.run(LocalSettings.flask_host, flask_port_set, debug = True)
