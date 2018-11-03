## Import Python Modules ##
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
from flask_assets import Bundle, Environment
from datetime import datetime
import sqlite3
import re
import json
import sys
import asyncio
import base64
import hashlib
import random
import bcrypt
import urllib.request

import LocalSettings

app = Flask(__name__)
app.secret_key = LocalSettings.crypt_secret_key

try:
    flask_port_set = int(sys.argv[1])
    print(' * 강제 포트 지정 설정됨 : {}'.format(flask_port_set))
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



class user_control:
    def load_nav_bar():
        ### Render Template ###
        template = """
        <ul class="nav navbar-nav ml-auto">
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" id="download"><img src="%_user_display_profile_img_%" width="10px" height="10px"> %_user_display_name_% <span class="caret"></span></a>
                <div class="dropdown-menu" aria-labelledby="download">
                    %_user_profile_menu_content_%
                </div>
            </li>
        </ul>
        """
        ### Render End ###
        user_profile_menu_content = ''
        if 'now_login' in session:
            ### Index Database Data ###
            user_data = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(session['now_login']))
            user_auth_group = sqlite3_control.select('select * from user_acl_list_tb where account_id = {}'.format(session['now_login']))
            user_auth = sqlite3_control.select('select * from user_group_acl where user_group = "{}"'.format(user_auth_group[0][1]))
            ### Index End ###

            ### Render Navbar ###
            template = template.replace('%_user_display_name_%', user_data[0][3])
            if user_auth[0][2] == 1:
                user_profile_menu_content += """
                <a class="dropdown-item" href="/admin/">관리자 메뉴</a>
                """
            user_profile_menu_content += """
            <a class="dropdown-item" href="/logout/">로그아웃</a>
            """
            ### Render End ###
        else:
            ### Render Navbar ###
            template = template.replace('%_user_display_name_%', '비로그인 상태')
            user_profile_menu_content += """
            <a class="dropdown-item" href="/login/">로그인</a>
            """
            ### Render End ###
        template = template.replace('%_user_profile_menu_content_%', user_profile_menu_content)
        return template
    
    def identify_user(target_id):
        user_auth_group = sqlite3_control.select('select * from user_acl_list_tb where account_id = {}'.format(target_id))
        user_auth = sqlite3_control.select('select * from user_group_acl where user_group = "{}"'.format(user_auth_group[0][1]))
        if user_auth[0][2] != 1 and user_auth[0][3] != 1:
            return False
        else:
            return True

    def user_controller(target_id):

        ## Index User Data ##
        user_data = sqlite3_control.select('select * from author_connect')
        ## Index End ##

        if 'now_login' in session:
            if user_control.identify_user(session['now_login']) == False:
                return user_data[0][1]
        else:
            return user_data[0][1]
        script = '<script>$(function () {$(\'[data-toggle="tooltip"]\').tooltip()})</script>'
        user_id_badge = ' <span class="badge badge-pill badge-success" data-toggle="tooltip" title="작성자 구분자: {}">{}</span>'.format(target_id, target_id)
        user_identify_badge = ' <a href="/admin/member/identify?user={}"><span class="badge badge-pill badge-info">명의</span></a>'.format(target_id)
        body_content = script + user_data[0][1] + user_id_badge + user_identify_badge
        return body_content
        
class config:
    def load_oauth_settings():
        oauth_native = open('oauthsettings.json', encoding='utf-8').read()
        oauth_json = json.loads(oauth_native)
        return oauth_json

    def load_verify_key(target, user_id):
        ### Check User Target's Authority ###
        user_auth_owner = sqlite3_control.select('select user_group_acl.site_owner from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = {} and user_group_acl.user_group = user_acl_list_tb.auth'.format(user_id))
        if user_auth_owner == 1:
            is_owner = True
        else:
            is_owner = False
        ### Check End ###

        ### Check Verify Key ###
        verify_key = open('verify_key', encoding='utf-8').read()
        if verify_key != target and verify_key+verify_key != target:
            return [False, False]
        ### Check End ###
        elif verify_key+verify_key == target:
            return [True, True] # is owner
        else:
            ### Verify Key Reset ###
            string = 'abcdefghijklmfgqrstuvwxyzabcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!?@#$%_-'
            verify_key = ''.join(random.choice(string) for x in range(10))
            with open('verify_key', mode='w', encoding='utf-8') as f:
                f.write(verify_key)
            ### Reset End ###
            return [True, False]

class viewer:
    def load_petition(target_id):
        body_content = ''

        ### Index Data from Database ###
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(target_id))
        react_data = sqlite3_control.select('select * from peti_react_tb where peti_id = {}'.format(target_id))
        ### Index End ###

        ### Load Template ###
        template = open('templates/a.html', encoding='utf-8').read()
        ### Load End ###

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

        ### Get Author Data ###
        author_data = sqlite3_control.select('select * from author_connect where peti_author_id = {}'.format(peti_data[0][4]))
        ### Get End ###

        ### Render Template ###
        author_data_display = user_control.user_controller(author_data[0][0])
        template = template.replace('%_article_display_name_%', peti_data[0][1])
        template = template.replace('%_article_publish_date_%', peti_data[0][2])
        template = template.replace('%_article_author_display_name_%', author_data_display)
        template = template.replace('%_article_body_content_%', peti_data[0][5])
        template = template.replace('%_article_react_count_%', str(len(react_data)))
        template = template.replace('%_article_reacts_%', react_body_content)
        body_content += template
        ### Render End ###
        
        return body_content

    def load_sns_login_status(content):
        if 'now_login' in session:
            user_profile_data = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(session['now_login']))
            content = content.replace('%_sns_login_status_%', '로그인 됨: {}'.format(user_profile_data[0][3]))
        else:
            content = content.replace('%_sns_login_status_%', '비로그인 상태로 비공개 청원을 작성합니다. 또는 <a href="/login">로그인</a>.')
        return content

    def load_search():
        ### Render Searchbar ###
        searchbar = """
        <div class="form-group">
            <div class="form-group">
                <div class="input-group mb-3">
                    <input type="number" class="form-control" id="search" onChange="revealResult()" aria-label="검색">
                    <div class="input-group-append">
                        <span class="input-group-text" id="search"><i class="fas fa-search"></i></span>
                    </div>
                </div>
            </div>
        </div>
        <div id="result"></div>
        """

        ### Render End ###

        ### CSS Code Render ###
        css_code = """
        <style>
            #overlay {
                position: fixed;
                display: none;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: rgba(0,0,0,0.5);
                z-index: 2;
            }

            #text{
                position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%,-50%);
                -ms-transform: translate(-50%,-50%);
            }

            .bs-docs-section{
                width: 70%;
                background-color: white;
                border-radius: 10px;
                padding: 50px;
            }
        </style>
        """
        ## need to edit: .bs-docs-section. mediaquery
        ### Render End ###

        ### Overlay HTML Render ###
        overlay_code = """
<div id="overlay">
    <div id="text">
  
        <div class="bs-docs-section">
            <p class="close" onclick="overlay_off()">x</p>
            <h1>작업 수행 확인</h1>
            <div class="bs-component">
                <form action="" accept-charset="utf-8" name="" method="post">
                    <fieldset>
                        <div class="form-group">
                            <div class="form-group">
                                %_sns_login_status_%
                            </div>
                            <div class="form-group">
                                <label class="custom-control-label" for="description">처리 사유를 입력하십시오.</label>
                                <input type="text" class="form-control" name="description" id="description" placeholder="" required>

                                <input type="hidden" id="target_id" name="target_id" value="">
                            </div>
                        </div>
                    </fieldset>
                    <div class="custom-control custom-checkbox">
                        <input type="checkbox" class="custom-control-input" id="Check" required>
                        <label class="custom-control-label" for="Check">해당 작업 처리 시 서버에 요청 기록이 남음을 확인하고 이 작업을 계속합니다.</label>
                    </div>
                    <button type="submit" name="submit" class="btn btn-primary" value="publish">계속하기</button>
                </form>
            </div>
        </div>
    </div>
</div>
        """
        overlay_code = viewer.load_sns_login_status(overlay_code)
        ### Render End ###

        ### Javascript Code Render ###
        user_data_sqlite = sqlite3_control.select('select account_id, sns_id, sns_type, user_display_profile_img from site_user_tb')
        json_code = '['
        for i in range(len(user_data_sqlite)):
            json_code += '{{account_id : "{}", sns_id : "{}", sns_type : "{}", user_display_profile_img : "{}" }}'.format(
                user_data_sqlite[i][0], user_data_sqlite[i][1], user_data_sqlite[i][2], user_data_sqlite[i][3])
            if i != len(user_data_sqlite) - 1:
                json_code += ','
        json_code += ']'
        js_code = """
        <script>
            var target
            var user_data = %_user_data_list_%
            function revealResult() {
                target = parseInt(document.getElementById("search").value) - 1
                document.getElementById("result").innerHTML = "<h2>검색결과</h2><table class='table table-hover'><thead><tr><th scope='col'>ID</th><th>고유 식별자</th><th>사용 SNS</th><th>확인</th></tr><tbody><td scope='row'>"+user_data[target]["account_id"]+"</td><td>"+user_data[target]["sns_id"]+"</td><td>"+user_data[target]["sns_type"]+"</td><td><a onClick='overlay_on()' class='btn btn-link' style='margin: 0; padding: 0'>확인</a></td></tbody></thead></table>"
            }
            function overlay_on() {
                document.getElementById("target_id").value = target + 1;
                document.getElementById("overlay").style.display = "block";
            }

            function overlay_off() {
                document.getElementById("overlay").style.display = "none";
            }
        </script>
        """
        js_code = js_code.replace('%_user_data_list_%', json_code)
        ### Render End ###
        body_content = js_code + css_code + searchbar + overlay_code
        return body_content

    def load_identify(target):
        target_data = sqlite3_control.select('select ') ## 수정 필요

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
    nav_bar = user_control.load_nav_bar()
    
    ### Load From Database ###
    static_data = sqlite3_control.select('select * from static_page_tb where page_name = "frontpage"')
    ### Load End ###

    body_content += static_data[0][1]

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

### Account Route ###
@app.route('/login/', methods=['GET', 'POST'])
def flask_login():
    if 'now_login' in session:
        return redirect('/')
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### 오류 처리
    if request.args.get('error') == 'null':
        pass
    ###

    ## Render OAuth Buttons ##
    login_button_display = """
    <ul>
        <li><a href="/login/naver/">네이버 로그인</a></li>
        <li><a href="/login/facebook/">Facebook 로그인</a></li>
        <li><a href="/login/entree/">entree 엔진 로그인</a></li>
    </ul>
    """
    ## Render End ##
    body_content += 'SNS 로그인 시 해당 SNS의 로그인 상태가 유지됩니다. 공용 컴퓨터에서 SNS 로그인을 사용하는 경우 시크릿 모드(Inprivate 모드)에서 로그인을 계속하십시오.'
    body_content += login_button_display
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/login/naver/', methods=['GET', 'POST'])
def flask_login_naver():
    nav_bar = user_control.load_nav_bar()
    oauth = config.load_oauth_settings()
    if request.args.get('error') == 'no_get_values':
        body_content = '요구 로그인 값을 충족시키지 못했습니다..'
        return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
    if oauth['facebook_client_id'] == '' or oauth['facebook_client_secret'] == '':
        body_content = '관리자가 이 기능을 비활성화 시켰습니다.'
        return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

    data = {
        'client_id' : oauth['naver_client_id'],
        'redirect_uri' : LocalSettings.publish_host_name + '/login/naver/callback/',
        'state' : LocalSettings.crypt_secret_key
    }
    return redirect('https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id={}&redirect_uri={}&state={}'.format(
        data['client_id'], data['redirect_uri'], data['state']
    ))

@app.route('/login/naver/callback/', methods=['GET', 'POST'])
def flask_login_naver_callback():
    oauth = config.load_oauth_settings()

    ###  ###
    try:
        code = request.args.get('code')
        state = request.args.get('state')
    except:
        return redirect('/login/naver/?error=no_get_values')
    ###
    data = {
        'client_id' : oauth['naver_client_id'],
        'client_secret' : oauth['naver_client_secret'],
        'code' : code
    }
    ###

    ##
    token_access = 'https://nid.naver.com/oauth2.0/token?grant_type=authorization_code&client_id={}&client_secret={}&code={}&state={}'.format(
        data['client_id'], data['client_secret'], data['code'], state
    )
    token_result = urllib.request.urlopen(token_access).read().decode('utf-8')
    token_result_json = json.loads(token_result)
    ###

    ###
    headers = {'Authorization': 'Bearer {}'.format(token_result_json['access_token'])}
    profile_access = urllib.request.Request('https://openapi.naver.com/v1/nid/me', headers = headers)
    profile_result = urllib.request.urlopen(profile_access).read().decode('utf-8')
    profile_result_json = json.loads(profile_result)
    ###

    ### 아이디 유효성 검사 ###
    result_id = sqlite3_control.select('select * from site_user_tb')
    if len(result_id) == 0:
        data_len = len(sqlite3_control.select('select account_id from site_user_tb'))
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, user_display_profile_img) values("naver", "{}", "{}", "{}")'.format(
            profile_result_json['response']['id'], profile_result_json['response']['name'], profile_result_json['response']['profile_image']
        ))
        ### Insert User Account into Database ###
        same_id_getter = sqlite3_control.select('select * from site_user_tb')
        if len(same_id_getter) != 0:
            sqlite3_control.commit('insert into user_acl_list_tb values({}, "user")'.format(same_id_getter[0][0]+1))
        ### Insert End ###
        session['now_login'] = str(data_len + 1)
    else:
        session['now_login'] = result_id[0][0]
    return redirect('/')

@app.route('/login/facebook/', methods=['GET', 'POST'])
def flask_login_facebook():
    nav_bar = user_control.load_nav_bar()
    oauth = config.load_oauth_settings()
    if request.args.get('error') == 'no_get_values':
        body_content = '요구 로그인 값을 충족시키지 못했습니다..'
        return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)
    if oauth['facebook_client_id'] == '' or oauth['facebook_client_secret'] == '':
        body_content = '관리자가 이 기능을 비활성화 시켰습니다.'
        return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

    data = {
        'client_id' : oauth['facebook_client_id'],
        'redirect_uri' : LocalSettings.publish_host_name + '/login/facebook/callback/',
        'state' : LocalSettings.crypt_secret_key
    }
    return redirect('https://www.facebook.com/v3.1/dialog/oauth?client_id={}&redirect_uri={}&state={}'.format(
        data['client_id'], data['redirect_uri'], data['state']
    ))

@app.route('/login/facebook/callback/', methods=['GET', 'POST'])
def flask_login_facebook_callback():
    oauth = config.load_oauth_settings()

    ###  ###
    try:
        code = request.args.get('code')
        state = request.args.get('state')
    except:
        return redirect('/login/facebook/?error=no_get_values')
    ###
    data = {
        'client_id' : oauth['facebook_client_id'],
        'redirect_uri' : LocalSettings.publish_host_name + '/login/facebook/callback/',
        'client_secret' : oauth['facebook_client_secret'],
        'code' : code
    }
    ###

    ##
    token_access = 'https://graph.facebook.com/v3.1/oauth/access_token?client_id={}&redirect_uri={}&client_secret={}&code={}'.format(
        data['client_id'], data['redirect_uri'], data['client_secret'], data['code']
    )
    token_result = urllib.request.urlopen(token_access).read().decode('utf-8')
    token_result_json = json.loads(token_result)
    ###

    ###
    profile_access = 'https://graph.facebook.com/me?fields=id,name,picture&access_token={}'.format(token_result_json['access_token'])
    profile_result = urllib.request.urlopen(profile_access).read().decode('utf-8')
    profile_result_json = json.loads(profile_result)
    ###

    ### 아이디 유효성 검사 ###
    result_id = sqlite3_control.select('select * from site_user_tb')
    if len(result_id) == 0:
        data_len = len(sqlite3_control.select('select account_id from site_user_tb'))
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, user_display_profile_img) values("facebook", "{}", "{}", "{}")'.format(
            profile_result_json['id'], profile_result_json['name'], profile_result_json['picture']['data']['url']
        ))
        ### Insert User Account into Database ###
        same_id_getter = sqlite3_control.select('select * from site_user_tb')
        if len(same_id_getter) != 0:
            sqlite3_control.commit('insert into user_acl_list_tb values({}, "user")'.format(same_id_getter[0][0]+1))
        ### Insert End ###
        session['now_login'] = str(data_len + 1)
    else:
        session['now_login'] = result_id[0][0]
    return redirect('/')

@app.route('/login/entree/', methods=['GET', 'POST'])
def flask_login_entree():
    body_content = ''
    nav_bar = user_control.load_nav_bar()
    
    ### Render Template ###
    template = open('templates/account.html', encoding='utf-8').read()
    form_body_content = '<div class="form-group"><div class="form-group"><input type="text" class="form-control form-login-object" name="account_id" placeholder="계정명" required></div><div class="form-group"><input type="password" class="form-control form-login-object" name="account_password" placeholder="비밀번호" required></div></div>'
    form_button = '<button type="submit" class="btn btn-primary">로그인</button><a href="/register/">계정이 없으신가요?</a>'
    template = template.replace('%_page_title_%', '로그인')
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
        elif bcrypt.hashpw(account_password.encode(), user_data[0][5].encode()) == user_data[0][5].encode():
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
            ### 로그인 실패 #

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
    nav_bar = user_control.load_nav_bar()

    body_content += '<h1>로그아웃 완료</h1><p>{}에서 로그아웃되었습니다.</p><p>브라우저 캐시를 삭제하지 않으면 로그인한 것처럼 보일 수도 있음에 유의하세요.</p>'.format(LocalSettings.entree_appname)
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/register/', methods=['GET', 'POST'])
def flask_register():
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Render Template ###
    template = open('templates/account.html', encoding='utf-8').read()
    form_body_content = '<div class="form-group"><div class="form-group"><input type="text" class="form-control form-login-object" name="account_id" placeholder="계정명" required></div><div class="form-group"><input type="password" class="form-control form-login-object" name="account_password" placeholder="비밀번호" required></div><div class="form-group"><input type="text" class="form-control form-login-object" name="user_display_name" placeholder="이름" required></div><div class="form-group"><input type="text" class="form-control form-login-object" name="verify_key" placeholder="Verify Key" required></div></div>'
    template = template.replace('%_page_title_%', '회원가입')
    template = template.replace('%_form_body_content_%', form_body_content)
    template = template.replace('%_form_button_%', '<p>주의: 본 서비스는 이메일 주소를 수집하고 있지 않습니다. 비밀번호를 잃어버리게 되면 복잡한 절차를 밟아야 하니 꼭 기억하세요.</p><button type="submit" class="btn btn-primary">가입하기</button>')
    body_content += template
    ### Render End ###

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
        account_password_hash = bcrypt.hashpw(account_password.encode(), bcrypt.gensalt())
        ### Encrypt End ###

        ### Insert User Account into Database ###
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, account_password_hash) values("entree", "{}", "{}", "{}")'.format(
            sns_id, user_display_name, account_password_hash.decode()
        ))
        same_id_getter = sqlite3_control.select('select * from site_user_tb where sns_type = "entree" and sns_id = "{}"'.format(sns_id))
        if same_id_getter[0][0] != 1:
            sqlite3_control.commit('insert into user_acl_list_tb values({}, "user")'.format(same_id_getter[0][0]))
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
            <strong>환영합니다! %_user_display_name_%</strong><br> 이제 <a href="/login/entree/" class="alert-link">로그인</a> 해보시겠어요?
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
    nav_bar = user_control.load_nav_bar()
    
    ### Index Database ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_status != 1 and peti_status != 404 order by peti_id desc')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>새로운 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">청원 제목</th></tr></thead><tbody>'
    for i in range(len(peti_data)):
        body_content += '<tr><th scope="row">{}</th><td><a href="/a/{}/">{}</a></td></tr>'.format(peti_data[i][0], peti_data[i][0], peti_data[i][1])
    body_content += '</tbody></table>'
    body_content += '<button onclick="window.location.href=\'write\'" class="btn btn-primary" value="publish">청원 등록</button>'
    ### Render End ###
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/a/<article_id>/', methods=['GET', 'POST'])
def flask_a_article_id(article_id):
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Load Petition Data ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(article_id))

    if peti_data[0][3] == 1 or peti_data[0][3] == 404:
        abort(404)
    ### Load End ###

    if request.args.get('error') == 'no_login':
        pass ## return error



    ### Render Bodycontent ###
    body_content += viewer.load_petition(article_id)
    if 'now_login' in session:
        body_content = body_content.replace('%_enabled_content_%', '')
    else:
        body_content = body_content.replace('%_is_enabled_%', 'disabled')
        body_content = body_content.replace('%_enabled_content_%', '비로그인 상태에서는 청원 반응이 불가능합니다.')
    ### Render End ###
    if request.method == 'POST':
        ### Collect React Data ###
        peti_id = article_id
        author_id = 0 ##<< 이거 수정 (Todo List)
        content = parser.anti_injection(request.form['react_content'])
        author_display = parser.anti_injection(request.form['react_author_display_name'])
        if author_display == '':
            author_display = '익명 사용자'
        ### Collect End ###

        ### Save React Author Data ###
        if 'now_login' in session:
            author_list_len = len(sqlite3_control.select('select * from author_connect'))
            sqlite3_control.commit('insert into author_connect (peti_author_display_name, account_user_id) values("{}", {})'.format(
                author_display, session['now_login']))
            react_author_id = author_list_len + 1
        else:
            return redirect('?error=no_login')
        ### Save End ###

        ### Insert Data into Database ###
        sqlite3_query = 'insert into peti_react_tb (peti_id, author_id, content) values({}, {}, "{}")'.format(
            peti_id,
            react_author_id,
            content
        )
        sqlite3_control.commit(sqlite3_query)
        ### Insert End ###
        return redirect('/a/{}'.format(article_id))
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/a/write/', methods=['GET', 'POST'])
def flask_a_write():
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    template = open('templates/a_write.html', encoding='utf-8').read()
    
    ### Template Rendering ###
    if 'now_login' in session:
        user_profile_data = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(session['now_login']))
        template = template.replace('%_sns_login_status_%', '로그인 됨: {}'.format(user_profile_data[0][3]))
    else:
        template = template.replace('%_sns_login_status_%', '비로그인 상태로 비공개 청원을 작성합니다. 또는 <a href="/login">로그인</a>.')
    ### Rendering End ###

    if request.method == 'POST':
        ### Get Login Data ###
        if 'now_login' in session:
            peti_status = 0
        else:
            peti_status = 1
        ### Get End ###

        ### Get POST Data ###
        peti_display_name =  parser.anti_injection(request.form['peti_display_name'])
        peti_publish_date = datetime.today()
        peti_author_display_name = parser.anti_injection(request.form['peti_author_display_name'])
        peti_body_content = parser.anti_injection(request.form['peti_body_content'])
        ### Get End ###

        ### Save Author Data ###
        if peti_status == 1:
            account_user_id = 0
        else:
            account_user_id = session['now_login']
        author_list_len = len(sqlite3_control.select('select * from author_connect'))
        sqlite3_control.commit('insert into author_connect (peti_author_display_name, account_user_id) values("{}", {})'.format(
            peti_author_display_name,
            account_user_id
        ))
        peti_author_id = author_list_len + 1
        ### Save End ###

        ### Insert Data into Database ###
        sqlite3_query = 'insert into peti_data_tb (peti_display_name, peti_publish_date, peti_status, peti_author_id, peti_body_content) values("{}", "{}", {}, {}, "{}")'.format(
            peti_display_name,
            peti_publish_date,
            peti_status,
            peti_author_id,
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
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    template = open('templates/confirm.html', encoding='utf-8').read()
    body_content += template

    ### Render Login Status ###
    user_profile = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(session['now_login']))
    body_content = body_content.replace('%_sns_login_status_%', '{} 연결됨: {}'.format(user_profile[0][1], user_profile[0][3]))
    ### Render End ###
    
    if request.method == 'POST':
        ### Log Activity ###
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(article_id))
        activity_date = datetime.today()
        activity_object = '청원(<i>{}</i>)'.format(peti_data[0][1])
        activity_description = request.form['description']
        sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values({}, "{}", "{}", "{}", "{}")'.format(
            session['now_login'],
            activity_object,
            '삭제',
            activity_description,
            activity_date
        ))
        ### Log End ###

        sqlite3_control.commit('update peti_data_tb set peti_status = 404 where peti_id = {}'.format(article_id))
        return redirect('/a/')
    body_content = body_content.replace('%_form_alerts_%', '')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


### Log Route ###
@app.route('/log/')
def flask_log():        
    body_content = ''
    body_content += '<h1>투명성 보고서</h1>'

    ### Index Server Log ###
    log = sqlite3_control.select('select * from user_activity_log_tb order by log_id desc')
    ### Index End ###

    ### Render Log ###
    for i in range(len(log)):
        profile = sqlite3_control.select('select * from site_user_tb where account_id = {}'.format(log[i][1]))
        body_content += '<p>{}  {}(이)가 {}을(를) {}함 (사유: {})'.format(log[i][5], profile[0][3], log[i][2], log[i][3], log[i][4])
    ### Render End ###

    nav_bar = user_control.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


### Administrator Menu Route ###
@app.route('/admin/')
def flask_admin():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')
    body_content = ''        

    ### Load From Database ###
    static_data = sqlite3_control.select('select * from static_page_tb where page_name = "adminpage"')
    ### Load End ###

    body_content += static_data[0][1]

    nav_bar = user_control.load_nav_bar()

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/member/')
def flask_admin_member():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Index User List form Database ###
    user_list = sqlite3_control.select('select * from site_user_tb')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>사용자 목록</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">이름</th><th>내부 구분자, 아이디(구분자)</th><th>플랫폼</th></tr></thead><tbody>'
    for i in range(len(user_list)):
        if user_list[i][1] == 'facebook':
            user_id_display = '<a href="https://facebook.com/{}" target="_blank">{}</a>'.format(user_list[i][2], user_list[i][2])
        else:
            user_id_display = user_list[i][2]
        user_display_name = '<img src="{}" width="20" height="20" />  {}'.format(user_list[i][4], user_list[i][3])
        body_content += '<tr><th scope="row"></th><td>{}</td><td>{}, {}</td><td>{}</td></tr>'.format(user_display_name, user_list[i][0], user_id_display, user_list[i][1])
    body_content += '</tbody></table>'
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/member/identify/', methods=['GET', 'POST'])
def flask_admin_identify():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')
        
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Render Errors ###
    if request.args.get('error') == 'no_int':
        body_content += """<div class="alert alert-dismissible alert-danger">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <strong>으악!</strong><p>이건 검색할 수 있는 아이디가 아니잖아요.</p>
        </div>"""
    ### Render End ###

    ### Review Errors ###
    if request.args.get('user') != None:
        try:
            target_id = int(request.args.get('user'))
        except:
            return redirect('/?error=need_enough_data')
    #else:
    #    return redirect('/?error=need_enough_data')
    ### Review End ###

    ### Render
    form_template = open('templates/confirm.html', encoding="utf-8").read()
    form_rendered = form_template.replace('%_confirm_head_%', '작업 확인')
    form_rendered = form_rendered.replace('%_form_alerts_%', '<input type="hidden" id="target_id" name="target_id" value="{}">'.format(target_id))
    form_rendered = viewer.load_sns_login_status(form_rendered)
    body_content += form_rendered
    ### Render End

    if request.method == 'POST':
        try:
            account_id = session['now_login']
            activity_object = request.form['target_id']
            activity_description = request.form['description']
        except:
            pass
        target_data_sqlite = sqlite3_control.select('select site_user_tb.account_id, site_user_tb.user_display_name, site_user_tb.sns_id, site_user_tb.sns_type, site_user_tb.user_display_profile_img, author_connect.peti_author_display_name from site_user_tb, author_connect where author_connect.peti_author_id = {} and author_connect.account_user_id = site_user_tb.account_id'.format(
            target_id
        ))

        activity_date = datetime.today()
        sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values({}, "{}", "{}", "{}", "{}")'.format(
        session['now_login'],
        '닉네임 ' + target_data_sqlite[0][5],
        '명의를 확인',
        activity_description,
        activity_date
        ))

        table_template = """
        <h2>검색결과</h2>
        <table class='table table-hover'>
            <thead>
            <tr><th scope='col'>ID</th><th>실명</th><th>고유 식별자</th><th>사용 SNS</th><th>사용한 닉네임</th></tr>
            <tbody>
            <td scope='row'>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tbody></thead></table>
        """.format(target_data_sqlite[0][0], target_data_sqlite[0][1], target_data_sqlite[0][2], target_data_sqlite[0][3], target_data_sqlite[0][5])

        body_content = table_template
    
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/admins/')
def flask_admin_admins():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Index User List form Database ###
    user_list = sqlite3_control.select('select * from site_user_tb')
    user_admin_list = []
    user_auth_list = []
    for i in range(len(user_list)):
        administrator_data = sqlite3_control.select('select user_group_acl.site_administrator, user_group_acl.user_group from user_group_acl, user_acl_list_tb where user_acl_list_tb.account_id = {} and user_acl_list_tb.auth = user_group_acl.user_group'.format(i+1))
        if administrator_data[0][0] == 1:
            user_admin_list += [i]
        user_auth_list += [administrator_data[0][1]]
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>관리자 목록</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">이름</th><th>내부 구분자, 아이디(구분자)</th><th>플랫폼</th><th>권한</th></tr></thead><tbody>'
    for i in range(len(user_admin_list)):
        j = user_admin_list[i]
        if user_list[j][1] == 'facebook':
            user_id_display = '<a href="https://facebook.com/{}" target="_blank">{}</a>'.format(user_list[j][2], user_list[j][2])
        else:
            user_id_display = user_list[j][2]
        user_display_name = '<img src="{}" width="20" height="20" />  {}'.format(user_list[j][4], user_list[j][3])
        body_content += '<tr><th scope="row"></th><td>{}</td><td>{}, {}</td><td>{}</td><td>{}</td></tr>'.format(user_display_name, user_list[j][0], user_id_display, user_list[j][1], user_auth_list[j])
    body_content += '</tbody></table>'

    body_content += '<a href="/admin/admins/add/" class="btn btn-primary">관리자 추가</a>'
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/admins/add/', methods=['GET', 'POST'])
def flask_admin_admins_add():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')
        
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Render Errors ###
    if request.args.get('error') == 'no_int':
        body_content += """<div class="alert alert-dismissible alert-danger">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <strong>으악!</strong><p>이건 검색할 수 있는 아이디가 아니잖아요.</p>
        </div>"""
    ### Render End ###

    ### Review Errors ###
    if request.args.get('user') != None:
        try:
            target_id = int(request.args.get('user'))
        except:
            return redirect('?error=no_int')
    ### Review End ###

    ### Get Target User Data ###
    target = request.args.get('user')
    if target == None:
        target = ''
    else:
        try:
            int(target)
        except:
            target =''
    ### Get End ###

    ### Render Search Page ###
    body_content += viewer.load_search()
    ### Render End ###

    ### Update User Data ###
    if request.method == 'POST':
        try:
            account_id = session['now_login']
            activity_object = request.form['target_id']
            activity_description = request.form['description']
        except:
            pass ### 오류!
        target_user_data = sqlite3_control.select('select user_display_name from site_user_tb where account_id = {}'.format(activity_object))
        activity_date = datetime.today()
        sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values({}, "{}", "{}", "{}", "{}")'.format(
        session['now_login'],
        '사용자 ' + target_user_data[0][0],
        '관리자로 등록',
        activity_description,
        activity_date
        ))
        user_auth_owner = sqlite3_control.select('select user_group_acl.site_owner from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = {} and user_group_acl.user_group = user_acl_list_tb.auth'.format(activity_object))
        if user_auth_owner[0][0] == 0:
            sqlite3_control.commit('update user_acl_list_tb set auth="administrator" where account_id = {}'.format(activity_object))
        return redirect('/admin/admins/')
    
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


@app.route('/admin/acl/', methods=['GET', 'POST'])
def flask_admin_acl():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    table_container = ''
    nav_bar = user_control.load_nav_bar()

    ### Index User ACL ###
    acl_data = sqlite3_control.select('select * from user_group_acl')
    acl_name = sqlite3_control.select('pragma table_info(user_group_acl)')
    ### Index End ###

    ### Render Error ###
    if request.args.get('error') == 'out_of_range':
        body_content += """<div class="alert alert-dismissible alert-warning">
            <button type="button" class="close" data-dismiss="alert">&times;</button>
            <h4 class="alert-heading">오류!</h4>
            <p class="mb-0">권한 우선도는 0부터 1000 사이의 정수만 가능합니다.</p>
        </div>"""
    ### End Render ###


    ### Render Template ###
    body_content += '<h1>사용자 권한 레벨</h1><table class="table table-hover"><thead><tr><th width="10%">N</th><th scope="col" width="30%">그룹 이름</th><th width="15%">권한 우선도</th><th width="45%">권한 리스트</th><th width="10%">편집</th></tr></thead></table>'
    table_template = '<form action="" accept-charset="utf-8" method="post"><table class="table table-hover"><tbody>%_table_content_%</tbody></table></form>'
    for i in range(len(acl_data)):
        table_content = ''
        acl_control_template = """
            <div class="custom-control custom-checkbox">
                <input type="checkbox" class="custom-control-input" id="%_acl_data_id_%" name="%_acl_data_id_name_%" %_is_enabled_% | %_is_locked_%>
                <label class="custom-control-label" for="%_acl_data_id_%">%_acl_data_name_%</label>
            </div>
        """
        acl_control_rendered = ''
        for j in range(len(acl_name)-2):
            if acl_data[i][j+2] == 0:
                is_enabled = ''
            else:
                is_enabled = 'checked'
            acl_control_display = acl_control_template
            acl_control_display = acl_control_display.replace('%_acl_data_id_%', str(i)+str(j))
            acl_control_display = acl_control_display.replace('%_acl_data_id_name_%', str(j))
            acl_control_display = acl_control_display.replace('%_is_enabled_%', is_enabled)
            acl_control_display = acl_control_display.replace('%_acl_data_name_%', acl_name[j+2][1])
            if j+1 == 1 or j+1 == 14:
                acl_control_display = acl_control_display.replace('%_is_locked_%', 'disabled')
            else:
                acl_control_display = acl_control_display.replace('%_is_locked_%', '')
            acl_control_rendered += acl_control_display

            ### Render Etc. ###
            link_editor = '<a href="?target=%_target_id_%"><input type="submit" value="편집" class="btn btn-link"></input></a><input type="hidden" name="acl_group" value="{}">'.format(acl_data[i][0])
            link_editor_rendered = link_editor.replace('%_target_id_%', str(i))
            priority_rendered = '<input type="number" class="form-control" name="group_priority" value="{}">'.format(acl_data[i][1])

            if i == 0:
                link_editor_rendered = '<input type="submit" value="불가" class="btn btn-link" disabled></input></a>'
                priority_rendered = '<input type="number" class="form-control" name="group_priority" value="{}" disabled>'.format(acl_data[i][1])
            ### Render End ###
        table_content += '<tr><th width="10%"></th><td scope="row" width="30%">{}</td><td width="15%">{}</td><td width="45%">{}</td><td width="10%">{}</td></tr>'.format(acl_data[i][0], priority_rendered, acl_control_rendered, link_editor_rendered)
        table_container += table_template.replace('%_table_content_%', table_content)
    ### Render End ###

    ### Confirm Edit ###
    if request.method == 'POST':

        acl_group = request.form['acl_group']

        ### Check Auth ###
        #### 1: manage auth ####
        acl_data = sqlite3_control.select('select user_acl_list_tb.auth, user_group_acl.manage_acl from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = {} and user_acl_list_tb.auth = user_group_acl.user_group'.format(session['now_login']))
        if acl_data[0][1] == 1:
            pass
        else:
            return redirect('/error/acl/')
        
        #### 2: acl priority ####
        acl_pri_user = sqlite3_control.select('select user_group_acl.group_priority from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = {} and user_acl_list_tb.auth = user_group_acl.user_group'.format(session['now_login']))
        acl_pri_target = sqlite3_control.select('select group_priority from user_group_acl where user_group = "{}"'.format(acl_group))
        if acl_pri_user[0][0] < acl_pri_target[0][0]:
            return redirect('/error/acl/?error=high_acl')
        ### Check End ###

        ### Check group_priority Value ###
        group_priority = int(request.form['group_priority'])
        if group_priority >= 0 and group_priority <= 1000:
            pass
        else:
            return redirect('/admin/acl/?error=out_of_range')
        ### Check End ###


        new_acl_data = []
        for i in range(14):
            acl_data = request.form.get(str(i))
            if acl_data == None:
                new_acl_data += [0]
            else:
                new_acl_data += [1]
        
        sqlite3_control.commit('update user_group_acl set group_priority = {}, site_owner = {}, site_administrator = {}, peti_read = {}, peti_write = {}, peti_react = {}, peti_disable = {}, peti_delete = {}, user_identify = {}, user_block = {}, manage_user = {}, manage_acl = {}, manage_static_page = {}, manage_notion = {}, not_display_log = {} where user_group = "{}"'.format(
            group_priority,
            new_acl_data[0],
            new_acl_data[1],
            new_acl_data[2],
            new_acl_data[3],
            new_acl_data[4],
            new_acl_data[5],
            new_acl_data[6],
            new_acl_data[7],
            new_acl_data[8],
            new_acl_data[9],
            new_acl_data[10],
            new_acl_data[11],
            new_acl_data[12],
            new_acl_data[13],
            acl_group
        ))
        return redirect('/admin/acl/')
    ### Confirm End ###

    body_content += table_container
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/verify_key/')
def flask_admin_verify_key():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    body_content += '<h1>verify_key 정보</h1>'
    verify_key = open('verify_key', encoding='utf-8').read()
    ###
    verify_key_template = """
<div class="form-group">
  <div class="form-group">
    <div class="input-group mb-3 single-center">
      <div class="input-group-prepend">
        <span class="input-group-text"></span>
      </div>
      <input type="text" class="form-control" id="verify_key_value" value="%_verify_key_value_%" disabled>
      <div class="input-group-append">
        <span class="input-group-text" id="copy_target" onclick="copy_to_clipboard()" data-toggle="tooltip" title="복사" style="cursor: pointer;"><i class="fas fa-copy"></i></span>
      </div>
    </div>
  </div>
</div>
<script type="text/javascript">
function copy_to_clipboard() {
  var copyText = document.getElementById("copy_target");
  copyText.select();
  document.execCommand("Copy");
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})
</script>
    """
    ###
    body_content += verify_key_template.replace('%_verify_key_value_%', verify_key)
    body_content += '<p>verify_key는 1회 사용시 갱신됩니다.</p>'
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/petition/')
def flask_admin_petition():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Index Database ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_status = 1 or peti_status = 404 order by peti_id desc')
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>비활성화 / 삭제된 청원들</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">제목</th><th>상태</th></tr></thead><tbody>'
    for i in range(len(peti_data)):
        if peti_data[i][3] == 1:
            peti_status = '비공개'
        if peti_data[i][3] == 404:
            peti_status = '삭제됨'
        body_content += '<tr><th scope="row">{}</th><td><a href="/admin/petition/{}/">{}</a></td><td>{}</td></tr>'.format(peti_data[i][0], peti_data[i][0], peti_data[i][1], peti_status)
    body_content += '</tbody></table>'
    ### Render End ###
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/petition/<article_id>/', methods=['GET', 'POST'])
def flask_admin_petition_article_id(article_id):
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = {}'.format(article_id))
    template = open('templates/a.html', encoding='utf-8').read()

    ### Index React Content ###
    react_data = sqlite3_control.select('select * from peti_react_tb where peti_id = {}'.format(article_id))
    ### Index End ###

    ### Get Author Data ###
    author_data = sqlite3_control.select('select * from author_connect where peti_author_id = {}'.format(peti_data[0][4]))
    author_display_name = author_data[0][1]
    ### Get End ###

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
    template = template.replace('%_article_author_display_name_%', author_display_name)
    template = template.replace('%_article_body_content_%', peti_data[0][5])
    template = template.replace('%_article_react_count_%', str(len(react_data)))
    template = template.replace('%_article_reacts_%', react_body_content)
    body_content += template
    ### Render End ###

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/static/', methods=['GET', 'POST'])
def flask_admin_static():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')
        
    body_content = ''
    body_content += '<h1>정적 페이지 관리</h1>'

    ### Index Static Page Data ###
    static_page = sqlite3_control.select('select * from static_page_tb')
    template = """
    <ul class="nav nav-pills">
        %_pill_body_content_%
    </ul>
    """
    ### Index End ###

    ### Render Pill Object ###
    pill_body_content = ''
    for i in range(len(static_page)):
        pill_body_object = '<li class="nav-item"><a class="nav-link %_is_active_%" href="?page={}">{}</a></li>'.format(static_page[i][0], static_page[i][0])
        if request.method == 'GET':
            if request.args.get('page') == static_page[i][0]:
                pill_body_object = pill_body_object.replace('%_is_active_%', 'active')
        pill_body_content += pill_body_object
    template = template.replace('%_pill_body_content_%', pill_body_content)
    body_content += template
    ### End Render ###

    ### Render Ststic Page Editor ###
    if request.args.get('page') != None:
        target = request.args.get('page')
        target_content = sqlite3_control.select('select * from static_page_tb where page_name = "{}"'.format(target))
        textarea = """
        <div class="bs-docs-section">
            <form action="" accept-charset="utf-8" method="post">
                <textarea class="form-control" name="content" rows="3" placeholder="html 코드로 작성합니다.">%_textarea_content_%</textarea>
                <button type="submit" name="submit" class="btn btn-primary" value="publish">업데이트</button>
            </form>
        </div>
        """
        textarea = textarea.replace('%_textarea_content_%', target_content[0][1])
        body_content += textarea
    ### End Render ###

    if request.method == 'POST':
        ### Update Static Page Data ###
        received_content = request.form['content'].replace('"', '""')
        sqlite3_control.commit('update static_page_tb set content = "{}" where page_name = "{}"'.format(received_content, request.args.get('page')))
        ### End Update ###
        return redirect('/admin/static/?page={}'.format(request.args.get('page')))

    nav_bar = user_control.load_nav_bar()

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

### Assets Route ###
@app.route('/img/<assets>/')
def serve_pictures(assets):
    return static_file(assets, root='views/img')

### Error Handler ###
@app.route('/error/acl/', methods=['GET'])
def error_acl():
    body_content = '<h1>Oops!</h1><h2>ACL NOT SATISFIED</h2>'
    if request.args.get('error') == 'no_write':
        body_content += '<p>당신의 acl은 쓰기 권한을 포함하고 있지 않습니다.<p><p>당신의 <i>%_block_cause_%<i>로 이 서비스 사용이 일시적으로 중지된 것 같습니다.</p>'
    elif request.args.get('error') == 'acl_high':
        body_content += '<p>당신보다 낮은 acl 우선도를 가지고 있는 사용자 그룹의 acl만 편집할 수 있습니다.</p>'
    else:
        body_content += '<p>ACL이 만족되지 않아 접근할 수 없습니다.</p>'
    nav_bar = user_control.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.errorhandler(404)
def error_404(self):
    body_content = '<h1>Oops!</h1><h2>404 NOT FOUND</h2><p>존재하지 않는 페이지입니다.</p>'
    nav_bar = user_control.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

app.run(LocalSettings.flask_host, flask_port_set, debug = True)
