## Import Python Modules ##
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
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

class parser:
    def anti_injection(content):
        content = content.replace('"', '""')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        return content

class sqlite3_control:
    def select(query):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.execute(query)
        result = curs.fetchall()
        conn.close()
        return result

    def commit(query):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.execute(query)
        conn.commit()
        conn.close()

    def executescript(query):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.executescript(query)
        conn.commit()
        conn.close()

### Create Database Table ###
try:
    sqlite3_control.select('select * from peti_data_tb limit 1')
except:
    database_query = open('tables/initial.sql', encoding='utf-8').read()
    sqlite3_control.executescript(database_query)
### Create End ###

### Main Route ###
@app.route('/', methods=['GET', 'POST'])
def flask_main():
    body_content = ''
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

### Account Route ###
@app.route('/login/', methods=['GET', 'POST'])
def flask_login():
    body_content = ''
    template = open('templates/login.html', encoding='utf-8').read()
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/register/', methods=['GET', 'POST'])
def flask_register():
    body_content = ''
    template = open('templates/login.html', encoding='utf-8').read()
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)


### Petition Route ###
@app.route('/a/', methods=['GET', 'POST'])
def flask_a():
    body_content = ''
    
    ### Index Database ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_status != 404')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>새로운 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">Column heading</th></tr></thead><tbody>'
    for i in range(len(peti_data)):
        body_content += '<tr><th scope="row">{}</th><td><a href="/a/{}/">{}</a></td></tr>'.format(peti_data[i][0], peti_data[i][0], peti_data[i][1])
    body_content += '</tbody></table>'
    body_content += '<button onclick="window.location.href=\'write\'" class="btn btn-primary" value="publish">청원 등록</button>'
    ### Render End ###
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/a/<article_id>/', methods=['GET', 'POST'])
def flask_a_article_id(article_id):
    body_content = ''
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(article_id))
    template = open('templates/a.html', encoding='utf-8').read()

    ### Index React Content ###
    react_data = sqlite3_control.select('select * from peti_react_tb where peti_id = {}'.format(article_id))
    ### Index End ###

    if peti_data[0][3] == 404:
        abort(404)
    ### Render React ###
    template_react = """
            <div class="container">
                <h5>%_article_react_author_display_name_%</h5>
                <p>%_article_react_body_content_%</p>
            </div>
            """
    react_body_content = ''
    for i in range(len(react_data)):
        react_render_object = template_react
        react_render_object = react_render_object.replace('%_article_react_author_display_name_%', str(react_data[i][2]))
        react_render_object = react_render_object.replace('%_article_react_body_content_%', react_data[i][3])
        react_body_content += react_render_object
    ### Render End ###

    ### Render Template ###
    template = template.replace('%_article_display_name_%', peti_data[0][1])
    template = template.replace('%_article_publish_date_%', peti_data[0][2])
    template = template.replace('%_article_author_display_name_%', peti_data[0][4])
    template = template.replace('%_article_body_content_%', peti_data[0][5])
    template = template.replace('%_article_react_count_%', str(len(react_data)))
    template = template.replace('%_article_reacts_%', react_body_content)
    body_content += template
    ### Render End ###

    if request.method == 'POST':

        ### Collect React Data ###
        peti_id = article_id
        # author_id = 
        author_id = 0
        content = parser.anti_injection(request.form['react_content'])
        ### Collect End ###

        ### Insert Data into Database ###
        sqlite3_query = 'insert into peti_react_tb (peti_id, author_id, content) values({}, {}, "{}")'.format(
            peti_id,
            author_id,
            content
        )
        sqlite3_control.commit(sqlite3_query)
        ### Insert End ###
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

@app.route('/a/write/', methods=['GET', 'POST'])
def flask_a_write():
    body_content = ''
    template = open('templates/a_write.html', encoding='utf-8').read()
    
    ### Template Rendering ###
    template = template.replace('%_sns_login_status_%', '비활성화 됨')
    ### Rendering End ###

    if request.method == 'POST':
        ### Get POST Data ###
        peti_display_name =  parser.anti_injection(request.form['peti_display_name'])
        peti_publish_date = datetime.today()
        peti_author_display_name = parser.anti_injection(request.form['peti_author_display_name'])
        peti_body_content = parser.anti_injection(request.form['peti_body_content'])
        ### Get End ###

        ### Insert Data into Database ###
        sqlite3_query = 'insert into peti_data_tb (peti_display_name, peti_publish_date, peti_status, peti_author_id, peti_body_content) values("{}", "{}", 0, "{}", "{}")'.format(
            peti_display_name,
            peti_publish_date,
            peti_author_display_name,
            peti_body_content
        )
        sqlite3_control.commit(sqlite3_query)
        ### Insert End ###

        return redirect('/a/')
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)
#### To-Do ####
"""
 * author_id에 고유 코드 기록 (현재: 그냥 유저가 입력한 정보 그대로 insert)
"""
#### To-Do End ####


@app.route('/a/<article_id>/delete/', methods=['GET', 'POST'])
def flask_a_article_id_delete(article_id):
    body_content = ''
    template = open('templates/a_delete.html', encoding='utf-8').read()
    body_content += template
    if request.method == 'POST':
        sqlite3_control.commit('update peti_data_tb set peti_status = 404 where peti_id = {}'.format(article_id))
        return redirect('/a/')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

### Administrator Menu Route ###
@app.route('/admin/')
def flask_admin():
    body_content = ''
    return render_template('index.html')

### Server Log Route ###
@app.route('/log/')
def flask_log():
    body_content = ''
    return render_template('index.html')

### Assets Route ###
@app.route('/img/<assets>/')
def serve_pictures(assets):
    return static_file(assets, root='views/img')

### Error Handler ###
@app.errorhandler(404)
def error_404(self):
    body_content = '<h1>Oops!</h1><h2>404 NOT FOUND</h2><p>존재하지 않는 페이지입니다.</p>'
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content)

app.run(LocalSettings.flask_host, flask_port_set, debug = True)
