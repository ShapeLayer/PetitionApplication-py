## Import Python Modules ##
from flask import Flask, render_template, request, jsonify, redirect
from flask_assets import Bundle, Environment
from flask_login import LoginManager
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
import sqlite3
import re
import json
import libgravatar
import sys
import asyncio

import LocalSettings

app = Flask(__name__)

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
    curs.execute('select * from FORM_DATA_TB limit 1')
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


## Flask Route ##
@app.route('/', methods=['GET', 'POST'])
def main():
    BODY_CONTENT = ''
    BODY_CONTENT += open('templates/index_content.html', encoding='utf-8').read()
    BODY_CONTENT = BODY_CONTENT.replace('| version |', LocalSettings.OFORM_RELEASE)
    curs.execute('select * from FORM_DATA_TB')
    form_data = curs.fetchall()
    for i in range(len(form_data)):
        pass
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

## ================================================================================
@app.route('/peti/')
def petitions():
    BODY_CONTENT = ''
    curs.execute('select * from PETITION_DATA_TB')
    result = curs.fetchall()
    BODY_CONTENT += '<h1>새로운 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">Column heading</th></tr></thead><tbody>'
    for i in range(len(result)):
        BODY_CONTENT += '<tr><th scope="row">{}</th><td><a href="/peti/a/{}">{}</a></td></tr>'.format(result[i][0], result[i][0], result[i][1])
    BODY_CONTENT += '</tbody></table>'
    BODY_CONTENT += '<button onclick="window.location.href=\'write\'" class="btn btn-primary" value="publish">청원 등록</button>'
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

@app.route('/peti/a/<form_id>/')
def peti_a(form_id):
    if form_id == '':
        return 404
    BODY_CONTENT = ''
    print(form_id)
    try:
        curs.execute('select * from PETITION_DATA_TB where form_id = {}'.format(form_id))
        result = curs.fetchall()
    except:
        return 404
    form_display_name = result[0][1]
    form_publish_date = result[0][2]
    form_author = result[0][4]
    form_body_content = result[0][5]
    BODY_CONTENT += open('templates/peti_viewer.html').read()
    
    BODY_CONTENT = BODY_CONTENT.replace(' form_display_name ', form_display_name)
    BODY_CONTENT = BODY_CONTENT.replace(' form_publish_date ', form_publish_date)
    BODY_CONTENT = BODY_CONTENT.replace(' form_author ', form_author)
    BODY_CONTENT = BODY_CONTENT.replace(' form_body_content ', form_body_content)
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)


@app.route('/peti/write/', methods=['GET', 'POST'])
def petitions_write():
    BODY_CONTENT = ''
    if request.method == 'POST':
        form_display_name = request.form['form_display_name']
        form_author_name = request.form['form_author_name']
        form_body_content = request.form['form_body_content']
        form_body_content = form_body_content.replace('"', '\\"')
        form_enabled = 1
        form_author = form_author_name
        form_publish_date = datetime.today()
        curs.execute('insert into PETITION_DATA_TB (form_display_name, form_publish_date, form_enabled, form_author, form_body_content) values("{}", "{}", {}, "{}", "{}")'.format(
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
        return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

## ================================================================================
@app.route('/articles/', methods=['GET', 'POST'])
def articles():
    return 0

@app.route('/articles/write/', methods=['GET', 'POST'])
def articles_write():
    BODY_CONTENT = ''
    if request.method == 'POST':
        form_display_name = request.form['form_display_name']
        form_notice_level = request.form['form_notice_level']
        form_body_content = request.form['form_body_content']
        if request.form['submit'] == 'publish':
            form_enabled = 1
        elif request.form['submit'] == 'preview':
            form_enabled = 0
        form_publish_date = datetime.today()
        curs.execute('insert into FORM_DATA_TB (form_display_name, form_notice_level, form_publish_date, form_enabled, form_body_content) values("{}", "{}", "{}", {}, "{}")'.format(form_display_name, form_notice_level, form_publish_date, form_enabled, form_body_content))
    else:
        BODY_CONTENT += CONVERSTATIONS_DICT['articles_write']
        return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

while(1):
    app.run(LocalSettings.FLASK_HOST, FLASK_PORT_SET, debug = True)