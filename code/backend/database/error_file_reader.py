import json
from bd import DBaseRusNLP
from db_writer import WriterDBase


def parse_else(list_of_errors):
    title_ = None
    url_ = None
    authors_ = None
    for string in list_of_errors:
        if string.startswith("title"):
            title_ = string.replace("title: ", "")
        elif string.startswith("url"):
            url_ = string.replace("url: ", "")
        elif string.startswith("author"):
            authors_ = json.loads(string.replace("authors: ", ""))
    return title_, url_, authors_


def update_authors(author_list, common_id):
    c.cursor.execute('''SELECT catalogue.id, article_id, conference_id FROM catalogue JOIN article ON catalogue.article_id=article.id WHERE common_id="{}"'''.format(common_id))
    old_data = list(set(c.cursor.fetchall()))[0]
    c.delete(table="catalogue", column="id", condition=old_data[0])
    for author in author_list:
        c.cursor.execute('''SELECT id FROM author WHERE name="{}"'''.format(author))
        author_id = c.cursor.fetchall()
        author_id = author_id[0][0] if author_id != [] else None
        if author_id:
            db_write_helper.insert_to_catalogue(author_id, old_data[1], old_data[2])
        # else:
        #     pass
        #     print(author)
        #     #db_write_helper.insert_into_author(c.select_max('author') + 1, author, "", "")


def update(common_id, title, url, authors):
    if title is not None:
        c.update("article", "title", title, "common_id", common_id)
    if url is not None:
        c.update("article", "url", url, "common_id", common_id)
    # if authors is not None:
    #     update_authors(authors, common_id)


c = DBaseRusNLP("rus_nlp_withouttexts.db", "meta_data.json")
db_write_helper = WriterDBase(c)

# ---- process errors -----------------------------------

for i in range(3):
    with open("../../file/errors{}.txt".format(i), 'r', encoding="utf-8") as e:
        errors_ = [j.split("\t") for j in e.read().split("\n")]

    for line in errors_:
        common_id = line[0]
        title, url, authors = parse_else(line[1:])
        update(common_id, title, url, authors)
