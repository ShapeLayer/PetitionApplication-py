Fe-tea, PetitionApplication based on Flask
====

![Python Required](https://img.shields.io/badge/python-3.5%20or%20higher-blue.svg?longCache=true&style=flat-square)
[![Latest Release](https://img.shields.io/badge/latest%20release-0.1.1--alpha--180923--de634fc--remake-yellow.svg?longCache=true&style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases/tag/0.1.1-alpha-180923-de634fc-remake)
[![Latest Stable Release](https://img.shields.io/badge/stable-none-red.svg?longCache=true&style=flat-square)](https://github.com/kpjhg0124/PetitionApplication-py/releases)

Fe-tea는 숭덕고등학교 학생회의 요청으로 개발되고 있는 플라스크 기반의 청원 수집 웹 애플리케이션입니다. Fe-tea는 학교 내에서 발생하는 문제점에 대해 구성원이 직접 의견을 공개적으로 올릴 수 있게 합니다. 공개된 의견은 다른 구성원들이 청원 반응 기능으로 청원에 대한 의견을 보낼 수 있게 해 해당 의견에 대한 여론도 확인할 수 있습니다. 또한 장난성 청원 방지 대책으로 SNS 로그인 기능이 추가되어 있으며, SNS 로그인을 사용하지 않고 청원을 작성할 경우, 비공개로 운영자에게 청원을 작성 할 수 있게 되어 있습니다.

자동 생성된 다량 청원 방지 대책으로 reCaptcha가 추가되어(아직 미구현됨)있으며, 익명 청원에 대한 법적 문제 해결을 위해 익명 사용자의 명의를 기록, 확인하는 기능도 추가되어 있습니다.

# 시작하기
Fe-tea는 파이썬 환경에서 동작하는 파이썬 애플리케이션으로, 파이썬 환경을 필요로 합니다. 

## 환경 구성
[파이썬 설치 가이드]를 참고하여 파이썬을 설치합니다.

[릴리즈]에서 Fe-tea의 릴리즈 판을 다운로드 받고, 압축을 해제합니다.

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
pip install -r requirements.txt
```

Fe-tea를 시작합니다.
```
python app.py
```
리눅스 환경의 경우 다음 명령으로 실행해야 합니다.
```
python3 app.py
```

# 포함된 외부 프로젝트
* [Bootstrap](https://getbootstrap.com/) - Bootstrap - [MIT License](https://opensource.org/licenses/MIT) _CDN Uses_
* [Minty](https://bootswatch.com/minty/) - [Thomas Park](https://thomaspark.co/) - [MIT License](https://opensource.org/licenses/MIT)

# 저자
* [kpjhg0124](https://github.com/kpjhg0124) - _initial work_ - [me@ho9.me](mailto:me@ho9.me)

# 라이선스
This project is licensed under the BSD 3-Clause License. See the [LICENSE](/LICENSE) file for details.
