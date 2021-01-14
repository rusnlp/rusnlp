import csv
from gensim import models
import gzip
import logging
import zipfile
import os
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


def send_to_archieve(archieve_path, model_path, remove_source=True):
    with gzip.open(archieve_path, 'wb') as zipped_file:
        logging.info('Saving vectors into archieve')
        zipped_file.writelines(open(model_path, 'rb'))
        logging.info('Vectors are saved into archieve')
    if remove_source:
        logging.info('Deleting source file {}'.format(model_path))
        os.remove(model_path)
    logging.info('Saved vectors {} to archive {}'.format(model_path, archieve_path))


def save_text_vectors(vectors, output_path, remove_source=True):
    # генерим пути
    if output_path.endswith('gz'):  # если путь -- архив
        model_path = clean_ext(output_path)
        archieve_path = output_path
    else:
        model_path = output_path
        archieve_path = ''

    binary = get_binarity(output_path)

    if binary:  # если название бинарное, а нам нужно временное текстовое
        text_model_path = clean_ext(model_path)+'.vec'
        bin_model_path = output_path  # возможно, оно уже с архивом, gensim разберётся
    else:
        text_model_path = model_path
        bin_model_path = ''

    # print('''
    # text_model_path: {}
    # bin_model_path: {}
    # archieve_path: {}
    # '''.format(text_model_path, bin_model_path, archieve_path))

    # генерим текстовый формат w2v
    logging.info('Saving vectors in the text w2v format to {}'.format(text_model_path))
    vec_str = '{} {}'.format(len(vectors), len(list(vectors.values())[0]))
    for word, vec in tqdm(vectors.items(), desc='Formatting'):
        vec_str += '\n{} {}'.format(word, ' '.join(str(v) for v in vec))
    open(text_model_path, 'w', encoding='utf-8').write(vec_str)

    if binary:  # конвертируем через gensim и сразу архивируем
        logging.info('Converting text w2v format into binary to {}'.format(bin_model_path))
        model = load_embeddings(text_model_path)
        model.save_word2vec_format(bin_model_path, binary=True)
        if remove_source:
            logging.info('Deleting source file {}'.format(text_model_path))
            os.remove(text_model_path)

    else:  # если нужен текстовый формат, проверяем, нужно ли архивировать
        if archieve_path:
            send_to_archieve(archieve_path, text_model_path, remove_source)
        else:
            logging.info('Saved vectors to {}'.format(output_path))


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
