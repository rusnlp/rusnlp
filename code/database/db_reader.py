import numpy as np
from pandas import DataFrame
from nltk import word_tokenize


class ReaderDBase:
    def __init__(self, db):
        self.db = db
        self.counted_corpus_size = 7515811
        self.df_statistics = None
        self.update_statistics()

    def get_statistics(self):
        return self.bd.get_statistics()

    def select_articles_of_author(self, name):
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article JOIN author_alias ON author.id=author_alias.author_id AND " \
                "catalogue.author_id=author.id AND catalogue.article_id=article.id"
        condition = "author_alias.alias =" + self.check(name)
        result = self.bd.select(what, where, condition)
        return [res[0] for res in result]

    def select_articles_from_conference(self, conf_name, year=None):
        what = "DISTINCT article.title"
        where = "catalogue JOIN conference JOIN article ON catalogue.conference_id=conference.id " \
                "AND catalogue.article_id=article.id"
        condition = "conference.conference='" + conf_name + "'"
        if not year:
            condition += "AND conference.year=" + str(year)
        result = self.bd.select(what, where, condition)
        return [res[0] for res in result]

    def select_article_by_affiliation(self, affiliation):
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article"
        condition = "author.affiliation = '" + affiliation + "'"
        result = self.bd.select(what, where, condition)
        return result

    def select_author_by_affiliation(self, affiliation):
        what = "DISTINCT author.id, author.name"
        where = "author"
        condition = "author.affiliation = '" + affiliation + "'"
        return self.bd.select(what, where, condition)

    def select_title_by_id(self, article_id):
        what = '''DISTINCT title'''
        where = '''article '''
        condition = '''common_id=''' + str(article_id)
        result = self.bd.select(what, where, condition)
        return result

    def select_author_by_id(self, article_id):
        what = '''DISTINCT name'''
        where = '''author JOIN catalogue JOIN article'''
        condition = '''common_id=''' + str(article_id)
        result = self.bd.select(what, where, condition)
        return result

    def select_author_and_title_by_id(self, article_id):
        title = list(self.select_title_by_id(article_id)[0])
        authors = [j[0] for j in self.select_author_by_id(article_id)]
        return title + [authors]

    def select_all_from(self, where):
        return self.bd.select("*", where)

    def select_all_from_column(self, column, condition=None):
        where = "catalogue JOIN conference JOIN article JOIN author JOIN author_alias ON " \
                "author.id=author_alias.author_id AND catalogue.conference_id=conference.id " \
                "AND catalogue.article_id=article.id AND author.id=catalogue.author_id"
        return self.bd.select('DISTINCT ' + column, where, condition)

    def update_statistics(self):
        df = DataFrame(index=np.arange(0, 6), columns=["parameter", "count"])
        df.loc[0] = ("количество статей", self.bd.select_max('article'))
        df.loc[1] = ("количество авторов", self.bd.select_max('author_alias'))
        df.loc[2] = ("количество аффилиаций", self.bd.select_max('affiliation_alias'))
        df.loc[3] = ("количество русских статей", self.count_articles_with_lang('ru'))
        df.loc[4] = ("количество английских статей", self.count_articles_with_lang('en'))
        df.loc[5] = ("объем корпуса в токенах", self.count_corpus_size())
        self.df_statistics = df

    def count_articles_with_lang(self, language):
        what = '''COUNT(id) '''
        where = '''article'''
        condition = '''language="''' + language + '''"'''
        result = self.bd.select(what, where, condition)
        return result[0][0]

    def count_corpus_size(self):
        texts = self.select_all_from_column("article")
        return sum([len(word_tokenize(text[0])) for text in texts])