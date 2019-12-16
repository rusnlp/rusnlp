from os import walk, path, listdir
from collections import defaultdict
from pickle import dump
from langdetect import detect_langs
from platform import system
from hashlib import sha1
from transliterate import translit
from re import sub, search
from typing import Tuple, Dict, List

import json
import git


class Parser:

    def __init__(self):
        self.path_to_dataset_repo = 'https://username:password@gitlab.com/bakarov/rusnlp.git'
        self.path_to_ud_en_model = '/Users/amir/Documents/projects/rusnlp/udpipe/english-ewt-ud-2.4-190531.udpipe'
        self.path_to_ud_ru_model = '/Users/amir/Documents/projects/rusnlp/udpipe/russian-syntagrus-ud-2.4-190531.udpipe'
        self.splitter = '%\n%\n'
        self.number_of_splits = 4
        self.serialized_name = 'tmp.pickle'
        self.empty_symbol = '-'
        self.minimum_text_length = 50
        self.authors_list = {}
        self.l1 = 'en'
        self.l2 = 'ru'
        self.metadata = defaultdict(lambda: {})

    def lemmatize(self, text, pipeline):
        indent = 4
        word_id = 1
        lemma_id = 2
        pos_id = 3
        punct_tag = 'PUNCT'
        lemmatized_text = []
        for par in pipeline.process(text).split('\n\n'):
            for parsed_word in par.split('\n')[indent:]:
                word = parsed_word.split('\t')[word_id].lower()
                lemma = parsed_word.split('\t')[lemma_id]
                pos = parsed_word.split('\t')[pos_id]
                if pos == punct_tag:
                    continue
                lemmatized_text.append(lemma)
        return ' '.join(lemmatized_text)

    def parse_filename(self, filename: str, windows_id: str = 'Windows'):
        chunks = filename.split('\\') if system() == windows_id else filename.split('/')
        self.metadata['year'] = chunks[~0]
        self.metadata['conference'] = chunks[~1]
        self.metadata['path'] = filename.replace('\\', '/')

    def get_url(self) -> str:
        url = self.empty_symbol
        if self.text[0] == '%' and self.text[2] != '%':
            url = self.text.split('%\n%\n', 1)[0][2:].replace('\n', '')
        return url

    def set_language_metadata(self, lang_1_tag: str = 'en', lang_2_tag: str = 'ru'):
        self.metadata['language_1']['lang'] = lang_1_tag
        self.metadata['language_2']['lang'] = lang_2_tag

    def get_metadata_positions(self, english_label: str = '==ENGLISH==\n', russian_label: str = '==RUSSIAN==\n',
                               lang_label_length: int = 13) -> Dict:
        lang_positions = {}
        ru_pos = search(russian_label, self.text)
        lang_positions['ru'] = ru_pos.start() + lang_label_length if ru_pos else ru_pos
        en_pos = search(english_label, self.text)
        lang_positions['en'] = en_pos.start() + lang_label_length if en_pos else en_pos
        return lang_positions

    def get_author_metadata(self, text: str) -> Dict:
        if len(text) < 5:
            return self.empty_symbol
        data = {}
        data_fields = text.split('\n')
        # for k, v in authors_list.items():
        #     if data_fields[0] in v:
        #         data['author'] = k
        #     else:
        #         data['author'] = data_fields[0].strip()
        data['author'] = data_fields[0].strip()
        data['affiliations'] = [affil.strip() for affil in data_fields[1].split(';')]
        data['email'] = [email.strip() for email in data_fields[2].split(',')]
        return data

    def parse_authors(self, text_: str) -> List:
        authors = []
        text = text_ + '%\n' if '%\n' not in text_ else text_
        for author in text.split('%\n'):
            authors.append(self.get_author_metadata(author))
        return authors

    def parse_keywords(self, text: str) -> List:
        return text.replace('\n', ' ').strip().split(',')

    def parse_title(self, title: str) -> str:
        return sub(' +', ' ', title.replace('%', '').replace('\n', ' ').strip().lower().title())

    def get_language_metadata(self, language_number: int, language_name: str, text_chunks: List):
        language_id = 'language_{}'.format(language_number)
        self.metadata[language_id]['title'] = self.parse_title(text_chunks[0])
        self.metadata[language_id]['authors'] = self.parse_authors(text_chunks[1])
        self.metadata[language_id]['abstract'] = text_chunks[2].replace('\n', ' ').strip()
        self.metadata[language_id]['keywords'] = self.parse_keywords(text_chunks[3])
        self.metadata[language_id]['language'] = language_name

    def get_text_language(self, text: str) -> Tuple[str, float]:
        language = '-'
        probability = 0.0
        if len(text) > self.minimum_text_length:
            lang = detect_langs(text)
            language = lang[0].lang
            probability = round(lang[0].prob, 2)
        return language, probability

    def generate_hash(self) -> str:
        hasher = sha1()
        title = self.metadata['language_1']['title']
        hasher.update(translit(title.replace(' ', '_').lower(), 'ru', reversed=True).encode())
        return '{}_{}_{}'.format(self.metadata['conference'], self.metadata['year'],
                                 str(hasher.hexdigest())).lower()

    def get_full_text_metadata(self, start: int, lemmatize: bool = False) -> str:
        text = ' '.join(self.text[start:].split(self.splitter, self.number_of_splits)[4:])
        self.metadata['full_text'] = text
        text_language, language_probability = self.get_text_language(text)
        text_metadata = {}
        text_metadata['token_length'] = len(text.split())
        text_metadata['url'] = self.get_url()
        text_metadata['text_language'] = text_language
        text_metadata['probability'] = language_probability
        if lemmatize:
            pipeline = self.en_pipeline if text_language == 'en' else self.ru_pipeline
            self.metadatata['full_text_lemmatized'] = self.lemmatize(text, pipeline)
        text_metadata['hash'] = self.generate_hash()
        self.metadata['text'] = text_metadata

    def parse_paper(self):
        lang_positions = self.get_metadata_positions()
        enumerator = 1
        for language, start in lang_positions.items():
            if not start:
                continue
            text_chunks = self.text[start:].split(self.splitter, self.number_of_splits)
            self.get_language_metadata(enumerator, language, text_chunks)
            enumerator += 1
        last_lang_position = max(filter(lambda x: x is not None, lang_positions.values()))
        self.get_full_text_metadata(last_lang_position)

    def serialize_data(self):
        with open(self.serialized_name, 'wb') as f:
            dump(self.metadata, f)

    # def make_clusters(data):
    #     affiliations = defaultdict(lambda: set())
    #     authors = defaultdict(lambda: set())
    #     for paper in data.values():
    #         for language_id in ['language_1', 'language_2']:
    #             if language_id in paper.keys():
    #                 lang = paper[language_id]['lang']
    #                 for author in paper[language_id]['authors']:
    #                     affiliations[lang].update(author['affiliations'])
    #                     authors[lang].add(author['author'])
    #     serialize_data(dict(authors), 'auth.pkl')
    #     serialize_data(dict(affiliations), 'aff.pkl')

    def parse_single_file(self, file_path: str):
        name_of_file = path.splitext(path.basename(file_path))[0]
        with open(file_path, 'r', encoding='utf-8') as f:
            self.metadata = defaultdict(lambda: {})
            self.text = f.read()
            self.parse_filename(path.dirname(file_path))
            self.parse_paper()
        self.result.append(dict(self.metadata))
            # datapath_ = path.join('parsed')
            # makedirs(path.join(datapath_, conference, year, name_of_file))
            # with open(path.join(datapath_, conference, year, name_of_file,
            #                     'lang_1.json'), 'w', encoding='utf-8') as f:
            #     json.dump(self.metadata['language_1'], f, ensure_ascii=False, indent=4, sort_keys=True)
            # if 'language_2' in self.metadata:
            #     with open(path.join(datapath_, conference, year, name_of_file,
            #                         'lang_2.json'), 'w', encoding='utf-8') as f:
            #         json.dump(self.metadata['language_2'], f, ensure_ascii=False, indent=4, sort_keys=True)
            # with open(path.join(datapath_, conference, year, name_of_file,
            #                     'common.json'), 'w', encoding='utf-8') as f:
            #     json.dump(self.metadata['text'], f, ensure_ascii=False, indent=4, sort_keys=True)
            # with open(path.join(datapath_, conference, year, name_of_file,
            #                     'text.txt'), 'w', encoding='utf-8') as f:
            #     f.write(self.metadata['full_text'])

    def parse(self, path_to_dataset):
        self.result = []
        # ru_ud_model = Model.load(self.path_to_ud_ru_model)
        # self.u_pipeline = Pipeline(ru_ud_model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        # en_ud_model = Model.load(self.path_to_ud_en_model)
        # self.en_pipeline = Pipeline(en_ud_model, 'tokenize', Pipeline.DEFAULT, Pipeline.DEFAULT, 'conllu')
        if not path_to_dataset:
            path_to_dataset = path.join('rusnlp', 'DATASET', 'conferences')
            git.Git('./').clone(self.path_to_dataset_repo)
        for root, dirs, files in walk(path_to_dataset):
            for file in files:
                if path.splitext(file)[1] == '.txt':
                    self.parse_single_file(path.join(root, file))
        print('Done')
