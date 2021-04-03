"""
python clusters_extractor.py --in_paths=current_authors.tsv+current_affiliations.tsv --out_paths=authors.json+affiliations.json
"""

import argparse
from json import dump

lat = 'qwertyuiopasdfghjklzxcvbnm'
cyr = 'ёйцукенгшщзхъфывапролджэячсмитьбю'


def get_alplha_set(alpha):
    return set(alpha.lower()) | set(alpha.upper())


lat_set = get_alplha_set(lat)
cyr_set = get_alplha_set(cyr)


def parse_args():
    parser = argparse.ArgumentParser(
        description='Извлечение уникальных авторов и аффилиаций в json')
    parser.add_argument('--in_paths', type=str, required=True,
                        help='Путь к данным current_ в формате tsv (можно перечислить через +)')
    parser.add_argument('--out_paths', type=str,
                        help='Путь к извлечённым уникальным значениям в формате json (можно перечислить через +)')
    parser.add_argument('--tab_count', type=int, default=2,
                        help='Сколько \t должно быть в строке данных (default: 2)')
    parser.add_argument('--test', action='store_true',
                        help='Проверка данных на соотвествие формату (количество \t) без записи в json')

    return parser.parse_args()


def test_tabs(raw, tab_count=2):
    invalid_lines = ['\t{}: {}'.format(i+1, line.split('\t')) for i, line in enumerate(raw) if line and line.count('\t') != tab_count]
    if invalid_lines:
        print('Некорректные табы:\n{}'.format('\n'.join(invalid_lines)))
        return False
    else:
        print('Табы корректны')
        return True


def test_alphas(clusters):
    invalid_lines = []
    for cluster in clusters:
        for word in cluster.split():
            intersects = [set(word) & alpha for alpha in [lat_set, cyr_set]]
            if intersects[1]:
                invalid_lines.append('\t{} - {} - {}'.format(cluster, word, intersects[1]))
    if invalid_lines:
        print('Некорректные кластеры:\n{}'.format('\n'.join(invalid_lines)))
        return False
    else:
        print('Кластеры корректны')
        return True


def collect_data(in_path, tab_count=2):
    print(in_path)
    raw_data = [line for line in open(in_path, encoding='utf-8').read().split('\n') if line]
    if test_tabs(raw_data, tab_count):
        clusters = set([line.split('\t')[1] for line in raw_data])
        print('{} строк -> {} уникальных значений'.format(len(raw_data), len(clusters)))
        test_alphas(clusters)
    else:
        clusters = []
    return clusters


def main(test=False):
    args = parse_args()
    in_paths = args.in_paths.split('+')
    if not args.test:
        if args.out_paths:
            out_paths = args.out_paths.split('+')
        else:
            raise Exception('Введите out_paths!')
    else:
        out_paths = ['']*len(in_paths)

    for in_path, out_path in zip(in_paths, out_paths):
        data = collect_data(in_path, args.tab_count)
        if data and not args.test:
            dump(sorted(list(data)), open(out_path, 'w', encoding='utf-8'), indent=4, ensure_ascii=False)
            print('Кластеры сохранены в {}'.format(out_path))
        print()


if __name__ == '__main__':
    main()
