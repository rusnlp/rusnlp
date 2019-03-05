from os import walk, path, makedirs
from collections import defaultdict
from pickle import dump, load
from langdetect import detect_langs
from platform import system
from hashlib import sha1
from transliterate import translit
import json

path_to_dataset = path.join('DATASET', 'conferences')
splitter = '%\n%\n'
english_label = '==ENGLISH==\n'
russian_label = '==RUSSIAN==\n'
number_of_splits = 4
serialized_name = 'tmp.pickle'
empty_symbol = '-'
minimum_text_length = 50
authors_list = {}
global_affils = set()


def get_data_from_filename(filename):
    metadata = defaultdict(lambda: {})
    if system() == 'Windows':
        chunks = filename.split('\\')
    else:
        chunks = filename.split('/')
    year = chunks[~0]
    conference = chunks[~1]
    metadata['year'] = year
    metadata['conference'] = conference
    metadata['path'] = filename
    return year, conference, metadata


def set_language_metadata(lang_1_tag, lang_2_tag, metadata):
    metadata['language_1']['lang'] = lang_1_tag
    if not lang_2_tag:
        return metadata
    metadata['language_2']['lang'] = lang_2_tag
    return metadata


def define_first_and_last_to_seek(text, filepath, metadata):
    if english_label in text and russian_label in text:
        if text.find(english_label) > text.find(russian_label):
            first_to_seek = russian_label
            last_to_seek = english_label
            metadata = set_language_metadata('ru', 'en', metadata)
        else:
            first_to_seek = english_label
            last_to_seek = russian_label
            metadata = set_language_metadata('en', 'ru', metadata)
    elif english_label in text and russian_label not in text:
        first_to_seek = english_label
        last_to_seek = None
        metadata = set_language_metadata('en', None, metadata)
    elif english_label not in text and russian_label in text:
        first_to_seek = russian_label
        last_to_seek = None
        metadata = set_language_metadata('ru', None, metadata)
    else:
        with open('errors.txt', 'a') as f:
            f.write('{}\n'.format(filepath))
    return first_to_seek, last_to_seek, metadata


def fillna(metadata_):
    metadata = metadata_
    source = 'language_2'
    target = 'language_1'
    if 'language_1' in metadata and 'language_2' in metadata:
        if metadata['language_2']['authors'][0]['author'] == empty_symbol:
            source = 'language_1'
            target = 'language_2'
        target_lang = metadata[target]['lang']
        reverse = False
        if target_lang == 'en':
            target_lang = metadata[source]['lang']
            reverse = True
        metadata[target]['authors'] = []
        for author in metadata[source]['authors']:
            author_trans = defaultdict(lambda: [])
            author_trans['author'] = translit(author['author'], target_lang, reversed=reverse)
            for affiliation in author['affiliations']:
                author_trans['affiliations'].append(translit(affiliation, target_lang, reversed=reverse))
            author_trans['email'] = author['email']
            metadata[target]['authors'].append(dict(author_trans))
    return metadata


def add_author_metadata(author):
    if '\n' not in author:
        return empty_symbol
    data = {}
    data_fields = author.split('\n')
    for k, v in authors_list.items():
        if data_fields[0] in v:
            data['author'] = k
        else:
            data['author'] = data_fields[0]
    data['affiliations'] = data_fields[1].split(';')
    for affil in data_fields[1].split(';'):
        global_affils.add(affil)
    try:
        data['email'] = data_fields[2].split(',')
    except:
        data['email'] = '-'
    return data


def parse_authors(authors_list):
    authors = []
    if '%\n' not in authors_list:
        author = authors_list
        authors.append(add_author_metadata(author))
        return authors
    for author in authors_list.split('%\n'):
        authors.append(add_author_metadata(author))
    return authors


def parse_keywords(keyword_string):
    return keyword_string.replace('\n', ' ').strip().split(',')


def parse_title(title):
    return sub(' +', ' ', title.replace('%', '').replace('\n', ' ').strip().lower().title())


def generate_hash(text_metadata, title):
    hasher = sha1()
    hasher.update(translit(title.replace(' ', '_').lower(), 'ru', reversed=True).encode())
    text_metadata['hash'] = '{}_{}_{}'.format(metadata['conference'], metadata['year'], str(hasher.hexdigest())).lower()
    return text_metadata


def update_metadata(metadata, language_num, chunks):
    metadata[language_num]['title'] = parse_title(chunks[0])
    metadata[language_num]['authors'] = parse_authors(chunks[1])
    metadata[language_num]['abstract'] = chunks[2].replace('\n', ' ').strip()
    try:
        metadata[language_num]['keywords'] = parse_keywords(chunks[3])
    except IndexError:
        print(parse_title(chunks[0]))
    text = None
    if len(chunks) > number_of_splits:
        text = chunks[4]
    return metadata, text


def detext_text_language(text_metadata, text):
    language = '-'
    probability = '-'
    if len(text) > minimum_text_length:
        lang = detect_langs(text)
        language = lang[0].lang
        probability = round(lang[0].prob, 2)
    text_metadata['language'] = language
    text_metadata['probability'] = probability
    return text_metadata


def update_text_metadata(text, title, url):
    if not text:
        text = '-'
    text_metadata = {}
    text_metadata['token_length'] = len(text.split())
    text_metadata['url'] = url
    text_metadata = detext_text_language(text_metadata, text)
    text_medatata = generate_hash(text_metadata, title)
    return text_metadata


def find_url(text, metadata):
    url = 'not yet parsed'
    if text[0] == '%' and text[2] != '%':
        url = text.split('%\n%\n', 1)[0][2:].replace('\n', '')
    return url


def parse_paper(text, filepath, metadata):
    first_to_seek, last_to_seek, metadata = define_first_and_last_to_seek(text, filepath, metadata)
    url = find_url(text, metadata)
    fts_pos = text.find(first_to_seek) + len(first_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_1', text[fts_pos:].split(splitter, number_of_splits))
    if not last_to_seek:
        metadata['text'] = update_text_metadata(text, metadata['language_1']['title'], url)
        metadata['text-text'] = text
        return dict(metadata)
    lts_pos = text.find(last_to_seek) + len(last_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_2', text[lts_pos:].split(splitter, number_of_splits))
    if metadata['language_1']['title'] != '-':
        metadata['text'] = update_text_metadata(text, metadata['language_1']['title'], url)
    elif metadata['language_2']['title'] != '-':
        metadata['text'] = update_text_metadata(text, metadata['language_2']['title'], url)
    metadata['text-text'] = text
    return dict(metadata)
    metadata['text-text'] = text
    return dict(metadata)


def serialize_data(data):
    with open(serialized_name, 'wb') as f:
        dump(data, f)


if __name__ == '__main__':
    with open('authors.pickle', 'rb') as f:
        authors_list = load(f)
    data = {}
    for root, dirs, files in walk(path_to_dataset):
        for file in files:
            if path.splitext(file)[1] == '.txt':
                name_of_file = path.splitext(file)[0]
                with open(path.join(root, file), 'r', encoding='utf-8') as f:
                    read = f.read()
                    metadata = parse_paper(read, path.join(root, file), metadata)
                    metadata = fillna(metadata)
                    year, conference, metadata = get_data_from_filename(root)
                    data[path.join(root, file)] = metadata
                    datapath_ = path.join('DATASET')
                    if not path.exists(
                            path.join(datapath_, conference, year, name_of_file)):
                        makedirs(path.join(datapath_, conference, year, name_of_file))
                    with open(path.join(datapath_, conference, year, name_of_file,
                                        'lang_1' + '.json'), 'w') as f:
                        json.dump(metadata['language_1'], f, indent=4, sort_keys=True)
                    try:
                        with open(path.join(datapath_, conference, year, name_of_file,
                                            'lang_2' + '.json'), 'w') as f:
                            json.dump(metadata['language_2'], f, indent=4, sort_keys=True)
                    except KeyError:
                        pass
                    with open(path.join(datapath_, conference, year, name_of_file,
                                        'common' + '.json'), 'w') as f:
                        json.dump(metadata['text'], f, indent=4, sort_keys=True)
                    try:
                        with open(path.join(datapath_, conference, year, name_of_file,
                                            'text' + '.txt'), 'w', encoding='utf-8') as f:
                            f.write(metadata['text-text'])
                    except TypeError:
                        pass
                    with open('affiliations_set', 'wb') as f:
                        dump(global_affils, f)
    serialize_data(data)
    print('Done')
