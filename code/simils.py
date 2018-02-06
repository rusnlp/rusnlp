#!/usr/bin/python3

import fileinput
import sys
from Levenshtein import distance
from transliterate import translit
from itertools import combinations
import langid
import json

langid.set_languages(['en', 'ru'])
titles = {}

print('Analyzing titles...', file=sys.stderr)
for line in fileinput.input():
    res = line.strip()
    lang = langid.classify(res)[0]
    titles[res] = lang

distances = {}

print('Calculating similarities...', file=sys.stderr)
for pair in combinations(titles.keys(), 2):
    title0 = pair[0]
    title1 = pair[1]
    lev_distance = distance(title0, title1)
    distances[(title0, title1)] = lev_distance
    lang0 = titles[title0]
    lang1 = titles[title1]
    if lang0 != lang1:
        if lang0 == 'ru':
            tr_title0 = translit(title0, 'ru', reversed=True)
            lev_distance1 = distance(tr_title0, title1)
        elif lang1 == 'ru':
            tr_title1 = translit(title1, 'ru', reversed=True)
            lev_distance1 = distance(title0, tr_title1)
        if lev_distance1 < lev_distance and lev_distance1 < 7:
            distances[(title0, title1)] = lev_distance1

print('Filtering very similar...', file=sys.stderr)
similarities = {}
for title in titles:
    similar = []
    for key in distances:
        if title in key and distances[key] < 7:
            neighbour = [el for el in key if el != title]
            similar += neighbour
    similarities[title] = similar

print(json.dumps(similarities, ensure_ascii=False))
