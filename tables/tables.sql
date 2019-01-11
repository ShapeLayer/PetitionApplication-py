/*Sqlite3 Query*/

/* Petition Article data */
CREATE TABLE peti_data_tb(
    peti_id INTEGER primary key AUTOINCREMENT,
    peti_display_name TEXT NOT NULL,
    peti_publish_date TEXT NOT NULL,
    peti_status INTEGER NOT NULL, /* 0: Published  1: Disabled  2: Completed  404: Return 404*/
    peti_author_id INTEGER NOT NULL,
    peti_body_content TEXT NOT NULL
);
CREATE TABLE peti_react_tb(
    react_id INTEGER primary key AUTOINCREMENT,
    peti_id INTEGER NOT NULL,
    author_id INTEGER NOT NULL,
    react_type TEXT NOT NULL, /* default, offical */
    content TEXT NOT NULL
);

/* User Data */
CREATE TABLE site_user_tb(
    account_id INTEGER primary key AUTOINCREMENT,
    sns_type TEXT NOT NULL,
    sns_id TEXT NOT NULL,
    user_display_name TEXT NOT NULL,
    user_display_profile_img TEXT,
    account_password_hash TEXT
);
CREATE TABLE user_acl_list_tb(
    account_id INTEGER NOT NULL,
    auth TEXT NOT NULL
);
CREATE TABLE author_connect(
    peti_author_id INTEGER primary key AUTOINCREMENT,
    peti_author_display_name TEXT NOT NULL,
    account_user_id INTEGER NOT NULL,
    target_article INTEGER NOT NULL
);
CREATE TABLE block_user_tb(
    account_id INTEGER NOT NULL,
    block_delay INTEGER NOT NULL
);
CREATE TABLE user_group_acl(
    user_group TEXT NOT NULL,
    group_priority INTEGER NOT NULL,
    site_owner INTEGER NOT NULL, /* Limited */
    site_administrator INTEGER NOT NULL, 
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
);

/* Application Manage Log */
CREATE TABLE user_activity_log_tb(
    log_id INTEGER primary key AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    activity_object TEXT NOT NULL,
    activity TEXT NOT NULL,
    activity_description TEXT NOT NULL,
    activity_date TEXT NOT NULL
    /* <activity_date>  <account_id:user_display_name>이(가) 
    <activity_object>을(를) <activity>함. (<activity_description>)*/
);

CREATE TABLE articles_indexing_tb(
    articles_type TEXT NOT NULL,
    articles_index INTEGER NOT NULL
);

/* Static Page */
CREATE TABLE static_page_tb(
    page_name TEXT NOT NULL,
    title TEXT NOT NULL,
    editor TEXT NOT NULL,
    editdate TEXT NOT NULL,
    content TEXT NOT NULL
);

/**/
CREATE TABLE server_set(
    name TEXT NOT NULL,
    data TEXT NOT NULL
);