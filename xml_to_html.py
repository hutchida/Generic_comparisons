import glob
import os
from lxml import etree
import re

NSMAP_Prec = {'lnb-prec': 'http://www.lexisnexis.com/namespace/uk/precedent', 'core': 'http://www.lexisnexis.com/namespace/sslrp/core', 'fn': 'http://www.lexisnexis.com/namespace/sslrp/fn', 'header': 'http://www.lexisnexis.com/namespace/uk/header', 'kh': 'http://www.lexisnexis.com/namespace/uk/kh', 'lnb': 'http://www.lexisnexis.com/namespace/uk/lnb', 'lnci': 'http://www.lexisnexis.com/namespace/common/lnci', 'tr': 'http://www.lexisnexis.com/namespace/sslrp/tr', 'atict': 'http://www.arbortext.com/namespace/atict'}       
NSMAP = {'core': 'http://www.lexisnexis.com/namespace/sslrp/core', 'fn': 'http://www.lexisnexis.com/namespace/sslrp/fn', 'header': 'http://www.lexisnexis.com/namespace/uk/header', 'kh': 'http://www.lexisnexis.com/namespace/uk/kh', 'lnb': 'http://www.lexisnexis.com/namespace/uk/lnb', 'lnci': 'http://www.lexisnexis.com/namespace/common/lnci', 'tr': 'http://www.lexisnexis.com/namespace/sslrp/tr', 'atict': 'http://www.arbortext.com/namespace/atict', 'leg':'http://www.lexis-nexis.com/glp/leg' , 'docinfo':'http://www.lexis-nexis.com/glp/docinfo' }

def remove_element(xpath, root):
    for child in root.xpath(xpath, namespaces=NSMAP):
        print(child)
        parent = child.getparent()
        parent.remove(child)
    return root

def convert(directory):
    print('Converting xml to html...')
    for i, xml_filepath in enumerate(glob.iglob(directory+"*.xml")):
        print(xml_filepath)
        html_filepath = xml_filepath[0:-4]+ ".html"
        tree = etree.parse(xml_filepath)
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
        #save to html file
        f = open(html_filepath, 'wb')
        intro = b'<html><head><title></title></head><body><div>'   
        outro = b'</div></body></html>'
        f.write(intro + html + outro) #html.encode('utf8')
        f.close()
        print(html_filepath)
