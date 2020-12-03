import csv
from gensim import models
import gzip
import logging
import zipfile
import os
import sys
from utils.preprocessing import clean_ext

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


def load_embeddings(embeddings_path):  # TODO: пометить, что чужое
    """
    :param embeddings_path: путь к модели эмбеддингов (строка)
    :return: загруженная предобученная модель эмбеддингов (KeyedVectors)
    """
    # Бинарный формат word2vec:
    if embeddings_path.endswith('.bin.gz') or embeddings_path.endswith('.bin'):
        model = models.KeyedVectors.load_word2vec_format(embeddings_path, binary=True,
                                                         unicode_errors='replace')
    # Текстовый формат word2vec:
    elif embeddings_path.endswith('.txt.gz') or embeddings_path.endswith('.txt') \
            or embeddings_path.endswith('.vec.gz') or embeddings_path.endswith('.vec'):
        model = models.KeyedVectors.load_word2vec_format(
            embeddings_path, binary=False, unicode_errors='replace')

    # ZIP-архив из репозитория NLPL:
    elif embeddings_path.endswith('.zip'):
        with zipfile.ZipFile(embeddings_path, "r") as archive:
            # Loading and showing the metadata of the model:
            # metafile = archive.open('meta.json')
            # metadata = json.loads(metafile.read())
            # for key in metadata:
            #    print(key, metadata[key])
            # print('============')

            # Загрузка самой модели:
            stream = archive.open("model.bin")  # или model.txt, чтобы взглянуть на модель
            model = models.KeyedVectors.load_word2vec_format(
                stream, binary=True, unicode_errors='replace')
    else:
        # Native Gensim format?
        model = models.KeyedVectors.load(embeddings_path)
        # If you intend to train further: emb_model = models.Word2Vec.load(embeddings_file)

    model.init_sims(replace=True)  # Unit-normalizing the vectors (if they aren't already)
    return model


def save_text_vectors(vectors, output_path):

    if output_path.endswith('gz'):  # если путь -- архив
        model_path = clean_ext(output_path)
        archieve_path = output_path
    else:
        model_path = output_path
        archieve_path = ''

    vec_str = '{} {}'.format(len(vectors), len(list(vectors.values())[0]))
    for word, vec in vectors.items():
        vec_str += '\n{} {}'.format(word, ' '.join(str(v) for v in vec))
    open(model_path, 'w', encoding='utf-8').write(vec_str)

    if archieve_path:
        with gzip.open(archieve_path, 'wb') as zipped_file:
            zipped_file.writelines(open(model_path, 'rb'))
        # os.remove(model_path)
        print('Сохранил вектора {} в архив {}'.format(model_path, archieve_path), file=sys.stderr)
    else:
        print('Сохранил вектора в {}'.format(model_path), file=sys.stderr)


def load_task_terms(file_path, column_name):
    task_terms = {}
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter='\t')
        for row in csvreader:
            descript = row['description']
            task_name = 'TASK::{}'.format(descript.replace(' ', '_'))
            terms = row[column_name].split()
            # print(task_name, terms, url)
            task_terms[task_name] = terms
        return task_terms
