import csv
from gensim import models, utils as gensim_utils
import logging
import numpy as np
import zipfile
from tqdm import tqdm
try:
    from utils.preprocessing import clean_ext
except ModuleNotFoundError:
    from backend.search_muse.utils.preprocessing import clean_ext

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)


w2v_path_binarity = {
    '.bin.gz': True,
    '.bin': True,
    '.txt.gz': False,
    '.txt': False,
    '.vec.gz': False,
    '.vec': False
}


def get_binarity(path):
    binary = 'NA'
    for ext in w2v_path_binarity:
        if path.endswith(ext):
            binary = w2v_path_binarity.get(ext)
            break
    return binary


def load_embeddings(embeddings_path):
    binary = get_binarity(embeddings_path)

    if binary != 'NA':
        model = models.KeyedVectors.load_word2vec_format(embeddings_path, binary=binary,
                                                         unicode_errors='replace')
    # ZIP archive from the NLPL vector repository:
    elif embeddings_path.endswith('.zip'):
        with zipfile.ZipFile(embeddings_path, "r") as archive:
            # Loading and showing the metadata of the model:
            # metafile = archive.open('meta.json')
            # metadata = json.loads(metafile.read())
            # for key in metadata:
            #    print(key, metadata[key])
            # print('============')

            stream = archive.open("model.bin")  # или model.txt, чтобы взглянуть на модель
            model = models.KeyedVectors.load_word2vec_format(
                stream, binary=True, unicode_errors='replace')
    else:
        # Native Gensim format?
        model = models.KeyedVectors.load(embeddings_path)
        # If you intend to train further: emb_model = models.Word2Vec.load(embeddings_file)

    model.init_sims(replace=True)  # Unit-normalizing the vectors (if they aren't already)
    return model


def save_w2v(vocab, output_path):
    """аналог save_word2vec_format для простого словаря, не сортируем по частотам"""
    binary = get_binarity(output_path)
    total_vec = len(vocab)
    vectors = np.array(list(vocab.values()))
    vector_size = vectors.shape[1]
    logging.info("storing {}x{} projection weights into {}".format(total_vec, vector_size, output_path))
    assert (len(vocab), vector_size) == vectors.shape
    with gensim_utils.open(output_path, 'wb') as fout:
        fout.write(gensim_utils.to_utf8("%s %s\n" % (total_vec, vector_size)))
        # TODO: store in sorted order: most frequent words at the top
        for word, row in tqdm(vocab.items(), desc='Saving'):
            if binary:
                row = row.astype(np.float32)
                fout.write(gensim_utils.to_utf8(word) + b" " + row.tostring())
            else:
                fout.write(gensim_utils.to_utf8("{} {}\n".format(word, ' '.join(repr(val) for val in row))))


def format_task_name(description):
    return 'TASK::{}'.format(description.replace(' ', '_'))


def load_task_terms(file_path, column_name):
    task_terms = {}
    with open(file_path, 'r', encoding='utf-8') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter='\t')
        for row in csvreader:
            descript = row['description']
            task_name = format_task_name(descript)
            terms = row[column_name].split()
            # print(task_name, terms, url)
            task_terms[task_name] = terms
        return task_terms


def split_paths(joint_path, texts_paths):
    # делим пути по + или задаём столько пустых, сколько пришло папок с текстами
    if joint_path:
        paths = joint_path.split('+')
    else:
        paths = [''] * len(texts_paths)
    return paths