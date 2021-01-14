import numpy as np
from numpy.linalg import norm
from tqdm import tqdm


def empty_vec(model):
    return np.zeros(model.vector_size)


def str_model(model, embeddings_file):
    return '{}:\nModel: {}\nDim: {}'.format(type(model), embeddings_file, model.vector_size)


def get_words(tokens, model, no_duplicates=0):
    words = [token for token in tokens if token in model]
    # если прилетел пустой текст, то он так и останется пустым просто
    if no_duplicates:
        words = set(words)
    return words


def get_norm_vec(vec):
    vec = vec / norm(vec)
    return vec


def get_mean_vec(vecs, words):
    vec = np.sum(vecs, axis=0)
    vec = np.divide(vec, len(words))  # TODO: почему не np.mean? Другая длина words?
    # vec = np.mean(vec, axis=0)
    return vec


def get_norm_mean_vec(vecs, words):
    vec = get_mean_vec(vecs, words)
    vec = get_norm_vec(vec)
    return vec


def vectorize_text(tokens, model, no_duplicates=0):
    # простая векторизация моделью
    words = get_words(tokens, model, no_duplicates)

    if not words:
        # print('Я ничего не знаю из этих токенов: {}'.format(tokens), file=sys.stderr)
        return empty_vec(model)

    t_vecs = np.zeros((len(words), model.vector_size))
    for i, token in enumerate(words):
        t_vecs[i, :] = model[token]
    t_vec = get_norm_mean_vec(t_vecs, words)

    return t_vec


def vectorize_corpus(corpus, model, no_duplicates=0):
    # векторизация корпуса в словарь
    not_vectorized = []
    corp_vectors = {}

    for name, text in tqdm(corpus.items(), desc='Vectorizing'):
        vector = vectorize_text(text, model, no_duplicates)
        if not np.array_equal(vector, empty_vec(model)):  # если это не зарезервированный вектор
            corp_vectors[name] = vector

        else:
            not_vectorized.append(name)
            continue

    return corp_vectors, not_vectorized
