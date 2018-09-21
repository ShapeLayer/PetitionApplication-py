/*Sqlite3 Query*/

/* Petition Article data */
CREATE TABLE peti_data_tb(
    peti_id INTEGER primary key AUTOINCREMENT,
    peti_display_name TEXT NOT NULL,
    peti_publish_date TEXT NOT NULL,
    peti_status INTEGER NOT NULL, /* 0: Published  1: Disabled  2: Completed */
    peti_author_id TEXT NOT NULL,
    peti_body_content TEXT NOT NULL
);
CREATE TABLE peti_react_tb(
    peti_id
    react_id
    fb_id
    content TEXT NOT NULL
);

/* User Data */
CREATE TABLE site_user_tb(
    account_id
    sns_type
    sns_id
    user_display_name
    user_display_profile_img
    account_password
)
CREATE TABLE user_administrator_list_tb(
    fb_id TEXT NOT NULL,
    auth TEXT NOT NULL
);
CREATE TABLE author_connect(
    peti_author_id INTEGER NOT NULL,
    account_user_id INTEGER NOT NULL
)
CREATE TABLE user_group_auth(
    user_group TEXT NOT NULL,
    site_owner INTEGER NOT NULL, /* Limited */
    peti_read INTEGER NOT NULL,
    peti_write INTEGER NOT NULL,
    peti_react INTEGER NOT NULL,
    peti_disable INTEGER NOT NULL,
    peti_delete INTEGER NOT NULL,
    user_identify INTEGER NOT NULL,
    user_block INTEGER NOT NULL,
    manage_user INTEGER NOT NULL,
    manage_acl INTEGER NOT NULL,
    manage_static_page INTEGER NOT NULL,
    manage_notion INTEGER NOT NULL,
    not_display_log INTEGER NOT NULL /* Limited */
)

/* Application Manage Log */
CREATE TABLE user_activity_log_tb(
    log_id INTEGER primary key AUTOINCREMENT,
    fb_id TEXT NOT NULL,
    activity TEXT NOT NULL,
    activity_date TEXT NOT NULL
);

CREATE TABLE articles_indexing_tb(
    articles_type TEXT NOT NULL,
    articles_index INTEGER NOT NULL
);

