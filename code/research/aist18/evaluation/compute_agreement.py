from pandas import read_csv
from collections import defaultdict
from os import path
import numpy as np

NUMBER_OF_ASSESSORS = 3
ASSESSMENT_FOLDER = 'assessments'
ASSESSMENT_FILE_DUMMY = 'assessor'


def nominal_metric(a, b):
    return a != b


def interval_metric(a, b):
    return (a - b) ** 2


def ratio_metric(a, b):
    return ((a - b) / (a + b)) ** 2


def krippendorff_alpha(data, metric=interval_metric, force_vecmath=False, convert_items=float, missing_items=None):
    m = len(data)
    if missing_items is None:
        maskitems = []
    else:
        maskitems = list(missing_items)
    if np is not None:
        maskitems.append(np.ma.masked_singleton)
    units = {}
    for d in data:
        try:
            diter = d.items()
        except AttributeError:
            diter = enumerate(d)
        for it, g in diter:
            if g not in maskitems:
                try:
                    its = units[it]
                except KeyError:
                    its = []
                    units[it] = its
                its.append(convert_items(g))

    units = dict((it, d) for it, d in units.items() if len(d) > 1)
    n = sum(len(pv) for pv in units.values())

    if n == 0:
        raise ValueError('No items to compare.')

    np_metric = (np is not None) and ((metric in (interval_metric, nominal_metric, ratio_metric)) or force_vecmath)

    Do = 0.
    for grades in units.values():
        if np_metric:
            gr = np.asarray(grades)
            Du = sum(np.sum(metric(gr, gri)) for gri in gr)
        else:
            Du = sum(metric(gi, gj) for gi in grades for gj in grades)
        Do += Du / float(len(grades) - 1)
    Do /= float(n)

    if Do == 0:
        return 1.

    De = 0.
    for g1 in units.values():
        if np_metric:
            d1 = np.asarray(g1)
            for g2 in units.values():
                De += sum(np.sum(metric(d1, gj)) for gj in g2)
        else:
            for g2 in units.values():
                De += sum(metric(gi, gj) for gi in g1 for gj in g2)
    De /= float(n * (n - 1))

    return 1. - Do / De if (Do and De) else 1.


def parse_assessment_values():
    agreements = defaultdict(lambda: [])
    for i in range(1, NUMBER_OF_ASSESSORS + 1):
        values = read_csv(path.join(ASSESSMENT_FOLDER, ASSESSMENT_FILE_DUMMY + '{}.csv'.format(i)))[1:-1].reset_index(
            drop=True)
        for column in values.iloc[:, 1:]:
            agreements[column].append([float(i.replace(',', '.')) for i in values[column].values])
    return agreements


def print_agreement(agreements):
    for k, v in agreements.items():
        print('{}: {:0.2f}'.format(k, krippendorff_alpha(v)))


if __name__ == '__main__':
    print_agreement(parse_assessment_values())
