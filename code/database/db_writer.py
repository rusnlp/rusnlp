import sqlite3
from pandas import DataFrame
from nltk.corpus import stopwords
import shutil


class WriterDBase:
    def __init__(self, db):
        self.db = db
        self.stop_words_ru = set(stopwords.words('russian'))
        self.stop_words_en = set(stopwords.words('english'))
        self.list_of_chars = ('‘', '+', ')', ':', '2', '(', '/', '—', '…', '-', '„', '.', '1', ',', '<', '“', '«', '6', '–', '[')

    def insert_into_conference(self, values):
        """
        Insert new conference to the list of conferences.

        :param values: list of strings
            New papers
        :return: None
        """
        max_id = self.db.select_max('conference')
        for i in range(len(values)):
            row = [max_id + 1] + list(values[i])
            self.db.insert('conference', row, columns=['id', 'conference', 'year'])

    def insert_into_author(self, id_, name, affiliation, email):
        """
        Insert new author to the list of authors.

        :param id_: string
            Unique identifier of the paper
        :param name: string
            Name of the author
        :param affiliation: string
            Affiliation of the author
        :param email:
            Email of the author
        :return: None
        """
        self.db.insert('author', (id_, name, email, affiliation), ["id", "name", "email", "affiliation"])

    def insert_into_article(self, id_, title, text, abstract, bibliography, keywords,  url, filepath, common_id):
        """
        Insert new paper's metadata to the specified paper.

        :param id_: string
            Unique identifier of the paper
        :param title: string
            Title of the paper
        :param text:
            Text of the paper
        :param abstract:
            Abstract of tha paper
        :param bibliography:
            Bibliography of the paper
        :param keywords:
            Keywords of the paper
        :param url:
            URL of the paper
        :param filepath:
            Path to the paper in RusNLP folder
        :param common_id:
            I don't know what this means
        :return: None
        """
        self.db.insert('article', (id_, title, keywords, abstract, bibliography, text, url, common_id, filepath), 
                     ['id', 'title', 'keywords', 'abstract', 'bibliography', 'text', 'url', 'common_id', 'filepath'])
    
    def insert_into_author_alias(self, alias, variant):
        """
        Associate author with a new alias for her name.

        :param alias: string
            Unique author identified
        :param variant: string
            New variant of author's name
        :return: None
        """
        max_id = self.db.select_max('author_alias')
        max_id += 1
        variant_alias_id = self.select_id_from_author_alias(variant)
        if not variant_alias_id:
            self.db.insert('author_alias', (max_id, alias, variant), ["id", "alias", "author_id"])
    
    def select_id_from_author_alias(self, variant):
        """
        Get identifies of papers associated with an alias

        :param variant: string
            Author's name
        :return: list of strings
            Titles of the papers
        """
        where = ' author_id = {}'.format(self.db.check(variant))
        rows = self.db.select(what='id', where='author_alias', condition=where)
        if rows:
            return rows[0][0]

    def insert_into_affiliation_alias(self, cluster, alias, author):
        """
        Associate affiliation with a new alias for its name.

        :param cluster: string
            Unique affiliation identified
        :param alias: string
            New variant of author's name
        :param author: string
            I don't know why its here
        :return: None
        """
        max_id = self.db.select_max('affiliation_alias')
        max_id += 1
        self.db.insert('affiliation_alias', (max_id, cluster, alias, author), ["id", "cluster",  "alias", "author_id"])

    def insert_new_article(self, author, article, conference_name, url, file_path, common_id, year):
        """

        :param author:
        :param article:
        :param conference_name:
        :param url:
        :param file_path:
        :param common_id:
        :param year:
        :return:
        """
        article_id = self.get_article_id(article, url, file_path, common_id)
        author_id = self.get_author_id(author)
        conference_id = self.get_conference_id(conference_name, year)
        for auth_id in author_id:
            self.insert_to_catalogue(auth_id, article_id, conference_id)

    def get_author_id(self, author):
        """

        :param author:
        :return:
        """
        list_of_authors_id = []
        for auth in author:
            author_id = self.select_id_from_author(auth['name'])
            if not author_id:
                author_id = self.db.select_max('author') + 1
                if type(auth['email']) != str:
                    # TODO: Replace prints with logging
                    # print(str(auth['email']) + " " + str(type(auth['email'])))
                    raise Exception("2 emails")
                self.insert_into_author(id_=author_id, name=auth['name'],
                                        email=auth['email'],
                                        affiliation=auth['affiliation'])
            list_of_authors_id.append(author_id)
        return list_of_authors_id

    def select_id_from_author(self, name):
        """

        :param name:
        :return:
        """
        where = ' name = {}'.format(self.db.check(name))
        rows = self.db.select(what='id', where='author', condition=where)
        return rows[0][0] if rows != [] else None

    def get_article_id(self, article, url, file_path, common_id):
        """

        :param article:
        :param url:
        :param file_path:
        :param common_id:
        :return:
        """
        new_title = self.reformat_title(article['title'])
        article_id = self.select_id_from_article(common_id)
        if not article_id:
            article_id = self.db.select_max('article') + 1
            if 'bibliography' not in article.keys():
                # TODO: Replace prints with logging
                # print("no_bibl")
                article['bibliography']="-"
            else:
                pass
                # TODO: Replace prints with logging
                # print('bibliography IS here = ', article['bibliography'])
            if 'keywords' not in article.keys():
                article['keywords']="-"
            article_text = article['text']
            self.insert_into_article(id_=article_id, title=new_title, text=article_text,
                                     abstract=article['abstract'], bibliography=article['bibliography'],
                                     keywords=article['keywords'], url=url, filepath=file_path, common_id=common_id)
        return article_id

    def reformat_title(self, title):
        """

        :param title:
        :return:
        """
        new_title = []
        for word in title.lower().split(' '):
            if word not in self.stop_words_ru and word not in self.stop_words_en:
                new_word = str.strip(word).capitalize()
                if new_word == new_word.lower():
                    for i in range(len(new_word)):
                        if new_word[i].isalpha and new_word[i] not in self.list_of_chars:
                            new_word = new_word[:i]+new_word[i:].capitalize()
                            break

            else:
                new_word = word
            new_title.append(new_word)
        return ' '.join([new_title[0].capitalize()] + new_title[1:])

    def select_id_from_article(self, common_id):
        """

        :param common_id:
        :return:
        """
        where = """common_id = {}""".format(self.db.check(common_id))
        rows = self.db.select(what='id', where='article', condition=where)
        # TODO: Replace prints with logging
        # print(rows)
        return rows[0][0] if rows != [] else None

    def get_conference_id(self, conference_name, year):
        """

        :param conference_name:
        :param year:
        :return:
        """
        conference_id = self.select_id_from_conference(conference_name, year)
        if not conference_id:
            # TODO: Replace prints with logging
            # print(conference_name +  " " + str(year))
            raise ValueError('wrong combination of year and conference name')
        return conference_id

    def select_id_from_conference(self, conference_name, year):
        """

        :param conference_name:
        :param year:
        :return:
        """
        where = ''' year = ''' + str(year) + ''' AND conference = "''' + conference_name + '";'
        rows = self.db.select(what='id', where='conference', condition=where)
        return rows[0][0] if rows != [] else None
    
    def insert_to_catalogue(self, auth_id, article_id, conference_id):
        """

        :param auth_id:
        :param article_id:
        :param conference_id:
        :return:
        """
        catalog_id = self.select_id_from_catalogue(auth_id, article_id, conference_id)
        if not catalog_id:
            catalog_id = self.db.select_max('catalogue') + 1
            self.db.insert('catalogue', (int(catalog_id), int(auth_id), int(article_id),
                                         int(conference_id)),
                           columns=['id', 'author_id', 'article_id', 'conference_id'])
    
    def select_id_from_catalogue(self, auth_id, article_id, conference_id):
        """

        :param auth_id:
        :param article_id:
        :param conference_id:
        :return:
        """
        where = '''author_id = {} AND article_id = {} AND conference_id = {};'''.format(str(auth_id), str(article_id), str(conference_id))
        rows = self.db.select(what='id', where='catalogue', condition=where)
        if rows:
            return rows[0][0]

    def load(self, article):
        """

        :param article:
        :return:
        """
        counter = 0
        try:
            file_path = article['filepath']
        except KeyError:
            file_path=None
        self.insert_new_article(author=article['author'],
                                article=article['text'],
                                conference_name=article['conference'],
                                url=article['url'],
                                file_path= file_path,
                                common_id = article['id'],
                                year=int(article['year']))
        counter += 1
        # print(counter)

    def update_language(self, file_path, delimeter=','):
        """

        :param file_path:
        :param delimeter:
        :return:
        """
        languages = DataFrame.from_csv(file_path, sep=delimeter)
        for i in range(len(languages.Lang.values)):
            self.db.update("article", 'language', languages.Lang.values[i], 'common_id', languages.ID.values[i])

    def load_to_author_alias(self, file_path):
        """

        :param file_path:
        :return:
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            string = f.read().split('\n')
        aliases = {}
        for name in string:
            alias, variants = [i.strip() for i in name.split(':')]
            new_variants = [variant.strip() for variant in variants[1:-1].split(',')]
            for variant in new_variants:
                aliases[variant] = alias
        self.db.cursor.execute("""SELECT DISTINCT id, name FROM author""")
        old_names = dict([(n[1], n[0]) for n in self.db.cursor.fetchall()])
        exceptions = []
        for name, index in old_names.items():
            try:
                self.db.insert_into_author_alias(aliases[name.replace(",", "").strip()],index)
            except:
                exceptions.append((name, index))
        return exceptions
    
    def load_to_affiliation_alias(self, file_path):
        """

        :param file_path:
        :return:
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            affiliations = f.readlines()
        results = {}
        for aff_cluster in range(1, len(affiliations)+1):
            for aff in affiliations[aff_cluster-1].split("\t"):
                results[aff] = aff_cluster
        self.db.cursor.execute("""SELECT id, affiliation FROM author""")
        results_aff = self.db.cursor.fetchall()
        for affiliation in results_aff:
            try:
                self.db.insert_into_affiliation_alias(results[affiliation[1]], affiliation[1], affiliation[0])
            except sqlite3.IntegrityError as e:
                pass
                # TODO: Replace prints with logging
                # print("foreign key error:\n", e,  "for \n", results[affiliation[1]], affiliation[1], affiliation[0])
        
    def delete_column(self, table, column):
        """
        Delete column from table by copying table
        
        :param table: string
            Table from wheredelete column
        :param column: string
            Column to delete
        :return: None
        """
        split_name, dim = self.db.db_path.split(".db")
        middle_name = table+"2"
        shutil.copyfile(self.db.db_path, split_name+"_old.db")
        article_table_info = self.db.tables[table]
        del article_table_info[0][column]
        self.db.create_table(middle_name, article_table_info)
        self.db.cursor.execute("INSERT INTO {} SELECT {} FROM {}"
                               .format(middle_name, 
                                       ", ".join(list(article_table_info[0].keys())), 
                                       table))
        self.db.cursor.execute("DROP TABLE {}".format(table))
        self.db.conn.isolation_level = None
        self.db.cursor.execute('VACUUM')
        self.db.conn.isolation_level = ''
        self.db.conn.commit()
        self.db.cursor.execute("ALTER TABLE {} RENAME TO {}".format(middle_name,
                               table))
        self.db.conn.commit()