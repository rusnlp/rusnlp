#!/usr/bin/env python3

import sys
import os
import json
from gensim import similarities
from gensim.corpora import Dictionary
from gensim.models import TfidfModel


def extract_lemmas(lines):
    lemmas = []
    for line in lines:
        if line.startswith('#') or len(line.strip()) == 0:
            continue
        res = line.split('\t')
        lemma = res[2].strip().lower()
        pos = res[3].strip()
        if pos != 'PUNCT':
            lemmas.append(lemma + '_' + pos)
    return lemmas


if __name__ == '__main__':
    textdirectory = sys.argv[1]

    files = [f for f in os.listdir(textdirectory) if f.endswith('.conllu')]

    order = json.dumps(files, indent=4, sort_keys=True)
    orderfile = open('docorder.json', 'w')
    orderfile.write(order)
    orderfile.close()

    texts = []

    for doc in files:
        # print(doc, file=sys.stderr)
        data = open(os.path.join(textdirectory, doc), errors='replace').readlines()
        text = extract_lemmas(data)
        texts.append(text)



    dictionary = Dictionary(texts)
    dictionary.save('tfidf.dic')

    corpus = [dictionary.doc2bow(line) for line in texts]
    # print(corpus)

    model = TfidfModel(corpus, id2word=dictionary)
    model.save('tfidf.model')
    sim_index = similarities.MatrixSimilarity(model[corpus])
    sim_index.save('tfidf.index')
