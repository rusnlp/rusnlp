#!/usr/bin/python3

import sys
from os import path
import json
import logging
from gensim import similarities
sys.path.insert(0, '../database/')
from bd import DBaseRusNLP
from db_reader import ReaderDBase

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

bd_m = DBaseRusNLP(path.join('..', '..', '..', 'database', 'rus_nlp_withouttexts.db'),
                   path.join('..', '..', '..', 'database', 'database_metadata.json'))
reader = ReaderDBase(bd_m)

orderfile = sys.argv[1]
indexfile = sys.argv[2]

sim_index = similarities.MatrixSimilarity.load(indexfile)

orderdata = open(orderfile, 'r').read()
order = json.loads(orderdata)

user_query = input('Enter a filename to find its nearest neighbors '
                   '(for example, dialogue_2017_3eac013c2e6d4618fe7308a71e2ef06257ee69db.conll):')

position = order.index(user_query)

counter = 0
for sim in sim_index:
    if counter == position:
        similarities = sim
        break
    counter += 1

sims = sorted(enumerate(similarities), key=lambda item: -item[1])
for sim in sims[:10]:
    print(order[sim[0]], sim[1])
