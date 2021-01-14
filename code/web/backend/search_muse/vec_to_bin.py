import argparse
import logging
import os
from utils.loaders import load_embeddings, send_to_archieve

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser(
        description='Преобразование векторов из текстового формата в бинарный')
    parser.add_argument('--text_path', type=str, required=True,
                        help='Путь к векторам в текстовом формате')
    parser.add_argument('--bin_path', type=str, required=True,
                        help='Путь к векторам в бинарном формате')
    parser.add_argument('--remove_source_text', type=int, default=0,
                        help='Удалять ли исходный файл с векторами в текстовом формате (default: 0)')

    return parser.parse_args()


def main():
    args = parse_args()

    logging.info('Конвертирую текстовый формат w2v в бинарный в {}'.format(args.bin_path))
    model = load_embeddings(args.text_path)
    model.save_word2vec_format(args.bin_path, binary=True)
    if args.remove_source_text:
        logging.info('Удаляю исходный файл {}'.format(args.text_path))
        os.remove(args.text_path)


if __name__ == '__main__':
    main()
