from leven import levenshtein
import numpy as np
from numpy.linalg import norm
from tqdm import tqdm


def empty_vec(model):
    return np.zeros(model.vector_size)


def str_model(model, embeddings_file):
    return '{}:\nModel: {}\nDim: {}'.format(type(model), embeddings_file, model.vector_size)


def choose_first(words, vocab):
    positions = {word: vocab.index(word) for word in words}
    sorted_pos = sorted(positions, key=positions.get)
    return sorted_pos[0]


def find_substitution(token, model, max_end=3):
    model_vocab = list(model.vocab)
    for i in range(1, max_end+1):
        dists = {word: levenshtein(token, word) for word in model_vocab
                    if word.startswith(token[:-i])}
        if dists:
            if len(dists) == 1:
                sub_word = list(dists.keys())[0]
            else:  # выбираем слова с минимальной дистанцией
                min_dist = min(dists.values())
                pos_subs = {word: dists[word] for word in dists if dists[word] == min_dist}
                if len(pos_subs) == 1:
                    sub_word = list(pos_subs.keys())[0]
                else:  # выбираем самую частотную форму (на основе порядка в модели)
                    sub_word = choose_first(pos_subs.keys(), model_vocab)
            print('{} --> {}. Edit distance = {}'.format(token, sub_word, i))
            return sub_word
        else:
            return ''


def get_words(tokens, model, no_duplicates=0, substitute=0, max_end=3):
    if substitute:
        words = []
        for token in tokens:
            if token in model:
                words.append(token)
            else:
                sub = find_substitution(token, model, max_end)
                if sub:
                    words.append(sub)
    else:
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
    vec = np.divide(vec, len(words))
    return vec


def get_norm_mean_vec(vecs, words):
    vec = get_mean_vec(vecs, words)
    vec = get_norm_vec(vec)
    return vec


def vectorize_text(tokens, model, no_duplicates=0, substitute=0, max_end=3):
    # простая векторизация моделью
    words = get_words(tokens, model, no_duplicates, substitute, max_end)

    if not words:
        return empty_vec(model)

    t_vecs = np.zeros((len(words), model.vector_size))
    for i, token in enumerate(words):
        t_vecs[i, :] = model[token]
    t_vec = get_norm_mean_vec(t_vecs, words)

    return t_vec


def vectorize_corpus(corpus, model, no_duplicates=0, substitute=0, max_end=3):
    # векторизация корпуса в словарь
    not_vectorized = []
    corp_vectors = {}

    for name, text in tqdm(corpus.items(), desc='Vectorizing'):
        vector = vectorize_text(text, model, no_duplicates, substitute, max_end)
        if not np.array_equal(vector, empty_vec(model)):  # если это не зарезервированный вектор
            corp_vectors[name] = vector

        else:
            not_vectorized.append(name)
            continue

    return corp_vectors, not_vectorized
