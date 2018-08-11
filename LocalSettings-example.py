##############################  LocalSettings.py  ##############################
####################### ENTREE Flask Web App Config File #######################

# SQLITE3_FILENAME must be in string format.
SQLITE3_FILENAME = 'db.db' 
# SQLITE3_NO_DB_IGNORE must be in string format. Possible values are 'error_page' or 'ignore'.
SQLITE3_NO_DB_IGNORE = 'error_page'

# FLASK_HOST must be in string format.
FLASK_HOST = 'localhost'
# FLASK_HOST must be in integer format.
FLASK_HOST_PORT = 5000

# CRYPT_SECRET_KEY must be in string format.
CRYPT_SECRET_KEY = 'This is a secret key.'

# ENTREE_APPNAME must be in string format.
ENTREE_APPNAME = 'ENTREE'
# ENTREE_LANGUAGE must be in string format.
ENTREE_LANGUAGE = 'ko-KR'
# ENTREE_DEVICE_TYPE must be in string format.
ENTREE_DEVICE_TYPE = 'host'
# ENTREE_GETHOST must be in string format.
ENTREE_GETHOST = 'https://github.com/kpjhg0124/entree'
# ENTREE_LICENSE_AGREE must be in bool format.
ENTREE_LICENSE_AGREE = True

# If ENTREE_DEVICE_TYPE's value is 'client':
# ENTREE_CLIENT_HOST must be in string format.
ENTREE_CLIENT_HOST = '192.168.55.176:5000'
# ENTREE_CLIENT_HOST_SECRET_KEY must be in string format.
ENTREE_CLIENT_HOST_SECRET_KEY = 'This is a secret key'
