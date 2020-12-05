#!/usr/bin/python3

import sys
from build_tfidf import extract_lemmas
from os import listdir
from os.path import join
import logging
import gensim
import multiprocessing
cores = multiprocessing.cpu_count()


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    vectorsize = 40
    textdirectory = sys.argv[1]

    files = [f for f in listdir(textdirectory) if f.endswith('.conll')]

    texts = {}

    for doc in files:
        data = open(join(textdirectory, doc)).readlines()
        text = extract_lemmas(data)
        texts[doc.split('.')[0]] = text

    documents = [gensim.models.doc2vec.TaggedDocument(words=texts[text], tags=[text]) for text in texts]
    model = gensim.models.Doc2Vec(documents, vector_size=vectorsize, dm=0, dm_mean=1, dbow_words=1,
                                  window=5, min_count=2, workers=cores, sample=0, epochs=50)

    filename = 'doc2vec_en_'+str(vectorsize)+'.model'
    model.save(filename)
