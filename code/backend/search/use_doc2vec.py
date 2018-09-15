#!/usr/bin/python3

import sys
from os import path, listdir
import logging
from gensim.models.doc2vec import Doc2Vec

sys.path.insert(0, '../database/')
from bd import DBaseRusNLP
from db_reader import ReaderDBase

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

modelfile = sys.argv[1]
testdir = sys.argv[2]
model = Doc2Vec.load(modelfile)
model.init_sims(replace=True)

bd_m = DBaseRusNLP(path.join('..', '..', '..', 'database', 'rus_nlp_withouttexts.db'),
                   path.join('..', '..', '..', 'database', 'database_metadata.json'))
reader = ReaderDBase(bd_m)

# user_query = input('Enter a paper ID to find its nearest neighbors '
#                    '(for example, dialogue_2017_3eac013c2e6d4618fe7308a71e2ef06257ee69db):')

print('Rank\tTitle\tAuthors\tID\tSimilarity')
testfiles = [f.split('.')[0] for f in listdir(testdir) if path.isfile(path.join(testdir, f))]

for user_query in testfiles:
    sims = model.docvecs.most_similar(user_query)

    title = reader.select_title_by_id(user_query)
    authors = reader.select_author_by_id(user_query)
    authors = ','.join([w for w in authors])
    rank = 0
    print(str(rank) + '\t' + title + '\t' + authors + '\t' + user_query + '\t' + '1.0')
    print('==========================')
    for sim in sims:
        rank += 1
        doc = sim[0]
        similarity = sim[1]
        authors = reader.select_author_by_id(doc)
        authors = ','.join([w for w in authors])
        title = reader.select_title_by_id(doc)
        output = '\t'.join([str(rank), title, authors, doc, str(similarity)])
        print(output)
        rank += 1
    print('==========================')
    print('==========================')
