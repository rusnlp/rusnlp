import sqlite3
from pandas import DataFrame


class WriterDBase:
    def __init__(self, db):
        self.db = db

    def insert_into_conference(self, values):
        max_id = self.bd.select_max('conference')
        for i in range(len(values)):
            row = [max_id + 1] + list(values[i])
            self.db.insert('conference', row, columns=['id', 'conference', 'year'])

    def insert_into_author(self, id_, name, affiliation, email):
        self.db.insert('author', (id_, name, email, affiliation), ["id", "name", "email", "affiliation"])

    def insert_into_article(self, id_, title, text, abstract, bibliography, keywords, url, file_path, common_id):
        self.db.insert('article', (id_, title, keywords, abstract, bibliography, text, url, common_id, file_path),
                       ['id', 'title', 'keywords', 'abstract', 'bibliography', 'text', 'url', 'common_id', 'filepath'])

    def insert_into_author_alias(self, alias, variant):
        max_id = self.bd.select_max('author_alias')
        max_id += 1
        variant_alias_id = self.select_id_from_author_alias(variant)
        if not variant_alias_id:
            self.db.insert('author_alias', (max_id, alias, variant), ["id", "alias", "author_id"])

    def select_id_from_author_alias(self, variant):
        where = ' author_id = ' + self.db.check(variant)
        rows = self.db.select(what='id', where='author_alias', condition=where)
        return rows[0][0] if rows != [] else None

    def insert_into_affiliation_alias(self, cluster, alias, author):
        max_id = self.db.select_max('affiliation_alias')
        max_id += 1
        self.db.insert('affiliation_alias', (max_id, cluster, alias, author), ["id", "cluster",  "alias", "author_id"])

    def insert_new_article(self, author, article, conference_name, url, file_path, common_id, year):
        article_id = self.get_article_id(article, url, file_path, common_id)
        author_id = self.get_author_id(author)
        conference_id = self.get_conference_id(conference_name, year)
        for auth_id in author_id:
            self.insert_to_catalogue(auth_id, article_id, conference_id)

    def get_author_id(self,author):
        list_of_authors_id = []
        for auth in author:
            author_id = self.select_id_from_author(auth['name'])
            if not author_id:
                author_id = self.bd.select_max('author') + 1
                if type(auth['email'])!=str:
                    # print(str(auth['email']) + " " + str(type(auth['email']))) TODO: Replace prints with logging
                    raise Exception("2 emails")
                self.insert_into_author(id_=author_id, name=auth['name'],
                                        email=auth['email'],
                                        affiliation=auth['affiliation'])
            list_of_authors_id.append(author_id)
        return list_of_authors_id

    def select_id_from_author(self, name):
        where = ' name = ' + self.check(name)
        rows = self.bd.select(what='id', where='author', condition=where)
        return rows[0][0] if rows != [] else None

    def get_article_id(self, article, url, file_path, common_id):
        new_title = self.reformat_title(article['title'])
        article_id = self.select_id_from_article(common_id)
        if not article_id:
            article_id = self.bd.select_max('article') + 1
            if 'bibliography' not in article.keys():
                # print("no_bibl") TODO: Replace prints with logging
                article['bibliography'] = "-"
            else:
                pass
                # print('bibliography IS here = ', article['bibliography']) TODO: Replace prints with logging
            if 'keywords' not in article.keys():
                article['keywords'] = "-"
            article_text = article['text']
            self.insert_into_article(id_=article_id, title=new_title, text=article_text,
                                     abstract=article['abstract'], bibliography=article['bibliography'],
                                     keywords=article['keywords'], url=url, file_path=file_path, common_id=common_id)
        return article_id

    def reformat_title(self, title):
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
        return ' '.join([new_title[0].capitalize()]+new_title[1:])

    def select_id_from_article(self, common_id):
        where = """common_id =""" + self.bd.check(common_id)
        rows = self.bd.select(what='id', where='article', condition=where)
        # print(rows) TODO: Replace prints with logging
        return rows[0][0] if rows != [] else None

    def get_conference_id(self, conference_name, year):
        conference_id = self.select_id_from_conference(conference_name, year)
        if not conference_id:
            # print(conference_name + " " + str(year)) TODO: Replace prints with logging
            raise ValueError('wrong combination of year and conference name')
        return conference_id

    def select_id_from_conference(self, conference_name, year):
        where = ''' year = ''' + str(year) + ''' AND conference = "''' + conference_name + '";'
        rows = self.bd.select(what='id', where='conference', condition=where)
        return rows[0][0] if rows != [] else None

    def insert_to_catalogue(self, auth_id, article_id, conference_id):
        catalog_id = self.select_id_from_catalogue(auth_id, article_id, conference_id)
        if not catalog_id:
            catalog_id = self.bd.select_max('catalogue') + 1
            self.bd.insert('catalogue', (int(catalog_id), int(auth_id),
                                         int(article_id), int(conference_id)),
                           columns=['id', 'author_id', 'article_id', 'conference_id'])

    def select_id_from_catalogue(self, auth_id, article_id, conference_id):
        where = ''' author_id = ''' + str(auth_id) + ''' AND article_id = ''' + str(article_id) + \
                ''' AND conference_id = ''' + str(conference_id) + ';'
        rows = self.bd.select(what='id', where='catalogue', condition=where)
        return rows[0][0] if rows != [] else None

    def load(self, article):
        counter = 0
        try:
            file_path = article['filepath']
        except KeyError:
            file_path=None
        self.insert_new_article(author=article['author'],
                                article=article['text'],
                                conference_name=article['conference'],
                                url=article['url'],
                                file_path=file_path,
                                common_id=article['id'],
                                year=int(article['year']))
        counter += 1
        print(counter)

    def update_language(self, filepath, delimeter=','):
        languages = DataFrame.from_csv(filepath, sep=delimeter)
        for i in range(len(languages.Lang.values)):
            self.bd.update("article", 'language', languages.Lang.values[i], 'common_id', languages.ID.values[i])

    def load_to_author_alias(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            string = f.read().split('\n')
        aliases = {}
        for name in string:
            alias, variants = [i.strip() for i in name.split(':')]
            new_variants = [variant.strip() for variant in variants[1:-1].split(',')]
            for variant in new_variants:
                aliases[variant] = alias
        self.bd.cursor.execute("""SELECT DISTINCT id, name FROM author""")
        old_names = dict([(n[1],n[0]) for n in self.bd.cursor.fetchall()])
        exceptions = []
        for name, index in old_names.items():
            try:
                self.bd.insert_into_author_alias(aliases[name.replace(",", "").strip()],index)
            except:
                exceptions.append((name, index))
        return exceptions

    def load_to_affiliation_alias(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            affiliations = f.readlines()
        results = {}
        for aff_cluster in range(1, len(affiliations)+1):
            for aff in affiliations[aff_cluster-1].split("\t"):
                results[aff] = aff_cluster
        self.bd.cursor.execute("""SELECT id, affiliation FROM author""")
        results_aff = self.bd.cursor.fetchall()
        for affiliation in results_aff:
            try:
                self.bd.insert_into_affiliation_alias(results[affiliation[1]], affiliation[1], affiliation[0])
            except sqlite3.IntegrityError as e:
                pass
                # TODO: Replace prints with logging
                # print('Foreign key error:\n {} for {} \n'.format(e, results[affiliation[1]], affiliation[1], affiliation[0]))
