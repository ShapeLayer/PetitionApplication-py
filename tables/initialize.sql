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
    "block",
    0,
    0,
    0,
    1,
    0,
    0,
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
INSERT INTO static_page_tb values("frontpage", "");
INSERT INTO static_page_tb values("adminpage", "<h1>환영합니다!</h1><p>이곳은 관리자 페이지입니다. 관리자 권한을 받은 acl 그룹의 유저만 접근할 수 있으며, 메인 페이지의 각종 작업들을 수행할 수 있습니다.</p>")