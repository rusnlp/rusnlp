#!/usr/bin/python3

import sys
from build_tfidf import extract_lemmas
from os import listdir
from os.path import join
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
import numpy as np


if __name__ == '__main__':
    textdirectory = sys.argv[1]

    files = [f for f in listdir(textdirectory) if f.endswith('.txt')]

    texts = [''] * len(files)

    for doc in files:
        data = open(join(textdirectory, doc)).readlines()
        text = extract_lemmas(data)
        texts[int(doc.split('.'))] = text

    sentences = [gensim.models.doc2vec.TaggedDocument(words=text, tags=[tid]) for tid, text in enumerate(texts)]
    model = Doc2Vec(size=100, window=10, min_count=2, workers=4, alpha=0.025, min_alpha=0.01, dm=0)
    model.build_vocab(sentences)
    model.train(sentences, total_examples=len(sentences), epochs=10)

    model.save('doc2vec-en.model')
