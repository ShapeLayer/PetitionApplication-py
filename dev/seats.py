template = '<style>.table-seat .block{margin : 0;padding : 0;border-color : #fff;width : 25px;height : 25px;background-color : #693;align-content : flex-start;display : inline-block;}</style><section class="table table-seat"><h1>TABLE_NAME</h1><table><tbody><content></tbody></table></section>'
content = ''
for i in range(10):
    content += '<tr><th>%d열</th><td>' % ( i + 1 )
    for j in range(20):
        content += '<div class="block" id="x%dy%d" data-toggle="tooltip" title="data."></div>' % (i, j)
    content += '</td></tr>'
template = template.replace('<content>', content)

with open('seats.html', mode='w', encoding='utf-8') as f:
    f.write(template)
