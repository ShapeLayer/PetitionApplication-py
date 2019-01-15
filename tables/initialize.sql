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
    "not_signed_in",
    15,
    0,
    0,
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
    0,
    0
);

INSERT INTO user_acl_list_tb values(1, "owner");
INSERT INTO static_page_tb (page_name, title, editor, editdate, content) values("frontpage", "%_appname_%: 대문", "System", "", "<div class='container'><h1>BLEND IT<br>WITH<BR>YOUR WAY</h1><h2>당신의 힘으로 바꿔보세요. %_appname_% 청원페이지</h2><a href='/login' class='btn btn-primary'>시작하기</a><a href='/a' class='btn btn-link'>청원 둘러보기</a><a href='/a/write' class='btn btn-link'>청원 생성하기</a></div>
");
INSERT INTO static_page_tb (page_name, title, editor, editdate, content) values("adminpage", "관리자: 대문", "System", "", "<h1>환영합니다!</h1><p>이곳은 관리자 페이지입니다. 관리자 권한을 받은 acl 그룹의 유저만 접근할 수 있으며, 메인 페이지의 각종 작업들을 수행할 수 있습니다.</p>");
INSERT INTO static_page_tb (page_name, title, editor, editdate, content) values("notice", "공지", "System", "", "아직 공지가 없습니다.");

INSERT INTO server_set (name, data) values("custom_header_top", "");
INSERT INTO server_set (name, data) values("custom_header_bottom", "");

INSERT INTO server_set (name, data) values("petition_publish_default", "0");