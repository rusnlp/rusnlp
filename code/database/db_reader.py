import numpy as np
import re
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
        what = "DISTINCT article.common_id"
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
        conf_name = conf_name.upper() if conf_name.upper()=="AIST" or conf_name.upper()=="AINL" else "Dialogue"
        what = "DISTINCT article.common_id"
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
        what = "DISTINCT article.common_id"
        where = "catalogue JOIN author JOIN article ON article.id=article_id AND author.id=author_id"
        condition = "author.affiliation = '{}'".format(affiliation)
        return [res[0] for res in self._bd.select(what, where, condition)]
    
    def select_articles_from_years(self, begin, end):
        what = "DISTINCT article.common_id"
        where = "catalogue JOIN conference JOIN article ON article.id=article_id AND conference.id=conference_id"
        condition = "year BETWEEN {} and {}".format(begin, end)
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
        what = '''DISTINCT alias'''
        where = '''author JOIN catalogue JOIN article JOIN author_alias ON author.id=catalogue.author_id AND article_id=article.id AND author.id=author_alias.author_id'''
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

    def select_url_by_id(self, article_id):
        what = '''DISTINCT url'''
        where = '''article'''
        condition = '''common_id="{}"'''.format(str(article_id))
        return self._bd.select(what, where, condition)[0][0]

    def select_year_by_id(self, article_id):
        return self.select_by_id("year", article_id)

    def select_conference_by_id(self, article_id):
        return self.select_by_id("conference", article_id)

    def select_by_id(self, what, article_id):
        what = '''DISTINCT conference.{}'''.format(what)
        where = '''article INNER JOIN catalogue INNER JOIN conference ON article.id=article_id AND conference_id=conference.id'''
        condition = '''common_id="{}"'''.format(str(article_id))
        return self._bd.select(what, where, condition)[0][0]

    def select_abstract_by_id(self, article_id):
        what = '''abstract'''
        where = '''article'''
        condition = '''common_id = "{}"'''.format(article_id)
        return self._bd.select(what, where, condition)[0][0]

    def select_affiliation_by_id(self, article_id):
        where = "catalogue JOIN author JOIN article ON article.id=catalogue.article_id AND author.id=catalogue.author_id"
        affiliations = list(set([i[0] for i in self._bd.select("author.affiliation", where, '''common_id="{}"'''.format(article_id))]))
        aff_list = []
        for affiliation in affiliations:
            cluster = self.select_aff_cluster_by_affiliation(affiliation)
            if cluster is not None:
                aff_list.append(self.select_affiliation_by_cluster(cluster))
            else:
                affiliation = re.sub("^, ", '', affiliation.replace("\n", "")).strip()
                if affiliation not in aff_list:
                    aff_list.append("*{}".format(affiliation))
        return "; ".join(list(set(aff_list)))

    def select_aff_cluster_by_affiliation(self, affiliation):
        where = """author JOIN affiliation_alias ON affiliation_alias.author_id=author.id """
        condition = '''affiliation="{}"'''.format(affiliation)
        result = list(set(self._bd.select("cluster", where, condition)))
        return int(result[0][0]) if len(result) == 1 else None

    def select_aff_clusters_by_id(self, common_id):
        where = "catalogue JOIN author JOIN article JOIN affiliation_alias ON article.id=catalogue.article_id AND author.id=catalogue.author_id AND affiliation_alias.author_id=author.id"
        cluster = set([i[0] for i in self._bd.select("cluster", where, '''common_id="{}"'''.format(common_id))])
        return cluster
    
    def select_articles_by_cluster(self, cluster_id):
        where = "catalogue JOIN author JOIN article JOIN affiliation_alias ON article.id=catalogue.article_id AND author.id=catalogue.author_id AND affiliation_alias.author_id=author.id"
        condition = "cluster={}".format(cluster_id)
        return set([i[0] for i in self._bd.select("common_id", where, condition)])
    
    def select_affiliation_by_language(self, lang):
        where = "catalogue JOIN author JOIN article ON article.id=catalogue.article_id AND author.id=catalogue.author_id"
        condition = '''language="{}"'''.format(lang)
        return set([re.sub("^, ", '', i[0].replace("\n", "")).strip() for i in self._bd.select("affiliation", where, condition)])
        
    def select_author_cluster_by_alias_name(self, alias):
        where = "author_alias"
        condition = '''alias="{}"'''.format(alias)
        return self._bd.select("cluster_author", where, condition)[0][0]
    
    def select_alias_name_by_author_cluster(self, cluster):
        where = "author_alias"
        condition = '''cluster_author={}'''.format(cluster)
        return self._bd.select("alias", where, condition)[0][0]
    
    def select_cluster_author_by_common_id(self, common_id):
        where = "catalogue JOIN author JOIN article JOIN author_alias ON article.id=catalogue.article_id AND author.id=catalogue.author_id AND author_alias.author_id=author.id"
        condition = '''common_id="{}"'''.format(common_id)
        return set([i[0] for i in self._bd.select("cluster_author", where, condition)])

    def select_all_from(self, what, where):
        """
        Get all data from the database.

        :param where: string
            Condition for selection
        :return: list of strings
            All rows of the database.
        """
        return self._bd.select(what, where)	

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
        where = '''catalogue JOIN conference  JOIN article  JOIN author  JOIN author_alias  JOIN affiliation_alias ON''' \
                ''' author.id=author_alias.author_id AND catalogue.conference_id=conference.id AND ''' \
                '''catalogue.article_id=article.id AND author.id=catalogue.author_id AND affiliation_alias.author_id=author.id'''
        return [i[0] for i in self._bd.select('DISTINCT '+ column, where, condition)]

    def select_all_common_ids(self):
        return [i[0] for i in self.select_all_from("DISTINCT common_id", "article")]


    def select_all_authors(self):
        return [i[0] for i in self.select_all_from("DISTINCT alias", "author_alias")]

    def select_all_affiliations(self):
        clusters = [i[0] for i in self.select_all_from("DISTINCT cluster", "affiliation_alias")]
        cluster_names = []
        for cluster in clusters:
            cluster_names.append(self.select_affiliation_by_cluster(cluster))
        return cluster_names

    def select_affiliation_by_cluster(self, cluster_id):
        all_names = [i[0] for i in self._bd.select("alias", "affiliation_alias", "cluster={}".format(cluster_id))]
        return sorted(all_names, key=lambda x:len(x))[0]

    def update_statistics(self):
        """
        Update corpus statistics in a DataFrame format.

        :return: None
        """
        df = DataFrame(index=np.arange(0, 7), columns=['parameter', 'count'])
        df.loc[0]=('Overall amount of papers', self.select_count('article'))
        df.loc[1]=('Amount of unique authors', len(self.select_all_authors()))
        df.loc[2]=('Amount of unique affiliations', len(self.select_all_affiliations()))
        df.loc[3]=('Amount of Russian papers', self.count_articles_with_lang('ru'))
        df.loc[4]=('Amount of English papers', self.count_articles_with_lang('en'))
        #df.loc[5]=('Amount of Russian authors',len(self.select_all_from_column("author_alias.alias", '''language="ru"''')))
        df.loc[5]=('Amount of English authors',len(self.select_all_from_column("author_alias.alias", '''language="en"''')))
        #df.loc[7]=('Amount of Russian affiliations',len(self.select_all_from_column("affiliation_alias.cluster", '''language="ru"''')))
        df.loc[6]=('Amount of Eglish affiliations',len(self.select_all_from_column("affiliation_alias.cluster", '''language="en"''')))
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

    def select_count(self, where):
        """
        Get amount of articles on the specified language.

        :param language: string
            Language of an article (two options: 'ru' and 'en')
        :return: int
            Amount of the articles with the specified language
        """
        what = '''COUNT(DISTINCT id) '''
        where = '''{}'''.format(where)
        result = self._bd.select(what, where)
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

    def get_dict_of_conference_description(self, confname):
        self._bd.cursor.execute('SELECT description_ru, description_en, url FROM conference WHERE conference.conference="{}"'.format(confname))
        result = self._bd.cursor.fetchall()[0]
        return {"ru": result[0], "en": result[1], "url": result[2]}
