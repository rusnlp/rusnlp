import sys
from os import path, listdir
import logging
from gensim import similarities
import gensim
import pickle

sys.path.insert(0, '../database/')
from code.web.db_classes.db import DBaseRusNLP
from code.web.db_classes.db_reader import ReaderDBase


def getpos(ordering, name):
    return ordering.index(name + '.conll')


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

bd_m = DBaseRusNLP(path.join('..', '..', '..', 'database', 'rus_nlp_withouttexts.db'),
                   path.join('..', '..', '..', 'database', 'database_metadata.json'))
reader = ReaderDBase(bd_m)

lemmasfile = sys.argv[1]
modelfile = sys.argv[2]
testdir = sys.argv[3]

with open(lemmasfile, 'rb') as handle:
    all_texts_dict = pickle.load(handle)
order = list(all_texts_dict.keys())

data = [all_texts_dict[val] for val in order]

ldamodel = gensim.models.ldamodel.LdaModel.load(modelfile)
dictionary = ldamodel.id2word

corpus = [dictionary.doc2bow(doc) for doc in data]
ldacorpus = ldamodel[corpus]

index = similarities.MatrixSimilarity(ldacorpus)

print('Rank\tTitle\tAuthors\tID\tSimilarity')
testfiles = [f.split('.')[0] for f in listdir(testdir) if path.isfile(path.join(testdir, f))]

for name in testfiles:
    print('==========================\n')
    print(name)
    position = getpos(order, name)

    counter = 0
    for sim in index:
        if counter == position:
            sims = sim
            break
        counter += 1

    sims = sorted(enumerate(sims), key=lambda item: -item[1])
    rank = 0
    for sim in sims[:11]:
        doc = order[sim[0]].split('.')[0]
        print(doc)
        similarity = sim[1]
        authors = reader.select_author_by_id(doc)
        authors = ','.join([w for w in authors])
        title = reader.select_title_by_id(doc)
        if doc == name:
            print('==========================')
            output = '\t'.join([str(rank), title, authors, doc, str(similarity)])
            print(output)
        else:
            output = '\t'.join([str(rank), title, authors, doc, str(similarity)])
            print(output)
        rank += 1
    print('==========================')
