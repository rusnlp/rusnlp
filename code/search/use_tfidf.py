#!/usr/bin/python3

import sys
from os import path, listdir
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
testdir = sys.argv[3]

sim_index = similarities.MatrixSimilarity.load(indexfile)

orderdata = open(orderfile, 'r').read()
order = json.loads(orderdata)

print('Rank\tTitle\tAuthors\tID\tSimilarity')
testfiles = [f.split('.')[0] for f in listdir(testdir) if path.isfile(path.join(testdir, f))]

# user_query = input('Enter a paper ID to find its nearest neighbors '
#                    '(for example, dialogue_2017_3eac013c2e6d4618fe7308a71e2ef06257ee69db):')
for user_query in testfiles:
    print('==========================')
    position = order.index(user_query + '.conll')

    counter = 0
    for sim in sim_index:
        if counter == position:
            similarities = sim
            break
        counter += 1

    sims = sorted(enumerate(similarities), key=lambda item: -item[1])

    rank = 0
    for sim in sims[:11]:
        doc = order[sim[0]].split('.')[0]
        similarity = sim[1]
        authors = reader.select_author_by_id(doc)
        authors = ','.join([w for w in authors])
        title = reader.select_title_by_id(doc)
        output = '\t'.join([str(rank), title, authors, doc, str(similarity)])
        print(output)
        rank += 1
        if doc == user_query:
            print('==========================')
    print('==========================')
