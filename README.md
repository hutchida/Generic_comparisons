# Generic_comparisons

This is essentially a Html comparison tool that makes use of the Python module lxml's built in diff function. The script looks in two specified directories for a 'latest' and 'previous' version of a document. It converts any docx, xml, or pdf to html first, then the comparison takes place. Two html files are produced in an output folder. One shows the final merged file with redline changes on its own, and the other shows the previous, the latest, and the merged with redline side by side. 
