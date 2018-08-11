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

import installation

app = Flask(__name__)

try:
    FLASK_PORT_SET = int(sys.argv[1])
    print(' * 강제 포트 설정 지정됨.')
except:
    FLASK_PORT_SET = 2500

try:
    import LocalSettings
except:
    print(' * LocalSettings.py를 찾을 수 없습니다. ')
    installation.start(FLASK_PORT_SET)
    import LocalSettings

import ReadLocalSettings



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

    return render_template('index.html', ENTREE_APPNAME = LocalSettings.ENTREE_APPNAME, ENTREE_CONTENT = BODY_CONTENT)
### Route: Login ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST': 
        account_id = request.json['account_id']
        account_pw_hash = request.json['account_pw_hash']
        if account_id not in USERS:
            json_res={'ok': False, 'error': 'Invalid account_id or password'}
        elif not USERS[account_id].can_login(account_pw_hash):
            json_res = {'ok': False, 'error': 'Invalid account_id or password'}
        else:
            json_res={'ok': True, 'msg': 'user <%s> logined' % account_id}
            USERS[account_id].authenticated = True
            login_user(USERS[account_id], remember=True)
        return jsonify(json_res)
    else:
        BODY_CONTENT = CONVERSTATIONS_DICT['LOGIN']
        return render_template('form.html', ENTREE_APPNAME = 'ENTREE - 로그인', ENTREE_CONTENT = BODY_CONTENT)


### Route: Manage ###
@app.route('/manage')
def flask_manage():
    BODY_CONTENT = ''
    
    ## Check Member IS EXISTED ##
    try:
        curs.execute('select * from MEMBER_TB limit 1')
        MEMBER_IS_EXISTED = True
    except:
        MEMBER_IS_EXISTED = False

    ## Check Seat IS EXISTED ##
    try:
        curs.execute('select * from SEAT_LOCATION_TB limit 1')
        SEAT_LOCATION_IS_EXISTED = True
    except:
        SEAT_LOCATION_IS_EXISTED = False

    ## MEMBER_IS_EXISTED ##
    if MEMBER_IS_EXISTED:
        pass
    else:
        BODY_CONTENT += CONVERSTATIONS_DICT['MEMBER_IS_EXISTED_FALSE']

    ## SEAT_LOCATION_IS_EXISTED ##
    if SEAT_LOCATION_IS_EXISTED:
        pass
    else:
        BODY_CONTENT += CONVERSTATIONS_DICT['SEAT_LOCATION_IS_EXISTED_FALSE']

    BODY_CONTENT += CONVERSTATIONS_DICT['MANAGE_MEMBER_TRIGGER_BUTTONS']

    return render_template('index.html', ENTREE_APPNAME = LocalSettings.ENTREE_APPNAME, ENTREE_CONTENT = BODY_CONTENT)

### Route: Settings ###
@app.route('/settings')
def flask_settings():
    return ''

@app.route('/settings/system')
def flask_settings_system():
    BODY_CONTENT = ''
    ENTREE_SETTINGS = ReadLocalSettings.Request_LocalSettings()

    BODY_CONTENT += '<div class="bs-component"><form action="/" accept-charset="utf-8" name="installation" method="post"><fieldset><div class="form-group">'
    for i in range(len(ENTREE_SETTINGS)):
        SETTINGS_NAME = ENTREE_SETTINGS['SETTINGS_'+str(i)]['NAME'].lower()
        BODY_CONTENT += '<div class="form-group"><label for="' + SETTINGS_NAME + '">' + SETTINGS_NAME + '</label><input type="text" class="form-control" name="' + SETTINGS_NAME + '" placeholder="'+ str(ENTREE_SETTINGS['SETTINGS_'+str(i)]['VALUE']) +'"'
        if ENTREE_SETTINGS['SETTINGS_'+str(i)]['EDITABLE']:
            pass
        else:
            BODY_CONTENT += 'id="disabledInput" disabled=""'
        BODY_CONTENT += '>'
        try:
            SETTINGS_DETAIL = ENTREE_SETTINGS['SETTINGS_'+str(i)]['DETAIL']
            BODY_CONTENT += '<small id="' + SETTINGS_NAME + '_help" class="form-text text-muted">' + SETTINGS_DETAIL + '</small>'
        except:
            pass
        BODY_CONTENT += '</div>'

    return render_template('index.html', ENTREE_APPNAME = LocalSettings.ENTREE_APPNAME, ENTREE_CONTENT = BODY_CONTENT)

@app.route('/settings/member')
def flask_settings_member():
    return ''

@app.route('/settings/member/add', methods=['GET', 'POST'])
def flask_settings_member_add():
    BODY_CONTENT = open('templates/member.html', encoding='utf-8').read()
    if request.method == 'POST':
        MEMBER_LIST_NATIVE = request.form['member-data']
        MEMBER_LIST_LIST = MEMBER_LIST_NATIVE.splitlines()
        for i in range(len(MEMBER_LIST_LIST)):
            EXECUTED = True
            try:
                MEMBER_USER_CLASS, MEMBER_USER_DISPLAY_NAME = MEMBER_LIST_LIST[i].split()
            except:
                BODY_CONTENT += '오류: {}열, 학반과 이름을 분리할 수 없습니다.<br />'.format(i+1)
                EXECUTED = False
            if EXECUTED:
                try:
                    MEMBER_USER_CLASS = int(MEMBER_USER_CLASS)
                except:
                    BODY_CONTENT += '오류: {}열, 학반이 정수로 이루어지지 않은 것 같습니다.<br />'.format(i+1)
                    EXECUTED = False
            if EXECUTED and len(str(MEMBER_USER_CLASS)) != 5:
                BODY_CONTENT += '오류: {}열, 학반이 다섯자리 정수로 이루어지지 않은 것 같습니다.<br />'.format(i+1)
                EXECUTED = False
            if EXECUTED:
                BODY_CONTENT += '완료: {}열: {} {}.<br />'.format(i+1, MEMBER_USER_CLASS, MEMBER_USER_DISPLAY_NAME)
                curs.execute('insert into MEMBER_TB (MEMBER_USER_DISPLAY_NAME, MEMBER_USER_CLASS, MEMBER_USER_IS_ENABLED) values ("%s", %d, %d)' % (MEMBER_USER_DISPLAY_NAME, MEMBER_USER_CLASS, 1))
        conn.commit()
    return render_template('index.html', ENTREE_APPNAME = LocalSettings.ENTREE_APPNAME, ENTREE_CONTENT = BODY_CONTENT)


## Application Run ##
if __name__ == "__main__":
    app.run(LocalSettings.FLASK_HOST, LocalSettings.FLASK_HOST_PORT, debug = True)