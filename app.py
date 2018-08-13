## Import Python Modules ##
from flask import Flask, render_template, request, jsonify
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
    curs.execute('select * from FORM_DATA_TB')
    form_data = curs.fetchall()
    for i in range(len(form_data)):
        pass
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

## ================================================================================
@app.route('/peti')
def petitions():
    curs.execute('select * from PETITION_DATA_TB')
    result = curs.fetchall()
    return result

@app.route('/peti/a/<form_id>')
def peti_a(form_id):
    if type(form_id) != 'int':
        return 404
    try:
        curs.execute('select * from FORM_DATA_TB where form_id = {}', form_id)
        result = curs.fetchall()
    except:
        return 404
    return result

@app.route('/peti/write', methods=['GET', 'POST'])
def petitions_write():
    BODY_CONTENT = ''
    if request.method == 'POST':
        form_display_name = request.form['form_display_name']
        form_body_content = request.form['form_body_content']
        form_body_content = form_body_content.replace('"', '\\"')
        form_enabled = 1
        form_publish_date = datetime.today()
        curs.execute('insert into PETITION_DATA_TB (form_display_name, form_publish_date, form_enabled, form_body_content) values("{}", "{}", {}, "{}")'.format(form_display_name, form_publish_date, form_enabled, form_body_content))
        conn.commit()
        return 'insert into PETITION_DATA_TB (form_display_name, form_publish_date, form_enabled, form_body_content) values("{}", "{}", {}, "{}")'.format(form_display_name, form_publish_date, form_enabled, form_body_content)
    else:
        BODY_CONTENT += open('templates/petitions.html', encoding='utf-8').read()
        return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

## ================================================================================
@app.route('/articles', methods=['GET', 'POST'])
def articles():
    return 0

@app.route('/articles/write', methods=['GET', 'POST'])
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