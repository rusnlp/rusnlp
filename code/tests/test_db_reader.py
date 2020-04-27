import json
import os

from code.web.db_classes.db import DBaseRusNLP
from code.web.db_classes.db_writer import WriterDBase
from code.web.db_classes.db_reader import ReaderDBase
from helper import *

db = DBaseRusNLP("..///backend///database///rusnlp2.0.db", "..///backend///database///metadata.json")
reader = ReaderDBase(db)
base_path = "<base path>"  # "D:/syncthing/RusNLP/data-txt/"
title2hash = create_title2hash(os.path.join(base_path, 'hash_title_url.tsv'))
hash2url = create_hash2url(os.path.join(base_path, 'hash_title_url.tsv'))


def test_title_by_id():
    for (title, conference, year), hash in title2hash.items():
        new_titles = reader.select_title_by_id(hash)
        if reader.select_language_by_id(hash) == 'en':
            assert len(new_titles) == 1, f"{new_titles}, {title}, {hash}"
            assert new_titles[0][0].lower() == title.lower().replace("'", ' ').replace('"', ' '), \
                "{}, {}, {}".format(new_titles, title, hash)


def test_authors_by_id():
    for title, hash in title2hash.items():
        if reader.select_language_by_id(hash) == 'en':
            authors = reader.select_author_by_id(hash)
            assert authors


def test_all_authors():
    for i in reader.select_all_authors():
        print(i)


def test_year_by_id():
    for _, hash in title2hash.items():
        if reader.select_language_by_id(hash) == 'en':
            assert int(hash.split("_")[1]) == reader.select_year_by_id(hash)


def test_conference_by_id():
    for _, hash in title2hash.items():
        if reader.select_language_by_id(hash) == 'en':
            assert hash.split("_")[0].lower() == reader.select_conference_by_id(hash).lower()


def test_url_by_id():
    for hash in hash2url:
        if reader.select_language_by_id(hash) == 'en':
            assert hash2url[hash] == reader.select_url_by_id(hash)


def test_abstract_by_id():
    for hash in hash2url:
        print(reader.select_abstract_by_id(hash))


def test_select_articles_from_conference():
    dialogue = set(reader.select_articles_from_conference('Dialogue'))
    aist = set(reader.select_articles_from_conference('AIST'))
    ainl = set(reader.select_articles_from_conference('AINL'))

    hashes = set()

    with open(os.path.join(base_path, "metadata.jsonlines"), 'r', encoding='utf-8') as f:
        for line in f:
            metadata = json.loads(line)
            if metadata['language'] == "en":  # TODO: del if when both languages
                assert metadata['hash'] in dialogue or metadata['hash'] in aist \
                       or metadata['hash'] in ainl, "Not found: {}".format(metadata['hash'])
                if metadata['hash'] not in hashes:
                    hashes.add(metadata['hash'])
                else:
                    raise Exception(metadata['hash'])

    # TODO: change when both languages
    assert len(ainl) == 93
    assert len(aist) == 70
    assert len(dialogue) == 353


def test_select_articles_from_years():
    year_min = 2019
    year_max = 2019
    articles = set(reader.select_articles_from_years(year_min, year_max))
    articles_true = set()
    with open(os.path.join(base_path, "metadata.jsonlines"), 'r', encoding='utf-8') as f:
        for line in f:
            metadata = json.loads(line)
            if year_min <= int(metadata['year']) <= year_max and metadata['language'] == 'en':
                assert metadata['hash'] in articles
                articles_true.add(metadata['hash'])
    articles_hashes = set()
    articles_absent = set()
    for hash in hash2url.keys():
        year = int(hash.split("_")[1])
        if year_min <= year <= year_max:
            if hash in articles and hash in articles_true:
                articles_hashes.add(hash)
            else:
                articles_absent.add(hash)
    assert len(articles_hashes) + len(articles_absent) == 89
    assert len(articles_absent) == 25
    assert len(articles_true) == len(articles), "{}".format(articles.difference(articles_true))


def test_select_alias_name_by_author_cluster():
    with open(os.path.join(base_path, "current_authors.tsv"), 'r', encoding='utf-8') as f:
        for line in f:
            if line:
                id_, name = line.split('\t')[:2]
                assert reader.select_alias_name_by_author_cluster(int(id_)) == name, name


def test_select_affiliation_by_cluster():
    with open(os.path.join(base_path, "current_affiliations.tsv"), 'r', encoding='utf-8') as f:
        for line in f:
            if line:
                id_, name = line.split('\t')[:2]
                print(id_, name)
                assert reader.select_affiliation_by_cluster(int(id_)) == name


def test_select_aff_cluster_by_affiliation():
    with open(os.path.join(base_path, "current_affiliations.tsv"), 'r', encoding='utf-8') as f:
        for line in f:
            if line:
                id_, name = line.split('\t')[:2]
                print(id_, name)
                assert reader.select_aff_cluster_by_affiliation(name) == int(id_)


def test_select_cluster_author_by_common_id():
    hash = "dialogue_2012_be2fb882e4f57d648998046ecf2bfdf0757f8fb3"
    assert reader.select_cluster_author_by_common_id(hash) == {288, 776, 442, 860}

    hash = "ainl_2015_860916ac622ec0a6242f810c5702fb9eb36e52c4"
    assert reader.select_cluster_author_by_common_id(hash) == {467, 688}


def test_get_dict_of_conference_description():
    aist = reader.get_dict_of_conference_description("AIST")
    ainl = reader.get_dict_of_conference_description("AINL")
    dialogue = reader.get_dict_of_conference_description("Dialogue")

    assert aist['url'] == 'https://aistconf.org/'
    assert ainl['url'] == 'https://ainlconf.ru/'
    assert dialogue['url'] == 'http://www.dialog-21.ru/'

    assert aist['ru'].startswith("AIST - это конференция,")
    assert ainl['ru'].startswith("AINL - это конференция по искусственному интеллекту")
    assert dialogue['ru'].startswith("Диалог - старейшая и крупнейшая российская")

    assert aist['en'].startswith("AIST is a conference dedicated")
    assert ainl['en'].startswith("AINL is a conference in Artificial Intelligence")
    assert dialogue['en'].startswith("Dialogue is the oldest and the largest")


def test_select_articles_by_cluster():
    assert {"ainl_2018_0dc0b8f51dfc6921e7babb9eeadb5e38858c8145",
            "aist_2019_eafd213fcbc1fb8e5913b0a6193488a6e14a4ec3",
            "dialogue_2014_09e1d38981a72e53b0f19cd0de4dc9e7cc18deb1",
            "dialogue_2015_6e1f13dd827d92f1a0900435f28e1829c76fcd01",
            "dialogue_2016_3dbd5431a9535b9f758f3512e3e32ff150d1b0d8",
            "dialogue_2016_9385c1fb0119d54169158dff324dd43fb25e0e37",
            "dialogue_2017_c3891ca5834982ee8e7fc5585002508bf40f0f52"} == set(reader.select_articles_by_cluster(185))


def test_select_articles_of_author():
    assert {"ainl_2018_0dc0b8f51dfc6921e7babb9eeadb5e38858c8145",
            "aist_2019_eafd213fcbc1fb8e5913b0a6193488a6e14a4ec3",
            "dialogue_2017_c3891ca5834982ee8e7fc5585002508bf40f0f52",
            "dialogue_2016_9385c1fb0119d54169158dff324dd43fb25e0e37"
            } == set(reader.select_articles_of_author("Sysoev A. A."))


def test_get_statistics():
    stats = reader.get_statistics()
    assert stats['Overall amount of papers'] == 516
    authors = WriterDBase.convert_to_set(os.path.join(base_path, "current_authors.tsv"))
    affiliations = WriterDBase.convert_to_set(os.path.join(base_path, "current_affiliations.tsv"))
    assert stats['Amount of unique authors'] == len(authors)
    assert stats['Amount of unique affiliations'] == len(affiliations)
