from os import path, walk, makedirs
from collections import defaultdict
from itertools import takewhile
from re import compile, sub
from pickle import dump, load


TITLE = 'title'
AUTHOR = 'author'
NAME = 'name'
AFFILIATION = 'affiliation'
EMAIL = 'email'
TEXT = 'text'
REFERENCES = 'references'
REF_MARKER = '\xa0 ЛИТЕРАТУРА \xa0'
KEYWORDS_MARKER = 'Ключевые слова'
KEYWORDS = 'keywords'
ABSTRACT = 'abstract'
CONFERENCE = 'conference'
YEAR = 'year'


def remove_bad(string):
    return sub('\t|\xa0', '', string.replace('\n', ' ')).strip()


def encounter_utility_file(filename):
    if any(name in filename for name in ['DS_Store', 'zip']):
        return True


def parse_keywords(keywords):
    keywords = keywords.replace('-\n','').replace('\n', ' ').replace('\x01', '').replace('\xa0', '')
    if 'Ключевые  слова:' in keywords:
        keywords = keywords.split('Ключевые  слова:')[1]
    elif 'Ключевые слова:' in keywords:
        keywords = keywords.split('Ключевые слова:')[1]
    elif 'Keywords:' in keywords:
        keywords = keywords.split('Keywords:')[1]
    if ', ' in keywords:
        keywords = keywords.split(', ')
    elif '·' in keywords:
        keywords = keywords.split('·')
    elif ';' in keywords:
        keywords = keywords.split(';')
    elif '  ' in keywords:
        keywords = keywords.split('  ')
    return [word.strip().lower() for word in keywords]


def add_paper_data(content, conference, year):
    if int(year) >= 2007:
        parse_dialogue_2007_plus(content, conference, year)
    else:
        parse_dialogue_until_2007(content, conference, year)


def parse_dialogue_until_2007(content, conference, year):
    if int(year) == 2002:
        return
    splits = content.replace('  \n', '\n').replace('\t', '').replace('\xa0', '').replace('\n \n', '\n\n').replace('\n\n \n', '\n\n\n').replace('\n \n\n', '\n\n\n').split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('\n')[0]
        d[EMAIL] = author.split('\n')[2]
        d[AFFILIATION] = author.split('\n')[1]
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0]
    d[ABSTRACT] = splits[2]
    d[TEXT] = splits[3:]
    if 'Keywords:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Keywords:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    elif 'Kлючевые слова:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Kлючевые слова:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    elif 'Key words:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Key words:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    else:
         d[KEYWORDS] = '-'
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    result.append(data)


def parse_dialogue_2007_plus(content, conference, year):
    splits = content.replace('\n \n', '\n\n').replace('\n\n \n', '\n\n\n').split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('(')[0]
        d[EMAIL] = author[author.find('(') + 1:author.find(')')]
        d[AFFILIATION] = author.split(')')[1]
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0]
    d[ABSTRACT] = splits[2]
    d[TEXT] = splits[3:]
    if 'Keywords:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Keywords:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    elif 'Key words:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Key words:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    elif 'Kлючевые слова:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Kлючевые слова:')
        try:
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        except:
            print(text)
    else:
         d[KEYWORDS] = '-'
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    result.append(data)


def parse_dialogue_all():
    result = []
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[0]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                add_paper_data(input_stream.read(), conferences[0], year)

    with open('{}.pickle'.format(conferences[0]), 'wb') as f:
        dump(result, f)


def parse_aist(content, conference, year):
    splits = content.split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('\n')[0]
        d[EMAIL] = author.split('\n')[2]
        d[AFFILIATION] = author.split('\n')[1]
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0]
    d[ABSTRACT] = splits[2]
    d[KEYWORDS] = ', '.join(parse_keywords(splits[3])).replace('.','')
    d[TEXT] = splits[4:]
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    result.append(data)


def parse_aist_all():
    result = []
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[1]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                papers = input_stream.read().split('==')
                for paper in papers:
                    parse_aist(paper, conferences[1], year)
    with open('{}.pickle'.format(conferences[1]), 'wb') as f:
        dump(result, f)


def parse_ainl(content, conference, year):
    splits = content.split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('\n')[0]
        d[EMAIL] = author.split('\n')[2]
        d[AFFILIATION] = author.split('\n')[1]
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0]
    d[ABSTRACT] = splits[2]
    if str(year) != '2015':
        d[KEYWORDS] = ', '.join(parse_keywords(splits[3])).replace('.','')
    else:
        d[KEYWORDS] = '-'
    d[TEXT] = splits[3:]
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    result.append(data)


def parse_ainl_all():
    result = []
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[2]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                papers = input_stream.read().split('==')
                for paper in papers:
                    parse_ainl(paper, conferences[2], year)
    with open('{}.pickle'.format(conferences[2]), 'wb') as f:
         dump(result, f)


if __name__ == '__main__':
    parse_dialogue_all()
    parse_aist_all()
    parse_ainl_all()
