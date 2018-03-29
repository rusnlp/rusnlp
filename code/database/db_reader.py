import numpy as np
from pandas import DataFrame
from nltk import word_tokenize


class ReaderDBase:
    def __init__(self, db):
        self._bd = db
        self.__counted_corpus_size = 7515811
        self.__db_statistics = None
        self.update_statistics()

    def get_statistics(self):
        return self.__db_statistics

    def select_articles_of_author(self, name):
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article JOIN author_alias ON author.id=author_alias.author_id" \
                " AND catalogue.author_id=author.id AND catalogue.article_id=article.id"
        condition = "author_alias.alias ={}".format(self._bd.check(name))
        result = self._bd.select(what, where, condition)
        return [res[0] for res in result]

    def select_articles_from_conference(self, conf_name, year=None):
        what = "DISTINCT article.title"
        where = "catalogue JOIN conference JOIN article ON catalogue.conference_id=conference.id" \
                " AND catalogue.article_id=article.id"
        condition = "conference.conference='{}'".format(conf_name)
        if year:
            condition += "AND conference.year={}".format(str(year))
        result = self._bd.select(what, where, condition)
        return [res[0] for res in result]
    
    def select_article_by_affiliation(self, affiliation):
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article ON article.id=article_id AND author.id=author_id"
        condition = "author.affiliation = '{}'".format(affiliation)
        result = self._bd.select(what, where, condition)
        return result
    
    def select_author_by_affiliation(self, affiliation):
        what = "DISTINCT author.id, author.name"
        where = "author"
        condition = "author.affiliation = '{}'".format(affiliation)
        result = self._bd.select(what, where, condition)
        return result
    
    def select_title_by_id(self, article_id):
        what = '''DISTINCT title'''
        where = '''article '''
        condition = '''common_id="{}"'''.format(str(article_id))
        result = self._bd.select(what, where, condition)
        return result
    
    def select_author_by_id(self, article_id):
        what = '''DISTINCT name'''
        where = '''author JOIN catalogue JOIN article ON author.id=author_id AND article_id=article.id'''
        condition = '''common_id="{}"'''.format(str(article_id))
        result = self._bd.select(what, where, condition)
        return result
        
    def select_author_and_title_by_id(self, article_id):
        title_result = self.select_title_by_id(article_id) 
        title = list(title_result[0]) if title_result != [] else "No id in db" 
        result_author = self.select_author_by_id(article_id)
        authors = str([j[0] for j in result_author]) if result_author != [] else ""
        return title+authors
    
    def select_all_from(self, where):
        return self._bd.select("*", where)	

    def select_all_from_column(self, column, condition=None):
        where = "catalogue INNER JOIN conference INNER JOIN article INNER JOIN author INNER JOIN author_alias ON" \
                " author.id=author_alias.author_id AND catalogue.conference_id=conference.id AND " \
                "catalogue.article_id=article.id AND author.id=catalogue.author_id"
        return self._bd.select('DISTINCT '+column, where, condition)

    def update_statistics(self):
        df = DataFrame(index=np.arange(0, 6), columns=["parameter", "count"])
        df.loc[0]=("количество статей", self._bd.select_max('article'))
        df.loc[1]=("количество авторов", self._bd.select_max('author_alias'))
        df.loc[2]=("количество аффилиаций", self._bd.select_max('affiliation_alias'))
        df.loc[3]=("количество русских статей", self.count_articles_with_lang('ru'))
        df.loc[4]=("количество английских статей", self.count_articles_with_lang('en'))
        df.loc[5]=("объем корпуса в токенах",  7515811)
        self.__db_statistics = df

    def count_articles_with_lang(self, language):
        what = '''COUNT(id) '''
        where = '''article'''
        condition = '''language="''' + language + '''"'''
        result = self._bd.select(what, where, condition)
        return result[0][0]
    
    def count_corpus_size(self):
        texts = self.select_all_from_column("article")
        all_text_len = sum([len(word_tokenize(text[0])) for text in texts])
        return all_text_len