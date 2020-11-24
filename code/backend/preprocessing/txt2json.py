import json
import os
import re
import sys
from hashlib import sha1
from langdetect import detect_langs
from transliterate import translit
from helper import *

splitter = '%\n%\n'
english_label_p = re.compile('==ENGLISH==\n%\n%\n')
russian_label_p = re.compile('==RUSSIAN==\n%\n%\n')
number_of_splits = 4
empty_symbol = '-'


def get_data_from_filename(root):
    chunks = os.path.normpath(root).split(os.sep)
    return chunks[~0], chunks[~1]


def parse_keywords(keyword_string):
    return keyword_string.replace('\n', ' ').strip().split(',')


def parse_title(title):
    return re.sub(' +', ' ', title.replace('%', '').replace('\n', ' ').strip().lower().title())


def parse_authors(authors_list, filename):
    authors = []
    if '%\n' not in authors_list:
        author = authors_list
        if '-\n' != author:
            authors.append(add_author_metadata(author, filename))
        return authors
    for author in authors_list.split('%\n'):
        if '-\n' != author:
            authors.append(add_author_metadata(author, filename))
    return authors


def add_author_metadata(author, filename):
    metadata = {}
    name, affiliations, email = author.split('\n')[:3]
    metadata['email'] = email
    metadata['name_id'], metadata['name'] = get_name_with_id(name.strip(", "), filename)
    metadata['affiliations'] = get_affiliations_with_id(affiliations.strip(", "), filename)
    return metadata


def get_name_with_id(name, filename):
    name = name.replace("\n", " ").strip()
    if name in name2author:
        return name2author[name]
    else:
        missing_authors.write(filename + "\t" + str([name]) + "\n")
        return None, None


def get_affiliations_with_id(names, filename):
    result_affiliations = []
    names = names.replace("\r\n", "").replace("\n", ' ').replace("  ", " ").replace(",  ", "")
    for name in names.split(";"):
        name = name.strip()
        if name in name2affiliation:
            affiliation_id, affiliation_name = name2affiliation[name]
            result_affiliations.append({"affiliation_id": affiliation_id,
                                        "affiliation_name": affiliation_name})
        else:
            missing_affiliations.write(filename + "\t" + str([name]) + "\n")
    return result_affiliations


def find_url(text, metadata):
    url = hash2url.get(metadata['hash'], None)
    if not url and text[0] == '%' and text[5] != '%':
        url = text.split('%\n%\n', 1)[0][2:].replace('\n', '')
    assert url is not None and url != "-"
    return url


def generate_hash(metadata):
    conference = metadata['conference'].lower()
    year = str(metadata['year'])

    if metadata['article'].get('title'):
        title = metadata['article']['title'].lower().replace("\n", ' ')
        old_hash = title2hash.get((title, conference, year))
        if old_hash:
            return old_hash
    print('No hash for article data: %s, title: %s' % ([metadata['article']],
                                                       metadata['article'].get('title')))
    title = metadata['article']['title']
    hasher = sha1()
    hasher.update(translit(title.replace(' ', '_').lower(), 'ru', reversed=True).encode())
    return '{}_{}_{}'.format(metadata['conference'], metadata['year'],
                             str(hasher.hexdigest())).lower()


def extract_metadata_from_text(pattern, text, filename):
    metadata = {}
    header = re.search(pattern, text)
    end = 0
    if header:
        end = header.end()
        title, authors, abstract, keywords = text[header.end():].split(splitter,
                                                                       number_of_splits)[:-1]
        metadata['title'] = parse_title(title)
        metadata['authors'] = parse_authors(authors, filename)
        metadata['abstract'] = abstract.strip()
        metadata['keywords'] = parse_keywords(keywords)
    return metadata, end


def extract_text(full_text, end):
    return splitter.join(full_text[end:].split(splitter)[number_of_splits:])


def detect_language(text):
    lang = detect_langs(text)
    language = lang[0].lang
    probability = round(lang[0].prob, 2)
    return {'language': language, 'probability': probability}


def choose_between_metadata(metadata1, metadata2):
    article_metadata = {
        'title': metadata1['title'] if metadata1['title'] and metadata1['title'].strip() != "-"
        else metadata2['title'],

        'authors': metadata1['authors'] if metadata1['authors'] else metadata2['authors'],

        'abstract': metadata1['abstract'] if metadata1['abstract'] and
        metadata1['abstract'].strip() != "-"
        else metadata2['abstract'],
        'keywords': metadata1['keywords'] if metadata1['keywords'] else metadata2['keywords']}

    return article_metadata


def choose_correct_metadata(metadata, metadata_ru, metadata_en):
    if metadata_ru and not metadata_en:
        return metadata_ru
    if metadata_en and not metadata_ru:
        return metadata_en
    if metadata_en and metadata_ru:
        if metadata['language'] == 'en':
            return choose_between_metadata(metadata_en, metadata_ru)
        elif metadata['language'] == 'ru':
            return choose_between_metadata(metadata_ru, metadata_en)
        else:
            raise Exception("undefined language")
    else:
        raise Exception('No metadata at all for %s' % metadata)


def get_metadata_from_file(root_, filename_):
    metadata = {}

    year, conference = get_data_from_filename(root_)
    metadata['year'] = year
    metadata['conference'] = conference

    with open(os.path.join(root_, filename_), 'r', encoding='utf-8') as f:
        text = f.read()
        metadata.update(detect_language(text))

        metadata_en, en_end = extract_metadata_from_text(english_label_p, text,
                                                         os.path.join(basedir, fname))
        metadata_ru, ru_end = extract_metadata_from_text(russian_label_p, text,
                                                         os.path.join(basedir, fname))
        metadata["article"] = choose_correct_metadata(metadata, metadata_ru=metadata_ru,
                                                      metadata_en=metadata_en)

        metadata['hash'] = generate_hash(metadata)
        metadata['url'] = find_url(text, metadata)

        if params.get("out_texts_dir"):
            if metadata['language'] == 'en':
                output_path = os.path.join(params["out_texts_dir"], 'EN', metadata['hash'])
            elif metadata['language'] == 'ru':
                output_path = os.path.join(params["out_texts_dir"], 'RU', metadata['hash'])
            with open(output_path, 'w', encoding='utf-8', newline='\n') as t:
                t.write(extract_text(text, max(en_end, ru_end)))

    return metadata


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise Exception("Please specify path to config_file")
    with open(sys.argv[1], "r", encoding="utf-8") as config:
        params = json.loads(config.read())

    title2hash = create_title2hash(params["hash_title_url"])
    hash2url = create_hash2url(params["hash_title_url"])
    name2author = create_name2author(params["name2author"])
    name2affiliation = create_name2affiliation(params["name2affiliation"])

    missing_authors = open(params["missing_authors"], 'w', encoding='utf-8', newline='\n')
    missing_affiliations = open(params["missing_affiliations"], 'w', encoding='utf-8', newline='\n')

    with open(params["out_metadata_path"], 'w', encoding='utf-8', newline='\n') as w:
        for basedir, dirs, files in os.walk(params["input_file"]):
            for fname in files:
                if fname.endswith('.txt'):
                    meta_data = get_metadata_from_file(basedir, fname)
                    w.write(json.dumps(meta_data) + "\n")

    missing_authors.close()
    missing_affiliations.close()
