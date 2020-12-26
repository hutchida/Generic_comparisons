import glob
import os
import mammoth

def convert(directory):
    print('Converting docx to html...')
    for i, docx_filepath in enumerate(glob.iglob(directory+"*.docx")):
        html_filepath = docx_filepath[0:-5]+ ".html"
        f = open(docx_filepath, 'rb')
        b = open(html_filepath, 'wb')
        document = mammoth.convert_to_html(f)
        intro = b'<html><head><title></title></head><body><div>'   
        outro = b'</div></body></html>'
        b.write(intro + document.value.encode('utf8') + outro)
        f.close()
        b.close()
        print(html_filepath)
