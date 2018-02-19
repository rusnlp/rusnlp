#!/usr/bin/python3

import sys
import os
import pickle


def extract_lemmas(lines):
    lemmas = []
    for line in lines:
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        res = line.split('\t')
        lemma = res[2].strip().lower()
        pos = res[3].strip()
        lemmas.append(lemma + '_' + pos)
    return lemmas


picklefile = sys.argv[1]

textdir = sys.argv[2]

documents = [f for f in os.listdir(textdir) if f.endswith('.txt')]

f = open(picklefile, 'rb')

e = pickle.load(f)
e = set(e)
print(e)

for doc in documents:
    if int(doc.split('.')[0]) in e:
        text = open(os.path.join(textdir, doc), 'r').readlines()
        words = extract_lemmas(text)
        print(' '.join(words))
