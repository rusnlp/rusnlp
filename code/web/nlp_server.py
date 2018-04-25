#!/usr/bin/python3
# coding: utf-8


import configparser
import datetime
import fnmatch
import json
import logging
import socket
import sys
from os import path
import gzip
from _thread import *
from gensim.models import TfidfModel
from gensim.matutils import cossim
from bd import DBaseRusNLP
from db_reader import ReaderDBase


# Function for handling connections. This will be used to create threads
def clientthread(conn, addr):
    # Sending message to connected client
    conn.send(bytes(b'RusNLP model server'))

    # infinite loop so that function do not terminate and thread do not end.
    while True:
        # Receiving from client
        data = conn.recv(1024)
        if not data:
            break
        data = data.decode("utf-8")
        query = json.loads(data)

        now = datetime.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M"), '\t', addr[0] + ':' + str(addr[1]), '\t', data, file=sys.stderr)

        output = queryparser(query)

        reply = json.dumps(output, ensure_ascii=False) + '&&&'
        conn.sendall(reply.encode('utf-8'))
        break

    # came out of loop
    conn.close()


# Vector functions
def find_nearest(q_vector, q, number, restrict=None):
    if restrict:
        similarities = {d: cossim(q_vector, text_vectors[d]) for d in restrict if cossim(q_vector,
            text_vectors[d]) > 0.01}
    else:
        similarities = {d: cossim(q_vector, text_vectors[d]) for d in text_vectors.keys() if d != q
                and cossim(q_vector, text_vectors[d]) > 0.01}
    neighbors = sorted(similarities, key=similarities.get, reverse=True)[:number]
    results = [
        (i, reader.select_title_by_id(i), reader.select_author_by_id(i), reader.select_year_by_id(i),
         reader.select_conference_by_id(i), reader.select_url_by_id(i), reader.select_affiliation_by_id(i),
         similarities[i]) for i in neighbors]
    return results


def f_conf(q):
    results = set()
    for conference in q:
        c_results = set(reader.select_articles_from_conference(conference))
        results = results.union(c_results)
    return results


def f_year(q):
    (year_min, year_max) = q
    if year_min == "":
        year_min = 2005
    if year_max == "":
        year_max = 2020
    results = reader.select_articles_from_years(year_min, year_max)
    results = set(results)
    return results


def f_author(q):
    results = set()
    if q in authorsindex:
        results = set(reader.select_articles_of_author(q))
    else:
        for q_author in authorsindex:
            if fnmatch.fnmatch(q_author.lower(), q.lower()):
                results = results.union(set(reader.select_articles_of_author(q_author)))
    return results


def f_title(q):
    results = set()
    if q in titlesindex:
        results.add(titlesindex[q])
    else:
        for title in titlesindex:
            if fnmatch.fnmatch(title.lower(), q.lower()):
                results.add(titlesindex[title])
    return results


def search(sets, number, keywords=None):
    intersect = set.intersection(*sets)
    valid = [doc for doc in intersect if doc in id_index]
    if keywords:
        q_vector = model[dictionary.doc2bow(keywords)]
        results = find_nearest(q_vector, keywords, number, restrict=valid)
    else:
        results = [(i, reader.select_title_by_id(i), reader.select_author_by_id(i), reader.select_year_by_id(i),
                    reader.select_conference_by_id(i), reader.select_url_by_id(i),
                    reader.select_affiliation_by_id(i)) for i in valid]
    return results


def finder(userquery, number):
    answers = []
    if len(userquery) == 0:
        return None
    else:
        for field in userquery:
            if userquery[field] == '' or field == 'threshold' or field == 'keywords':
                continue
            oper = eval(field)
            answer = oper(userquery[field])
            answers.append(answer)
    results = search(answers, number, keywords=userquery['keywords'])
    return results


def queryparser(query):
    (operation, searchstring, number) = query
    if operation == 1:
        article_id = searchstring
        if article_id not in id_index:
            output = {'meta': 'Publication not found'}
            return output
        q_vector = text_vectors[article_id]
        output = {}
        output['neighbors'] = operations[operation](q_vector, article_id, number)
        output['meta'] = {'title': reader.select_title_by_id(article_id),
                          'author': reader.select_author_by_id(article_id),
                          'year': reader.select_year_by_id(article_id),
                          'conference': reader.select_conference_by_id(article_id),
                          'affiliation': reader.select_affiliation_by_id(article_id),
                          'url': reader.select_url_by_id(article_id)}
        output['meta']['filename'] = article_id
        return output
    else:
        output = operations[operation](searchstring, number)
        return output


if __name__ == "__main__":
    operations = {1: find_nearest, 2: finder}

    config = configparser.RawConfigParser()
    config.read('rusnlp.cfg')

    root = config.get('Files and directories', 'root')
    HOST = config.get('Sockets', 'host')  # Symbolic name meaning all available interfaces
    PORT = config.getint('Sockets', 'port')  # Arbitrary non-privileged port

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    databasefile = config.get('Files and directories', 'database')
    metadatafile = config.get('Files and directories', 'database_meta')

    bd_m = DBaseRusNLP(path.join('data', 'rus_nlp_withouttexts.db'),
                       path.join('data', 'database_metadata.json'))
    reader = ReaderDBase(bd_m)

    # Loading model
    for line in open(root + config.get('Files and directories', 'models'), 'r').readlines():
        if line.startswith("#"):
            continue
        res = line.strip().split('\t')
        (mod_identifier, mod_description, mod_path) = res
        model = TfidfModel.load(path.join(mod_path, 'tfidf.model'))
        dictionary = model.id2word
        text_vectors = gzip.open(path.join(mod_path, 'tfidf_corpus.json.gz'), 'r').read()
        text_vectors = json.loads(text_vectors.decode('utf-8'))
        print("Model", model, "from file", path.join(mod_path, 'tfidf.model'), "loaded successfully.", file=sys.stderr)

    id_index = text_vectors.keys()
    authorsindex = set(reader.select_all_authors())
    titlesindex = {reader.select_title_by_id(ident): ident for ident in id_index}

    # Bind socket to local host and port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created', file=sys.stderr)

    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print('Bind failed.' + str(msg), file=sys.stderr)
        sys.exit()

    print('Socket bind complete', file=sys.stderr)

    # Start listening on socket
    s.listen(100)
    print('Socket now listening on port', PORT, file=sys.stderr)

    # now keep talking with the client
    while True:
        # wait to accept a connection - blocking call
        connection, address = s.accept()

        # start new thread takes 1st argument as a function name to be run,
        # second is the tuple of arguments to the function.
        start_new_thread(clientthread, (connection, address))
