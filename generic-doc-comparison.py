#Generic document comparison tool - the user puts an old version and a new version of a doc in two separate locations, 
# they can  be either pdf or docx. Both docs are converted to html and then a comparison is made producing 
# two redline html files in an output folder
#Developed by Daniel Hutchings - November 2020
import sys
import pandas as pd
import numpy as np
import time
import xml.etree.ElementTree as ET
from lxml import etree
from difflib import ndiff
import csv
import os
import glob
import datetime
import re
import string
import shutil
from lxml.html.diff import htmldiff
from lxml import html 
from lxml.html.clean import Cleaner
from bs4 import BeautifulSoup

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO
import pdf_to_docx
import docx_to_html
import xml_to_html
import metrics

pd.set_option('display.max_colwidth', -1) #stop the dataframe from truncating cell contents.


def find_most_recent_file(directory, pattern):
    try:
        filelist = os.path.join(directory, pattern) #builds list of file in a directory based on a pattern
        filelist = sorted(glob.iglob(filelist), key=os.path.getmtime, reverse=True) #sort by date modified with the most recent at the top
        return filelist[0]
    except: return 'na'            


def log(message):
    l = open(JCSLogFile,'a')
    l.write(message + '\n')
    l.close()
    print(message)

def convert_to_single_html(page_title, doc_title, FilepathXML, FilepathHTML):
    html = etree.Element('html')
    head = etree.SubElement(html, 'head')
    meta = etree.SubElement(head, 'meta')
    meta.set('http-equiv', 'Content-Type')
    meta.set('content', 'text/html; charset=utf-8')
    link = etree.SubElement(head, 'link') #local css
    link.set('rel', 'stylesheet')
    link.set('type', 'text/css')
    link.set('href', 'file:///' + main_dir + 'css/style.css')
    link = etree.SubElement(head, 'link') #bootstrap
    link.set('rel', 'stylesheet')
    link.set('href', 'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css')
    link.set('itegrity', 'sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm')
    link.set('crossorigin', 'anonymous')
    style = etree.SubElement(head, 'style') #doc css
    style.text = 'h1{ font-size: 2rem} .insertion, ins {background-color: #66ff99;} .deletion, del {background-color: #ff6666;}'

    title = etree.SubElement(head, 'title')
    title.text = 'Redline comparison - ' + page_title + ' - ' + doc_title
    body = etree.SubElement(html, 'body')
    divmain = etree.SubElement(body, 'div')
    divmain.set('class', 'container')
    h1 = etree.SubElement(divmain, 'h1')
    h1.text = doc_title #+ ':'
    hr = etree.SubElement(divmain, 'hr')

    divcenter = etree.SubElement(divmain, 'div')
    #divcenter.set('contenteditable', 'true')
    divcenter.set('class', 'container')
    divcenter.set('style', 'width: 100%; height: 0%;')   
     
    HTMLTree = etree.parse(FilepathXML)
    HTMLRoot = HTMLTree.getroot()
    divcenter.append(HTMLRoot.find('.//div'))

    tree = etree.ElementTree(html)
    tree.write(FilepathHTML,encoding='utf-8')
    
def convert_to_html(template_filepath, title, previous_html, latest_html, compared_html, output_filepath):
    with open(template_filepath,'r') as template:
        htmltemplate = template.read()        
    with open(output_filepath,'w', encoding='utf-8') as f:            
        html = htmltemplate.replace('__TITLE__', title).replace('__PREVIOUS__', previous_html).replace('__LATEST__', latest_html).replace('__COMPARED__', compared_html) #.replace('&lt;', '<').replace('&gt;', '>').replace('\\', '/').replace('\u2011','-').replace('\u2015','&#8213;').replace('ī','').replace('─','&mdash;')
        f.write(html)
        f.close()
        pass

def levenshtein_distance(str1, str2, ):
    counter = {"+": 0, "-": 0}
    distance = 0
    for edit_code, *_ in ndiff(str1, str2):
        if edit_code == " ":
            distance += max(counter.values())
            counter = {"+": 0, "-": 0}
        else: 
            counter[edit_code] += 1
    distance += max(counter.values())
    return distance

def create_html_report(Date, changeLen, df_change, additionsLen, df_additions, report_dir, report_filepath):
    log('Creating report html...')
    pd.set_option('display.max_colwidth', -1) #stop the dataframe from truncating cell contents. This needs to be set if you want html links to work in cell contents
    
    with open(report_dir + 'ReportTemplate.html','r') as template:
        htmltemplate = template.read()

    additionsTable = df_additions.to_html(na_rep = " ",index = False,  classes="table table-bordered text-left table-striped table-hover table-sm")
    changeTable = df_change.to_html(na_rep = " ",index = False,  classes="table table-bordered text-left table-striped table-hover table-sm")

    with open(report_filepath,'w', encoding='utf-8') as f:            
        html = htmltemplate.replace('__DATE__', Date).replace('__CHANGELEN__', changeLen).replace('__DFCHANGES__', changeTable)
        if len(df_additions) > 0: html = html.replace('__ADDITIONSLEN__', additionsLen).replace('__DFADDITIONS__', additionsTable)
        else: html = html.replace('__ADDITIONSLEN__', additionsLen).replace('__DFADDITIONS__', '')
        html = html.replace('&lt;', '<').replace('&gt;', '>').replace('\\', '/').replace('\u2011','-').replace('\u2015','&#8213;').replace('ī','').replace('─','&mdash;')
        f.write(html)
        f.close()
        pass

    log("Exported html report to..." + report_filepath)

def strip_dodgy_characters(tree):
    for elem in tree.iterfind(".//u"): toReplaceText = elem.text
    try: elem.text = toReplaceText.replace('&lt;', '').replace('&gt;','').replace('<', '').replace('>','')
    except: pass

def strip_navigation(data):
    try:
        for navElement in data.findall('.//nav'): 
            navElement.getparent().remove(navElement)
        print('Nav elements removed before comparison...', data)
    except: 
        print('No Nav elements to remove...', data)


def archive_files_in(directory, archive_dir):
    filelist = glob.iglob(os.path.join(directory, '*.*')) 
    for filepath in filelist:
        filename = filepath.split('\\')[-1]
        shutil.copy(filepath, archive_dir + filename)
        os.remove(filepath)
        

# import mammoth
# def convert_docx_to_html(filename):
#     f = open(main_dir + filename, 'rb')
#     output_filename = filename.replace('.docx','') + '.html'
#     b = open(main_dir + output_filename, 'wb')
#     document = mammoth.convert_to_html(f)
#     intro = b'<html><head><title></title></head><body><div>'   
#     outro = b'</div></body></html>'
#     b.write(intro + document.value.encode('utf8') + outro)
#     f.close()
#     b.close()
#     return output_filename



state = 'live'
#state = 'dev'
#state = 'local'

if state == 'local': main_dir = ""
if state == 'dev': main_dir = "\\\\atlas\\lexispsl\\Automation-DEV\\Generic-comparison\\"
if state == 'live': main_dir = "\\\\atlas\\lexispsl\\Automation\\Generic-comparison\\"

watched_dir = main_dir + "Auto-gen\\"
assets_dir = main_dir + "Workspace\\"
log_dir = assets_dir + 'logs\\'
archive_dir = assets_dir + 'archive\\'
output_dir = main_dir + 'Output\\'
prev_dir = main_dir + 'Old_version\\'
latest_dir = main_dir + 'New_version\\'

three_way_template = r'\\atlas\lexispsl\Automation\Generic-comparison\Workspace\templates\side-by-side.html'
redline_only_template = r'\\atlas\lexispsl\Automation\Generic-comparison\Workspace\templates\redline-only.html'

logdatetime =  str(time.strftime("%Y%m%d-%H%M%S"))
logdate = str(time.strftime("%Y-%m-%d"))
archive_list = []



JCSLogFile = log_dir + 'generic-comparison-' + logdatetime + '.log'
l = open(JCSLogFile,'w')
l.write("Start generic document comparison..."+logdatetime+"\n")
l.close()


# #directory analysis
# print(find_most_recent_file(latest_dir, '.*pdf'))
# print(find_most_recent_file(prev_dir, '.*pdf'))
#list all existing files in directory

#convert
log('Converting previous doc from pdf to docx if pdf available...')
pdf_to_docx.convert(prev_dir)
log('Converting latest doc from pdf to docx if pdf available...')
pdf_to_docx.convert(latest_dir)
log('Converting previous doc from xml to html...')
xml_to_html.convert(prev_dir)
log('Converting latest doc from xml to html...')
xml_to_html.convert(latest_dir)
log('Converting previous doc from docx to html...')
docx_to_html.convert(prev_dir)
log('Converting latest doc from docx to html...')
docx_to_html.convert(latest_dir)


#SETTING FILEPATHS FOR ALL THE FILES TO GENERATE
latest_filepath_html = find_most_recent_file(latest_dir, '*.html')
previous_filepath_html = find_most_recent_file(prev_dir, '*.html')

filename = latest_filepath_html.split('\\')[-1]
filename = filename[0:-5] #remove the last 5 chars i.e. .html

dated_directory = output_dir + str(time.strftime("%Y-%m-%d"))
try: os.makedirs(dated_directory)   
except FileExistsError: print('Output folder already exists...' + dated_directory) 

compared_filepath_xml = dated_directory + '\\' + filename + '-' + str(time.strftime("%d%m%Y")) +'-compared.xml'
compared_filepath_html = dated_directory + '\\' + filename + '-'  + str(time.strftime("%d%m%Y")) +'-side-by-side.html'
redline_filepath_html = dated_directory + '\\' + filename + '-'  + str(time.strftime("%d%m%Y")) +'-redline-only.html'
error_filepath_html = dated_directory + '\\ERROR-' + filename + '-'  + str(time.strftime("%d%m%Y")) +'.html'

cleaner = Cleaner(remove_unknown_tags=False, allow_tags=['table', 'tgroup', 'tbody', 'colspec', 'tr', 'td', 'th', 'p', 'h5', 'h4', 'sup', 'blockquote'], page_structure=True)

log('Cleaning latest html...' + latest_filepath_html)
with open(latest_filepath_html,'r', encoding='latin1') as file:
    latest_html = html.fromstring(cleaner.clean_html(file.read()))
log('Cleaning previous html...' + previous_filepath_html)
with open(previous_filepath_html,'r', encoding='latin1') as file:
    previous_html = html.fromstring(cleaner.clean_html(file.read()))
# parser = etree.XMLParser(recover=True) #create parser that tries to recover doc after encountering html characters
# previous_tree = etree.parse(previous, parser=parser)
# latest_tree = etree.parse(latest, parser=parser)
# log('Loading into etree...')
# latest_tree = etree.ElementTree(latest_html)
# previous_tree = etree.ElementTree(previous_html)

# #strip_dodgy_characters(latest_tree)
# #strip_dodgy_characters(previous_tree)
# etree.strip_tags(latest_tree,etree.Comment,'html', 'head', 'body', 'meta', 'link', 'style', 'strong', 'it', 'a', 'img', 'em', 'span')
# etree.strip_tags(previous_tree,etree.Comment,'html', 'head', 'body', 'meta', 'link', 'style', 'strong', 'it', 'a', 'img', 'em', 'span')


# latest_root = latest_tree.getroot()
# previous_root = previous_tree.getroot()

# previous_data = previous_tree.find('.//div')
# latest_data = latest_tree.find('.//div')  
# #print(etree.tostring(previous_data))
#DIFF - GET REDLINE
log('About to do comparison...')
diffed_version = htmldiff(previous_html, latest_html) #Get the diff html from lxml built in method    
log('Comparison done! Cleaning up compared version...')
soup = BeautifulSoup(diffed_version)
diffed_version = str(soup.prettify())
soup = BeautifulSoup(etree.tostring(previous_html))
previous_html = str(soup.prettify())
soup = BeautifulSoup(etree.tostring(latest_html))
latest_html = str(soup.prettify())

# diffed_version = diffed_version.replace('<br>', '<br/>').replace('<hr>', '<hr/>').replace('&lt;', '<').replace('&gt;','>').replace('<ul><li></ul>', '')
# diffed_version = diffed_version.replace('<SOLS', '').replace('(SOLS)>', '')        
# diffed_version = re.sub(r'<img ([^>]*)>', r'<img \1 />', diffed_version)
# diffed_version = re.sub(r'<LPUTeam([^>]*)>', r'<p>LPUTeam\1 </p>', diffed_version)
# diffed_version = re.sub(r'<5x5x5gateway@DWP.GSI.GOV.UK.', r'5x5x5gateway@DWP.GSI.GOV.UK.', diffed_version)
# diffed_version = re.sub(r'<APA.mailbox@hmrc.gov.uk>', r'APA.mailbox@hmrc.gov.uk', diffed_version)
# diffed_version = re.sub(r'”', r'"', diffed_version)
# diffed_version = re.sub(r'<span [^>]*>', r'<span>', diffed_version)
# diffed_version = re.sub(r'<span>', '', diffed_version)
# diffed_version = re.sub(r'</span>', '', diffed_version)
# diffed_version = re.sub(r' class="[^"]*"', '', diffed_version)
# diffed_version = re.sub(r'<p> <p>', '<p>', diffed_version)

# #INSERT DIFF HTML INTO SKELETON TREE - if there's a script failure it's usually here because of some dodgy tags that haven't been accounted for and that make the doc structurally invalid. Uncomment the print below to inspect further, then make search and replace directly above this line
# #print(diffed_version)
# log('Inserting comparison into xml shell...')
# diff_data = etree.Element('data') #create xml shell
# try:
#     diff_root = diff_data.insert(0, etree.fromstring(diffed_version)) #insert diff html into shell
# except:
#     #print(diffed_version)
#     diffed_version = '<div>' + diffed_version + '</div>'
#     print(diffed_version)
#     error_diff = open(error_filepath_html,'w', encoding='utf-8')
#     error_diff.write(diffed_version)
#     error_diff.close()
#     diff_root = diff_data.insert(0, etree.fromstring(diffed_version)) #insert diff html into shell

# diff_tree = etree.ElementTree(diff_data)  #define the shell as the tree  
# diff_tree.write(compared_filepath_xml,encoding='utf-8') #write the tree out    

#CREATE WEBPAGE WITH 3 DIVS - 1 shows previous, 1 shows latest, 1 shows differences in redline
log('Converting comparison html to 3 way html...')
convert_to_html(three_way_template, filename, previous_html, latest_html, diffed_version, compared_filepath_html)
log('Exported to: ' + compared_filepath_html)
log('Converting to single redline html...')
convert_to_html(redline_only_template, filename, previous_html, latest_html, diffed_version, redline_filepath_html) 
log('Exported to: ' + redline_filepath_html)

# log('Cleaning up the folders...')
# archive_files_in(prev_dir, prev_dir + 'archive//')
# log('Previous directory now empty and files archived...')
# archive_files_in(latest_dir, latest_dir + 'archive//')
# log('Latest directory now empty and files archived...')
# shutil.copy(compared_filepath_xml, archive_dir + compared_filepath_xml.split('\\')[-1])
# os.remove(compared_filepath_xml)

# if state == 'live':
#     metrics.add(log_dir+r'\generic-comparison-metrics.csv', 1, 'Generic comparison', filename)

log('Finished!')