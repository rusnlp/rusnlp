from os import walk, path
from collections import defaultdict
from pickle import dump
from langdetect import detect_langs

path_to_dataset = path.join('..', '..', '..', '..', '..', 'gitlab-rusnlp', 'rusnlp', 'DATASET', 'conferences/')
splitter = '%\n%\n'
english_label = '==ENGLISH==\n'
russian_label = '==RUSSIAN==\n'
number_of_splits = 4
serialized_name = 'tmp.pickle'
empty_symbol = '-'
minimum_text_length = 50


def get_data_from_filename(filename):
    chunks = filename.split('/')
    year = chunks[~0]
    conference = chunks[~1]
    return year, conference


def set_language_metadata(lang_1_tag, lang_2_tag):
    metadata = defaultdict(lambda: {})
    metadata['language_1']['lang'] = lang_1_tag
    if not lang_2_tag:
        return metadata
    metadata['language_2']['lang'] = lang_2_tag
    return metadata


def define_first_and_last_to_seek(text):
    if english_label in text and russian_label in text:
        if text.find(english_label) > text.find(russian_label):
            first_to_seek = russian_label
            last_to_seek = english_label
            metadata = set_language_metadata('ru', 'en')
        else:
            first_to_seek = english_label
            last_to_seek = russian_label
            metadata = set_language_metadata('en', 'ru')
    elif english_label in text and russian_label not in text:
        first_to_seek = english_label
        last_to_seek = None
        metadata = set_language_metadata('en', None)
    elif english_label not in text and russian_label in text:
        first_to_seek = russian_label
        last_to_seek = None
        metadata = set_language_metadata('ru', None)
    else:
        raise Exception('WTF')
    return first_to_seek, last_to_seek, metadata


def add_author_metadata(author):
    if '\n' not in 'author':
        return empty_symbol
    data = {}
    data_fields = author.split('\n')
    data['author'] = data_fields[0]
    data['affiliations'] = data_fields[1].split(';')
    data['email'] = data_fields[2].split(',')
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
    return title.replace('\n', ' ').strip().lower().title()


def update_metadata(metadata, language_num, chunks):
    metadata[language_num]['title'] = parse_title(chunks[0])
    metadata[language_num]['authors'] = parse_authors(chunks[1])
    metadata[language_num]['abstract'] = chunks[2].replace('\n', ' ').strip()
    metadata[language_num]['keywords'] = parse_keywords(chunks[3])
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


def update_text_metadata(text):
    if not text:
        text = '-'
    text_metadata = {}
    text_metadata['text'] = text
    text_metadata['token_length'] = len(text.split())
    text_metadata = detext_text_language(text_metadata, text)
    return text_metadata


def parse_paper(text):
    first_to_seek, last_to_seek, metadata = define_first_and_last_to_seek(text)
    fts_pos = text.find(first_to_seek) + len(first_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_1', text[fts_pos:].split(splitter, number_of_splits))
    if not last_to_seek:
        metadata['text'] = update_text_metadata(text)
        return dict(metadata)
    lts_pos = text.find(last_to_seek) + len(last_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_2', text[lts_pos:].split(splitter, number_of_splits))
    metadata['text'] = update_text_metadata(text)
    return dict(metadata)


def serialize_data(data):
    with open(serialized_name, 'wb') as f:
        dump(data, f)


if __name__ == '__main__':
    data = {}
    for root, dirs, files in walk(path_to_dataset):
        for file in files:
            if path.splitext(file)[1] == '.txt':
                year, conference = get_data_from_filename(root)
                with open(path.join(root, file), 'r', encoding='utf-8') as f:
                    read = f.read()
                    data[path.join(root, file)] = parse_paper(read)
    serialize_data(data)
    print('Done')
