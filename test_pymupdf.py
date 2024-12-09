import pymupdf

pdf = pymupdf.open('test.pdf', filetype='pdf')

pdf_page = pdf[0]

pdf_page.get_pixmap().writePNG('test.png')