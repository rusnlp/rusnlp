"""
Вспомогательный модуль, основанный на
https://github.com/akutuzov/webvectors/blob/master/preprocessing/rus_preprocessing_udpipe.py
"""

import os
import re
from string import punctuation
from tqdm import tqdm

punctuation = punctuation + '«»—…“”*№́–'
stop_pos = {'AUX', 'NUM', 'DET', 'PRON', 'ADP', 'SCONJ', 'CCONJ', 'INTJ', 'PART', 'X'}
alphabet = {
    'lat': 'qwertyuiopasdfghjklzxcvbnm',
    'cyr': 'ёйцукенгшщзхъфывапролджэячсмитьбю'
}


class Token:
    def __init__(self, token, lemma, pos):
        self.token = token
        self.lemma = lemma
        self.pos = pos

    def __repr__(self):
        return '{}({})_{}'.format(self.token, self.lemma, self.pos)


def x_replace(word):
    newtoken = 'x' * len(word)
    return newtoken


def clean_word(word, pos, misc):
    # clean_token + clean_lemma
    out_word = word.strip().lower().replace(' ', '')
    out_word = out_word.replace('́', '')  # так не видно, но тут ударение
    out_word = out_word.replace('_', '')  # TODO: надо, если так соединяют сущности в muse?

    if '|' in out_word or out_word.endswith('.jpg') or out_word.endswith('.png')\
            or word == 'Файл' and 'SpaceAfter=No' in misc:
        return None

    if pos != 'PUNCT':
        out_word = out_word.strip(punctuation)

    return out_word


def list_replace(search, replacement, text):
    search = [el for el in search if el in text]
    for c in search:
        text = text.replace(c, replacement)
    return text


def unify_sym(text):
    # ['«', '»', '‹', '›', '„', '‚', '“', '‟', '‘', '‛', '”', '’']  ->  ['"']
    text = list_replace \
        ('\u00AB\u00BB\u2039\u203A\u201E\u201A\u201C\u201F\u2018\u201B\u201D\u2019',
         '\u0022', text)

    # ['‒', '–', '—', '―', '‾', '̅', '¯']  ->  [' -- ']
    text = list_replace \
        ('\u2012\u2013\u2014\u2015\u203E\u0305\u00AF',
         '\u2003\u002D\u002D\u2003', text)

    # ['‐', '‑']  ->  ['-']
    text = list_replace('\u2010\u2011', '\u002D', text)

    # [' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', ' ', '​', ' ', ' ', '⁠', '　'] -> [' ']
    text = list_replace \
            (
            '\u2000\u2001\u2002\u2004\u2005\u2006\u2007\u2008\u2009\u200A\u200B\u202F\u205F\u2060\u3000',
            '\u2002', text)

    # ['  '] -> [' ']
    text = re.sub('\u2003\u2003', '\u2003', text)

    text = re.sub('\t\t', '\t', text)

    # ['ˌ', '̇', '̣', '•', '‣', '⁃', '⁌', '⁍', '∙', '◦', '·', '×', '⋅', '∙', '⁢']  ->  ['.']
    text = list_replace \
            (
            '\u02CC\u0307\u0323\u2022\u2023\u2043\u204C\u204D\u2219\u25E6\u00B7\u00D7\u22C5\u2219\u2062',
            '.', text)

    # ['∗']  ->  ['*']
    text = list_replace('\u2217', '\u002A', text)

    # ['≁', '≋', 'ⸯ', '҃']  ->  ['∽']
    text = list_replace('\u2241\u224B\u2E2F\u0483', '\u223D', text)

    text = list_replace('…', '...', text)

    # с надстрочными знаками и т.п.
    text = list_replace('\u00C4', 'A', text)
    text = list_replace('\u00E4', 'a', text)
    text = list_replace('\u00CB', 'E', text)
    text = list_replace('\u00EB', 'e', text)
    text = list_replace('\u1E26', 'H', text)
    text = list_replace('\u1E27', 'h', text)
    text = list_replace('\u00CF', 'I', text)
    text = list_replace('\u00EF', 'i', text)
    text = list_replace('\u00D6', 'O', text)
    text = list_replace('\u00F6', 'o', text)
    text = list_replace('\u00DC', 'U', text)
    text = list_replace('\u00FC', 'u', text)
    text = list_replace('\u0178', 'Y', text)
    text = list_replace('\u00FF', 'y', text)
    text = list_replace('\u00DF', 's', text)
    text = list_replace('\u1E9E', 'S', text)

    # валютные знаки
    currencies = list \
            (
            '\u20BD\u0024\u00A3\u20A4\u20AC\u20AA\u2133\u20BE\u00A2\u058F\u0BF9\u20BC'
            '\u20A1\u20A0\u20B4\u20A7\u20B0\u20BF\u20A3\u060B\u0E3F\u20A9\u20B4\u20B2'
            '\u0192\u20AB\u00A5\u20AD\u20A1\u20BA\u20A6\u20B1\uFDFC\u17DB\u20B9\u20A8'
            '\u20B5\u09F3\u20B8\u20AE\u0192'
        )

    alphabet = list \
            (
            '\t\n\r '
            'абвгдеёзжийклмнопрстуфхцчшщьыъэюяАБВГДЕЁЗЖИЙКЛМНОПРСТУФХЦЧШЩЬЫЪЭЮЯ'
            ',.[]{}()=+-−*&^%$#@!~;:§/\|"'
            '0123456789'
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ ' + "'"
        )

    allowed = set(currencies + alphabet)

    cleaned_text = [sym for sym in text if sym in allowed]
    cleaned_text = ''.join(cleaned_text)

    return cleaned_text


def parse_file(conllu_text):
    """
    :param conllu_text: прочитанный файл conllu
    :return: список словарей {sent_id, text, parsed=список строк-слов}
    """
    par_sents = (conllu_text.split('# newpar\n'))[1:]  # берём распаршенные предложения

    sents = []
    for par_sent in par_sents:
        parts = par_sent.split('\n')
        sent = {'sent_id': parts[0].replace('# sent_id = ', ''),
                'text': parts[1].replace('# text = ', ''),
                'parsed': parts[2:]}

        sents.append(sent)

    return sents


def hold_propn(memory, tagged_toks, join_propn, join_token='::'):
    if join_propn:  # соединяем memory
        tagged_toks.append(Token(join_token.join(memory['token']),
                                 join_token.join(memory['lemma']),
                                 'PROPN'))
    else:  # добавляем токены из memory по отдельности
        for i in range(len(memory['token'])):
            tagged_toks.append(Token(memory['token'][i], memory['lemma'][i], 'PROPN'))
    named = False
    memory = {'token': [], 'lemma': []}
    return named, memory, tagged_toks


def process_line(content, lemmatize=1, keep_pos=1, keep_punct=0, keep_stops=1,
                 join_propn=0, join_token='::'):
    # join_propn в текущей реализации работает только для русского,
    # потому что опирается на падеж и число

    # если подали строку -- делим на абзацы
    if isinstance(content, str):
        content = content.split('\n')

    entities = {'PROPN'}
    named = False
    memory = {'token': [], 'lemma': []}  # храним и токены, и леммы частей именованных сущностей
    mem_case = None
    mem_number = None
    tagged_toks = []

    # извлекаем из обработанного текста леммы, теги и морфологические характеристики
    tagged = [w.split('\t') for w in content if w]

    for line_tags in tagged:

        if len(line_tags) != 10:
            continue

        (word_id, token, lemma, pos, xpos, feats, head, deprel, deps, misc) = line_tags
        token = clean_word(token, pos, misc)
        lemma = clean_word(lemma, pos, misc)

        if not lemma or not token:
            continue

        if pos in entities:
            if '|' not in feats:
                tagged_toks.append(Token(token, lemma, pos))
                continue
            morph = {el.split('=')[0]: el.split('=')[1] for el in feats.split('|')}

            if 'Case' not in morph or 'Number' not in morph:
                tagged_toks.append(Token(token, lemma, pos))
                continue

            if not named:
                named = True
                mem_case = morph['Case']
                mem_number = morph['Number']

            if morph['Case'] == mem_case and morph['Number'] == mem_number:
                memory['token'].append(token)
                memory['lemma'].append(lemma)
                if 'SpacesAfter=\\n' in misc or 'SpacesAfter=\s\\n' in misc:
                    named, memory, tagged_toks = hold_propn(memory, tagged_toks, join_propn, join_token)

            else:
                named, memory, tagged_toks = hold_propn(memory, tagged_toks, join_propn, join_token)
                tagged_toks.append(Token(token, lemma, pos))

        else:  # pos not in entities
            if not named:
                if pos == 'NUM' and token.isdigit():
                    lemma = x_replace(token)
                tagged_toks.append(Token(token, lemma, pos))

            else:
                named, memory, tagged_toks = hold_propn(memory, tagged_toks, join_propn, join_token)
                tagged_toks.append(Token(token, lemma, pos))

    if not keep_punct:
        tagged_toks = [tok for tok in tagged_toks if tok.pos != 'PUNCT']

    if not keep_stops:  # убираем ещё слова длиной 1
        tagged_toks = [tok for tok in tagged_toks if tok.pos not in stop_pos
                       and len(tok.lemma) > 1
                       and len(tok.token) > 1]

    if lemmatize:
        words = [tok.lemma for tok in tagged_toks]
    else:
        words = [tok.token for tok in tagged_toks]

    if keep_pos:
        words = ['{}_{}'.format(word, tok.pos) for word, tok in zip(words, tagged_toks)]

    return words


def get_text(conllu_text, lemmatize, keep_pos, keep_punct, keep_stops,
             join_propn, join_token, unite=1):
    # соединяем предложения из conllu в текст
    sents = parse_file(conllu_text)
    lines = []
    for sent in sents:
        line = process_line(sent['parsed'], lemmatize, keep_pos, keep_punct, keep_stops,
                            join_propn, join_token)
        if unite:
            lines.extend(line)
        else:
            if line:
                lines.append(line)
    return lines


def clean_ext(name):
    return '.'.join(name.split('.')[:-1])


def get_corpus(texts_path, lemmatize, keep_pos, keep_punct, keep_stops, join_propn, join_token, unite):
    """собираем файлы conllu в словарь {файл: список токенов}"""
    texts = {}
    for file in tqdm(os.listdir(texts_path), desc='Collecting'):
        text = open('{}/{}'.format(texts_path, file), encoding='utf-8').read().strip()
        preprocessed = get_text(text, lemmatize, keep_pos, keep_punct, keep_stops,
                                join_propn, join_token, unite)
        texts[clean_ext(file)] = preprocessed

    return texts