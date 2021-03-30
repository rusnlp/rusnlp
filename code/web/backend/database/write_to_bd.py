import os
import sys
from code.web.db_classes.db import DBaseRusNLP
from code.web.db_classes.db_writer import WriterDBase

if __name__ == '__main__':
    if len(sys.argv) < 5:
        raise Exception("Please specify paths: <data-txt> <db name> <metadata db path> <metadate jsonlines path>")
    basepath = sys.argv[1]
    db = DBaseRusNLP(sys.argv[2], os.path.join(sys.argv[3], "metadata.json"))
    for i in db.get_db_info():
        print(i[1], db.select_columns_name(i[1]))

    # -------------------------------------------------------------------
    # Initial db construction
    # -------------------------------------------------------------------
    db_writer = WriterDBase(db)
    if db.select_max('conference') == 0:
        db_writer.add_conference_data(sys.argv[3])
    if db.select_max('author') == 0:
        db_writer.add_author_data(os.path.join(basepath, "current_authors.tsv"))
    if db.select_max('affiliation') == 0:
        db_writer.add_affiliation_data(os.path.join(basepath, "current_affiliations.tsv"))

    # -------------------------------------------------------------------
    # Add json data
    # -------------------------------------------------------------------

    with open(os.path.join(basepath, sys.argv[4]), 'r', encoding='utf-8') as f:
        for line in f:
            db_writer.add_jsonline(line)
