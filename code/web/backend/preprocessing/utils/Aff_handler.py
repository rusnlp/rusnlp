import pandas as pd
import numpy as np
import pickle


class AffiliationsHandler:

  def __init__(self, aff_tsv: str = 'current_affiliations.tsv', model_path: str = 'aff_classifier.pkl'):
    """
    Class for semi-automated affiliations annotation.
    :param aff_tsv: str, path to affiliations.tsv file
    :param model_path: str, path to model.pkl file
    """
    self.aff_tsv = aff_tsv
    self.aff_df = pd.read_csv(aff_tsv, sep='\t', index_col=0, names=['aff', 'variation'])
    self.ind2aff = dict()
    for ind in self.aff_df.index.unique(): # получаем словарь {index: affiliation}
      self.ind2aff[ind] = self.aff_df[self.aff_df.index==ind].aff.iloc[0]
    self.model = pickle.load(open(model_path, 'rb')) # загрузка модели

  def handle_affiliation(self, affiliation):
      """
      :param affiliation: affiliation from the article
      """
      prediction = self.model.predict([affiliation])
      return np.vectorize(self.ind2aff.get)(prediction)[0]

#if __name__=='__main__':
     #handler = AffiliationsHandler()
     #print(handler.handle_affiliation('Ломоносова '))
     #(handler.handle_affiliation('Московский лингвис'))
     #print(handler.handle_affiliation('Moscow state'))