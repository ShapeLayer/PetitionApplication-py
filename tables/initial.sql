/*Sqlite3 Query*/
CREATE TABLE peti_data_tb(
    form_id INTEGER primary key AUTOINCREMENT,
    form_display_name TEXT NOT NULL,
    form_publish_date TEXT NOT NULL,
    form_status INTEGER NOT NULL,
    /*form_enabled INTEGER NOT NULL,*/
    form_author TEXT NOT NULL,
    form_body_content TEXT NOT NULL
);
CREATE TABLE peti_control_log_tb(
    form_id INTEGER NOT NULL,
    control_date TEXT NOT NULL,
    user TEXT NOT NULL,
    fb_id TEXT NOT NULL
);
CREATE TABLE user_administrator_list_tb(
    fb_id TEXT NOT NULL,
    auth TEXT NOT NULL
);
CREATE TABLE articles_indexing_tb(
    articles_type TEXT NOT NULL,
    index INTEGER NOT NULL
);
CREATE TABLE user_activity_log_tb(
    log_id INTEGER primary key AUTOINCREMENT,
    fb_id TEXT NOT NULL,
    activity TEXT NOT NULL,
    activity_date TEXT NOT NULL
)