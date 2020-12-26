import glob
import os
from pdf2docx import parse

def convert(directory):
    print('Converting pdf to docx...')
    for i, pdf_filepath in enumerate(glob.iglob(directory+"*.pdf")):
        #filename = doc.split('\\')[-1]
        docx_filepath = pdf_filepath[0:-4]+ ".docx"
        parse(pdf_filepath, docx_filepath)#, start=0, end=1) #start and end are for page ranges
        print(docx_filepath)
