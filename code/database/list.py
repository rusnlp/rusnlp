#!/usr/bin/python3

import sys
from os import path, listdir
import logging
from bd import DBaseRusNLP
from db_reader import ReaderDBase


testdir = sys.argv[1]
bd_m = DBaseRusNLP(path.join('..', '..', '..', 'database', 'rus_nlp_withouttexts.db'),
                   path.join('..', '..', '..', 'database', 'database_metadata.json'))
reader = ReaderDBase(bd_m)

files = [f.split('.')[0] for f in listdir(testdir) if path.isfile(path.join(testdir, f))]

for query in files:
    if 'ainl_2015' in query:
        title = reader.select_title_by_id(query)
        authors = reader.select_author_by_id(query)
        authors = ','.join([w for w in authors])
        print(title + '\t' + authors + '\t' + query)
