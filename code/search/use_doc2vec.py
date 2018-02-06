#!/usr/bin/python3

import sys
import json
import logging
from gensim.models.doc2vec import Doc2Vec

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

model = Doc2Vec.load('doc2vec-en')

user_query = input('Enter a filename to find its nearest neighbors (for example, 130.txt):')

print(model.docvecs.most_similar(int(user_query.split('.')[0])))
