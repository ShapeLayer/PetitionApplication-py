Fe-tea, Flask 기반 청원 수집 웹 애플리케이션 
====

![Python Required](https://img.shields.io/badge/python-3.5%20or%20higher-blue.svg?style=flat-square)
![BSD-3 License](https://img.shields.io/badge/license-BSD--3-lightgrey.svg?style=flat-square)
[![Latest Release](https://img.shields.io/badge/latest%20release-1.2.2-Dockerized-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/tree/828ef831b0044a04f571920d93cd43ed2bb9127b)
[![Latest Stable Release](https://img.shields.io/badge/stable-1.2.2-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.2.2)
[![Bootstrap-License](https://img.shields.io/badge/bootstrap-MIT-cef19e.svg?style=flat-square)](https://github.com/twbs/bootstrap/blob/master/LICENSE)
[![Minty-License](https://img.shields.io/badge/minty-MIT-cef19e.svg?style=flat-square)](https://github.com/thomaspark/bootswatch/blob/master/LICENSE)

![](/.github/fe.png)

Fe-tea는 숭덕고등학교 학생회의 요청으로 개발되고 있는 플라스크 기반의 청원 수집 웹 애플리케이션입니다. Fe-tea는 학교 내에서 발생하는 문제점에 대해 구성원이 직접 의견을 공개적으로 올릴 수 있게 합니다.

공개된 의견은 다른 구성원들이 청원 반응 기능으로 청원에 대한 의견을 보낼 수 있게 해 해당 의견에 대한 여론도 확인할 수 있습니다. 또한 장난성 청원 방지 대책으로 SNS 로그인 기능이 추가되어 있으며, SNS 로그인을 사용하지 않고 청원을 작성할 경우, 비공개로 운영자에게 청원을 작성 할 수 있게 되어 있습니다.또한 익명 청원에 대한 법적 문제 해결을 위해 익명 사용자의 명의를 기록, 확인하는 기능도 추가되어 있습니다.

자동 생성된 다량 청원 방지 대책으로 reCaptcha v2가 추가되어있으며, 익명 청원에 대한 법적 문제 해결을 위해 익명 사용자의 명의를 기록, 확인하는 기능도 추가되어 있습니다. reCaptcha v2 API 키 정보를 `oauthsettings.json`에 추가하지 않으면 reCaptcha v2 정보를 입력하지 않으면 reCapthcha v2를 비활성화 한 것으로 처리됩니다.

# 시작하기
Fe-tea는 파이썬 환경에서 동작하는 파이썬 애플리케이션으로, 파이썬 환경을 필요로 합니다. 

## 환경 구성
### 파이썬 설치
[파이썬 설치 가이드](https://github.com/404-sdok/how-to-python/blob/master/0.md)를 참고하여 파이썬을 설치합니다.

### 릴리즈 다운로드
[릴리즈](https://github.com/kpjhg0124/PetitionApplication-py/releases)에서 Fe-tea의 릴리즈 판을 다운로드 받고, 압축을 해제합니다.
* 각 버전 사이 DB 변경점은 애플리케이션이 자동 반영하지 않으며, 버전 간 데이터 마이그레이션을 지원하지 않습니다. (저말고 아무도 안쓰는것 같아서요...)

| 구분 | 릴리즈 |
| :----: | :----: |
| stable | [![](https://img.shields.io/badge/stable-1.2.2-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.2.2) |
| stable | [![](https://img.shields.io/badge/stable-1.2.1-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.2.1-stable-fix) |
| stable | [![](https://img.shields.io/badge/stable-1.2-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.2) |
| stable | [![](https://img.shields.io/badge/stable-1.1-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.1-stable) |
| stable | [![](https://img.shields.io/badge/stable-1.0-brightgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.0) |
| beta | [![](https://img.shields.io/badge/beta-1.0--3-yellowgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.0-beta-3) |
| beta | [![](https://img.shields.io/badge/beta-1.0--2-yellowgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.0-beta-2) |
| beta | [![](https://img.shields.io/badge/beta-1.0-yellowgreen.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/1.0-beta) |
| alpha | [![](https://img.shields.io/badge/alpha-0.1.1-orange.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/0.1.1-alpha-180923-de634fc-remake) |
| alpha | [![](https://img.shields.io/badge/alpha-0.1--2-orange.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/0.1-Alpha-180817-02-98df461) |
| alpha | [![](https://img.shields.io/badge/alpha-0.1--1-orange.svg?style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/0.1-Alpha-180815-01-637212c) |

### 모듈 설치
다음 명령어로 Fe-tea 구성 파일이 위치한 디렉토리로 이동합니다.
```
cd [path]
```


다음 명령어로 Fe-tea 실행에 필요한 모듈을 설치합니다.
```
pip install -r requirements.txt
```
리눅스 환경의 경우 다음 명령으로 실행해야 합니다.
```
pip3 install -r requirements.txt
```

### API 키 설정
`oauthsettings.json`파일을 수정하여 각 API 키 값을 추가합니다.

| 속성 | 값 |
| :----: | :----: | 
| `facebook_client_id` | facebook 로그인 API 클라이언트 ID |
| `facebook_client_secret` | facebook 로그인 API 비밀키 |
| `naver_client_id` | 네이버 로그인 API 클라이언트 ID |
| `naver_client_secret` | 네이버 로그인 API 비밀키 |
| \*`recaptcha_site_key` | reCaptcha 사이트 키 |
| \*`recaptcha_secret_key` | reCaptcha 사이트 비밀키|
* \*는 필수값입니다.

SNS로그인 기능을 활성화하기 위해선 각 서비스 제공자로부터 API 키 값을 받아와야합니다. ([Facebook Developers](https://developers.facebook.com/), [네이버 개발자 센터](https://developers.naver.com/main/)) API 키 값은 [oauthsettings.json](/oauthsettings.json)파일에 직접 API 키 값을 추가할 수 있습니다.
  * 네이버 API의 경우 별도의 검수 절차가 필요하며, 페이스북 API의 경우 설정 패널에서 라이브 상태 설정만 해주면 로그인 기능 사용이 가능합니다.

## 애플리케이션 시작
### 애플리케이션 시작
Fe-tea를 시작합니다.
```
python app.py
```
리눅스 환경의 경우 다음 명령으로 실행해야 합니다.
```
python3 app.py
```

* Fe-tea의 첫 계정은 소유자 계정으로 설정됩니다. 소유자 계정은 SNS 계정이 아닌 내부계정(entree 엔진)으로 생성하는 것을 권장합니다.

### 애플리케이션 공개
SNS 로그인 기능으로 인해 페이지 공개 시 페이지는 https 연결을 사용해야 합니다. [LocalSettings.py](./LocalSettings.py) 파일의 `publish_host_name` 값을 https 프로토콜을 포함한 도메인 주소로 설정하고, 실제로 https 연결을 지원해야합니다. `flask_debug_mode`를 `False`로 설정하는 것을 권장하며, 도메인과의 연결은 리버스 프록시를 사용해 실현하십시오.

 * ([apache 설정 파일](./conf/apache/), [nginx 설정 파일](./conf/nginx.conf))

### 기타 사용 정보 

* 내부 계정은 관리자를 위해 추가한 기능으로, 사용시 verify_key값을 입력해야 합니다. 관리자 메뉴에서 확인하거나 [verify_key](/verify_key)파일에서 확인할 수 있습니다.

* 메인 페이지의 기본 문구는 ```정적 페이지 설정```에서 변경할 수 있으며 정적 페이지 기능은 HTML코드를 그대로 페이지에 표시합니다.

# 포함된 외부 프로젝트
* [Bootstrap](https://getbootstrap.com/) - [Bootstrap](https://github.com/twbs) - [MIT License](https://github.com/twbs/bootstrap/blob/master/LICENSE)
* [Minty](https://bootswatch.com/minty/) - [Thomas Park](https://thomaspark.co/) - [MIT License](https://github.com/thomaspark/bootswatch/blob/master/LICENSE)

# 저자
* [kpjhg0124](https://github.com/kpjhg0124) - _첫 삽_ - [me@ho9.me](mailto:me@ho9.me)

# 도움을 주신 분들
* [페이스북 그룹 생활코딩](https://www.facebook.com/groups/codingeverybody/) 멤버분들
* [2DU](https://github.com/2du)
* [숭덕고등학교 학생회](https://www.facebook.com/sungdeokcouncil/) 및 [IT 동아리 \n](https://github.com/404-sdok)

# 라이선스
fetea 프로젝트는 [BSD 3-Clause License](/LICENSE)(이하 BSD-3 라이선스)의 보호를 받고 있으며, fetea 프로젝트를 사용하고자 한다면 BSD-3 라이선스를 준수해야 합니다. 본 라이선스를 위반할 경우 개발자는 DMCA Takedown 등 관련 제재를 관계자에게 요청할 권리가 있으며, 그 책임은 모두 라이선스 위반 사용자에게 있습니다. 자세한 내용은 문서를 참고하세요.
