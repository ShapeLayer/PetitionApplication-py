## Import Python Modules ##
import random
from flask import Flask, redirect, url_for, request, render_template
from flask_assets import Bundle, Environment
import json

app = Flask(__name__)
verifiation_code = ''

## Assets Bundling ##

bundles = {
    'main_js' : Bundle(
        'js/bootstrap.min.js',
        output = 'gen/main.js'
    ),

    'main_css' : Bundle(
        'css/Litera.css',
        'css/custom.css',
        output = 'gen/main.css'
    )
}

assets = Environment(app)
assets.register(bundles)



## LOAD CONVERSTATIONS ##
CONVERSTATIONS_NATIVE = open('dic.json', encoding='utf-8').read()
CONVERSTATIONS_DICT = json.loads(CONVERSTATIONS_NATIVE)



## http://flask.pocoo.org/snippets/67/ ##
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()



## Flask Route ##
### Route: mainT ###
@app.route('/', methods=['GET', 'POST'])
def main():
    if request.method == 'POST': 
        post_verify = request.form['verifiation-code']
        SQLITE3_FILENAME = request.form['database-filename']
        FLASK_HOST_PORT = request.form['flask-host-port']
        CRYPT_SECRET_KEY = request.form['crypt-secret-key']
        if post_verify == verifiation_code:
            LocalSettingsValue = open('LocalSettings-template.py').read()
            LocalSettingsValue = LocalSettingsValue.replace('<SQLITE3_FILENAME>', SQLITE3_FILENAME)
            LocalSettingsValue = LocalSettingsValue.replace('<SQLITE3_NO_DB_IGNORE>', 'error_page')
            LocalSettingsValue = LocalSettingsValue.replace('<FLASK_HOST>', 'localhost')
            LocalSettingsValue = LocalSettingsValue.replace('<FLASK_HOST_PORT>', FLASK_HOST_PORT)
            LocalSettingsValue = LocalSettingsValue.replace('<CRYPT_SECRET_KEY>', CRYPT_SECRET_KEY)
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_APPNAME>', 'ENTREE')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_LANGUAGE>', 'ko-KR')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_ENTREE_DEVICE_TYPE>', 'host')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_GETHOST>', 'https://github.com/kpjhg0124/entree')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_LICENSE_AGREE>', 'True')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_HOST_PUBLISH>', 'local')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_CLIENT_HOST>', '192.168.55.176:5000')
            LocalSettingsValue = LocalSettingsValue.replace('<ENTREE_CLIENT_HOST_SECRET_KEY>', CRYPT_SECRET_KEY)
            with open('LocalSettings.py', 'w') as f:
                f.write(LocalSettingsValue)
            shutdown_server()
            return ''
        else:
            shutdown_server()
        return ''
    else:
        BODY_CONTENT = CONVERSTATIONS_DICT['INSTALLATION']
        return render_template('form.html', ENTREE_APPNAME = 'ENTREE', ENTREE_CONTENT = BODY_CONTENT)



## Start ##
def start(FLASK_PORT_SET):
    global verifiation_code
    verifiation_code = str(random.random())[2:8]
    print(' * http://localhost:' + str(FLASK_PORT_SET) + ' 에 접속하여 설정을 진행해 주십시오.')
    print(' * 소유자 증명 코드는  ' + verifiation_code + '  입니다.')
    app.run('localhost', FLASK_PORT_SET, debug = True)