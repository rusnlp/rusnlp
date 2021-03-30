#!/usr/bin/env python3
# coding:utf8

"""
this module reads strings.tsv, which contains all
the strings, and lets the main app use it
"""

import configparser
import csv
from builtins import next
from flask import Markup

config = configparser.RawConfigParser()
config.read('rusnlp.cfg')

root = config.get('Files and directories', 'root')
l10nfile = config.get('Files and directories', 'l10n')

# open the strings database:
csvfile = open(root + l10nfile, 'rU', encoding='utf-8')
acrobat = csv.reader(csvfile, dialect='excel', delimiter='\t')

# initialize a dictionary for each language:
language_dicts = {}
langnames = config.get('Languages', 'interface_languages').split(',')
header = next(acrobat)
included_columns = []
for langname in langnames:
    language_dicts[langname] = {}
    included_columns.append(header.index(langname))
n_cols = len(header)

# read the tab-separated file, populate language_dicts:
for i, row in enumerate(acrobat):
    if len(row) != n_cols:
        print('Invalid string № {}: {}'.format(i+2, row))
    for coln in included_columns:  # range(1, len(row)):
        # Markup() is used to prevent autoescaping in templates
        language_dicts[header[coln]][row[0]] = Markup(row[coln])
