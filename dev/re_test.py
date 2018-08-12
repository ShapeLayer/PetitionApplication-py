import re

title = re.compile('== [a-zA-Z가-힣ㄱ-ㅎ0-9\s]+ ==')
short_answer = re.compile('\|\|[a-zA-Z가-힣ㄱ-ㅎ0-9\s]?\|\|')
long_answer = re.compile('\|\|\|[a-zA-Z가-힣ㄱ-ㅎ0-9\s]?\|\|\|')
check_box = re.compile('\[\n?(\[ \][a-zA-Z가-힣ㄱ-ㅎ0-9\s]+\n?)*\]')
choice = re.compile('\(\n?(\( \)[a-zA-Z가-힣ㄱ-ㅎ0-9\s]+\n?)*\)')

text = '[[ ]가나](( )가나)||안녕|||||hello|||== title =='

title_match = title.match(text)
short_match = short_answer.match(text)
long_match = long_answer.match(text)
check_match = check_box.match(text)
choice_match = choice.match(text)

print(title_match.group())
print(short_match.group())
print(long_match.group())
print(check_match.group())
print(choice_match.group())