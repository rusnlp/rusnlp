#!/usr/bin/python3

import sys
import numpy as np
import logging
import pickle
from gensim.models import LdaModel
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import pyLDAvis.gensim
from main import _get_data_distribution

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def visual(dot_labels, features, classes):
    # Plot the vectors using PCA
    dot_labels = np.array(dot_labels)
    classes = np.array(classes)
    colors = {'dialog': 'blue', 'aist': 'red', 'ainl': 'darkorange', 'russir': 'brown'}
    pca = PCA(n_components=2)
    x_r = pca.fit_transform(features)
    plt.figure()
    for target_name in set(classes):
        plt.scatter(x_r[classes == target_name, 0], x_r[classes == target_name, 1],
                    s=8, color=colors[target_name], label=target_name, alpha=0.8)
    plt.legend(loc='best', scatterpoints=1)
    plt.show()
    #  plt.savefig('topics_documents_pca.pdf', dpi=300)
    plt.close()


modelfile = sys.argv[1]
corpusfile = sys.argv[2]
# conferencesfile = sys.argv[3]

model = LdaModel.load(modelfile)
vocab = model.id2word

print(model)
print(model.show_topics())

with open(corpusfile, 'rb') as handle:
    corpus = pickle.load(handle)

view = sys.argv[3]

corpus = _get_data_distribution(corpus, "years/" + view + "_en.pickle")

# conferences = open(conferencesfile, 'rb')
# conferences = pickle.load(conferences)

vectors = []
labels = []
#  venues = []  # conferences
vectorized_corpus = []

for i in corpus:
    labels.append(i)
    # found = False
    # for conf in conferences:
    #     if int(i) in conferences[conf]:
    #         venues.append(conf)
    #         found = True
    #         break
    # if not found:
    #     print(i)
    #     exit()
    vectorized = vocab.doc2bow(i)
    vectorized_corpus.append(vectorized)
    topic_vector = model.get_document_topics(vectorized, minimum_probability=0)
    topic_vector = np.array([el[1] for el in topic_vector])
    vectors.append(topic_vector)

# Generating PyLDAvis files
vis = pyLDAvis.gensim.prepare(model, vectorized_corpus, vocab)
pyLDAvis.save_html(vis, view + '.html')

# Generating PCA document plot
# visual(labels, vectors, venues)
