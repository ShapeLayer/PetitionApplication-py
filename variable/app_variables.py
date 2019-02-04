'''
fetea Global Variable File
app_variables.py

uses as 'vs'
'''

publish_option_name = ['공개', '비공개', '답변 완료', '삭제된 것으로 표시']

robots = """
User-agent: *
Disallow: /a/write
Disallow: /admin
Disallow: /admin/*
Disallow: /login
Disallow: /logout
Disallow: /register
"""

dynamic_var = ['%_url_%', '%_page_title_%', '%_appname_%', '%_now_%', '%_fetea_ver_%']

err = {
    'no_data_required' : {
        'code' : 'no_data_required',
        'head' : '이 작업을 수행하는데 필요한 데이터가 전송되지 않았습니다!',
        'body' : '이 작업을 수행하는데 필요한 데이터가 전송되지 않았습니다. 일시적인 문제일 확률이 높습니다. 다시 시도하세요.'
    },
    'err_code_not_found' : {
        'code' : 'err_code_not_found',
        'head' : '알수 없는 오류!',
        'body' : '기록된 오류가 아닙니다! 일시적인 문제일 확률이 높습니다. 다시 시도하세요.'
    }
}