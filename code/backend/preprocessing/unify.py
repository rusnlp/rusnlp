#!/usr/bin/python
# coding: utf-8

# Produced from https://github.com/TatianaShavrina/taiga/blob/master/tagging_pipeline/unify.py
import re
import os


# функция использует дефолтную библиотеку
def list_replace(search, replacement, text):
    search = [el for el in search if el in text]
    for c in search:
        text = text.replace(c, replacement)
    return text


def unify_sym(text):  # принимает строку в юникоде
    # пробел
    # 2000/2001/2002/2004/2005/2006/2007/2008/2009/200A/200B/202F/205F/2060/3000 --> 2003
    text = list_replace(
        '\xa0\u2000\u2001\u2002\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u202F\u205F\u2060\u3000',
        ' ', text)

    # 2 пробела в один и две табуляции в 1
    # здесь оставлены регулярки, т.к. здесь нужно заменять последовательность из 2 символов
    text = re.sub('  ', ' ', text)
    text = re.sub('\t\t', '\t', text)

    # многоточие --> три точки
    # text = list_replace('…', '...', text)

    # тильда к одному виду 2241/224B/2E2F/0483/--> 223D
    text = list_replace('\u2241\u224B\u2E2F\u0483', '\u223D', text)

    return text


path = "<your path>"

for root, dirs, files in os.walk(path):
    for filename in files:
        if filename.endswith('.txt'):
            print(root, filename)
            os.makedirs(os.path.join(root.replace("data-txt", "data-txt\\unified")), exist_ok=True)
            with open(os.path.join(root, filename), 'r', encoding='utf-8') as f, \
                    open(os.path.join(root.replace("data-txt", "data-txt\\unified"), filename),
                         'w', encoding='utf-8', newline="\n") as w:
                for line in f:
                    w.write(unify_sym(line[:-1])+"\n")
