#!/usr/bin/python3

import sys
import json
import logging
from gensim import similarities

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

orderfile = sys.argv[1]
indexfile = sys.argv[2]

sim_index = similarities.MatrixSimilarity.load(indexfile)

orderdata = open(orderfile, 'r').read()
order = json.loads(orderdata)

user_query = input('Enter a filename to find its nearest neighbors (for example, 80.txt):')

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




