import gensim
import pickle
from gensim import corpora
import os

def _load_data(path):
    with open(path, 'rb') as handle:
        all_texts_dict = pickle.load(handle)
    print("Data from " + path + " loaded")
    return all_texts_dict.values()

def _build_dictionary(data, num_most_frequent):
    dictionary = corpora.Dictionary(data)
    dictionary.filter_n_most_frequent(num_most_frequent)
    print("Dictionary built")
    return dictionary

def _build_corpus(data, dictionary):
    final_corpus = [dictionary.doc2bow(doc) for doc in data]
    print("Corpus built")
    return final_corpus

def _build_model(corpus, num_topics, dictionary):
    Lda = gensim.models.ldamodel.LdaModel
    ldamodel = Lda(corpus, num_topics=num_topics, id2word=dictionary, passes=50)
    print("Model built")
    print(ldamodel.print_topics(num_topics=num_topics, num_words=num_topics))
    return ldamodel

def _create_folder_if_absent(path):
    if not os.path.exists(path):
        os.mkdir(path)

def _save_model(output, name, model, num_most_frequent, num_topics, pos):
    dirname_to_save = "lda_model_normalized_words_freq_" + name + str(num_most_frequent) + "_topics_" + str(
        num_topics) + "_pos_"+str(pos)
    print(dirname_to_save)
    print(output)
    print(output+"/"+dirname_to_save)
    _create_folder_if_absent(os.path.join(output, dirname_to_save))
    full_path = os.path.join(output, dirname_to_save)
    print(full_path)

    model.save(os.path.join(full_path, dirname_to_save + name +".mdl"))


def _build_lda_model_with_params(output, name, data, num_topics=10, num_most_frequent=10, pos=0):
    dictionary = _build_dictionary(data, num_most_frequent)
    corpus = _build_corpus(data, dictionary)
    model = _build_model(corpus, num_topics, dictionary)
    _save_model(output, name, model, num_most_frequent, num_topics, pos)


