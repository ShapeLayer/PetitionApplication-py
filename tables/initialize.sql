/*Sqlite3 Query*/
/* initialize.sql */

INSERT INTO user_group_acl (
    user_group,
    group_priority,
    site_owner,
    site_administrator,
    peti_read,
    peti_write,
    peti_react,
    peti_disable,
    peti_delete,
    user_identify,
    user_block,
    manage_user,
    manage_acl,
    manage_static_page,
    manage_notion,
    not_display_log
) values(
    "owner",
    1001,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1
);

INSERT INTO user_group_acl (
    user_group,
    group_priority,
    site_owner,
    site_administrator,
    peti_read,
    peti_write,
    peti_react,
    peti_disable,
    peti_delete,
    user_identify,
    user_block,
    manage_user,
    manage_acl,
    manage_static_page,
    manage_notion,
    not_display_log
) values(
    "administrator",
    70,
    0,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    1,
    0
);

INSERT INTO user_group_acl (
    user_group,
    group_priority,
    site_owner,
    site_administrator,
    peti_read,
    peti_write,
    peti_react,
    peti_disable,
    peti_delete,
    user_identify,
    user_block,
    manage_user,
    manage_acl,
    manage_static_page,
    manage_notion,
    not_display_log
) values(
    "user",
    30,
    0,
    0,
    1,
    1,
    1,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0
);

INSERT INTO user_acl_list_tb values(1, "owner");
INSERT INTO static_page_tb values("frontpage", "")