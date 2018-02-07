#!/usr/bin/python3

import sys
import logging
from gensim.models.doc2vec import Doc2Vec

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

modelfile = sys.argv[1]
model = Doc2Vec.load(modelfile)

user_query = input('Enter a filename to find its nearest neighbors (for example, 80.txt):')

for i in model.docvecs.most_similar(int(user_query.split('.')[0])):
    print(i)
