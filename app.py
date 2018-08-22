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


app = Flask(__name__)
app.debug = True
app.secret_key = LocalSettings.CRYPT_SECRET_KEY
oauth = OAuth(app)

FACEBOOK_APP_ID = LocalSettings.FACEBOOK_APP_ID
FACEBOOK_APP_SECRET = LocalSettings.FACEBOOK_APP_SECRET

facebook = oauth.remote_app(
    'facebook',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'},
    base_url='https://graph.facebook.com',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    access_token_method='GET',
    authorize_url='https://www.facebook.com/dialog/oauth'
)

try:
    FLASK_PORT_SET = int(sys.argv[1])
    print(' * 강제 포트 설정 지정됨.')
except:
    FLASK_PORT_SET = LocalSettings.FLASK_HOST_PORT


## DATABASE CONNECTION ##
conn = sqlite3.connect(LocalSettings.SQLITE3_FILENAME, check_same_thread = False)
curs = conn.cursor()


## DATABASE TABLES CREATE ##
try:
    curs.execute('select * from peti_data_tb limit 1')
except:
    DATABASE_QUERY = open('tables/initial.sql').read()
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

## LOAD NAV BAR ##
def load_nav_bar():
    facebook_session = get_facebook_oauth_token()
    try:
        me = facebook.get('/me')
        FB_ACNT_IMG = '<i class="fab fa-facebook"></i>'
        FB_ACNT_USR_NAME = me.data['name']
        FB_ACNT_CTRL = '<a class="dropdown-item" href="#">LogOut</a>'
    except:
        FB_ACNT_IMG = '<i class="fab fa-facebook"></i>'
        FB_ACNT_USR_NAME = '로그인되지 않음'
        FB_ACNT_CTRL = '<a class="dropdown-item" href="#">LogIn</a>'
    acnt_nav_var = '<ul class="nav navbar-nav ml-auto"><li class="nav-item dropdown"><a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" id="usermenu">{{}}{{}} <span class="caret"></span></a><div class="dropdown-menu" aria-labelledby="usermenu"><a class="dropdown-item" href="#">{{}}</a></div></li></ul>'.format(FB_ACNT_IMG, FB_ACNT_USR_NAME, FB_ACNT_CTRL)
    return acnt_nav_var


## Flask Route ##
@app.route('/', methods=['GET', 'POST'])
def main():
    FB_NAV_VAR = load_nav_bar()
    BODY_CONTENT = ''
    BODY_CONTENT += open('templates/index_content.html', encoding='utf-8').read()
    BODY_CONTENT = BODY_CONTENT.replace('| version |', LocalSettings.OFORM_RELEASE)
    curs.execute('select * from peti_data_tb')
    form_data = curs.fetchall()
    for i in range(len(form_data)):
        pass
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

@app.route('/login', methods=['GET'])
def login():
    callback = url_for(
        'facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True
    )
    return facebook.authorize(callback=callback)

@app.route('/login/authorized')
def facebook_authorized():
    resp = facebook.authorized_response()
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    if isinstance(resp, OAuthException):
        return 'Access denied: %s' % resp.message
    
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    return redirect('/')
    #return 'Logged in as id=%s name=%s redirect=%s' % \
    #    (me.data['id'], me.data['name'], request.args.get('next'))

@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

## ================================================================================
@app.route('/peti/')
def petitions():
    FB_NAV_VAR = load_nav_bar()
    BODY_CONTENT = ''
    curs.execute('select * from peti_data_tb')
    result = curs.fetchall()
    BODY_CONTENT += '<h1>새로운 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">Column heading</th></tr></thead><tbody>'
    for i in range(len(result)):
        BODY_CONTENT += '<tr><th scope="row">{}</th><td><a href="/peti/a/{}">{}</a></td></tr>'.format(result[i][0], result[i][0], result[i][1])
    BODY_CONTENT += '</tbody></table>'
    BODY_CONTENT += '<button onclick="window.location.href=\'write\'" class="btn btn-primary" value="publish">청원 등록</button>'
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

@app.route('/peti/a/<form_id>/')
def peti_a(form_id):
    FB_NAV_VAR = load_nav_bar()
    if form_id == '':
        return 404
    BODY_CONTENT = ''
    try:
        curs.execute('select * from peti_data_tb where form_id = {}'.format(form_id))
        result = curs.fetchall()
    except:
        return 404
    if result[0][3] == 0:
        return '404'
    form_display_name = result[0][1]
    form_publish_date = result[0][2]
    form_author = result[0][4]
    form_body_content = result[0][5]
    BODY_CONTENT += open('templates/peti_viewer.html').read()
    
    BODY_CONTENT = BODY_CONTENT.replace(' form_display_name ', form_display_name)
    BODY_CONTENT = BODY_CONTENT.replace(' form_publish_date ', form_publish_date)
    BODY_CONTENT = BODY_CONTENT.replace(' form_author ', form_author)
    BODY_CONTENT = BODY_CONTENT.replace(' form_body_content ', form_body_content)
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

@app.route('/peti/a/<form_id>/delete/', methods=['GET', 'POST'])
def peti_a_delete(form_id):
    FB_NAV_VAR = load_nav_bar()
    facebook_session = get_facebook_oauth_token()

    ### === return 404
    if form_id == '':
        return '1'
    try:
        curs.execute('select * from peti_data_tb where form_id = {} '.format(form_id))
        result = curs.fetchall()
    except:
        return '2'
    try:
        me = facebook.get('/me')
        facebook_authorized_bool = True
    except:
        facebook_authorized_bool = False
    if facebook_authorized_bool == False:
        return '3'

    ### === body content
    BODY_CONTENT = ''
    if request.method == 'POST':
        secret_key_received = request.form['secret_key']
        print(secret_key_received)
        if secret_key_received != LocalSettings.CRYPT_SECRET_KEY:
            return '4'
        else:
            curs.execute('update peti_data_tb set form_enabled = 0 where form_id = {}'.format(form_id))
            conn.commit()
            BODY_CONTENT = '<h1>완료</h1><p>삭제되었습니다. <a href="/">메인으로 이동합니다.</a></p>'
            return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)
    BODY_CONTENT += open('templates/peti_delete.html', encoding='utf-8').read()
    BODY_CONTENT = BODY_CONTENT.replace('| sns_login_status |', '<i class="fab fa-facebook"></i> 페이스북 로그인됨: ' + me.data['name'])
    BODY_CONTENT = BODY_CONTENT.replace('| form_id |', form_id)
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

@app.route('/peti/write/', methods=['GET', 'POST'])
def petitions_write():
    FB_NAV_VAR = load_nav_bar()
    BODY_CONTENT = ''

    facebook_session = get_facebook_oauth_token()
    try:
        me = facebook.get('/me')
        facebook_authorized_bool = True
    except:
        facebook_authorized_bool = False
    if request.method == 'POST':
        form_display_name = request.form['form_display_name'].replace('"', '""')
        form_author_name = request.form['form_author_name'].replace('"', '""')
        form_body_content = request.form['form_body_content'].replace('"', '""')
        form_display_name = request.form['form_display_name'].replace('<', '&lt;')
        form_author_name = request.form['form_author_name'].replace('<', '&lt;')
        form_body_content = request.form['form_body_content'].replace('<', '&lt;')
        form_display_name = request.form['form_display_name'].replace('>', '&gt;')
        form_author_name = request.form['form_author_name'].replace('>', '&gt;')
        form_body_content = request.form['form_body_content'].replace('>', '&gt;')
        form_enabled = 1
        form_author = form_author_name
        form_publish_date = datetime.today()
        curs.execute('insert into peti_data_tb (form_display_name, form_publish_date, form_enabled, form_author, form_body_content) values("{}", "{}", {}, "{}", "{}")'.format(
            form_display_name, 
            form_publish_date, 
            form_enabled, 
            form_author, 
            form_body_content)
            )
        conn.commit()
        return redirect('/peti')
    else:
        BODY_CONTENT += open('templates/petitions.html', encoding='utf-8').read()
        if facebook_authorized_bool:
            BODY_CONTENT = BODY_CONTENT.replace('| sns_login_status |', '<i class="fab fa-facebook"></i> 페이스북 로그인됨: ' + me.data['name'])
        else:
            BODY_CONTENT = BODY_CONTENT.replace('| sns_login_status |', '<i class="fab fa-facebook"></i> 페이스북 로그인되지 않음. <a href="/login">로그인하기</a>')
        return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

## ================================================================================
@app.errorhandler(404)
def error_404(self):
    FB_NAV_VAR = load_nav_bar()
    BODY_CONTENT = '<h1>Oops!</h1><h2>404 NOT FOUND</h2><p>존재하지 않는 페이지입니다.</p>'
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT, GITHUB_REPO = LocalSettings.GITHUB_REPO, NAV_VAR = FB_NAV_VAR)

while(1):
    app.run(LocalSettings.FLASK_HOST, FLASK_PORT_SET, debug = True)
