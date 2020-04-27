import os
import sys

from code.web.db_classes.db import DBaseRusNLP
from code.web.db_classes.db_writer import WriterDBase

if __name__ == '__main__':
    if len(sys.argv) < 4:
        raise Exception("Please specify paths: <data-txt> <db name> <metadata path>")
    basepath = sys.argv[1]  # "D://syncthing//RusNLP//data-txt"
    db = DBaseRusNLP(sys.argv[2], sys.argv[3])  # "rusnlp2.0.db", "metadata.json"
    for i in db.get_db_info():
        print(i[1], db.select_columns_name(i[1]))

    # -------------------------------------------------------------------
    # Initial db construction
    # -------------------------------------------------------------------
    db_writer = WriterDBase(db)
    if db.select_max('conference') == 0:
        db_writer.add_conference_data()
    if db.select_max('author') == 0:
        db_writer.add_author_data(os.path.join(basepath, "current_authors.tsv"))
    if db.select_max('affiliation') == 0:
        db_writer.add_affiliation_data(os.path.join(basepath, "current_affiliations.tsv"))

    # -------------------------------------------------------------------
    # Add json data
    # -------------------------------------------------------------------

    with open(os.path.join(basepath, "metadata.jsonlines"), 'r', encoding='utf-8') as f:
        for line in f:
            db_writer.add_jsonline(line)
