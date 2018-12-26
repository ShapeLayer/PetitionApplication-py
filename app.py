# coding=utf-8
### === Import Python Modules === ###
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort, send_from_directory
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
### === Import End === ###

### === Initialize Application === ###
app = Flask(__name__)
app.secret_key = LocalSettings.crypt_secret_key

try:
    flask_port_set = int(sys.argv[1])
    print(' * 강제 포트 지정 설정됨 : {}'.format(flask_port_set))
except:
    flask_port_set = LocalSettings.flask_host_port

conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
curs = conn.cursor()

    #### == Assets Building == ####
bundles = {
    'main_js' : Bundle(
        'js/bootstrap.min.js',
        output = 'gen/main.js'
    ),

    'main_css' : Bundle(
        'css/minty.css',
        'css/custom.css',
        'css/oauth.css',
        'css/frontpage.css',
        output = 'gen/main.css'
    )
}

assets = Environment(app)
assets.register(bundles)

version = json.loads(open('version.json', encoding='utf-8').read())
fetea_ver = str(version['ver']) + '.' + str(version['rel'])
### === Initialize End === ###


### === Define Functions === ###
class parser:
    def anti_injection(content):
        content = content.replace('"', '""')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        return content

class sqlite3_control:
    def select(query, qlist):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.execute(query, qlist)
        result = curs.fetchall()
        conn.close()
        return result

    def commit(query, qlist):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.execute(query, qlist)
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
                <a class="nav-link dropdown-toggle" data-toggle="dropdown" href="#" id="download"><img src="%_user_display_profile_img_%" width="17px" height="17px"> %_user_display_name_% <span class="caret"></span></a>
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
            user_data = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
            user_auth_group = sqlite3_control.select('select * from user_acl_list_tb where account_id = ?', [session['now_login']])
            user_auth = sqlite3_control.select('select * from user_group_acl where user_group = ?', [user_auth_group[0][1]])
            ### Index End ###

            ### Render Navbar ###
            template = template.replace('%_user_display_name_%', user_data[0][3])
            if user_data[0][4] == None:
                template = template.replace('%_user_display_profile_img_%', '')
            else:
                template = template.replace('%_user_display_profile_img_%', user_data[0][4])
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
        user_auth_group = sqlite3_control.select('select * from user_acl_list_tb where account_id = ?', [target_id])
        user_auth = sqlite3_control.select('select * from user_group_acl where user_group = ?', [user_auth_group[0][1]])
        if user_auth[0][2] != 1 and user_auth[0][3] != 1:
            return False
        else:
            return True

    def user_controller(target_id):
        ## Index User Data ##
        user_data = sqlite3_control.select('select * from author_connect where peti_author_id = ?', [target_id])
        ## Index End ##

        if 'now_login' in session:
            if user_control.identify_user(session['now_login']) == False:
                return user_data[0][1]
        else:
            return user_data[0][1]

        if user_data[0][2] == 0:
            user_identify_badge = ' <span class="badge badge-pill badge-dark" data-toggle="tooltip" title="비로그인 청원 작성자는 명의를 확인할 수 없습니다.">명의</span>'.format(target_id)
        else:
            user_identify_badge = ' <a href="/admin/member/identify?user={}"><span class="badge badge-pill badge-info">명의</span></a>'.format(target_id)
        script = '<script>$(function () {$(\'[data-toggle="tooltip"]\').tooltip()})</script>'
        user_id_badge = ' <span class="badge badge-pill badge-success" data-toggle="tooltip" title="작성자 구분자: {}">{}</span>'.format(target_id, target_id)
        body_content = script + user_data[0][1] + user_id_badge + user_identify_badge
        return body_content
    
    def super_secret_settings(target_id):
        user_auth = sqlite3_control.select('select user_group_acl.site_owner from user_group_acl, user_acl_list_tb where user_acl_list_tb.account_id = ? and user_acl_list_tb.auth = user_group_acl.user_group', [target_id])[0][0]
        if user_auth == 1:
            return True
        else:
            return False
        
class config:
    def load_oauth_settings():
        oauth_native = open('oauthsettings.json', encoding='utf-8').read()
        oauth_json = json.loads(oauth_native)
        return oauth_json

    def load_verify_key(target, user_id):
        ### Check User Target's Authority ###
        user_auth_owner = sqlite3_control.select('select user_group_acl.site_owner from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = ? and user_group_acl.user_group = user_acl_list_tb.auth', [user_id])
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

    def recaptcha_existed():
        oauthsettings = json.loads(open('oauthsettings.json', encoding='utf-8').read())
        if oauthsettings['recaptcha_site_key'] == '' or oauthsettings['recaptcha_secret_key']:
            return False
        else:
            return True

class viewer:
    def load_petition(target_id):
        body_content = ''

        ### Load User Auth Data ###
        if 'now_login' in session:
            now_login = session['now_login']
            user_auth = sqlite3_control.select('select user_group_acl.site_administrator from user_group_acl, user_acl_list_tb where user_acl_list_tb.account_id = ? and user_acl_list_tb.auth = user_group_acl.user_group', [now_login])
            if user_auth[0][0] == 1:
                control_delete = ' <a href="/a/{}/delete/"><span class="badge badge-pill badge-danger">삭제</span></a>'.format(target_id)
                control_official_reply = ' <a href="/a/{}/official/"><span class="badge badge-pill badge-primary">답변</span></a>'.format(target_id)
                petition_control = '<p> 이 청원을... ' + control_delete + control_official_reply + '</p>'
            else:
                petition_control = ''
        else:
            petition_control = ''
        ### Load End ###

        ### Index Data from Database ###
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = ?', [target_id])
        react_data = sqlite3_control.select('select peti_react_tb.*, author_connect.account_user_id, author_connect.peti_author_display_name from peti_react_tb, author_connect where peti_react_tb.peti_id = ? and author_connect.peti_author_id = peti_react_tb.author_id and peti_react_tb.react_type = "default"', [target_id])
        author_nickname = sqlite3_control.select('select * from author_connect where peti_author_id = ?', [peti_data[0][4]])
        if peti_data[0][3] == 2:
            reply_official_data = sqlite3_control.select('select content from peti_react_tb where peti_id = ? and react_type = "official"', [target_id])
            reply_official_content = sqlite3_control.select('select * from static_page_tb where page_name = ?'.format, [reply_official_data[0][0]])
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
            if author_nickname[0][2] == react_data[i][5]:
                react_render_object = react_render_object.replace('%_article_react_author_display_name_%', str(react_data[i][6])+'   <span class="badge badge-pill badge-warning">작성자</span>')
            else:
                react_render_object = react_render_object.replace('%_article_react_author_display_name_%', str(react_data[i][6]))
            react_render_object = react_render_object.replace('%_article_react_body_content_%', react_data[i][4])
            react_body_content += react_render_object
        ### Render End ###

        ### Get Author Data ###
        author_data = sqlite3_control.select('select * from author_connect where peti_author_id = ?', [peti_data[0][4]])
        ### Get End ###

        ### 반응 중복 제거
        if 'now_login' in session:
            query_target = session['now_login']
        else:
            query_target = 0
        now_login = sqlite3_control.select('select * from author_connect where account_user_id = ? and target_article = ?', [query_target, target_id])
        if len(now_login) != 0:
            template = template.replace('%_react_author_display_name_%', now_login[0][1])
            template = template.replace('%_react_display_name_is_enabled_%', 'readonly')
        else:
            template = template.replace('%_react_author_display_name_%', '')
            template = template.replace('%_react_display_name_is_enabled_%', '')

        ### Render Template ###
        author_data_display = user_control.user_controller(author_data[0][0])
        template = template.replace('%_article_display_name_%', peti_data[0][1])
        template = template.replace('%_article_control_panel_%', petition_control)
        template = template.replace('%_article_publish_date_%', peti_data[0][2])
        template = template.replace('%_article_author_display_name_%', author_data_display)
        template = template.replace('%_article_body_content_%', peti_data[0][5])
        template = template.replace('%_article_react_count_%', str(len(react_data)))
        template = template.replace('%_article_reacts_%', react_body_content)

        #### Render Official Reply ####
        if peti_data[0][3] == 2:
            official_reply_content = '<p style="text-align: right; padding-bottom: 0; margin-bottom:0;">청원 답변</p><h4><a href="/static/'+reply_official_data[0][0]+'" data-toggle="tooltip" title="새 창으로 원문 보기" target="_blank">'+reply_official_content[0][1]+'</a></h4><b>사용자: '+reply_official_content[0][2]+' 마지막으로 수정 | '+reply_official_content[0][3]+'</b><hr>'+reply_official_content[0][4]
            template = template.replace('%_article_official_reply_%', official_reply_content)
        else:
            template = template.replace('%_article_official_reply_%', '')

        body_content += template
        ### Render End ###
        
        return body_content

    def load_sns_login_status(content):
        if 'now_login' in session:
            user_profile_data = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
            content = content.replace('%_sns_login_status_%', '로그인 됨: {}'.format(user_profile_data[0][3]))
        else:
            content = content.replace('%_sns_login_status_%', '비로그인 상태로 비공개 청원을 작성합니다. 또는 <a href="/login">로그인</a>.')
        return content

    def load_metatag():
        meta = """
        <meta name="description" content="%_desc_%>
        <meta name="keyword" content="%_keyword_%">
        <meta name="distribution" content="%_dist_%">
        <meta property="og:type" content="website">
        <meta property="og:url" content="url">
        <meta property="og:title" content="%_title_%">
        <meta property="og:description" content="%_desc_%">
        """
        meta = meta.replace('%_desc_%', LocalSettings.entree_appname + ', 청원페이지입니다.')
        meta = meta.replace('%_dist_%', LocalSettings.entree_appname)
        meta = meta.replace('%_title_%', LocalSettings.entree_appname)
        meta = meta.replace('%_keyword_%', LocalSettings.entree_appname + ' ' + '청원페이지 청원')
        return meta

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
                width: 70vw;
                background-color: white;
                border-radius: 10px;
                padding: 50px;
            }

            @media (max-width: 767px) {
                .bs-docs-section{
                width: 95vw;
                }
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
        user_data_sqlite = sqlite3_control.select('select account_id, sns_id, sns_type, user_display_name, user_display_profile_img from site_user_tb')
        json_code = '['
        for i in range(len(user_data_sqlite)):
            json_code += '{{account_id : "{}", sns_id : "{}", sns_type : "{}", user_display_name: "{}", user_display_profile_img : "{}" }}'.format(
                user_data_sqlite[i][0], user_data_sqlite[i][1], user_data_sqlite[i][2], user_data_sqlite[i][3], user_data_sqlite[i][4])
            if i != len(user_data_sqlite) - 1:
                json_code += ','
        json_code += ']'
        js_code = """
        <script>
            var target
            var user_data = %_user_data_list_%
            function revealResult() {
                target = parseInt(document.getElementById("search").value) - 1
                document.getElementById("result").innerHTML = "<h2>검색결과</h2><table class='table table-hover'><thead><tr><th scope='col'>ID</th><th>실명</th><th>고유 식별자</th><th>사용 SNS</th><th>확인</th></tr><tbody><td scope='row'>"+user_data[target]["account_id"]+"</td><td><img src="+user_data[target]["user_display_profile_img"]+" width='20' height='20' />  "+user_data[target]["user_display_name"]+"</td><td>"+user_data[target]["sns_id"]+"</td><td>"+user_data[target]["sns_type"]+"</td><td><a onClick='overlay_on()' class='btn btn-link' style='margin: 0; padding: 0'>확인</a></td></tbody></thead></table>"
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

    def render_var(content):
        content = content.replace('%_appname_%', LocalSettings.entree_appname)
        content = content.replace('%_now_%', str(datetime.today()))
        content = content.replace('%_fetea_ver_%', fetea_ver)
        return content

def register(callback_json, sns_type):
    account_data = sqlite3_control.select('select * from site_user_tb where sns_type = ? and sns_id = ?', [sns_type, callback_json['id']])
    if len(account_data) == 0: # 회원가입 절차
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, user_display_profile_img) values(?, ?, ?, ?)', [sns_type, callback_json['id'], callback_json['name'], callback_json['picture']])
        account_ids = sqlite3_control.select('select account_id from site_user_tb')
        if len(account_ids) == 1: # 소유자 권한 제공
            sqlite3_control.commit('insert into user_acl_list_tb values(?, "owner")', [len(account_ids)])
        else: # 유저 권한 제공
            sqlite3_control.commit('insert into user_acl_list_tb values(?, "user")', [len(account_ids)])
        session['now_login'] = len(account_ids)
    else:
        sqlite3_control.commit('update site_user_tb set user_display_name = ?, user_display_profile_img = ? where sns_id = ?', [callback_json['name'], callback_json['picture'], callback_json['id']])
        session['now_login'] = account_data[0][0]

super_secret_button = '<button type="submit" name="submit" class="btn btn-link" value="super_secret_button">Super Secret Button...</button>'
### === Define End === ###


### === Initialize Database === ###
try:
    sqlite3_control.select('select * from peti_data_tb limit 1')
except:
    database_query = open('tables/tables.sql', encoding='utf-8').read()
    sqlite3_control.executescript(database_query)
    database_query = open('tables/initialize.sql', encoding='utf-8').read()
    sqlite3_control.executescript(database_query)
### === Initialize End === ###


### === Flask Routes === ###
# ## flask: MainPage
@app.route('/', methods=['GET', 'POST'])
def flask_main():
    body_content = ''
    nav_bar = user_control.load_nav_bar()
    
    ### Load From Database ###
    static_data = sqlite3_control.select('select * from static_page_tb where page_name = "frontpage"')
    ### Load End ###
    
    body_content = static_data[0][4]
    body_content = viewer.render_var(body_content)

    return render_template('frontpage.html', appname = LocalSettings.entree_appname, nav_bar = nav_bar)

# ## flask: login
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

    oauth = config.load_oauth_settings()
    if oauth['naver_client_id'] == '' or oauth['naver_client_secret'] == '':
        naver_comment = '관리자가 이 기능을 비활성화 시켰습니다.'
    else:
        naver_comment = ''

    if oauth['facebook_client_id'] == '' or oauth['facebook_client_secret'] == '':
        facebook_comment = '관리자가 이 기능을 비활성화 시켰습니다.'
    else:
        facebook_comment = ''

    ## Render OAuth Buttons ##
    tooltip_script = """
<script>
$(document).ready(function(){
    $('[data-toggle="tooltip"]').tooltip(); 
});
</script>
    """
    oauth_supported = []
    oauth_content = '<div class="oauth-wrapper"><ul class="oauth-list">'
    oauth_settings = config.load_oauth_settings()
    if oauth_settings['facebook_client_id'] != '' or oauth_settings['facebook_client_secret'] != '':
        oauth_supported += ['facebook']
    if oauth_settings['naver_client_id'] != '' or oauth_settings['naver_client_secret'] != '':
        oauth_supported += ['naver']

    for i in range(len(oauth_supported)):
        if oauth_supported[i] == 'facebook':
            oauth_comment = 'Facebook으로 로그인'
        else:
            oauth_comment = '네이버 아이디로 로그인'
        oauth_content +=    '''
            <li>
                <a href="/login/{}/">
                    <div class="oauth-btn oauth-btn-{}">
                        <div class="oauth-btn-logo oauth-btn-{}"></div>
                        {}
                    </div>
                </a>
            </li>
            '''.format(
                oauth_supported[i], 
                oauth_supported[i], 
                oauth_supported[i], 
                oauth_comment
            )
    oauth_content += '</ul></div><hr><a href="/login/entree/">entree 계정으로 로그인</a>'    
    ## Render End ##
    body_content += '<p style="margin:0;">SNS 로그인 시 해당 SNS 서비스의 로그인 상태가 유지됩니다.</p><p>공용 컴퓨터에서 SNS 로그인을 사용하는 경우 시크릿 모드(Inprivate 모드)에서 로그인을 계속하십시오.</p>'
    body_content += oauth_content
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
    stand_json = {'id' : profile_result_json['response']['id'], 'name' : profile_result_json['response']['name'], 'picture' : profile_result_json['response']['profile_image']}
    register(stand_json, 'naver')
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

    stand_json = {'id': profile_result_json['id'], 'name': profile_result_json['name'], 'picture': profile_result_json['picture']['data']['url']}
    register(stand_json, 'facebook')
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
        user_data = sqlite3_control.select('select * from site_user_tb where sns_id = ?', [sns_id])
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

    body_content = body_content.replace('%_form_alerts_%', '')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Logout
@app.route('/logout/')
def flask_logout():
    body_content = ''
    session.pop('now_login', None)
    nav_bar = user_control.load_nav_bar()

    body_content += '<h1>로그아웃 완료</h1><p>{}에서 로그아웃되었습니다.</p><p>브라우저 캐시를 삭제하지 않으면 로그인한 것처럼 보일 수도 있음에 유의하세요.</p>'.format(LocalSettings.entree_appname)
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: register
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
        same_id_getter = sqlite3_control.select('select * from site_user_tb where sns_type = "entree" and sns_id = ?', [sns_id])
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
        sqlite3_control.commit('insert into site_user_tb (sns_type, sns_id, user_display_name, account_password_hash) values("entree", ?, ?, ?)', [sns_id, user_display_name, account_password_hash.decode()])
        same_id_getter = sqlite3_control.select('select * from site_user_tb where sns_type = "entree" and sns_id = "{}"'.format(sns_id))
        if same_id_getter[0][0] != 1:
            sqlite3_control.commit('insert into user_acl_list_tb values(?, "user")', [same_id_getter[0][0]])
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

# ## flask: Petition List
@app.route('/a/', methods=['GET', 'POST'])
def flask_a():
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Index Database ###
    if request.args.get('type') == 'done':
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_status = 2 order by peti_id desc')
        title_comment = '완료된 청원들'
    else:
        peti_data = sqlite3_control.select('select * from peti_data_tb order by peti_id desc')
        title_comment = '새로운 청원들'
    ### Index End ###

    ### Render Template ###
    body_content += '<h1>{}</h1><table class="table table-hover"><thead><tr><th scope="col">N</th><th scope="col">청원 제목</th></tr></thead><tbody>'.format(title_comment)
    for i in range(len(peti_data)):
        if peti_data[i][3] == 1:
            body_content += '<tr><th scope="row">{}</th><td><a>비공개 청원</a></td></tr>'.format(peti_data[i][0])
        elif peti_data[i][3] == 404:
            body_content += '<tr><th scope="row">{}</th><td><a>삭제된 청원</a></td></tr>'.format(peti_data[i][0])
        else:
            if peti_data[i][3] == 2:
                peti_title = peti_data[i][1] + '  <span class="badge badge-pill badge-success">처리 완료</span>'
            else:
                peti_title = peti_data[i][1]
            body_content += '<tr><th scope="row">{}</th><td><a href="/a/{}/">{}</a></td></tr>'.format(peti_data[i][0], peti_data[i][0], peti_title)
    body_content += '</tbody></table>'
    if len(peti_data) == 0:
        body_content += '<p style="margin-left: 20px;">청원이 없습니다.</p>'
    body_content += '<button onclick="window.location.href=\'write\'" class="btn btn-primary" value="publish">청원 등록</button>'
    ### Render End ###
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Petition Article
@app.route('/a/<article_id>/', methods=['GET', 'POST'])
def flask_a_article_id(article_id):
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    ### Load Petition Data ###
    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = ?', [article_id])

    if peti_data[0][3] == 1 or peti_data[0][3] == 404:
        abort(404)
    ### Load End ###

    if request.args.get('error') == 'no_login':
        pass ## return error


    ### Render Bodycontent ###
    body_content += viewer.load_metatag()
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
        content = parser.anti_injection(request.form['react_content'])
        author_display = parser.anti_injection(request.form['react_author_display_name'])
        if author_display == '':
            author_display = '익명 사용자'
        ### Collect End ###
        
        ### 반응 중복 제거
        now_login = sqlite3_control.select('select * from author_connect where account_user_id = ? and target_article = ?', [session['now_login'], article_id])
        if len(now_login) != 0:
            author_display = now_login[0][1]
            is_existed = True
        else:
            is_existed = False

        ### Save React Author Data ###
        if 'now_login' in session and is_existed == False:
            author_list_len = len(sqlite3_control.select('select * from author_connect'))
            sqlite3_control.commit('insert into author_connect (peti_author_display_name, account_user_id, target_article) values(?, ?, ?)', [author_display, session['now_login'], article_id])
            react_author_id = author_list_len + 1
        elif 'now_login' in session and is_existed == True:
            react_author_id = now_login[0][0]
        else:
            return redirect('?error=no_login')
        ### Save End ###

        ### Insert Data into Database ###
        sqlite3_control.commit('insert into peti_react_tb (peti_id, author_id, react_type, content) values(?, ?, "default", ?)', [peti_id, react_author_id, content])
        ### Insert End ###
        return redirect('/a/{}'.format(article_id))
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Petition Write
@app.route('/a/write/', methods=['GET', 'POST'])
def flask_a_write():
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    template = open('templates/a_write.html', encoding='utf-8').read()
    
    recaptcha_site_key = config.load_oauth_settings()['recaptcha_site_key']
    template = template.replace('%_recaptcha_site_key_%', recaptcha_site_key)

    ### Template Rendering ###
    if 'now_login' in session:
        user_profile_data = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
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

        ### reCaptcha Check ###
        if config.recaptcha_existed():
            recaptcha_response = request.form['g-recaptcha-response']
            recaptcha_secret_key = config.load_oauth_settings()['recaptcha_secret_key']
            url = 'https://www.google.com/recaptcha/api/siteverify?secret={}&response={}'.format(
                recaptcha_secret_key, recaptcha_response
            )
            recaptcha_check_json = json.loads(urllib.request.urlopen(url).read().decode('utf-8'))
            if recaptcha_check_json['success'] == False:
                return '오류! reCaptcha를 제대로 수행하세요.'

        ### Save Author Data ###
        if peti_status == 1:
            account_user_id = 0
        else:
            account_user_id = session['now_login']
        petition_list_len = len(sqlite3_control.select('select * from peti_data_tb')) + 1
        author_list_len = len(sqlite3_control.select('select * from author_connect'))
        sqlite3_control.commit('insert into author_connect (peti_author_display_name, account_user_id, target_article) values(?, ?, ?)', [peti_author_display_name, account_user_id, petition_list_len])
        peti_author_id = author_list_len + 1
        ### Save End ###

        ### Insert Data into Database ###
        sqlite3_control.commit('insert into peti_data_tb (peti_display_name, peti_publish_date, peti_status, peti_author_id, peti_body_content) values(?, ?, ?, ?, ?)', [peti_display_name, peti_publish_date, peti_status, peti_author_id, peti_body_content])
        ### Insert End ###

        return redirect('/a/')
    body_content += template
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Petition Delete
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
    user_profile = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
    body_content = body_content.replace('%_sns_login_status_%', '{} 연결됨: {}'.format(user_profile[0][1], user_profile[0][3]))
    body_content = body_content.replace('%_confirm_head_%', '청원 삭제')
    if user_control.super_secret_settings(session['now_login']) == True:
        body_content = body_content.replace('%_super_secret_button_%', super_secret_button)
    else:
        body_content = body_content.replace('%_super_secret_button_%', '')
    ### Render End ###
    
    if request.method == 'POST':
        ### Log Activity ###
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = ?', [article_id])
        activity_date = datetime.today()
        activity_object = '청원(<i>{}</i>)'.format(peti_data[0][1])
        activity_description = request.form['description']
        if user_control.super_secret_settings(session['now_login']) == True and request.form['submit'] == 'super_secret_button':
            pass
        else:
            sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values(?, ?, ?, ?, ?)', [
                session['now_login'],
                activity_object,
                '삭제',
                activity_description,
                activity_date
            ])
        ### Log End ###

        sqlite3_control.commit('update peti_data_tb set peti_status = 404 where peti_id = ?', [article_id])
        return redirect('/a/')
    body_content = body_content.replace('%_form_alerts_%', '')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Petition Official React
@app.route('/a/<article_id>/official/', methods=['GET', 'POST'])
def flask_a_article_id_official(article_id):
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    reply_template = """
<div class="bs-docs-section">
    <h1>청원 공식 답변</h1>
    <div class="bs-component">
        <form action="" accept-charset="utf-8" name="" method="post">
            <fieldset>
                <div class="form-group">
                    <div class="form-group">
                        %_sns_login_status_%
                    </div>
                </div>
            </fieldset>
            <div class="custom-control custom-checkbox">
                <input type="checkbox" class="custom-control-input" id="Check" required>
                <label class="custom-control-label" name="from_official_reply" for="Check">이 작업은 %_appname_%의 공식적인 입장입니다. <br>이후 수정하더라도 <a href="https://archive.is">archive.is</a>와 같은 웹사이트 기록 사이트에 아카이브되어 이전 답변을 확인할 수 있다는 것을 확인했습니다.</label>
            </div>
            <button type="submit" name="submit" class="btn btn-primary" value="publish">계속하기</button>
        </form>
    </div>
</div>
    """
    ### Render Login Status ###
    user_profile = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
    reply_template = reply_template.replace('%_sns_login_status_%', '{} 연결됨: {}'.format(user_profile[0][1], user_profile[0][3]))
    ### Render End ###

    reply_template = viewer.render_var(reply_template)
    body_content += reply_template

    if request.method == 'POST':
        return redirect('http://localhost:2500/admin/static/add?type=reply&target={}'.format(article_id))
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/a/<article_id>/complete/', methods=['GET', 'POST'])
def flask_a_article_id_complete(article_id):
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    body_content = ''
    nav_bar = user_control.load_nav_bar()

    template = open('templates/confirm.html', encoding='utf-8').read()
    body_content += template

    if user_control.super_secret_settings(session['now_login']) == True:
        body_content = body_content.replace('%_super_secret_button_%', super_secret_button)
    else:
        body_content = body_content.replace('%_super_secret_button_%', '')


    ### Render Login Status ###
    user_profile = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
    body_content = body_content.replace('%_sns_login_status_%', '{} 연결됨: {}'.format(user_profile[0][1], user_profile[0][3]))
    ### Render End ###
    
    if request.method == 'POST':
        ### Log Activity ###
        peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = ?', [article_id])
        activity_date = datetime.today()
        activity_object = '청원(<i>{}</i>)'.format(peti_data[0][1])
        activity_description = request.form['description']
        if user_control.super_secret_settings(session['now_login']) == True and request.form['submit'] == 'super_secret_button':
            pass
        else:
            sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values(?, ?, ?, ?, ?)', [
                session['now_login'],
                activity_object,
                '완료',
                activity_description,
                activity_date
            ])
        ### Log End ###

        sqlite3_control.commit('update peti_data_tb set peti_status = 2 where peti_id = ?', [article_id])
        return redirect('/a/')
    body_content = body_content.replace('%_form_alerts_%', '')
    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


# ## flask: Activity Log
@app.route('/log/')
def flask_log():        
    body_content = ''
    body_content += '<h1>투명성 보고서</h1>'

    ### Index Server Log ###
    log = sqlite3_control.select('select * from user_activity_log_tb order by log_id desc')
    ### Index End ###

    ### Render Log ###
    for i in range(len(log)):
        profile = sqlite3_control.select('select * from site_user_tb where account_id = ?', [log[i][1]])
        body_content += '<p>{}  {}(이)가 {}을(를) {}함 (사유: {})'.format(log[i][5], profile[0][3], log[i][2], log[i][3], log[i][4])
    ### Render End ###

    nav_bar = user_control.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Static Page Viewer
@app.route('/static/<title>')
def flask_static(title):    
    body_content = ''
    nav_bar = user_control.load_nav_bar()
    
    ### Load From Database ###
    static_data = sqlite3_control.select('select * from static_page_tb where page_name = ?', [title])
    if len(static_data) == 0:
        abort(404)
    ### Load End ###

    body_content += viewer.load_metatag()
    body_content += '<h2>'+static_data[0][1]+'</h2><b>사용자: '+static_data[0][2]+' 마지막으로 수정 | '+static_data[0][3]+'</b><hr>'+static_data[0][4]
    body_content = viewer.render_var(body_content)

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Notice Static Page
@app.route('/notice/')
def flask_notice():    
    body_content = ''
    nav_bar = user_control.load_nav_bar()
    
    ### Load From Database ###
    static_data = sqlite3_control.select('select * from static_page_tb where page_name = "notice"')
    print(static_data)
    ### Load End ###

    body_content += '<h2>'+static_data[0][1]+'</h2><b>사용자: '+static_data[0][2]+' 마지막으로 수정 | '+static_data[0][3]+'</b><hr>'+static_data[0][4]
    body_content = viewer.render_var(body_content)

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)


# ## flask: Admin Page
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

    body_content += '<h2>'+static_data[0][1]+'</h2><b>사용자: '+static_data[0][2]+' 마지막으로 수정 | '+static_data[0][3]+'</b><hr>'+static_data[0][4]
    body_content = viewer.render_var(body_content)

    nav_bar = user_control.load_nav_bar()

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-member
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

# ## flask: Admin-member-idnetify
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
    ### Review End ###

    ### Render
    form_template = open('templates/confirm.html', encoding="utf-8").read()
    form_rendered = form_template.replace('%_confirm_head_%', '작업 확인')
    form_rendered = form_rendered.replace('%_form_alerts_%', '<input type="hidden" id="target_id" name="target_id" value="{}">'.format(target_id))
    if user_control.super_secret_settings(session['now_login']):
        form_rendered = form_rendered.replace('%_super_secret_button_%', super_secret_button)
    else:
        form_rendered = form_rendered.replace('%_super_secret_button_%', '')
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
        if user_control.super_secret_settings(session['now_login']) == True and request.form['submit'] == 'super_secret_button':
            pass
        else:
            sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values(?, ?, ?, ?, ?)', [
            session['now_login'],
            '닉네임 ' + target_data_sqlite[0][5],
            '명의를 확인',
            activity_description,
            activity_date
            ])

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

# ## flask: Admin-admins
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

# ## flask: Admin-(add admins)
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
            return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = '<h1>!!</h1><h2>이 작업을 수행하기 위해 필요한 데이터가 충족되지 않았습니다.</h2><p>이전으로 돌아가 다시 시도하세요.</p>', nav_bar = nav_bar)
        target_user_data = sqlite3_control.select('select user_display_name from site_user_tb where account_id = ?', [activity_object])
        activity_date = datetime.today()
        sqlite3_control.commit('insert into user_activity_log_tb (account_id, activity_object, activity, activity_description, activity_date) values(?, ?, ?, ?, ?)', [
        session['now_login'],
        '사용자 ' + target_user_data[0][0],
        '관리자로 등록',
        activity_description,
        activity_date
        ])
        user_auth_owner = sqlite3_control.select('select user_group_acl.site_owner from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = ? and user_group_acl.user_group = user_acl_list_tb.auth', [activity_object])
        if user_auth_owner[0][0] == 0:
            sqlite3_control.commit('update user_acl_list_tb set auth="administrator" where account_id = ?', [activity_object])
        return redirect('/admin/admins/')
    
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-ACL Settings
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
        acl_data = sqlite3_control.select('select user_acl_list_tb.auth, user_group_acl.manage_acl from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = ? and user_acl_list_tb.auth = user_group_acl.user_group', [session['now_login']])
        if acl_data[0][1] == 1:
            pass
        else:
            return redirect('/error/acl/')
        
        #### 2: acl priority ####
        acl_pri_user = sqlite3_control.select('select user_group_acl.group_priority from user_acl_list_tb, user_group_acl where user_acl_list_tb.account_id = ? and user_acl_list_tb.auth = user_group_acl.user_group', [session['now_login']])
        acl_pri_target = sqlite3_control.select('select group_priority from user_group_acl where user_group = ?', [acl_group])
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
        
        sqlite3_control.commit('update user_group_acl set group_priority = ?, site_owner = ?, site_administrator = ?, peti_read = ?, peti_write = ?, peti_react = ?, peti_disable = ?, peti_delete = ?, user_identify = ?, user_block = ?, manage_user = ?, manage_acl = ?, manage_static_page = ?, manage_notion = ?, not_display_log = ? where user_group = ?', [
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
        ])
        return redirect('/admin/acl/')
    ### Confirm End ###

    body_content += table_container
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-verify_key
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
      <input type="text" class="form-control" id="verify_key_value" value="%_verify_key_value_%" disabled>
    </div>
  </div>
</div>
    """
    ###
    body_content += verify_key_template.replace('%_verify_key_value_%', verify_key)
    body_content += '<p>verify_key는 1회 사용시 갱신됩니다.</p>'
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-Update
@app.route('/admin/update/')
def flask_admin_update():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')

    nav_bar = user_control.load_nav_bar()

    body_content = '<h1>업데이트 확인</h1><p>fetea의 업데이트 파일을 확인합니다.</p><hr>'

    local_stable = json.loads(open('version.json', encoding='utf-8').read())
    
    try:
        github_stable = json.loads(urllib.request.urlopen('https://raw.githubusercontent.com/kpjhg0124/PetitionApplication-py/master/version.json').read().decode('utf-8'))
        done = True
    except:
        body_content += '업데이트 확인 작업 중 문제가 발생했습니다. 나중에 다시 시도하세요.'
        done = False
        github_stable = {'ver' : 0, 'rel' : 0}

    latest = '<i class="fas fa-check"></i> fetea가 최신버전입니다. 업데이트가 필요하지 않습니다.'
    old = '<i class="fas fa-download"></i> fetea의 최신버전이 발견되었습니다. <a href="https://github.com/kpjhg0124/PetitionApplication-py/releases">Github 릴리즈 페이지</a>에서 최신 릴리즈를 받아 업데이트하세요.'

    if local_stable['ver'] < github_stable['ver'] and done == True:
        body_content += old
    elif local_stable['rel'] < github_stable['rel'] and done == True:
        body_content += old
    elif done == True:
        body_content += latest

    body_content += '<hr><h4>fetea 버전</h4><p>현재: {}. {}번째 추가 릴리즈<br>최신: {}. {}번째 추가 릴리즈</p>'.format(local_stable['ver'], local_stable['rel'], github_stable['ver'], github_stable['rel'])
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-Petition Manage
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

    peti_data = sqlite3_control.select('select * from peti_data_tb where peti_id = ?', [article_id])
    template = open('templates/a.html', encoding='utf-8').read()

    ### Render Bodycontent ###
    body_content += viewer.load_metatag()
    body_content += viewer.load_petition(article_id)
    if 'now_login' in session:
        body_content = body_content.replace('%_enabled_content_%', '')
    else:
        body_content = body_content.replace('%_is_enabled_%', 'disabled')
        body_content = body_content.replace('%_enabled_content_%', '비로그인 상태에서는 청원 반응이 불가능합니다.')

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Admin-Manage Static Page
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
        pill_body_object = '<li class="nav-item"><a class="nav-link %_is_active_%" href="?page={}">{}({})</a></li>'.format(static_page[i][0], static_page[i][1], static_page[i][0])
        if request.method == 'GET':
            if request.args.get('page') == static_page[i][0]:
                pill_body_object = pill_body_object.replace('%_is_active_%', 'active')
        pill_body_content += pill_body_object
    pill_body_content += '<li class="nav-item"><a class="nav-link" href="/admin/static/add/">(추가)</a></li>'
    template = template.replace('%_pill_body_content_%', pill_body_content)
    body_content += template
    ### End Render ###

    ### Render Ststic Page Editor ###
    if request.args.get('page') != None:
        target = request.args.get('page')
        target_content = sqlite3_control.select('select * from static_page_tb where page_name = ?', [target])
        if len(target_content) == 0:
            abort(404)
        textarea = """
        <div class="bs-docs-section">
            <form action="" accept-charset="utf-8" method="post">
                <textarea class="form-control" name="content" rows="3" placeholder="html 코드로 작성합니다.">%_textarea_content_%</textarea>
                <button type="submit" name="submit" class="btn btn-primary" value="publish">업데이트</button>
            </form>
        </div>
        """
        textarea = textarea.replace('%_textarea_content_%', target_content[0][4])
        body_content += textarea
    ### End Render ###

    if request.method == 'POST':
        ### Update Static Page Data ###
        user_name = sqlite3_control.select('select user_display_name from site_user_tb where account_id = ?', [session['now_login']])
        received_content = request.form['content'].replace('"', '""')
        sqlite3_control.commit('update static_page_tb set editor = ?, editdate = ?, content = ? where page_name = ?',[
            parser.anti_injection(user_name[0][0]), 
            parser.anti_injection(str(datetime.today())), 
            received_content, 
            parser.anti_injection(request.args.get('page'))
        ]) # issue 27 작업 여기까지 끝냄. (수정)
        ### End Update ###
        return redirect('/admin/static/?page={}'.format(request.args.get('page')))

    nav_bar = user_control.load_nav_bar()

    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

@app.route('/admin/static/add/', methods=['GET', 'POST'])
def flask_admin_static_add():
    if 'now_login' in session:
        if user_control.identify_user(session['now_login']) == False:
            return redirect('/error/acl')
    else:
        return redirect('/error/acl/')
        
    body_content = ''
    nav_bar = user_control.load_nav_bar()

    template = """
<div class="bs-docs-section">
    <h1>정적 페이지 추가 %_additional_%</h1>
    <div class="bs-component">
        <form action="" accept-charset="utf-8" name="" method="post">
            <fieldset>
                %_form_alerts_%
                <div class="form-group">
                    <div class="form-group">
                        <input type="text" class="form-control" id="title_slug" name="title_slug" placeholder="설정할 링크(슬러그)" onChange="changeAlert()" style="width: 70vw;" value="%_slug_value_%" required %_canwrite_%>
                    </div>
                    <div class="form-group">
                        <input type="text" class="form-control" name="title_display_name" placeholder="표시할 이름" style="width: 70vw;" required>
                    </div>
                    <p id="slug_result">%_slug_result_%</p>
                    <textarea class="form-control" name="body_content" rows="20" placeholder="html 코드로 작성합니다." required></textarea>
                </div>
            </fieldset>
            <button type="submit" name="submit" class="btn btn-primary" value="publish">추가</button>
        </form>
    </div>
</div>
    """
    js_code ="""
    <script>
        function changeAlert() {
            var slug = document.getElementById("title_slug").value
            document.getElementById("slug_result").innerHTML = "이 페이지의 링크는 <a href='/static/"+slug+"'>%_publish_host_name_%/static/"+slug+"</a>가 될 것입니다.";
        }
    </script>
    """

    body_content += js_code + template
    ### Petition Official Reply ###
    if request.args.get('type') == 'reply':
        try:
            target = int(request.args.get('target'))
            body_content = body_content.replace('%_additional_%', '( <a href="/a/{}">{}번 청원</a> 답변 )'.format(target, target))
            body_content = body_content.replace('%_slug_value_%', 'a-reply-{}'.format(target))
            body_content = body_content.replace('%_canwrite_%', 'readonly')
            body_content = body_content.replace('%_slug_result_%', '이 페이지의 링크는 <a href="/static/a-reply-{}">%_publish_host_name_%/static/a-reply-{}</a>가 될 것입니다.'.format(target, target))
        except:
            return redirect('/admin/static/add?error=reply_target_not_int')
    else:
        body_content = body_content.replace('%_additional_%', '')
        body_content = body_content.replace('%_slug_value_%', '')
        body_content = body_content.replace('%_canwrite_%', '')
        body_content = body_content.replace('%_slug_result_%', '이 페이지의 링크가 설정되지 않았습니다.')

    ### error handler ###
    if request.args.get('error') != None:
        if request.args.get('error') == 'reply_target_not_int':
            error_msg = """
            <div class="alert alert-dismissible alert-warning">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <h4 class="alert-heading">오류!</h4>
                <p class="mb-0">청원 답변 기능 사용에 필요한 모든 정보가 수집되지 않았습니다.</p>
                <p class="mb-0">이전으로 되돌아가 다시 시도해 보세요. 만약 이 현상이 계속된다면 <a href="https://github.com/kpjhg0124/PetitionApplication-py/issues"><i class="fas fa-link"></i>   이곳</a>에 문제를 신고할 수 있습니다.</p>
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', error_msg)
        if request.args.get('error') == 'already_existed':
            error_msg = """
            <div class="alert alert-dismissible alert-warning">
                <button type="button" class="close" data-dismiss="alert">&times;</button>
                <h4 class="alert-heading">오류!</h4>
                <p class="mb-0">이미 해당 슬러그는 다른 정적 페이지가 사용하고 있습니다..</p>
                <p class="mb-0">이전으로 되돌아가 슬러그를 수정해 다시 시도해 보세요.</p>
            </div>
            """
            body_content = body_content.replace('%_form_alerts_%', error_msg)
    else:
        body_content = body_content.replace('%_form_alerts_%', '')
    
    body_content = body_content.replace('%_publish_host_name_%', LocalSettings.publish_host_name)

    if request.method == 'POST':
        ### Get POST Data ###
        static_slug =  parser.anti_injection(request.form['title_slug'])
        static_display_name =  parser.anti_injection(request.form['title_display_name'])
        static_body_content = request.form['body_content'].replace('"', '""')
        
        target = 0
        if request.args.get('type') == 'reply':
            try:
                target = int(request.args.get('target'))
                static_slug = 'a-reply-{}'.format(target)
            except:
                return redirect('/admin/static/add?error=reply_target_not_int')

        ### Get End ###
        search = sqlite3_control.select('select * from static_page_tb where page_name = ?', [static_slug])
        user_name = sqlite3_control.select('select user_display_name from site_user_tb where account_id = ?', [session['now_login']])
        if len(search) != 0:
            return redirect('/admin/static/add?error=already_existed')
        sqlite3_control.commit('insert into static_page_tb (page_name, title, editor, editdate, content) values(?, ?, ?, ?, ?)', [
            static_slug, static_display_name, parser.anti_injection(user_name[0][0]), parser.anti_injection(str(datetime.today())), parser.anti_injection(static_body_content)
        ])
        if target > 0:
            sqlite3_control.commit('insert into peti_react_tb (peti_id, author_id, react_type, content) values(?, 0, "official", ?)', [target, static_slug])
            sqlite3_control.commit('update peti_data_tb set peti_status = 2 where peti_id = ?', [target])

        return redirect('/admin/static?page={}'.format(static_slug))
    return render_template('admin.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

# ## flask: Assets Route
@app.route('/assets/<assets>/')
def serve_pictures(assets):
    return send_from_directory('assets', assets)

@app.route('/robots.txt')
def robots():
    robots = """
User-agent: *
Disallow: /admin
Disallow: /login
Disallow: /logout
Disallow: /register
    """
    return robots

# ## flask: Ajax Route
@app.route('/ajax/a/', methods=['GET', 'POST'])
def flask_ajax_a():
    request_lower_num = request.args.get('request-s')
    request_higher_num = request.args.get('request-e')
    request_type = request.args.get('type') # done / all
    if request_lower_num == None or request_higher_num == None or request_type == None:
        return 'unexpected request.'
    if request_type == 'done':
        additional_query = 'peti_status = 2 and'
    else:
        additional_query = ''
    peti_data = sqlite3_control.select('select * from peti_data_tb where ? peti_id >= ? and peti_id <= ? order by peti_id desc', [
        additional_query, request_lower_num, request_higher_num
    ])
    return_json = []
    for i in range(len(peti_data)):
        if peti_data[i][3] == 1:
            return_json += [{"peti_id" : peti_data[i][0], "peti_display" : "비공개 청원", "peti_status" : peti_data[i][3]}]
        elif peti_data[i][3] == 404:
            return_json += [{"peti_id" : peti_data[i][0], "peti_display" : "삭제된 청원", "peti_status" : peti_data[i][3]}]
        else:
            return_json += [{"peti_id" : peti_data[i][0], "peti_display" : peti_data[i][1], "peti_status" : peti_data[i][3]}]
    return str(return_json)

# ## flask: Error Handler
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
@app.errorhandler(500)
def error_500(self):
    body_content = '<h1>Oops!</h1><h2>500 Internal Server Error</h2><p>서버 내부에 오류가 발생했습니다.</p><p><a href="https://github.com/kpjhg0124/PetitionApplication-py/issues">Github의 fetea 이슈 트래커</a>에 버그 상황을 자세히 남겨주시면 바로 조치하겠습니다.</p>'
    nav_bar = user_control.load_nav_bar()

    return render_template('index.html', appname = LocalSettings.entree_appname, body_content = body_content, nav_bar = nav_bar)

### === Application Run === ###
app.run(LocalSettings.flask_host, flask_port_set, debug = LocalSettings.flask_debug_mode)
