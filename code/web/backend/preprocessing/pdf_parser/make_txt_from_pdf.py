from os import path, walk, makedirs
from io import StringIO
from pdfminer3.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer3.converter import TextConverter
from pdfminer3.layout import LAParams
from pdfminer3.pdfpage import PDFPage


def convert_pdf_to_txt(filepath):
    rm = PDFResourceManager()
    sio = StringIO()
    device = TextConverter(rm, sio, codec='utf-8', laparams=LAParams())
    interpreter = PDFPageInterpreter(rm, device)
    with open(filepath, 'rb') as fp:
        for page in PDFPage.get_pages(fp=fp, pagenos=set(), maxpages=0, password='',
                                      caching=True, check_extractable=True):
            interpreter.process_page(page)
    text = sio.getvalue()
    device.close()
    sio.close()
    return text


def write_errors(errors):
    with open('errors.txt', 'w', encoding='utf-8') as f:
        for error in errors:
            f.write('{}\n'.format(error))


def write_file(root, file, text):
    with open(path.join(root.replace(source_dir, saving_dir), file).replace('.pdf', '.txt'), 'w',
              encoding='utf-8') as f:
        f.write(text)


def convert(source_dir, saving_dir):
    errors = []
    for root, dirs, files in walk(source_dir):
        for file in files:
            if not file.endswith('pdf'):
                errors.append(path.join(root, file))
                continue
            text = convert_pdf_to_txt(path.join(root, file))
            try:
                write_file(root, file, text)
            except FileNotFoundError:
                makedirs(path.dirname(path.join(root.replace(source_dir, saving_dir), file)))
                write_file(root, file, text)
    write_errors(errors)


if __name__ == '__main__':
    saving_dir = 'parsed'
    source_dir = 'sources'
    convert(source_dir, saving_dir)

