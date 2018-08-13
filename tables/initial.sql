/*Sqlite3 Query*/
create table FORM_DATA_TB(
    form_id INTEGER primary key AUTOINCREMENT,
    form_display_name TEXT NOT NULL,
    form_notice_level TEXT NOT NULL,
    form_publish_date TEXT NOT NULL,
    form_enabled INTEGER NOT NULL,
    form_body_content TEXT NOT NULL
);
create table PETITION_DATA_TB(
    form_id INTEGER primary key AUTOINCREMENT,
    form_display_name TEXT NOT NULL,
    form_publish_date TEXT NOT NULL,
    form_enabled INTEGER NOT NULL,
    form_body_content TEXT NOT NULL
)