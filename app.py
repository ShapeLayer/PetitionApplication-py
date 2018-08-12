## Import Python Modules ##
from flask import Flask, render_template, request, jsonify
from flask_assets import Bundle, Environment
from flask_login import LoginManager
from flask_login import login_user, logout_user, current_user, login_required
import sqlite3
import re
import json
import libgravatar
import sys

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
    curs.execute('select * from SITE_USER_TB limit 1')
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
### Route: main ###
@app.route('/', methods=['GET', 'POST'])
def main():
    BODY_CONTENT = ''
    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

@app.route('/articles/write', methods=['GET', 'POST'])
def articles_write():
    BODY_CONTENT = ''
    if request.method == 'POST':
        form_display_name = request.form['form_display_name']
        form_notice_level = request.form['form_notice_level']
        form_body_content = request.form['form_body_content']
    else:
        BODY_CONTENT += CONVERSTATIONS_DICT['articles_write']
        return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)



## Application Run ##
if __name__ == "__main__":
    app.run(LocalSettings.FLASK_HOST, FLASK_PORT_SET, debug = True)