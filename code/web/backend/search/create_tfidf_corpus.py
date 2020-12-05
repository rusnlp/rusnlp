#!/usr/bin/env python3

import sys
from os import path, listdir
import json
import logging
from gensim.models import TfidfModel
from build_tfidf import extract_lemmas

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

modelfile = sys.argv[1]
corpusdir = sys.argv[2]

model = TfidfModel.load(modelfile)

dictionary = model.id2word

files = [f for f in listdir(corpusdir) if f.endswith('.conll')]

texts = {}

for doc in files:
    label = doc.split('.')[0]
    print('Loading', doc, file=sys.stderr)
    data = open(path.join(corpusdir, doc), errors='replace').readlines()
    text = extract_lemmas(data)
    texts[label] = model[dictionary.doc2bow(text)]

corpus = json.dumps(texts, ensure_ascii=False, indent=4, sort_keys=True)

print(corpus)
