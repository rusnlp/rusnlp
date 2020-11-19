from gensim. models import KeyedVectors
import numpy as np
from tqdm import tqdm
import gzip

nlpub_file_path = '../data/nlpub.tsv'
word_model_path = 'cross_muse.vec.gz'
nlpub_model_path = 'nlpub.vec'
nlpub_archieve_path = 'nlpub.vec.gz'


def vectorize_text(tokens, model):
    words = [token for token in tokens if token in model]
    vecs = np.zeros((len(words), model.vector_size))
    if not words:
        return np.zeros(model.vector_size)
    for i, token in enumerate(words):
        vecs[i, :] = model[token]
    vec = np.sum(vecs, axis=0)
    vec = np.divide(vec, len(words))
    vec = vec / np.linalg.norm(vec)

    return vec


def save_corpus_vectors(vectors, path):
    vec_str = '{} {}'.format(len(vectors), len(list(vectors.values())[0]))
    for word, vec in tqdm(vectors.items()):
        vec_str += '\n{} {}'.format(word, ' '.join(str(v) for v in vec))
    open(path, 'w', encoding='utf-8').write(vec_str)


# word_model = KeyedVectors.load_word2vec_format(word_model_path, binary=False, unicode_errors='replace')
#
# nlpub_terms = {}
# csvlines = open(nlpub_file_path, 'r', encoding='utf-8').readlines()
# for row in tqdm(csvlines):
#     descript, terms, url = row.split('\t')
#     terms = terms.split()
#     # print(descript, terms, url)
#     nlpub_terms[descript] = vectorize_text(terms, word_model)
#
# save_corpus_vectors(nlpub_terms, nlpub_model_path)


# nlpub_model = KeyedVectors.load_word2vec_format(nlpub_model_path, binary=False, unicode_errors='replace')

# with gzip.open(nlpub_archieve_path, 'wb') as zipped_file:
#     zipped_file.writelines(open(nlpub_model_path, 'rb'))
