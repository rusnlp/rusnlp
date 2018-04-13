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
        """
        Get database statistics in a DataFrame format.

        :return: Pandas DataFame
            Get a DataFrame with six specified rows.
        """
        return self.__db_statistics

    def select_articles_of_author(self, name):
        """
        Get articles by author's name.

        :param name: string
            Full name of the author (will be aliased, if possible)
        :return list of strings
            Names of articles of the author
        """
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article JOIN author_alias ON author.id=author_alias.author_id" \
                " AND catalogue.author_id=author.id AND catalogue.article_id=article.id"
        condition = "author_alias.alias ={}".format(self._bd.check(name))
        return [res[0] for res in self._bd.select(what, where, condition)]

    def select_articles_from_conference(self, conf_name, year=None):
        """
        Get articles articles from the all year proceedings of the selected conference (or selected conference
            of a certain year)

        :param conf_name: string
            Name of the conference (not aliased yet, should be exactly the same as in the database)
        :param year: int
            Additionally specifies the year of the conference. Should we really pass string and cast int on it?
        :return: list of strings
            Names of articles from the all year proceedings of the selected conference (or selected conference
            of a certain year)
        """
        what = "DISTINCT article.title"
        where = "catalogue JOIN conference JOIN article ON catalogue.conference_id=conference.id" \
                " AND catalogue.article_id=article.id"
        condition = "conference.conference='{}'".format(conf_name)
        if year:
            condition += "AND conference.year={}".format(str(year))
        return [res[0] for res in self._bd.select(what, where, condition)]
    
    def select_article_by_affiliation(self, affiliation):
        """
        Get articles by the affiliation.

        :param affiliation: string
            Affiliation of a research institution
        :return: list of strings
            Names of articles where the mentioned affiliation figures
        """
        what = "DISTINCT article.title"
        where = "catalogue JOIN author JOIN article ON article.id=article_id AND author.id=author_id"
        condition = "author.affiliation = '{}'".format(affiliation)
        return [res[0] for res in self._bd.select(what, where, condition)]
    
    def select_author_by_affiliation(self, affiliation):
        """
        Get authors by the affiliation.

        :param affiliation: string
            Affiliation of a research institution
        :return: list of string
            Name of authors which are affiliated with the mentioned in
        """
        what = "DISTINCT author.id, author.name"
        where = "author"
        condition = "author.affiliation = '{}'".format(affiliation)
        return [res[0] for res in self._bd.select(what, where, condition)]
    
    def select_title_by_id(self, article_id):
        """
        Get paper's title by its unique identifier.

        :param article_id: string
            Unique identifier of the paper (in format %s_%s_%s:(conference, year, lowercased underlined paper's title))
        :return: string
            Return a title of the paper associated with the specified identifier
        """
        what = '''DISTINCT title'''
        where = '''article '''
        condition = '''common_id="{}"'''.format(str(article_id))
        return self._bd.select(what, where, condition)[0][0]
    
    def select_author_by_id(self, article_id):
        """
        Get paper's authors by its unique identifier.

        :param article_id:
            Unique identifier of the paper (in format %s_%s_%s:(conference, year, lowercased underlined paper's title))
        :return: string
            Return a list of authors of the paper associated with the specified identifier
        """
        what = '''DISTINCT name'''
        where = '''author JOIN catalogue JOIN article ON author.id=author_id AND article_id=article.id'''
        condition = '''common_id="{}"'''.format(str(article_id))
        return [res[0] for res in self._bd.select(what, where, condition)]
        
    def select_author_and_title_by_id(self, article_id):
        """
        Get both paper's author and title by its unique identifier.

        :param article_id:
            Unique identifier of the paper (in format %s_%s_%s:(conference, year, lowercased underlined paper's title))
        :return: string
            Concatenated paper's name and authors.
        """
        title_result = self.select_title_by_id(article_id)
        if title_result:
            title = ' '.join(list(title_result[0]))
        else:
            title = "No id in db"
        result_author = self.select_author_by_id(article_id)
        if result_author:
            authors = ', '.join([j[0] for j in result_author])
        else:
            authors = ""
        return 'Title: "{}" Authors: {}'.format(title, authors)
    
    def select_all_from(self, where):
        """
        Get all data from the database.

        :param where: string
            Condition for selection
        :return: list of strings
            All rows of the database.
        """
        return self._bd.select("*", where)	

    def select_all_from_column(self, column, condition=None):
        """
        Get all data from the specified column (and, possibly, using the specified condition).

        :param column: string
            Specified column
        :param condition: string
            Condition for selection
        :return: list of strings
            All rows of a specified column.
        """
        where = "catalogue INNER JOIN conference INNER JOIN article INNER JOIN author INNER JOIN author_alias ON" \
                " author.id=author_alias.author_id AND catalogue.conference_id=conference.id AND " \
                "catalogue.article_id=article.id AND author.id=catalogue.author_id"
        return self._bd.select('DISTINCT '+ column, where, condition)

    def update_statistics(self):
        """
        Update corpus statistics in a DataFrame format.

        :return: None
        """
        df = DataFrame(index=np.arange(0, 6), columns=['parameter', 'count'])
        df.loc[0]=('Overall amount of papers', self._bd.select_max('article'))
        df.loc[1]=('Amount of unique authors', self._bd.select_max('author_alias'))
        df.loc[2]=('Amount of unique affiliations', self._bd.select_max('affiliation_alias'))
        df.loc[3]=('Amount of Russian papers', self.count_articles_with_lang('ru'))
        df.loc[4]=('Amount of English papers', self.count_articles_with_lang('en'))
        df.loc[5]=('Corpus size in tokens',  7515811)
        self.__db_statistics = df

    def count_articles_with_lang(self, language):
        """
        Get amount of articles on the specified language.

        :param language: string
            Language of an article (two options: 'ru' and 'en')
        :return: int
            Amount of the articles with the specified language
        """
        what = '''COUNT(id) '''
        where = '''article'''
        condition = '''language="''' + language + '''"'''
        result = self._bd.select(what, where, condition)
        return result[0][0]
    
    def count_corpus_size(self):
        """
        Get amount of tokens (all words) of concataned texts of all articles.

        :return: int
            Amount of tokens in the corpus
        """
        texts = self.select_all_from_column("article")
        all_text_len = sum([len(word_tokenize(text[0])) for text in texts])
        return all_text_len