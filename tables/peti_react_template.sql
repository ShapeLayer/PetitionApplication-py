/*Sqlite3 Query*/
CREATE TABLE peti_<id>_reaction_tb(
    react_id INTEGER primary key AUTOINCREMENT,
    fb_id INTEGER NOT NULL,
    fb_profile_img TEXT NOT NULL,
    content TEXT NOT NULL
)
