from os import walk, path
from collections import defaultdict

path_to_dataset = path.join('..', '..', '..', '..', 'gitlab-rusnlp', 'rusnlp', 'DATASET', 'conferences/')
splitter = '%\n%\n'
english_label = '==ENGLISH==\n'
russian_label = '==RUSSIAN==\n'
number_of_splits = 4

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
        raise Error('WTF')
    return first_to_seek, last_to_seek, metadata

def update_metadata(metadata, language_num, chunks):
    metadata[language_num]['title'] = chunks[0]
    metadata[language_num]['authors'] = chunks[1]
    metadata[language_num]['abstract'] = chunks[2]
    metadata[language_num]['keywords'] = chunks[3]
    text = None
    if len(chunks) > number_of_splits:
        text = chunks[4]
    return metadata, text

def parse_paper(text):
    first_to_seek, last_to_seek, metadata = define_first_and_last_to_seek(text)
    fts_pos = text.find(first_to_seek) + len(first_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_1', text[fts_pos:].split(splitter, number_of_splits))
    if not last_to_seek:
        metadata['text'] = text
        return metadata
    lts_pos = text.find(last_to_seek) + len(last_to_seek) + 1
    metadata, text = update_metadata(metadata, 'language_2', text[lts_pos:].split(splitter, number_of_splits))
    metadata['text'] = text
    return metadata

if __name__ == '__main___':
    data = {}
    for root, dirs, files in walk(path_to_dataset):
        for file in files:
            if path.splitext(file)[1] == '.txt':
                year, conference = get_data_from_filename(root)
                with open(path.join(root, file), 'r') as f:
                    read = f.read()
                    data[path.join(root, file)] = parse_paper(read)
    print('Done')
