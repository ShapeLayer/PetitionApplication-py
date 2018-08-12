##############################  LocalSettings.py  ##############################
####################### OFORM Flask Web App Config File #######################

# SQLITE3_FILENAME must be in string format.
SQLITE3_FILENAME = 'db.db'
# SQLITE3_NO_DB_IGNORE must be in string format. Possible values are 'error_page' or 'ignore'.
SQLITE3_NO_DB_IGNORE = 'error_page'

# FLASK_HOST must be in string format.
FLASK_HOST = 'localhost'
# FLASK_HOST must be in integer format.
FLASK_HOST_PORT = 2500

# CRYPT_SECRET_KEY must be in string format.
CRYPT_SECRET_KEY = 'SECRET_KEY'

# OFORM_APPNAME must be in string format.
OFORM_APPNAME = 'OFORM'
# OFORM_LANGUAGE must be in string format.
OFORM_LANGUAGE = 'ko-KR'
# OFORM_DEVICE_TYPE must be in string format.
OFORM_DEVICE_TYPE = '<OFORM_DEVICE_TYPE>'
# OFORM_GETHOST must be in string format.
OFORM_GETHOST = 'https://github.com/kpjhg0124/minty'
# OFORM_LICENSE_AGREE must be in bool format.
OFORM_LICENSE_AGREE = 'True'

# If OFORM_DEVICE_TYPE's value is 'client':
# OFORM_CLIENT_HOST must be in string format.
OFORM_CLIENT_HOST = '192.168.55.176:5000'
# OFORM_CLIENT_HOST_SECRET_KEY must be in string format.
OFORM_CLIENT_HOST_SECRET_KEY = 'SECRET_KEY'
