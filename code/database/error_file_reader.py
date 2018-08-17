import json
from bd import DBaseRusNLP
from db_writer import WriterDBase
from db_reader import ReaderDBase


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
    #c.delete(table="catalogue", column="id", condition=old_data[0])
    for author in author_list:
        c.cursor.execute('''SELECT id FROM author WHERE name="{}"'''.format(author))
        author_id = c.cursor.fetchall()
        author_id = author_id[0][0] if author_id != [] else None
        if author_id:
            db_write_helper.insert_into_author_alias(author, author_id)
            #db_write_helper.insert_to_catalogue(author_id, old_data[1], old_data[2])
        else:
            pass
            print("!!!!!!!!! no", author)
            #db_write_helper.insert_into_author(c.select_max('author') + 1, author, "", "")


def update(common_id, title, url, authors):
    # if title is not None:
    #     c.update("article", "title", title, "common_id", common_id)
    # if url is not None:
    #     c.update("article", "url", url, "common_id", common_id)
    if authors is not None:
        update_authors(authors, common_id)


c = DBaseRusNLP("rus_nlp_withouttexts_server_upd.db", "meta_data.json")
db_write_helper = WriterDBase(c)
db_read_helper = ReaderDBase(c)

print(db_read_helper.select_author_and_title_by_id("dialogue_2013_d2efceda61e865215a1af05413186ee009f74918"))
c.cursor.execute('SELECT * FROM author WHERE id={}'.format(2375))
print(c.cursor.fetchall())
print(c.select_max("author"))
c.cursor.execute('''SELECT catalogue.id, article_id, conference_id, author_id FROM catalogue JOIN article ON catalogue.article_id=article.id WHERE common_id="{}"'''.format(("dialogue_2013_d2efceda61e865215a1af05413186ee009f74918")))
print(c.cursor.fetchall())
#---- process errors -----------------------------------
#
# for i in range(3):
#     with open("../../file/errors{}.txt".format(i), 'r', encoding="utf-8") as e:
#         errors_ = [j.split("\t") for j in e.read().split("\n")]
#
#     for line in errors_:
#         common_id = line[0]
#         title, url, authors = parse_else(line[1:])
#         update(common_id, title, url, authors)
