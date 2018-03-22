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
FILEPATH = 'filepath'
URL = 'url'
ID = 'id'
saving_dir = '../prepared-data'
urls_dir = '../../data/URLs'
conferences = ['Dialogue', 'AIST', 'AINL']


def remove_bad(string):
    return sub('\t|\xa0', '', string.replace('\n', ' ')).strip()

def make_alpha(string):
    return sub('[^a-zA-Zа-яА-Я ]+', '', string)


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
    else:
        keywords = '-'
    return [word.strip().lower() for word in keywords]


def add_paper_data(filepath, content, conference, year, urls):
    if int(year) >= 2007:
        return parse_dialogue_2007_plus(filepath, content, conference, year, urls)
    else:
        return parse_dialogue_until_2007(filepath, content, conference, year, urls)


def parse_dialogue_until_2007(filepath, content, conference, year, urls):
    splits = content.replace('  \n', '\n').replace('\t', '').replace('\xa0', '').replace('\n \n', '\n\n').replace('\n\n \n', '\n\n\n').replace('\n \n\n', '\n\n\n').split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('\n')[0].strip()
        try:
            d[EMAIL] = author.split('\n')[2].strip()
        except:
            d[EMAIL] = '-'
        try:
            d[AFFILIATION] = author.split('\n')[1].strip()
        except:
            d[AFFILIATION] = '-'
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0].strip()
    d[ABSTRACT] = splits[2].strip()
    d[TEXT] = splits[3:]
    try:
        if 'Keywords:' in content:
            text = content.replace('-\n', '')
            kw_index = text.index('Keywords:')
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        elif 'Kлючевые слова:' in content:
            text = content.replace('-\n', '')
            kw_index = text.index('Kлючевые слова:')
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        elif 'Key words:' in content:
            text = content.replace('-\n', '')
            kw_index = text.index('Key words:')
            d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
        else:
             d[KEYWORDS] = '-'
    except:
        d[KEYWORDS] = '-'
    data[TEXT] = d
    data[CONFERENCE] = conference.strip()
    data[YEAR] = year.strip()
    data[FILEPATH] = filepath
    data[ID] = '{}_{}_{}'.format(conference, year, make_alpha(d[TITLE]).replace(' ', '_')).lower()
    try:
        data[URL] = urls[filepath.split('Dialogue/')[1]]
    except KeyError:
        data[URL] = '-'
    return data


def parse_dialogue_2007_plus(filepath, content, conference, year, urls):
    splits = content.replace('\n \n', '\n\n').replace('\n\n \n', '\n\n\n').split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('(')[0].strip()
        d[EMAIL] = author[author.find('(') + 1:author.find(')')].strip()
        d[AFFILIATION] = author.split(')')[1].strip()
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0].strip()
    d[ABSTRACT] = splits[2].strip()
    d[TEXT] = splits[3:]
    if 'Keywords:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Keywords:')
        d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
    elif 'Key words:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Key words:')
        d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
    elif 'Kлючевые слова:' in content:
        text = content.replace('-\n', '')
        kw_index = text.index('Kлючевые слова:')
        d[KEYWORDS] = text[kw_index:text.index('\n\n', kw_index)].replace('\n', ' ').split(': ', 1)[1].strip().lower()
    else:
         d[KEYWORDS] = '-'
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    data[FILEPATH] = filepath
    data[ID] = '{}_{}_{}'.format(conference, year, make_alpha(d[TITLE]).replace(' ', '_')).lower()
    try:
        data[URL] = urls[filepath.split('Dialogue/')[1]]
    except KeyError:
        data[URL] = '-'
    return data


def parse_dialogue_all():
    result = []
    with open('../../prepared-data/mapping.pickle', 'rb') as f:
        mapping = load(f)
    with open(path.join(urls_dir, 'url_fullpath_mapping_dialog_found_test.tsv'), 'r', encoding='utf-8') as f:
        urls_temp = f.read().split('\n')
    urls = {}
    for url in urls_temp:
        url_splitted = url.split('\t')
        try:
            mapped_url = mapping['../data/' + url_splitted[1]].split('Dialogue/')[1]
            urls[mapped_url] = url_splitted[0].strip()
        except (IndexError, KeyError):
            urls[url.strip().lower()] = '-'
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[0]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r', encoding='utf-8') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                result.append(add_paper_data(path.join(root, file), input_stream.read(), conferences[0], year, urls))

    # with open('{}.pickle'.format(conferences[0]), 'wb') as f:
    #     dump(result, f)

    return result


def parse_aist(filepath, content, conference, year, urls):
    splits = content.split('\n\n\n')
    data = {}
    authors = []
    for author in splits[1].split('\n\n'):
        d = {}
        d[NAME] = author.split('\n')[0].strip()
        d[EMAIL] = author.split('\n')[2].strip()
        d[AFFILIATION] = author.split('\n')[1].strip()
        authors.append(d)
    data[AUTHOR] = authors
    d = {}
    d[TITLE] = splits[0].strip()
    d[ABSTRACT] = splits[2].strip()
    d[KEYWORDS] = ', '.join(parse_keywords(splits[3])).replace('.','').strip()
    d[TEXT] = splits[4:]
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    data[FILEPATH] = filepath
    data[ID] = '{}_{}_{}'.format(conference, year, make_alpha(d[TITLE]).replace(' ', '_')).lower()
    try:
        data[URL] = urls[splits[0].lower().strip()]
    except KeyError:
        data[URL] = '-'
    return data


def parse_aist_all():
    result = []
    with open(path.join(urls_dir, 'url_mapping_aist.tsv'), 'r', encoding='utf-8') as f:
        urls_temp = f.read().split('\n')
    urls = {}
    for url in urls_temp:
        url_splitted = url.split('\t')
        try:
            urls[url_splitted[1].lower()] = url_splitted[0].strip()
        except IndexError:
            urls[url.strip().lower()] = '-'
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[1]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r', encoding='utf-8') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                papers = input_stream.read().split('==')
                result = [parse_aist(path.join(root, file), paper, conferences[1], year, urls) for paper in papers]

    # with open('{}.pickle'.format(conferences[1]), 'wb') as f:
    #     dump(result, f)

    return result


def parse_ainl(filepath, content, conference, year, urls):
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
    d[TEXT] = ' '.join(splits[3:]).encode('utf-8')
    data[TEXT] = d
    data[CONFERENCE] = conference
    data[YEAR] = year
    data[ID] = '{}_{}_{}'.format(conference, year, make_alpha(d[TITLE]).replace(' ', '_')).lower()
    try:
        data[URL] = urls[splits[0].lower().strip()]
    except KeyError:
        data[URL] = '-'
    return data


def parse_ainl_all():
    result = []
    with open(path.join(urls_dir, 'url_mapping_ainl.tsv'), 'r', encoding='utf-8') as f:
        urls_temp = f.read().split('\n')
    urls = {}
    for url in urls_temp:
        url_splitted = url.split('\t')
        try:
            urls[url_splitted[1].lower()] = url_splitted[0].strip()
        except IndexError:
            urls[url.strip().lower()] = '-'
    for root, dirs, files in walk(path.join('..', saving_dir, 'conferences', conferences[2]), 'r'):
         for file in files:
            with open(path.join(root, file), 'r', encoding='utf-8') as input_stream:
                if encounter_utility_file(file):
                    continue
                year = root.split('/')[~0]
                papers = input_stream.read().split('==')
                result = [parse_ainl(path.join(root, file), paper, conferences[2], year, urls) for paper in papers]

    # with open('{}.pickle'.format(conferences[2]), 'wb') as f:
    #      dump(result, f)

    return result


if __name__ == '__main__':

    result = []
    result += parse_dialogue_all()
    result += parse_aist_all()
    result += parse_ainl_all()

    for ind, data in enumerate(result[:-1]):
        with open(path.join('data', '{}.txt'.format(ind)), 'w', encoding='utf-8') as f:
            f.write(str(data[ID]) + '\n' + ' '.join(data[TEXT][TEXT]))

    with open('all.pickle', 'wb') as f:
         dump(result, f)
