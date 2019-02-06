# coding=utf-8
from flask import Flask, session
import sqlite3
import json
from datetime import datetime
import random
import urllib.parse, urllib.request

import LocalSettings
import variable.app_variables as vs

conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
curs = conn.cursor()

version = json.loads(open('version.json', encoding='utf-8').read())
fetea_ver = str(version['ver']) + '.' + str(version['rel'])

### === Define Functions === ###
class parser:
    def anti_injection(content):
        content = content.replace('"', '""')
        content = content.replace('<', '&lt;')
        content = content.replace('>', '&gt;')
        return content

class sqlite3_control:
    def select(query, qlist = []):
        conn = sqlite3.connect(LocalSettings.sqlite3_filename, check_same_thread = False)
        curs = conn.cursor()
        curs.execute(query, qlist)
        result = curs.fetchall()
        conn.close()
        return result

    def commit(query, qlist = []):
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
            template = template.replace('%_user_display_profile_img_%', 'http://www.gravatar.com/avatar/?d=identicon')
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

    def load_acl(acl_target):
        if 'now_login' in session:
            acl = sqlite3_control.select('select user_group_acl.{} from user_group_acl, user_acl_list_tb where user_acl_list_tb.auth = user_group_acl.user_group and user_acl_list_tb.account_id = ?'.format(acl_target), [session['now_login']])[0][0]
            if acl == 0:
                return False
            else:
                return True
        else:
            acl = sqlite3_control.select('select {} from user_group_acl where user_group = "not_signed_in"'.format(acl_target))[0][0]
            if acl == 0:
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
        if oauthsettings['recaptcha_site_key'] == '' or oauthsettings['recaptcha_secret_key'] == '':
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
        if sqlite3_control.select('select data from server_set where name = "petition_react_disabled"')[0][0] == '0':
            react_data = sqlite3_control.select('select peti_react_tb.*, author_connect.account_user_id, author_connect.peti_author_display_name from peti_react_tb, author_connect where peti_react_tb.peti_id = ? and author_connect.peti_author_id = peti_react_tb.author_id and peti_react_tb.react_type = "default"', [target_id])
        author_nickname = sqlite3_control.select('select * from author_connect where peti_author_id = ?', [peti_data[0][4]])
        if peti_data[0][3] == 2:
            reply_official_data = sqlite3_control.select('select content from peti_react_tb where peti_id = ? and react_type = "official"', [target_id])
            if len(reply_official_data) != 0:
                reply_official_content = sqlite3_control.select('select * from static_page_tb where page_name = ?', [reply_official_data[0][0]])
            else:
                reply_official_content = ''
        ### Index End ###

        ### Load Template ###
        template = open('templates/a.html', encoding='utf-8').read()
        ### Load End ###

        if sqlite3_control.select('select data from server_set where name = "petition_react_disabled"')[0][0] == '0':
            template = template.replace('%_react_body_%',
            '''
            <div class="bs-component">
                <form action="" accept-charset="utf-8" name="form_write" method="post">
                    <h3 id="progress-animated">청원 반응</h3>
                    <p> %_article_react_count_% 개 반응</p>
                    <input type="text" class="form-control" name="react_author_display_name" placeholder="이름" style="margin-bottom: 5px;" value="%_react_author_display_name_%" %_react_display_name_is_enabled_%>
                    <textarea class="form-control" id="react_content" name="react_content" rows="3" style="resize: none;" required></textarea>
                    <button type="submit" name="submit" class="btn btn-primary" value="publish" %_is_enabled_%>청원 반응하기</button>
                </form>
                <div class="bs-component article-margin">
                    %_article_reacts_%
                </div>
            </div>
            ''')
        else:
            template = template.replace('%_react_body_%', '')
        ### Render React ###
        if sqlite3_control.select('select data from server_set where name = "petition_react_disabled"')[0][0] == '0':
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

        ### Get Share Button ###
        oauth_settings = config.load_oauth_settings()
        share_render = ''
        now_settings = {}
        if oauth_settings['facebook_client_id'] != '':
            now_settings['facebook_share_enabled'] = sqlite3_control.select('select data from server_set where name = "facebook_share_enabled"')[0][0]
            if now_settings['facebook_share_enabled'] == '1':
                fb_url = 'https://www.facebook.com/sharer/sharer.php?u=' + urllib.parse.quote(LocalSettings.publish_host_name + '/a/' + target_id)
                share_render += ' <a href="{}"><span class="badge badge-pill badge-facebook"><i class="fab fa-facebook-f"></i> Facebook으로 공유</span></a>'.format(fb_url)
        ### Get End ###

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
        author_data_display = user_control.user_controller(author_data[0][0]) + share_render
        template = template.replace('%_article_display_name_%', peti_data[0][1])
        template = template.replace('%_article_control_panel_%', petition_control)
        template = template.replace('%_article_publish_date_%', peti_data[0][2])
        template = template.replace('%_article_author_display_name_%', author_data_display)
        template = template.replace('%_article_body_content_%', peti_data[0][5])
        if sqlite3_control.select('select data from server_set where name = "petition_react_disabled"')[0][0] == '0':
            template = template.replace('%_article_react_count_%', str(len(react_data)))
            template = template.replace('%_article_reacts_%', react_body_content)
        else:
            template = template.replace('%_article_react_count_%', '')
            template = template.replace('%_article_reacts_%', '')

        #### Render Official Reply ####
        if peti_data[0][3] == 2 and len(reply_official_data) != 0:
            official_reply_content = '<p style="text-align: right; padding-bottom: 0; margin-bottom:0;">청원 답변</p><h4><a href="/static/'+reply_official_data[0][0]+'" data-toggle="tooltip" title="새 창으로 원문 보기" target="_blank">'+reply_official_content[0][1]+'</a></h4><b>사용자: '+reply_official_content[0][2]+' 마지막으로 수정 | '+reply_official_content[0][3]+'</b><hr>'+reply_official_content[0][4]
            template = template.replace('%_article_official_reply_%', '<div class="bs-component bs-official-reply"><p>' + official_reply_content + '</p></div>')
        else:
            template = template.replace('%_article_official_reply_%', '')

        body_content += template
        ### Render End ###
        
        return body_content

    def load_sns_login_status():
        if 'now_login' in session:
            user_profile_data = sqlite3_control.select('select * from site_user_tb where account_id = ?', [session['now_login']])
            return '<label for="peti_author_display_name">로그인 됨: {}</label>'.format(user_profile_data[0][3])
        else:
            return '<label for="peti_author_display_name">비로그인 상태로 비공개 청원을 작성합니다. 또는 <a href="/login">로그인</a>.</label>'

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

    def render_var(content, target_page = None, title = None):
        if target_page:
            content = content.replace('%_url_%', LocalSettings.publish_host_name + target_page)
        if title:
            content = content.replace('%_page_title_%', title)
        else:
            content = content.replace('%_page_title_%', '')
        content = content.replace('%_appname_%', LocalSettings.entree_appname)
        content = content.replace('%_now_%', str(datetime.today()))
        content = content.replace('%_fetea_ver_%', fetea_ver)
        static = json.loads(open('variable/str_variables.json', encoding='utf-8').read())
        keys = list(static.keys())
        for i in range(len(static)):
            if i == 0:
                pass
            else:
                content = content.replace(keys[i], static[keys[i]])
        return content

    def render_err(code):
        if code not in vs.err:
            code = 'err_code_not_found'
        render = '<h1>{head}</h1><h2>{code}</h2><p>{body}</p>'.format(head = vs.err[code]['head'], code = vs.err[code]['code'], body = vs.err[code]['body'])
        return render

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

def load_header():
    now_header = []
    now_header += [sqlite3_control.select('select data from server_set where name="custom_header_top"')[0][0]]
    now_header += [sqlite3_control.select('select data from server_set where name="custom_header_bottom"')[0][0]]
    return now_header
### === Define End === ###
