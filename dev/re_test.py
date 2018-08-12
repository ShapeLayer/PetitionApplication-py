import re

title = re.compile(r'== [a-zA-Z가-힣ㄱ-ㅎ0-9\s]+? ==')
short_answer = re.compile(r'\|-[a-zA-Z가-힣ㄱ-ㅎ0-9\s]+?-\|')
long_answer = re.compile(r'\|=[a-zA-Z가-힣ㄱ-ㅎ0-9\s]+?=\|')
check_box = re.compile(r'\[\n?(\[ \][a-zA-Z가-힣ㄱ-ㅎ0-9\s]+\n?)*\]')
choice = re.compile(r'\(\n?(\( \)[a-zA-Z가-힣ㄱ-ㅎ0-9\s]+\n?)*\)')

text = '[[ ]ab] (( )ab) |- b rㄱ-| |=hello=| == title =='

title_match = title.search(text)
short_match = short_answer.search(text)
long_match = long_answer.search(text)
check_match = check_box.search(text)
choice_match = choice.search(text)

print(title_match.group())
print(short_match.group())
print(long_match.group())
print(check_match.group())
print(choice_match.group())
