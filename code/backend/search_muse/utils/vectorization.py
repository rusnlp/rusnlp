import numpy as np
from tqdm import tqdm
from numpy.linalg import norm

from utils.loaders import load_embeddings, save_text_vectors


class ModelVectorizer:
    def __init__(self, embeddings_path, no_duplicates):
        self.embeddings_file = embeddings_path
        self.no_duplicates = no_duplicates
        self.model = load_embeddings(embeddings_path)
        self.dim = self.model.vector_size
        self.empty = np.zeros(self.dim)  # TODO: возвращать вектор какого-то слова

    def __str__(self):
        return '{}:\nModel: {}\nDim: {}'.format(type(self), self.embeddings_file, self.dim)

    def get_words(self, tokens):
        words = [token for token in tokens if token in self.model]
        # если прилетел пустой текст, то он так и останется пустым просто

        if self.no_duplicates:
            words = set(words)

        return words

    def get_norm_vec(self, vec):
        vec = vec / norm(vec)
        return vec

    def get_mean_vec(self, vecs, words):
        vec = np.sum(vecs, axis=0)
        vec = np.divide(vec, len(words))  # TODO: почему не np.mean? Другая длина words?
        # vec = np.mean(vec, axis=0)
        return vec

    def get_norm_mean_vec(self, vecs, words):
        vec = self.get_mean_vec(vecs, words)
        vec = self.get_norm_vec(vec)
        return vec

    def vectorize_text(self, tokens):
        # простая векторизация моделью
        words = self.get_words(tokens)

        if not words:
            # print('Я ничего не знаю из этих токенов: {}'.format(tokens), file=sys.stderr)
            return self.empty

        t_vecs = np.zeros((len(words), self.dim))
        for i, token in enumerate(words):
            t_vecs[i, :] = self.model[token]
        t_vec = self.get_norm_mean_vec(t_vecs, words)

        return t_vec

    def vectorize_corpus(self, corpus):
        # векторизация корпуса в словарь
        not_vectorized = []
        corp_vectors = {}

        for name, text in tqdm(corpus.items()):
            vector = self.vectorize_text(text)
            if not np.array_equal(vector, self.empty):  # если это не зарезервированный вектор
                corp_vectors[name] = vector

            else:
                not_vectorized.append(name)
                continue

        return corp_vectors, not_vectorized



