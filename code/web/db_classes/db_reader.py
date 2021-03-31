class ReaderDBase:
    def __init__(self, db):
        self._bd = db

    # ==========================================================================================
    # AUTHORS
    # ==========================================================================================

    def select_author_by_id(self, article_id):
        """
        Get paper's authors by its unique identifier
        :param article_id:
           Unique identifier of the paper (%s_%s_%s:(conference, year, paper's title hash))
        :returns string
        Return a list of authors of the paper associated with the specified identifier
        """
        what = '''DISTINCT author.name'''
        where = '''author JOIN author_catalogue ON author.author_id=author_catalogue.author_id'''
        condition = '''author_catalogue.common_id="{}"'''.format(article_id)
        return [i[0] for i in self._bd.select(what, where, condition)]

    def select_all_authors(self):
        what = '''*'''
        where = '''author '''
        return self._bd.select(what, where)

    def select_alias_name_by_author_cluster(self, cluster):  # TODO: rename
        where = "author"
        condition = '''author_id={}'''.format(cluster)
        return self._bd.select("name", where, condition)[0][0]

    def select_cluster_author_by_common_id(self, common_id):
        where = "author_catalogue"
        condition = '''common_id="{}"'''.format(common_id)
        return set([i[0] for i in self._bd.select("author_id", where, condition)])

    # ==========================================================================================
    # AFFILIATIONS
    # ==========================================================================================

    def select_affiliation_by_cluster(self, cluster):  # TODO: rename
        where = "affiliation"
        condition = '''affiliation_id={}'''.format(cluster)
        result = self._bd.select_one("name", where, condition)
        return result[0] if result else "Unknown affiliation"

    def select_aff_cluster_by_affiliation(self, affiliation):
        where = "affiliation"
        condition = '''name="{}"'''.format(affiliation)
        result = self._bd.select_one("affiliation_id", where, condition)
        return result[0] if result else None

    def select_aff_clusters_by_id(self, common_id):
        where = "author_catalogue"
        condition = '''common_id="{}"'''.format(common_id)
        return set([i[0] for i in self._bd.select("affiliation_id", where, condition)])

    def select_all_affiliations(self):
        what = '''*'''
        where = '''affiliation '''
        return self._bd.select(what, where)

    # ==========================================================================================
    # TITLE
    # ==========================================================================================

    def select_title_by_id(self, article_id):
        """
        Get paper's title by its unique identifier.
        :param article_id: string
            Unique identifier of the paper (%s_%s_%s:(conference, year, paper's title hash))
        :returns string
            Returns a title of the paper associated with the specified identifier
        """
        what = '''DISTINCT title'''
        where = '''catalogue '''
        condition = '''common_id="{}"'''.format(article_id)
        return self._bd.select_one(what, where, condition)[0]

    # ==========================================================================================
    # CONFERENCE
    # ==========================================================================================

    def select_year_by_id(self, article_id):
        return self.select_by_id("year", article_id)

    def select_conference_by_id(self, article_id):
        return self.select_by_id("name", article_id)

    def select_by_id(self, what, article_id):
        what = '''DISTINCT conference.{}'''.format(what)
        where = '''catalogue INNER JOIN conference ON conference_id=conference.id'''
        condition = '''common_id="{}"'''.format(article_id)
        return self._bd.select_one(what, where, condition)[0]

    # ==========================================================================================
    # URL
    # ==========================================================================================

    def select_url_by_id(self, article_id):
        what = '''url'''
        where = '''catalogue'''
        condition = '''common_id="{}"'''.format(article_id)
        return self._bd.select_one(what, where, condition)[0]

    # ==========================================================================================
    # ABSTRACT
    # ==========================================================================================

    def select_abstract_by_id(self, article_id):
        what = '''DISTINCT abstract'''
        where = '''catalogue'''
        condition = '''common_id = "{}"'''.format(article_id)
        return self._bd.select_one(what, where, condition)[0]
    # ==========================================================================================
    # LANGUAGE
    # ==========================================================================================

    def select_language_by_id(self, article_id):
        what = '''DISTINCT language'''
        where = '''catalogue'''
        condition = '''common_id = "{}"'''.format(article_id)
        return [i[0] for i in self._bd.select(what, where, condition)]

    # ==========================================================================================
    # COMMON_ID
    # ==========================================================================================

    def select_articles_from_conference(self, conf_name, year=None):
        """
        Get articles articles from the all year proceedings of the selected conference
        (or selected conference of a certain year)

        :param conf_name: string
            Name of the conference (not aliased yet, should be exactly the same as in the database)
        :param year: int
            Additionally specifies the year of the conference.
            Should we really pass string and cast int on it?
        :return: list of strings
            Names of articles from the all year proceedings of the selected conference
            (or selected conference of a certain year)
        """
        conf_name = conf_name.upper() if conf_name.upper() == "AIST" or \
                                         conf_name.upper() == "AINL" else "Dialogue"
        what = "DISTINCT catalogue.common_id, catalogue.language"
        where = "catalogue JOIN conference ON catalogue.conference_id=conference.id"
        condition = "conference.name='{}'".format(conf_name)
        if year:
            condition += " AND conference.year={}".format(str(year))
        return [res for res in self._bd.select(what, where, condition)]

    def select_articles_from_years(self, begin, end):
        what = "DISTINCT catalogue.common_id, catalogue.language"
        where = "catalogue JOIN conference ON conference_id=conference.id"
        condition = "year BETWEEN {} and {}".format(begin, end)
        return [res for res in self._bd.select(what, where, condition)]

    def select_articles_of_author(self, name):
        """
        Get articles by author's name.

        :param name: string
            Full name of the author (will be aliased, if possible)
        :return list of strings
            Names of articles of the author
        """
        what = "DISTINCT catalogue.common_id, catalogue.language"
        where = "author_catalogue JOIN author JOIN catalogue ON author_catalogue.author_id=author.author_id and catalogue.common_id=author_catalogue.common_id"
        condition = '''author.name="{}"'''.format(name)
        return [res for res in self._bd.select(what, where, condition)]

    def select_articles_by_cluster(self, cluster_id):
        what = "DISTINCT catalogue.common_id, catalogue.language"
        where = "author_catalogue JOIN catalogue ON catalogue.common_id=author_catalogue.common_id"
        condition = '''author_catalogue.affiliation_id="{}"'''.format(cluster_id)
        return [res for res in self._bd.select(what, where, condition)]

    # ==========================================================================================
    # STATISTICS
    # ==========================================================================================

    def get_statistics(self):
        return {
            'Overall amount of papers': self._bd.select_count('catalogue'),
            'Amount of unique authors': len(self.select_all_authors()),
            'Amount of unique affiliations': len(self.select_all_affiliations()),
            'Amount of Russian papers': self.count_articles_with_lang('ru'),
            'Amount of English papers': self.count_articles_with_lang('en')
        }

    def get_dict_of_conference_description(self, confname):
        self._bd.cursor.execute(
            'SELECT description_ru, description_en, url FROM conference '
            'WHERE conference.name="{}"'.format(confname))
        result = self._bd.cursor.fetchall()[0]
        return {"ru": result[0], "en": result[1], "url": result[2]}

    def count_articles_with_lang(self, language):
        """
        Get amount of articles on the specified language.

        :param language: string
            Language of an article (two options: 'ru' and 'en')
        :return: int
            Amount of the articles with the specified language
        """
        what = '''COUNT(id) '''
        where = '''catalogue'''
        condition = '''language="{}"'''.format(language)
        result = self._bd.select_one(what, where, condition)[0]
        return result
