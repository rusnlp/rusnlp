import pandas as pd
import numpy as np
import pickle
from transliterate import translit
from Levenshtein import distance

class ParentHandler():
    """
    Parent class for classes - handlers used for semi-automated annotation.
    """
    def __init__(self, tsv_path):
        self.tsv = tsv_path
        self.df = pd.read_csv(self.tsv, sep='\t', names=['index', 'dict_name', 'var_name'])
        self.dict_names_mapping = {}
        pass


class AuthorsHandler(ParentHandler):
    """
    Class for semi-automated authors annotation.
    :param auth_tsv: str, path to authors.tsv file
    """
    def __init__(self, auth_tsv: str = 'current_authors.tsv'):
        super().__init__(auth_tsv)
        self.df['var_latine_name'] = \
            [translit(name, 'ru', reversed=True) for name in self.df['var_name']]

        # Сортируем словарные варианты написания, не учитывая инициалы вообще.
        for index, name in enumerate(self.df['dict_name']):
            name_list = name.split(' ')
            name_list = list(filter(None, name_list))
            surename = name_list[0].lower()
            # Если у автора указаны Фамилия И. О., отделяем фамилию и делаем ключом
            # словаря, в значении индекс.
            self.dict_names_mapping[surename] = [index]

    def search_lev(self, local_name, min=0, max=2, name_min_len=2):
        """
        Поиск совпадений по дистанции Левенштайна в окне между значеними min и max
        :param local_name: author's name from article
        :param min: min Lev distance
        :param max:
        :return: tuple with author dict name and index
        """
        auth_df = self.df
        dict_names_mapping = self.dict_names_mapping
        for dict_name in dict_names_mapping.keys():
            if min <= distance(dict_name, local_name) < max and len(local_name) > name_min_len:
                ind = dict_names_mapping.get(dict_name)[0]
                name = auth_df['dict_name'][ind]
                if len(dict_names_mapping.get(dict_name)) > 1:
                    name += dict_names_mapping.get(dict_name)[1]
                res = (auth_df['index'][ind], name)
                return res

    def handle_author(self, name):
        """
        :param name: author name from article
        :return: tuple with two author names and indexes
        """

        name = translit(name, 'ru', reversed=True).lower()
        name = name.replace("'", '')
        name = name.replace("ja", 'ya')

        if ' ' in name:
            name_list = name.split(' ')
        else:
            name_list = name.split('.')
        name_list = list(filter(None, name_list))

        # Фамилия может быть где угодно, так что итерируемся по всему списку,
        # ищем совпадения с имеющимися в словаре фамилиями.
        global_res = []

        # Cовпадения ищутся с помощью расстояния Левенштейна,
        # постепенно сдвигается в большую сторону окно поиска, пока не будет двух кандидатов
        my_min = 0
        my_max = 1
        while len(global_res) <= 1:
            for variant in name_list:
                local_res = self.search_lev(variant, max=my_max, min=my_min)
                if local_res:
                    global_res.append(local_res)
            if my_min > 30:
                global_res.append('nothing found')
                break
            my_min += 1
            my_max += 1
        return tuple(global_res[0])


class AffiliationsHandler(ParentHandler):

  def __init__(self, aff_tsv: str = 'current_affiliations.tsv', model_path: str = 'aff_classifier.pkl'):
    """
    :param aff_tsv: str, path to affiliations.tsv file
    :param model_path: str, path to model.pkl file
    """
    super().__init__(aff_tsv)
    for ind in self.df['index'].unique(): # получаем словарь {index: affiliation}
      self.dict_names_mapping[ind] = self.df[self.df['index'] == ind].dict_name.iloc[0]
    self.model = pickle.load(open(model_path, 'rb')) # загрузка модели

  def handle_affiliation(self, affiliation):
      """
      :param affiliation: affiliation from the article
      """
      prediction = self.model.predict([affiliation])
      return prediction[0], np.vectorize(self.dict_names_mapping.get)(prediction)[0]

# Use case:
# if __name__=='__main__':
#     handler = AuthorsHandler()
#     print(handler.handle_author('Митрофанова О. А.'))
#     print(handler.handle_author('Елизавета Былинина'))
#     print(handler.handle_author('Константинова Н.'))
#     handler = AffiliationsHandler()
#     print(handler.handle_affiliation('Ломоносова '))
#     print(handler.handle_affiliation('Московский лингвис'))
 #    print(handler.handle_affiliation('Moscow state'))
