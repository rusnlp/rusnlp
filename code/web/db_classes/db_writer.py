from collections import Counter
import json


class WriterDBase:
    def __init__(self, db):
        self.db = db
        self.db.cursor.execute('PRAGMA auto_vacuum = 1')

    # -------------------------------------------------------------------
    # insertions specific for RusNLP
    # -------------------------------------------------------------------

    def insert_into_conferences(self, name, year, description_ru, description_en, url):
        id_ = self.db.select_max('conference') + 1
        self.db.insert('conference', (id_, name, year, description_ru, description_en, url),
                       columns=['id', 'name', 'year', "description_ru", "description_en", "url"])

    def insert_into_authors(self, author_id, name):
        id_ = self.db.select_max('author') + 1
        self.db.insert('author', (id_, author_id, name), ["id", "author_id", "name"])

    def insert_into_affiliations(self, affiliation_id, name):
        id_ = self.db.select_max('affiliation') + 1
        self.db.insert('affiliation', (id_, affiliation_id, name),
                       ["id", "affiliation_id", "name"])

    def insert_into_catalogue(self, conference_id, language, common_id, url, title, abstract,
                              keywords):
        id_ = self.db.select_max('catalogue') + 1
        self.db.insert('catalogue', (id_, conference_id, language, common_id, url, title, abstract,
                                     keywords), ["id", "conference_id", "language", "common_id",
                                                 "url", "title", "abstract", "keywords"])

    def insert_into_author_catalogue(self, common_id, author_id, email, affiliation_id):
        id_ = self.db.select_max('author_catalogue') + 1
        self.db.insert('author_catalogue', (id_, common_id, author_id, email, affiliation_id),
                       ["id", "common_id", "author_id", "email", "affiliation_id"])

    # -------------------------------------------------------------------
    # add static data
    # -------------------------------------------------------------------

    def add_conference_data(self, end=2020):
        with open("conference_data.json", 'r', encoding='utf-8') as f:
            conferences = json.loads(f.read())
        for conference, (start, description_ru, description_en, url) in conferences.items():
            for year in range(start, end + 1):
                self.insert_into_conferences(conference, year, description_ru, description_en, url)

    def add_author_data(self, filename: str):
        authors = self.convert_to_set(filename)
        for id_, name in authors:
            self.insert_into_authors(id_, name)

    def add_affiliation_data(self, filename: str):
        affiliations = self.convert_to_set(filename)
        for id_, name in affiliations:
            self.insert_into_affiliations(id_, name)

    @staticmethod
    def convert_to_set(filename: str):
        data = set()
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                id_, name, _ = line[:-1].split('\t')
                data.add((int(id_), name))
        print(Counter([i[0] for i in data]))
        print(Counter([i[1] for i in data]))
        return data

    # -------------------------------------------------------------------
    # extract conference data
    # -------------------------------------------------------------------

    def get_conference_id(self, name, year):
        where = '''year={} AND name="{}";'''.format(year, name)
        rows = self.db.select(what='id', where='conference', condition=where)
        assert len(rows) == 1 and len(rows[0]) == 1
        return rows[0][0]

    # -------------------------------------------------------------------
    # add json data
    # -------------------------------------------------------------------

    def add_jsonline(self, json_line: str):
        metadata = json.loads(json_line)
        year = metadata['year']
        conference = metadata['conference']
        language = metadata['language']
        common_id = metadata['hash']
        url = metadata['url']

        # ------------- insert into catalogue -------------
        conference_id = self.get_conference_id(conference, year)
        title = metadata['article']['title']
        abstract = metadata['article']['abstract']
        keywords = metadata['article']['keywords']

        self.insert_into_catalogue(conference_id, language, common_id, url, title, abstract,
                                   ", ".join(keywords))

        # ------------- insert into author catalogue -------------
        for author in metadata['article']['authors']:
            author_id = author["name_id"]
            email = author['email']
            if author_id:  # TODO: delete line (not all authors are found)

                for affiliation in author["affiliations"]:
                    affiliation_id = affiliation["affiliation_id"]
                    self.insert_into_author_catalogue(common_id, author_id, email,
                                                      affiliation_id)

                if len(author["affiliations"]) == 0:  # TODO: replace with logging to file
                    with open("empty_affiliations.txt", 'a', encoding='utf-8') as f:
                        f.write(common_id+"\t"+author_id+"\t"+language+"\t"+title+"\n")
            else:  # TODO: delete line (not all authors are found)
                # TODO: replace with logging to file
                with open("empty_authors.txt", 'a', encoding='utf-8') as f:
                    f.write(common_id+"\t"+language+"\t"+title+"\n")
