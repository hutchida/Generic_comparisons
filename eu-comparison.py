#EU comparison tool - script loops over files in a dated folder for 8 different sources, does a comparison with the retained version
# two redline html files output to the same folder
#Developed by Daniel Hutchings - Christmas 2020
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
import xml_to_html
import metrics
import mailout as email

pd.set_option('display.max_colwidth', -1) #stop the dataframe from truncating cell contents.


def find_most_recent_file(directory, pattern):
    try:
        filelist = os.path.join(directory, pattern) #builds list of file in a directory based on a pattern
        filelist = sorted(glob.iglob(filelist), key=os.path.getmtime, reverse=True) #sort by date modified with the most recent at the top
        return filelist[0]
    except: return 'na'            


def log(message):
    l = open(log_filepath,'a')
    l.write(message + '\n')
    l.close()
    print(message)

def convert_to_html(lev_dist, template_filepath, title, previous_html, latest_html, compared_html, output_filepath):
    with open(template_filepath,'r') as template:
        htmltemplate = template.read()        
    with open(output_filepath,'w', encoding='utf8') as f:            
        html = htmltemplate.replace('__LEVDIST__',str(lev_dist)).replace('__TITLE__', title).replace('__PREVIOUS__', previous_html).replace('__LATEST__', latest_html).replace('__COMPARED__', compared_html) #.replace('&lt;', '<').replace('&gt;', '>').replace('\\', '/').replace('\u2011','-').replace('\u2015','&#8213;').replace('ī','').replace('─','&mdash;')
        f.write(html)
        f.close()
        pass

def levenshtein_distance(str1, str2, ):
    counter = {"+": 0, "-": 0}
    distance = 0
    try:
        for edit_code, *_ in ndiff(str1, str2):
            if edit_code == " ":
                distance += max(counter.values())
                counter = {"+": 0, "-": 0}
            else: 
                counter[edit_code] += 1
    except TypeError:
        print('TYPE ERROR RAISE ON NDIFF..')
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


def list_of_directories(directory): #sorted a-z
    return sorted(glob.iglob(os.path.join(directory, '*/')), key=os.path.dirname, reverse=True)

def archive_files_in(directory, archive_dir):
    filelist = glob.iglob(os.path.join(directory, '*.*')) 
    for filepath in filelist:
        filename = filepath.split('\\')[-1]
        shutil.copy(filepath, archive_dir + filename)
        os.remove(filepath)

def remove_element(xpath, root):
    for child in root.xpath(xpath, namespaces=NSMAP):
        #print(child)
        parent = child.getparent()
        parent.remove(child)
    return root

def convert(xml_filepath):
    #print('Converting xml to html...')    
    try: tree = etree.parse(xml_filepath)
    except OSError: return 'No file found', 'No file found'
    root = tree.getroot()
    etree.strip_tags(root,etree.Comment,'text', 'fnr', 'fnrtoken', 'fntoken', 'inlineobject', 'link', 'refpt', 'remotelink', 'em', 'a', 'docinfo:bookseqnum')
    #create new doc title element
    doc_title = etree.Element('blockquote')
    #extract from metadata
    doc_title.text = root.xpath('.//docinfo:hierlev/docinfo:hierlev/heading/title/text()', namespaces=NSMAP)[0]
    #remove a load of junk
    root = remove_element('.//docinfo:custom-metafields', root)
    root = remove_element('.//leg:endmatter', root)
    root = remove_element('.//docinfo', root)
    root = remove_element('.//leg:info', root)
    root = remove_element('.//leg:prelim', root)
    #insert the found title from metadata after deleting the metadata
    root.insert(0, doc_title) 
    html = etree.tostring(root)
    html = html.replace(b'entry',b'td')
    html = html.replace(b'row',b'tr')
    html = html.replace(b'title',b'h5')    
    text_only = " ".join(root.xpath("//text()")) #get text within tags only from the whole xml file, join together with a space
    html = html.decode('utf-8') #.encode('latin-1')
    return html, text_only
    # #save to html file
    # f = open(html_filepath, 'wb')
    # intro = b'<html><head><title></title></head><body><div>'   
    # outro = b'</div></body></html>'
    # f.write(intro + html + outro) #html.encode('utf8')
    # f.close()
    # print(html_filepath)


retained_dir = '\\\\lngoxfclup24va\\glpfab1\\build\\EU_Archive\\'
eu_dir = '\\\\lngoxfclup24va\\glpfab4\\Build\\EUCrawler\\_ComparisonContent\\'
log_dir = eu_dir + 'logs\\'
report_template = r'\\lngoxfclup24va\glpfab4\Build\EUCrawler\_ComparisonContent\templates\report-template.html'
three_way_template = r'\\lngoxfclup24va\glpfab4\Build\EUCrawler\_ComparisonContent\templates\side-by-side.html'
redline_only_template = r'\\lngoxfclup24va\glpfab4\Build\EUCrawler\_ComparisonContent\templates\redline-only.html'
NSMAP = {'core': 'http://www.lexisnexis.com/namespace/sslrp/core', 'fn': 'http://www.lexisnexis.com/namespace/sslrp/fn', 'header': 'http://www.lexisnexis.com/namespace/uk/header', 'kh': 'http://www.lexisnexis.com/namespace/uk/kh', 'lnb': 'http://www.lexisnexis.com/namespace/uk/lnb', 'lnci': 'http://www.lexisnexis.com/namespace/common/lnci', 'tr': 'http://www.lexisnexis.com/namespace/sslrp/tr', 'atict': 'http://www.arbortext.com/namespace/atict', 'leg':'http://www.lexis-nexis.com/glp/leg' , 'docinfo':'http://www.lexis-nexis.com/glp/docinfo' }
cleaner = Cleaner(remove_unknown_tags=False, allow_tags=['table', 'tgroup', 'tbody', 'colspec', 'tr', 'td', 'th', 'p', 'h5', 'h4', 'sup', 'blockquote'], page_structure=True)
receiver_email_list = 'daniel.hutchings.1@lexisnexis.co.uk; katy.forrester@lexisnexis.co.uk; rebecca.mitchell@lexisnexis.co.uk'
sender_email = 'LNGUKPSLDigitalEditors@ReedElsevier.com'

logdatetime =  str(time.strftime("%Y%m%d-%H%M%S"))
logdate = str(time.strftime("%Y-%m-%d"))
yesterday = (datetime.datetime.now() - datetime.timedelta(1)).strftime("%Y-%m-%d") #right now minus 1 day, put into the format we need
report_date = str(time.strftime("%#d %B %Y")) #hash before the %d turns off the leading zero for single digit days
archive_list = []

log_filepath = log_dir + 'eu-comparison-' + logdatetime + '.log'
l = open(log_filepath,'w')
l.write("Start EU comparison..."+logdatetime+"\n")
l.close()

report_list=[]
status_report = ''
start = datetime.datetime.now() 

#LOOP THROUGH ALL SOURCE DPSI FOLDERS
directories = list_of_directories(eu_dir) #search directory and add all dir to dict
for directory in directories:
    print(directory)
    if any(x in directory for x in ['logs', 'templates']) == False:
        dpsi = directory.split('\\')[-2]
        print(dpsi)
        sub_directories = list_of_directories(directory+'Crawled_Updates\\')        
        for sub_directory in sub_directories:
            if yesterday in sub_directory: #check if there's a dated folder in the dpsi directory that matches yesterday's date
                #latest_dir = list_of_directories(directory+'Crawled_Updates\\')[0] #most recent dated folder
                latest_dir = sub_directory
                print(latest_dir)
                #lmd = datetime.date.fromtimestamp(os.path.getmtime(latest_dir))
                #print(lmd)
                #print(time.strftime("%Y-%m-%d"))
                not_found=0
                not_found_list=[]
                found=0
                compared=0
                metadata_count=0
                for i, latest_xml_filepath in enumerate(glob.iglob(latest_dir+"*.xml")): #loop through all xml files in the dated folder
                    #print(i, latest_xml_filepath)
                    filename = latest_xml_filepath.split('\\')[-1]
                    if dpsi == '08LS': previous_dir = retained_dir + dpsi + '\\Data_XT_BSN\\'
                    else: previous_dir = retained_dir + dpsi + '\\Data_XT_DS_XT_BSN\\'
                    
                    previous_xml_filepath = previous_dir + filename
                    #print(previous_xml_filepath)
                    previous_html, previous_text = convert(previous_xml_filepath)
                    if previous_html != 'No file found':                
                        #ONCE WE ARE SURE A COMPARABLE FILE EXISTS, CONVERT EU DOC TO HTML
                        latest_html, latest_text = convert(latest_xml_filepath)
                        #DO A LEV DIST COMPARISON ON THE TEXT OF BOTH DOCS
                        lev_dist = levenshtein_distance(previous_text, latest_text)   
                        if lev_dist > 0: #ONLY DO A COMPARISON IF A CHANGE DETECTED IN MAIN TEXT, ELSE ITS A METADATA CHANGE
                            status = 'update'
                            redline_filepath = latest_xml_filepath[0:-4]+ "-redline-only.html"
                            three_way_filepath = latest_xml_filepath[0:-4]+ "-side-by-side.html"
                            #CLEAN UP HTML, ONLY PERMIT GIVEN TAGS IN THE CLEANER DEFINED ABOVE
                            latest_html = html.fromstring(cleaner.clean_html(latest_html))
                            previous_html = html.fromstring(cleaner.clean_html(previous_html))
                            #DIFF - GET REDLINE
                            diffed_version = htmldiff(previous_html, latest_html) #Get the diff html from lxml built in method    
                            #log('Comparison done! Cleaning up compared version...')
                            #PASS IT THROUGH BS TO REMOVE ALL THE NAMESPACES
                            soup = BeautifulSoup(diffed_version, "lxml")
                            diffed_version = str(soup.prettify())
                            soup = BeautifulSoup(etree.tostring(previous_html), "lxml")
                            previous_html = str(soup.prettify())
                            soup = BeautifulSoup(etree.tostring(latest_html), "lxml")
                            latest_html = str(soup.prettify())
                            #CREATE WEBPAGE WITH 3 DIVS - 1 shows previous, 1 shows latest, 1 shows differences in redline
                            #log('Converting comparison html to 3 way html...')
                            convert_to_html(lev_dist, three_way_template, filename, previous_html, latest_html, diffed_version, three_way_filepath)
                            log('Exported to: ' + three_way_filepath)
                            #log('Converting to single redline html...')
                            convert_to_html(lev_dist, redline_only_template, filename, previous_html, latest_html, diffed_version, redline_filepath) 
                            log('Exported to: ' + redline_filepath)
                            compared+=1
                            print(i, filename, ' lev: ', lev_dist, redline_filepath)
                        else:
                            status = 'metadata change'
                            redline_filepath = 'na'
                            three_way_filepath = 'na'
                            metadata_count+=1
                    
                        found+=1
                    else:
                        not_found+=1
                        not_found_list.append(filename)
                        previous_xml_filepath = 'NOT FOUND'
                        lev_dist = 'na'
                        status = 'na'
                        redline_filepath = 'na'
                        three_way_filepath = 'na'
                    report_list.append({'DPSI':dpsi, 'EU_dir':latest_dir, 'retained_dir':previous_dir, 'latest_doc': latest_xml_filepath, 'previous_doc': previous_xml_filepath, 'filename':filename, 'redline_filepath':redline_filepath, 'three_way_filepath':three_way_filepath, 'lev_dist':lev_dist, 'status': status})
                #print(str(not_found_list))
                status_report += '\n' + dpsi 
                status_report += '\nNumber of files not found: ' + str(not_found)
                status_report += '\nNumber of files found: ' + str(found)
                status_report += '\nNumber of files compared: ' + str(compared)
                status_report += '\nNumber of files with metadata changes only: ' + str(metadata_count)
                status_report += '\n\n'

print(report_list)
if len(report_list) > 0:    #if nothing has been added to the report list
        #wait = input("PAUSED...when ready press enter")
    log(status_report)
    df_report = pd.DataFrame(report_list)
    df_report.to_csv(log_dir + 'eu-comparison-' + logdatetime + '.csv', index=False)

    #df_report = pd.read_csv(log_dir + 'eu-comparison-20201224-151531.csv')
    #clean up dataframe before embedding in email

    #filter by redline not na
    df_report = df_report[df_report.redline_filepath != 'na']

    #sort by dpsi
    df_report['lev_dist'] = df_report['lev_dist'].astype(int)
    df_report = df_report.sort_values('lev_dist', ascending = False)

    #add sourcename
    df_report['Source'] = df_report['DPSI']

    #change remove file extension from filename
    df_report['filename'].replace( { r"\.xml" : '' }, inplace = True, regex = True) 
    df_report['Document'] = df_report['filename'].replace( { r"^\d" : '' }, regex = True) 

    #convert redline and compared filepaths to clickable
    df_report['Single redline'] = '<a href="file:///' + df_report['redline_filepath'] + '" target="_blank">View</a>'
    df_report['Side by side'] = '<a href="file:///' + df_report['three_way_filepath'] + '" target="_blank">View</a>'

    #remove latest_doc, previous_doc, retained_dir, EU_dir, 
    #del df_report['filename'], df_report['latest_doc'], df_report['previous_doc'], df_report['retained_dir'], df_report['EU_dir'], df_report['status'], df_report['DPSI'], df_report['redline_filepath'], df_report['three_way_filepath']
    df_report = df_report[['Document', 'Source', 'lev_dist', 'Single redline', 'Side by side']]
    pd.set_option('display.max_colwidth', -1) #stop the dataframe from truncating cell contents. This needs to be set if you want html links to work in cell contents

    if len(df_report) > 0: #only create and email the html if there's anything in the filtered list to send

        with open(report_template,'r') as template:
            htmltemplate = template.read()

        change_table = df_report.to_html(na_rep = " ",index = False,  classes="table table-bordered text-left table-striped table-hover table-sm")

        report_filepath = log_dir + 'eu-comparison-report-' + logdate + '.html'
        with open(report_filepath,'w', encoding='utf-8') as f:            
            html = htmltemplate.replace('__DATE__', report_date).replace('__CHANGELEN__', str(len(df_report))).replace('__DFCHANGES__', change_table) #.replace('__STATUS_REPORT__', status_report)
            html = html.replace('&lt;', '<').replace('&gt;', '>').replace('\\', '/').replace('\u2011','-').replace('\u2015','&#8213;').replace('ī','').replace('─','&mdash;')
            f.write(html)
            f.close()
            pass

        log("Exported html report to..." + report_filepath)

        email.send('EU comparison report - ' + logdate, html, receiver_email_list, sender_email)        
        metrics.add(log_dir+r'\eu-comparison-metrics.csv', 1, 'EU comparison', 'Number of files compared: ' + str(compared))
    else:
        log('After filtering the report it appears there were no entries, so no html was created or sent')
else: 
    log('No items were added to the report, probably because there were no dated folders with today\'s date... ' + logdate + ' ... Maybe yesterday was a weekend where no one was updating any EU sources...')
log("Finished! Time taken..." + str(datetime.datetime.now() - start))