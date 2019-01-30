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
INSERT INTO static_page_tb (page_name, title, editor, editdate, content) values("adminpage", "관리자: 대문", "System", "", "
<div class=""container"">
  <div class=""row"">
    <div class=""col-sm"">
      <h3>사용자 관리</h3>
      <ul>
        <li><a href=""/admin/member/"">전체 사용자 목록</a></li>
        <li><a href=""/admin/admins/"">관리자 관리</a></li>
        <li><a href=""/admin/acl/"">사용자 권한 레벨</a></li>
      </ul>
    </div>
    <div class=""col-sm"">
      <h3>청원 관리</h3>
      <ul>
        <li><a href=""/admin/petition/"">비정규 상태 청원 관리</a></li>
        <li><a href=""/admin/peti-default/"">청원 작성 기본 설정</a></li>
      </ul>
    </div>
    <div class=""col-sm"">
      <h3>시스템 관리</h3>
      <ul>
        <li><a href=""/admin/static/"">정적 페이지 관리</a></li>
        <li><a href=""/admin/verify_key/"">verify_key 정보</a></li>
        <li><a href=""/admin/update/"">시스템 업데이트 확인</a></li>
        <li><a href=""/admin/header/"">HTML 커스텀 head 설정</a></li>
      </ul>
    </div>
  </div>
</div>
");
INSERT INTO static_page_tb (page_name, title, editor, editdate, content) values("notice", "공지", "System", "", "아직 공지가 없습니다.");

INSERT INTO seo_set (name, data) values("og:url", "%_url_%");
INSERT INTO seo_set (name, data) values("og:title", "%_page_title_% - %_appname_%");
INSERT INTO seo_set (name, data) values("og:image", "%_app_image_%");
INSERT INTO seo_set (name, data) values("og:type", "article");
INSERT INTO seo_set (name, data) values("og:locale", "ko_KR");

INSERT INTO server_set (name, data) values("custom_header_top", "");
INSERT INTO server_set (name, data) values("custom_header_bottom", "");

INSERT INTO server_set (name, data) values("petition_publish_default", "0");
INSERT INTO server_set (name, data) values("petition_publish_fixed", "0");
INSERT INTO server_set (name, data) values("petition_react_disabled", "0");

INSERT INTO server_set (name, data) values("facebook_share_enabled", "1");