import LocalSettings

def Request_LocalSettings():
    ENTREE_SETTINGS = {
        'SETTINGS_0' : {
            'NAME' : 'SQLITE3_FILENAME',
            'VALUE' : LocalSettings.SQLITE3_FILENAME,
            'EDITABLE' : True
        },
        'SETTINGS_1' : {
            'NAME' : 'SQLITE3_NO_DB_IGNORE',
            'VALUE' : LocalSettings.SQLITE3_NO_DB_IGNORE,
            'EDITABLE' : False
        },
        'SETTINGS_2' : {
            'NAME' : 'FLASK_HOST',
            'VALUE' : LocalSettings.FLASK_HOST,
            'EDITABLE' : False
        },
        'SETTINGS_3' : {
            'NAME' : 'FLASK_HOST_PORT',
            'VALUE' : LocalSettings.FLASK_HOST_PORT,
            'EDITABLE' : True
        },
        'SETTINGS_4' : {
            'NAME' : 'CRYPT_SECRET_KEY',
            'VALUE' : LocalSettings.CRYPT_SECRET_KEY,
            'EDITABLE' : True
        },
        'SETTINGS_5' : {
            'NAME' : 'ENTREE_APPNAME',
            'VALUE' : LocalSettings.ENTREE_APPNAME,
            'EDITABLE' : False
        },
        'SETTINGS_6' : {
            'NAME' : 'ENTREE_LANGUAGE',
            'VALUE' : LocalSettings.ENTREE_LANGUAGE,
            'EDITABLE' : False
        },
        'SETTINGS_7' : {
            'NAME' : 'ENTREE_ENTREE_DEVICE_TYPE',
            'VALUE' : LocalSettings.ENTREE_DEVICE_TYPE,
            'EDITABLE' : False
        },
        'SETTINGS_8' : {
            'NAME' : 'ENTREE_GETHOST',
            'VALUE' : LocalSettings.ENTREE_GETHOST,
            'EDITABLE' : False
        },
        'SETTINGS_9' : {
            'NAME' : 'ENTREE_LICENSE_AGREE',
            'VALUE' : LocalSettings.ENTREE_LICENSE_AGREE,
            'EDITABLE' : False
        },
        'SETTINGS_10' : {
            'NAME' : 'ENTREE_CLIENT_HOST',
            'VALUE' : LocalSettings.ENTREE_CLIENT_HOST,
            'EDITABLE' : False
        },
        'SETTINGS_11' : {
            'NAME' : 'ENTREE_CLIENT_HOST_SECRET_KEY',
            'VALUE' : LocalSettings.ENTREE_CLIENT_HOST_SECRET_KEY,
            'EDITABLE' : False
        }   
    }

    return ENTREE_SETTINGS