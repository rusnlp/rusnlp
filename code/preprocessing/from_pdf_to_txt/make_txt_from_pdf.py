from os import path, walk, makedirs
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pickle import dump, load

conferences = ['Dialogue', 'AIST', 'AINL', 'RuSSIR']
saving_dir = path.join('..', '..', '..', '..', '..', 'data', 'TXTs', 'RAW')
source_dir = path.join('..', '..', '..', '..', '..', 'data', 'PDFs')
first_year = 2000
last_year = 2018


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = open(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ''
    maxpages = 0
    caching = True
    pagenos = set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)
    text = retstr.getvalue()
    fp.close()
    device.close()
    retstr.close()
    return text


def convert_all_pdf_to_text():
    papers = []
    mapping = {}
    for conference in conferences:
        for year in range(first_year, last_year):
            for root, dirs, files in walk(path.join(source_dir, conference, str(year)), 'rb'):
                for file in files:
                    try:
                        papers.append(convert_pdf_to_txt('{}/{}'.format(root, file)))
                        mapping['{}/{}'.format(root, file)] = str(path.join(saving_dir, conference, str(year))) + str
                    except:
                        continue
            for paper_id, paper in enumerate(papers):
                directory = path.join(saving_dir, conference, str(year))
                if not path.exists(directory):
                    makedirs(directory)
                with open(path.join(directory, str(paper_id)) + '.txt', 'w') as writefile:
                    writefile.write(paper)
            papers = []
    return mapping


if __name__ == '__main__':
    mapping = convert_all_pdf_to_text()
    with open(path.join('pickles', 'mapping.pickle'), 'wb') as f:
        dump(mapping, f)
