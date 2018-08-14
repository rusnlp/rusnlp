from bd import DBaseRusNLP


def parse_else(list_of_errors):
    title_ = None
    url_ = None
    authors_ = None
    affiliations_ = None
    for i in list_of_errors:
        if i.startswith("title"):
            title_ = parse_title(i)
        elif i.startswith("url"):
            url_ = parse_url(i)
        # elif i.startswith("author"):
        #     authors_ = parse_authors(i)
        # elif i.startswith("affiliation"):
        #     affiliations_ = parse_affiliation(i)
    return title_, url_, authors_, affiliations_


def parse_title(string):
    return string.replace("title: ", "")


def parse_url(string):
    return string.replace("url: ", "")


def parse_authors(string):
    return None


def parse_affiliation(string):
    return None


def update(common_id, title, url, authors, affiliations):
    if title is not None:
        c.update("article", "title", title, "common_id", common_id)
    if url is not None:
        c.update("article", "url", url, "common_id", common_id)
    # if authors is not None:
    #     c.update(table, column, value, what, condition)
    # if affiliations is not None:
    #     c.update(table, column, value, what, condition)

c = DBaseRusNLP("rus_nlp_from_up.db", "meta_data.json")

# ---------------------------------------------------
# ---- process e0 -----------------------------------

with open("../../file/errors0.txt", 'r') as e0:
    errors_e0 = [i.split("\t") for i in e0.read().split("\n")]

for i in errors_e0:
    common_id = i[0]
    title, url, authors, affiliations = parse_else(i[1:])
    update(common_id, title, url, authors, affiliations)

# ---------------------------------------------------
# ---- process e1 -----------------------------------

with open("../../file/errors1.txt", 'r', encoding="utf-8") as e1:
    errors_e1 = [i.split("\t") for i in e1.read().split("\n")]

for i in errors_e1:
    common_id = i[0]
    title, url, authors, affiliations = parse_else(i[1:])
    update(common_id, title, url, authors, affiliations)

# ---------------------------------------------------
# ---- process e2 -----------------------------------
with open("../../file/errors2.txt", 'r') as e2:
    errors_e2 = [i.split("\t") for i in e2.read().split("\n")]

for i in errors_e2:
    common_id = i[0]
    title, url, authors, affiliations = parse_else(i[1:])
    update(common_id, title, url, authors, affiliations)



