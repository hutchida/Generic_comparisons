import glob
import os
from lxml import etree
import re

#NSMAP_Prec = {'lnb-prec': 'http://www.lexisnexis.com/namespace/uk/precedent', 'core': 'http://www.lexisnexis.com/namespace/sslrp/core', 'fn': 'http://www.lexisnexis.com/namespace/sslrp/fn', 'header': 'http://www.lexisnexis.com/namespace/uk/header', 'kh': 'http://www.lexisnexis.com/namespace/uk/kh', 'lnb': 'http://www.lexisnexis.com/namespace/uk/lnb', 'lnci': 'http://www.lexisnexis.com/namespace/common/lnci', 'tr': 'http://www.lexisnexis.com/namespace/sslrp/tr', 'atict': 'http://www.arbortext.com/namespace/atict'}       
NSMAP = {'lnb-prec': 'http://www.lexisnexis.com/namespace/uk/precedent', 'core': 'http://www.lexisnexis.com/namespace/sslrp/core', 'fn': 'http://www.lexisnexis.com/namespace/sslrp/fn', 'header': 'http://www.lexisnexis.com/namespace/uk/header', 'kh': 'http://www.lexisnexis.com/namespace/uk/kh', 'lnb': 'http://www.lexisnexis.com/namespace/uk/lnb', 'lnci': 'http://www.lexisnexis.com/namespace/common/lnci', 'tr': 'http://www.lexisnexis.com/namespace/sslrp/tr', 'atict': 'http://www.arbortext.com/namespace/atict', 'leg':'http://www.lexis-nexis.com/glp/leg' , 'docinfo':'http://www.lexis-nexis.com/glp/docinfo' }

def remove_element(xpath, root, NSMAP):
    for child in root.xpath(xpath, namespaces=NSMAP):
        print(child)
        parent = child.getparent()
        parent.remove(child)
    return root

def convert(directory):    
    print('Converting xml to html...')
    for i, xml_filepath in enumerate(glob.iglob(directory+"*.xml")):
        print(xml_filepath)        
        print('Detecting type of markup...')
        xml = open(xml_filepath, 'r', encoding='utf-8')
        xml = xml.read()
        if xml.find('DOCTYPE LEGDOC') > -1 : 
            print('Doc is Legislation...')
            doc_title_xpath= './/docinfo:hierlev/docinfo:hierlev/heading/title/text()'
        if xml.find('DOCTYPE kh:document') > -1 : 
            print('Doc is Knowhow...')
            doc_title_xpath= './/kh:document-title/text()'
        if xml.find('lnb-prec:precedent') > -1 : 
            print('Doc is a Precedent...')
            doc_title_xpath= './/lnb-prec:title/lnb-prec:text/text()'
            #NSMAP = NSMAP_Prec
            
        html_filepath = xml_filepath[0:-4]+ ".html"
        tree = etree.parse(xml_filepath)
        root = tree.getroot()
        etree.strip_tags(root,etree.Comment,'text', 'fnr', 'fnrtoken', 'fntoken', 'inlineobject', 'link', 'refpt', 'remotelink', 'em', 'a', 'docinfo:bookseqnum')
        #create new doc title element
        doc_title = etree.Element('blockquote')
        #extract from metadata
        doc_title.text = root.xpath(doc_title_xpath, namespaces=NSMAP)[0]        
        print(doc_title.text)
        #remove a load of junk
        root = remove_element('.//docinfo:custom-metafields', root, NSMAP)
        root = remove_element('.//leg:endmatter', root, NSMAP)
        root = remove_element('.//docinfo', root, NSMAP)
        root = remove_element('.//leg:info', root, NSMAP)
        root = remove_element('.//leg:prelim', root, NSMAP)
        root = remove_element('.//header:metadata', root, NSMAP)
        #insert the found title from metadata after deleting the metadata
        root.insert(0, doc_title) 
        html = etree.tostring(root)
        html = html.replace(b'entry',b'td')
        html = html.replace(b'row',b'tr')
        html = html.replace(b'title',b'h5')
        #save to html file
        f = open(html_filepath, 'wb')
        intro = b'<html><head><title></title></head><body><div>'   
        outro = b'</div></body></html>'
        f.write(intro + html + outro) #html.encode('utf8')
        f.close()
        print(html_filepath)
