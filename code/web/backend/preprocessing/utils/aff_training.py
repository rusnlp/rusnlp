import pandas as pd
import numpy as np
import pickle
import argparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import linear_model
from sklearn.pipeline import Pipeline


def parse_args():
    parser = argparse.ArgumentParser(
        description='Обучение классификатора аффилиаций')
    parser.add_argument('--data_path', type=str, required=True,
                        help='Путь к tsv-файлу с аффилиациями')
    parser.add_argument('--save_path', type=str, required=True,
                        help='Путь для сохранения обученного классификатора')
    return parser.parse_args()


def train_classifier(data_path, save_path):
    aff = pd.read_csv(data_path, sep='\t', index_col=0, names=['aff', 'variation'])
    vect = CountVectorizer(analyzer='char', ngram_range=(1,4))
    reg_model = linear_model.LogisticRegression(max_iter=5000)
    pipe = Pipeline([('vect', vect),  ('logreg', reg_model)])
    pipe.fit(aff.variation, aff.index)
    pickle.dump(pipe, open(save_path, 'wb'))


if __name__ == '__main__':
    args = parse_args()
    train_classifier(args.data_path, args.save_path)
    # example of usage:
    # python aff_training.py --data_path=current_affiliations.tsv --save_path=aff_classifier.pkl
    'C:/Users/79850/Desktop/'