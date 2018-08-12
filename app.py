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


## Global User Settings ##
class User:
    def __init__(self, account_id, account_pw_hash=None,
                 authenticated=False):
        self.account_id = account_id
        self.authenticated = authenticated

    def __repr__(self):
        r = {
            'account_id': self.account_id,
            'authenticated': self.authenticated,
        }
        return str(r)

    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

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



## Member Import with File ##
def import_members_file(target):
    with open(target, 'r', encoding = 'utf-8') as data:
        lines = data.readlines()
    array = [[0 for cols in range(2)]for rows in range(len(lines))]
    for i in range(len(lines)):
        try:
            class_data, name_data = lines[i].split()
        except:
            return [500, i]
        try:
            class_data = int(class_data)
        except:
            return [501, i]
        if len(str(class_data)) != 5:
            return [502, i]
        array[i][0] = class_data
        array[i][1] = name_data
    return array

def import_members_insert(target):
    MEMBER_LIST = import_members_file(target)
    if MEMBER_LIST[0][0] <= 500 and MEMBER_LIST[0][0] >= 502:
        return MEMBER_LIST
    else:
        for i in range(len(MEMBER_LIST)):
            curs.execute('insert into MEMBER_TB (MEMBER_USER_DISPLAY_NAME, MEMBER_USER_CLASS, MEMBER_USER_IS_ENABLED) values ("' + MEMBER_LIST[i][1] + '", ' + str(MEMBER_LIST[i][0]) + ', 1)')
        conn.commit()


## Flask Route ##
### Route: main ###
@app.route('/')
def main():
    BODY_CONTENT = ''

    ## Check Application User Account ##
    try:
        curs.execute('select * from SITE_USER_TB limit 1')
        SITE_USER_IS_EXISTED = True
    except:
        SITE_USER_IS_EXISTED = False

    ## Main Page Container ##
    BODY_CONTENT += CONVERSTATIONS_DICT['MAIN_CONTAINER']
    ## Main Page: Register Suggestion ##
    if SITE_USER_IS_EXISTED:
        BODY_CONTENT = BODY_CONTENT.replace('<content>', '')
    else:
        BODY_CONTENT = BODY_CONTENT.replace('<content>', CONVERSTATIONS_DICT['MAIN_CONTAINER_NO_ACCOUNT'])

    return render_template('index.html', OFORM_APPNAME = LocalSettings.OFORM_APPNAME, OFORM_CONTENT = BODY_CONTENT)

## Application Run ##
if __name__ == "__main__":
    app.run(LocalSettings.FLASK_HOST, FLASK_PORT_SET, debug = True)