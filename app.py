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
import base64
import hashlib
import random
from Crypto.Cipher import AES

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

BS = 16
pad = (lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS).encode())
unpad = (lambda s: s[:-ord(s[len(s)-1:])])


class AESCipher(object):
    def __init__(self, key):
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, target):
        target = target.encode()
        raw = pad(target)
        cipher = AES.new(self.key, AES.MODE_CBC, self.__iv())
        enc = cipher.encrypt(raw)
        return base64.b64encode(enc).decode('utf-8')

    def __iv(self):
        return chr(0) * 16

class user_profile_data:
    def load_nav_bar():
        template = """
        <ul class="nav navbar-nav ml-auto">
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" id="download"><img src="%_user_display_profile_img_%" width="10px" height="10px"> %_user_display_name_% <span class="caret"></span></a>
                <div class="dropdown-menu" aria-labelledby="download">
                    %_user_profile_menu_content_%
                    <a class="dropdown-item" href="#"></a>
                </div>
            </li>
        </ul>
        """
        user_profile_menu_content = ''
        if 'now_login' in session:
            user_data = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(session['now_login']))
            user_auth_group = sqlite3_control.select('select * from user_administrator_list_tb where account_id = {}'.format(session['now_login']))
            user_auth = sqlite3_control.select('select * from user_group_acl where user_group = "{}"'.format(user_auth_group[0][1]))
            template = template.replace('%_user_display_name_%', user_data[0][3])
            if user_auth[0][2] == 1:
                user_profile_menu_content += """
                <a class="dropdown-item" href="/admin/">관리자 메뉴</a>
                """
            user_profile_menu_content += """
            <a class="dropdown-item" href="/logout/">로그아웃</a>
            """
        else:
            template = template.replace('%_user_display_name_%', '비로그인 상태')
            user_profile_menu_content += """
            <a class="dropdown-item" href="/login/">로그인</a>
            """
        template = template.replace('%_user_profile_menu_content_%', user_profile_menu_content)
        return template

### Create Database Table ###
try:
    sqlite3_control.select('select * from peti_data_tb limit 1')
except:
    database_query = open('tables/tables.sql', encoding='utf-8').read()
    sqlite3_control.executescript(database_query)
    ### Initialize Database ###
    database_query = open('tables/initialize.sql', encoding='utf-8').read()
    sqlite3_control.executescript(database_query)
    ### Initialize End ###
### Create End ###

### Main Route ###
@app.route('/', methods=['GET', 'POST'])
def flask_main():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

### Account Route ###
@app.route('/login/', methods=['GET', 'POST'])
def flask_login():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()
    
    ### Render Template ###
    template = open('templates/account.html', encoding='utf-8').read()
    form_body_content = '<div class="form-group"><div class="form-group"><input type="text" class="form-control form-login-object" name="account_id" placeholder="계정명" required></div><div class="form-group"><input type="password" class="form-control form-login-object" name="account_password" placeholder="비밀번호" required></div></div>'
    form_button = '<button type="submit" class="btn btn-primary">로그인</button><a href="/register/">계정이 없으신가요?</a>'
    template = template.replace('%_form_body_content_%', form_body_content)
    template = template.replace('%_form_button_%', form_button)
    ### Render End ###
    body_content += template

    if request.method == 'POST':
        sns_id = parser.anti_injection(request.form['account_id'])
        account_password = parser.anti_injection(request.form['account_password'])
        
        ### Get User Data ###
        user_data = sqlite3_control.select('select * from site_user_tb where sns_id = "{}"'.format(sns_id))
        ### Get End ###

        ### Encrypt Password ###
        aes = AESCipher(LocalSettings.crypt_secret_key)
        account_password_hash = aes.encrypt(account_password)
        ### Encrypt End ###
        if len(user_data) == 0:
            ### 아이디가 없습니다.
            alert_code = """
            <div class="alert alert-dismissible alert-danger">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <strong>누구세요?</strong><br> entree 엔진 서버에서 데이터를 찾을 수없습니다.
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', alert_code)
            return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
        elif account_password_hash == user_data[0][5]:
            session['now_login'] = user_data[0][0]
            alert_code = ''
            body_content = body_content.replace('%_form_alerts_%', alert_code)
            return redirect('/')
        else:
            alert_code = """
            <div class="alert alert-dismissible alert-danger">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <strong>로그인 실패</strong><br> 알맞지 않은 계정 정보입니다.
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', alert_code)
            return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
            ### 로그인 실패

    ### Render Alerts ###
    body_content = body_content.replace('%_form_alerts_%', '')
    ### Render End ###

### To-Do ###
# SNS 로그인 기능 재추가
### To-Do End ###
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/logout/')
def flask_logout():
    body_content = ''
    session.pop('now_login', None)
    nav_bar = user_profile_data.load_nav_bar()

    body_content += '<h1>로그아웃 완료</h1><p>{}에서 로그아웃되었습니다.</p><p>브라우저 캐시를 삭제하지 않으면 로그인한 것처럼 보일 수도 있음에 유의하세요.</p>'.format(LocalSettings.entree_appname)
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/register/', methods=['GET', 'POST'])
def flask_register():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    template = open('templates/account.html', encoding='utf-8').read()
    form_body_content = '<div class="form-group"><div class="form-group"><input type="text" class="form-control form-login-object" name="account_id" placeholder="계정명" required></div><div class="form-group"><input type="password" class="form-control form-login-object" name="account_password" placeholder="비밀번호" required></div><div class="form-group"><input type="text" class="form-control form-login-object" name="user_display_name" placeholder="이름" required></div><div class="form-group"><input type="text" class="form-control form-login-object" name="verify_key" placeholder="Verify Key" required></div></div>'
    template = template.replace('%_form_body_content_%', form_body_content)
    template = template.replace('%_form_button_%', '<p>주의: 본 서비스는 이메일 주소를 수집하고 있지 않습니다. 비밀번호를 잃어버리게 되면 복잡한 절차를 밟아야 하니 꼭 기억하세요.</p><button type="submit" class="btn btn-primary">가입하기</button>')
    body_content += template

    if request.method == 'POST':
        ### Check Verify Key ###
        verify_key = open('verify_key', encoding='utf-8').read()
        if verify_key != request.form['verify_key']:
            alert_code = """
            <div class="alert alert-dismissible alert-danger">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <strong>진심...인가요?</strong><br> verify_key 값이 틀렸습니다. 관리자에게 문의하세요.
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', alert_code)
            return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
        ### Check End ###

        ### Get Register Data ###
        sns_id = parser.anti_injection(request.form['account_id'])
        account_password = parser.anti_injection(request.form['account_password'])
        user_display_name = parser.anti_injection(request.form['user_display_name'])
        ### Get End ###

        ### Check Overlap ID ###
        same_id_getter = sqlite3_control.select('select * from site_user_tb where sns_type = "entree" and sns_id = "{}"'.format(sns_id))
        if len(same_id_getter) != 0:
            alert_code = """
            <div class="alert alert-dismissible alert-danger">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <strong>흐음..이미 있는 아이디네요.</strong><br> 이미 존재하는 아이디입니다. 다른 아이디를 선택하세요.
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', alert_code)
            return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
        ### Check End ###
        
        ### Encrypt Password ###
        aes = AESCipher(LocalSettings.crypt_secret_key)
        account_password_hash = aes.encrypt(account_password)
        ### Encrypt End ###

        ### Insert User Account into Database ###
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, account_password_hash) values("entree", "{}", "{}", "{}")'.format(
            sns_id, user_display_name, account_password_hash
        ))
        same_id_getter = sqlite3_control.select('select * from site_user_tb where sns_type = "entree" and sns_id = "{}"'.format(sns_id))
        if same_id_getter[0][0] != 1:
            sqlite3_control.commit('insert into user_administrator_list_tb values({}, "user")'.format(same_id_getter[0][0]))
        ### Insert End ###

        ### Verify Key Reset ###
        string = 'abcdefghijklmfgqrstuvwxyzabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!?@#$%_-'
        verify_key = ''.join(random.choice(string) for x in range(10))
        with open('verify_key', mode='w', encoding='utf-8') as f:
            f.write(verify_key)
        ### Reset End ###

        alert_code = """
        <div class="alert alert-dismissible alert-success">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <strong>환영합니다! %_user_display_name_%</strong><br> 이제 <a href="/login/" class="alert-link">로그인</a> 해보시겠어요?
        </div>
        """
        alert_code = alert_code.replace('%_user_display_name_%', user_display_name)
        body_content = body_content.replace('%_form_alerts_%', alert_code)
        return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
    
    body_content = body_content.replace('%_form_alerts_%', '')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


### Petition Route ###
@app.route('/a/', methods=['GET', 'POST'])
def flask_a():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()
    
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
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/a/<article_id>/', methods=['GET', 'POST'])
def flask_a_article_id(article_id):
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

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
        return redirect('/a/{}'.format(article_id))
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/a/write/', methods=['GET', 'POST'])
def flask_a_write():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

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
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
#### To-Do ####
"""
 * author_id에 고유 코드 기록 (현재: 그냥 유저가 입력한 정보 그대로 insert)
"""
#### To-Do End ####


@app.route('/a/<article_id>/delete/', methods=['GET', 'POST'])
def flask_a_article_id_delete(article_id):
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    template = open('templates/a_delete.html', encoding='utf-8').read()
    body_content += template
    if request.method == 'POST':
        sqlite3_control.commit('update peti_data_tb set peti_status = 404 where peti_id = {}'.format(article_id))
        return redirect('/a/')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

### Administrator Menu Route ###
@app.route('/admin/')
def flask_admin():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/member/')
def flask_admin_member():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    ### Index User List form Database ###
    user_list = sqlite3_control.select('select * from site_user_tb')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>사용자 목록</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">이름</th><th>내부 구분자, 아이디(구분자)</th><th>플랫폼</th></tr></thead><tbody>'
    for i in range(len(user_list)):
        body_content += '<tr><th scope="row"></th><td>{}</td><td>{}, {}</td><td>{}</td></tr>'.format(user_list[i][3], user_list[i][0], user_list[i][2], user_list[i][1])
    body_content += '</tbody></table>'
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/admins/')
def flask_admin_admins():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    ### Index Administrator List form Database ###
    admin_list = sqlite3_control.select('select * from user_administrator_list_tb')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>관리자 목록</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">이름</th><th>내부 구분자, 아이디(구분자)</th><th>플랫폼</th><th>권한 그룹</th></tr></thead><tbody>'
    for i in range(len(admin_list)):
        target_profile = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(admin_list[i][0]))
        body_content += '<tr><th scope="row"></th><td>{}</td><td>{}, {}</td><td>{}</td><td>{}</td></tr>'.format(target_profile[0][3], target_profile[0][0], target_profile[0][2], target_profile[0][1], admin_list[i][1])
    body_content += '</tbody></table>'
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/acl/')
def flask_admin_acl():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    ### Index User ACL ###
    acl_data = sqlite3_control.select('select * from user_group_acl')
    acl_name = sqlite3_control.select('pragma table_info(user_group_acl)')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>사용자 권한 레벨</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">그룹 이름</th><th>권한 리스트</th></tr></thead><tbody>'
    for i in range(len(acl_data)):
        acl_control_template = """
            <div class="custom-control custom-checkbox">
                <input type="checkbox" class="custom-control-input" id="%_acl_data_id_%" name="%_acl_data_id_%" %_is_enabled_% | %_is_locked_%>
                <label class="custom-control-label" for="%_acl_data_id_%">%_acl_data_name_%</label>
            </div>

        """
        acl_control_rendered = ''
        for j in range(len(acl_name)-1):
            if acl_data[i][j+1] == 0:
                is_enabled = ''
            else:
                is_enabled = 'checked'
            print('a')
            acl_control_display = acl_control_template
            acl_control_display = acl_control_display.replace('%_acl_data_id_%', str(j+1))
            acl_control_display = acl_control_display.replace('%_is_enabled_%', is_enabled)
            acl_control_display = acl_control_display.replace('%_acl_data_name_%', acl_name[j+1][1])
            if j+1 == 1 or j+1 == 13:
                acl_control_display = acl_control_display.replace('%_is_locked_%', 'disabled')
            else:
                acl_control_display = acl_control_display.replace('%_is_locked_%', '')
            print(acl_control_display)
            acl_control_rendered += acl_control_display
        body_content += '<tr><th scope="row"></th><td>{}</td><td>{}</td></tr>'.format(acl_data[i][0], acl_control_rendered)
    body_content += '</tbody></table>'
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/verify_key/')
def flask_admin_verify_key():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    body_content += '<h1>verify_key 정보</h1>'
    verify_key = open('verify_key', encoding='utf-8').read()
    body_content += '<input type="text" class="form-control" value="{}" disabled/>'.format(verify_key)
    body_content += '<p>verify_key는 1회 사용시 갱신됩니다.</p>'
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/petition/')
def flask_admin_petition():
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    ### Index Database ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_status = 1 or peti_status = 404')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>비활성화 / 삭제된 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">제목</th><th>상태</th></tr></thead><tbody>'
    for i in range(len(peti_data)):
        body_content += '<tr><th scope="row">{}</th><td><a href="/admin/petition/{}/">{}</a></td><td>{}</td></tr>'.format(peti_data[i][0], peti_data[i][0], peti_data[i][1], peti_data[i][3])
    body_content += '</tbody></table>'
    ### Render End ###
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/petition/<article_id>/', methods=['GET', 'POST'])
def flask_admin_petition_article_id(article_id):
    body_content = ''
    nav_bar = user_profile_data.load_nav_bar()

    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(article_id))
    template = open('templates/a.html', encoding='utf-8').read()

    ### Index React Content ###
    react_data = sqlite3_control.select('select * from peti_react_tb where peti_id = {}'.format(article_id))
    ### Index End ###

    ### Render React ###
    template_react = """
            <div class="container">
                <h5>%_article_react_author_display_name_%</h5>
                <p>%_article_react_body_content_%</p>
            </div>
            """
    react_body_content = ''
    template = template.replace('%_is_enabled_%', 'disabled')
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

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)



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
    nav_bar = user_profile_data.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

app.run(LocalSettings.flask_host, flask_port_set, debug = True)
