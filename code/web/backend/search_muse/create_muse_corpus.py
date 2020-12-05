'''
python code/web/backend/search_muse/create_muse_corpus.py --texts_path=texts/en_conllu+texts/ru_conllu --lemmatize=1 --embeddings_path=code/web/models/cross_muse.bin.gz --common_vectors_path=code/web/models/common_lem_muse.bin.gz --mis_path=texts/mis_lem_en.txt+texts/mis_lem_ru.txt --task_path=code/web/data/nlpub.tsv --task_column=terms_short
python code/web/backend/search_muse/create_muse_corpus.py --texts_path=texts/en_conllu+texts/ru_conllu --lemmatize=0 --embeddings_path=code/web/models/cross_muse.bin.gz --common_vectors_path=code/web/models/common_tok_muse.bin.gz --mis_path=texts/mis_tok_en.txt+texts/mis_tok_ru.txt --task_path=code/web/data/nlpub.tsv --task_column=terms_short
'''

import argparse
import os
import sys
from tqdm import tqdm

from utils.loaders import load_embeddings, save_text_vectors, load_task_terms
from utils.preprocessing import get_text, clean_ext
from utils.vectorization import vectorize_text, vectorize_corpus


def parse_args():
    parser = argparse.ArgumentParser(
        description='Векторизация корпусов в общую модель')
    parser.add_argument('--texts_path', type=str, required=True,
                        help='Путь к текстам в формате conllu (можно перечислить через +)')
    parser.add_argument('--lemmatize', type=int, required=True,
                        help='Брать ли леммы текстов (0/1)')
    parser.add_argument('--keep_pos', type=int, default=0,
                        help='Возвращать ли леммы, помеченные pos-тегами (0|1; default: 0)')
    parser.add_argument('--keep_punct', type=int, default=0,
                        help='Сохранять ли знаки препинания (0|1; default: 0)')
    parser.add_argument('--keep_stops', type=int, default=0,
                        help='Сохранять ли слова, получившие тег функциональной части речи '
                             '(0|1; default: 0)')
    parser.add_argument('--unite', type=int, default=1,
                        help='Убирать ли деление на предложения (0|1; default: 1)')
    parser.add_argument('--no_duplicates', type=int, default=0,
                        help='Брать ли для каждого типа в тексте вектор только по одному разу '
                             '(0|1; default: 0)')
    parser.add_argument('--embeddings_path', type=str, required=True,
                        help='Путь к модели векторизации')
    parser.add_argument('--common_vectors_path', type=str, required=True,
                        help='Путь к файлу, в котором лежит объединённый векторизованный корпус')
    parser.add_argument('--dir_vectors_path', type=str,
                        help='Путь к файлу, в котором лежит векторизованный корпус из папки '
                             '(можно перечислить через +)')
    parser.add_argument('--mis_path', type=str,
                        help='Путь к файлу с ошибками векторизации текстов '
                             '(можно перечислить через +)')
    parser.add_argument('--task_path', type=str, required=True,
                        help='Путь к файлу с темами из NLPub')
    parser.add_argument('--task_column', type=str, default='terms',
                        help='Какую колонку со словами брать изNLPub (default: terms)')

    return parser.parse_args()


def split_paths(joint_path, texts_paths):
    # делим пути по + или задаём столько пустых, сколько пришло папок с текстами
    if joint_path:
        paths = joint_path.split('+')
    else:
        paths = [''] * len(texts_paths)
    return paths


def get_corpus(texts_path, lemmatize, keep_pos, keep_punct, keep_stops, unite):
    """собираем тексты из conllu в список"""
    texts = {}
    for file in tqdm(os.listdir(texts_path)):
        text = open('{}/{}'.format(texts_path, file), encoding='utf-8').read().strip()
        preprocessed = get_text(text, lemmatize, keep_pos, keep_punct, keep_stops, unite)
        texts[clean_ext(file)] = preprocessed

    return texts


def main_onepath(texts_path, lemmatize, keep_pos, keep_punct, keep_stops, unite, embed_model,
                 no_duplicates, dir_vectors_path, mis_path):
    """делаем словарь векторов для папки"""
    # собираем тексты из conllu
    text_corpus = get_corpus(texts_path, lemmatize, keep_pos, keep_punct, keep_stops, unite)

    vec_corpus, not_vectorized = vectorize_corpus(text_corpus, embed_model, no_duplicates)

    if dir_vectors_path:
        save_text_vectors(vec_corpus, dir_vectors_path)

    if not_vectorized:
        print('Не удалось векторизовать текстов: {}'.format(len(not_vectorized)), file=sys.stderr)
        if mis_path:
            open(mis_path, 'w', encoding='utf-8').write('\n'.join(not_vectorized))

    return vec_corpus


def main():
    args = parse_args()

    texts_paths = args.texts_path.split('+')
    dir_vectors_paths = split_paths(args.dir_vectors_path, texts_paths)
    mis_paths = split_paths(args.mis_path, texts_paths)

    embed_model = load_embeddings(args.embeddings_path)
    common_vectors = {}

    for texts_path, dir_vectors_path, mis_path in zip(texts_paths, dir_vectors_paths, mis_paths):
        print('Векторизую {}'.format(texts_path), file=sys.stderr)
        text_vectors = main_onepath(texts_path, args.lemmatize, args.keep_pos, args.keep_punct,
                                    args.keep_stops, args.unite, embed_model, args.no_duplicates,
                                    dir_vectors_path, mis_path)

        common_vectors.update(text_vectors)

    task_terms = load_task_terms(args.task_path, args.task_column)
    task_vectors = {task: vectorize_text(terms, embed_model) for task, terms in task_terms.items()}
    common_vectors.update(task_vectors)

    save_text_vectors(common_vectors, args.common_vectors_path)


if __name__ == "__main__":
    main()
