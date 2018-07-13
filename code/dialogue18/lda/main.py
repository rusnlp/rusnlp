# -*- coding: utf-8 -*-
import sys
import os
import pickle
from conllu import parse
from collections import defaultdict

# --------------------------------------------------------------------
# sys
# --------------------------------------------------------------------
from nltk.corpus import stopwords

from lda import _build_lda_model_with_params


def _get_data_from_cmd(length, usage):
    args = sys.argv
    if len(args) != length:
        print(usage.format(args[0]))
        raise AttributeError("Wrong arguments")
    return sys.argv


def _create_folder_if_absent(path):
    if not os.path.exists(path):
        os.mkdir(path)


# --------------------------------------------------------------------
# read and write
# --------------------------------------------------------------------
def _read_file_lines(path):
    with open(path, 'r', encoding='utf-8') as file:
        full_data = file.read()
        data = parse(full_data)
        return data


def _write_to_file(dirname, name, data):
    filename = os.path.join(dirname, name)
    with open(filename, 'w', encoding="utf-8") as file_to_write:
        file_to_write.writelines(data)


def _check_lemma(lemma):
    return True == (lemma.isalpha() and len(lemma) > 3)


def _parse_files(filedir, pos=True):
    all_texts = defaultdict(list)
    for root, dirs, files in os.walk(filedir):
        for file in files:
            data = _read_file_lines(os.path.join(root, file))
            if pos:
                all_texts[os.path.splitext(file)[0]] = [word["lemma"] + "_" + word["upostag"] for sentence in data for
                                                        word
                                                        in sentence if
                                                        word["lemma"] not in stopwords.words(
                                                            "english") and _check_lemma(
                                                            word["lemma"])]
            else:
                all_texts[os.path.splitext(file)[0]] = [word["lemma"] for sentence in data for
                                                        word
                                                        in sentence if
                                                        word["lemma"] not in stopwords.words(
                                                            "english") and _check_lemma(
                                                            word["lemma"])]
    return all_texts


def _data_distribution(output, data, folder, topics, num_most_freq, pos):
    output = os.path.join(output, folder)
    _create_folder_if_absent(output)
    for root, dirs, files in os.walk(folder):
        for file in files:
            path = os.path.join(file)
            with open(os.path.join(folder, path), 'rb') as p:
                list_of_ids = pickle.load(p)
            list_of_docs = []
            for id in list_of_ids:
                list_of_docs.append(data[str(id)])
            print(os.path.splitext(path)[0])
            try:
                _build_lda_model_with_params(output, os.path.splitext(path)[0], list_of_docs, num_topics=topics, num_most_frequent=num_most_freq, pos=pos)
            except ValueError as e:
                print("no articles in"+os.path.splitext(path)[0])

def _get_data_distribution(data, folder):
    with open(folder, 'rb') as p:
        list_of_ids = pickle.load(p)
    list_of_docs = []
    for id in list_of_ids:
        list_of_docs.append(data[str(id)])
    return list_of_docs

def main():
    _, inputpath, outputpath = _get_data_from_cmd(3, "Usage: {} <input_directory> <output_directory>")

    with open(os.path.join(inputpath, "pos_lemmas_with_normalized_words.pickle"), 'rb') as handle:
        all_texts_dict_pos = pickle.load(handle)

    print("POS data prepared")

    with open(os.path.join(inputpath, "raw_lemmas_with_normalized_words.pickle"), 'rb') as handle:
        all_texts_dict_raw = pickle.load(handle)
    print("RAW data prepared")

    num_most_freq = [20]
    topics = [15]
    data_dicts = [all_texts_dict_pos]

    for data in data_dicts:
        for n_topics in topics:
            for freq in num_most_freq:
                _build_lda_model_with_params(outputpath,"_common_",  list(data.values()), num_topics=n_topics, num_most_frequent=freq,
                                             pos=data_dicts.index(data))
                _data_distribution(outputpath, data, "conferences", n_topics, freq,
                                  pos=data_dicts.index(data))
                _data_distribution(outputpath, data, "years", n_topics, freq,
                                   pos=data_dicts.index(data))
                _data_distribution(outputpath, data, "conference_years", n_topics, freq,
                                   pos=data_dicts.index(data))



if __name__ == '__main__':
    main()
