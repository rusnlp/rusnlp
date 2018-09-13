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
import threading
from gensim.models import TfidfModel
from gensim.matutils import cossim
from bd import DBaseRusNLP
from db_reader import ReaderDBase
import csv


class SrvThread(threading.Thread):
    def __init__(self, connect, address):
        threading.Thread.__init__(self)
        self.connect = connect
        self.address = address

    def run(self):
        threadLimiter.acquire()
        try:
            clientthread(self.connect, self.address)
        finally:
            threadLimiter.release()


# Function for handling connections. This will be used to create threads
def clientthread(connection, address):
    # Sending message to connected client
    connection.send(bytes(b'RusNLP model server'))

    # infinite loop so that function do not terminate and thread do not end.
    while True:
        # Receiving from client
        data = connection.recv(4096)
        if not data:
            break
        data = data.decode("utf-8")
        query = json.loads(data)

        now = datetime.datetime.now()
        print(now.strftime("%Y-%m-%d %H:%M"), '\t', address[0] + ':' + str(address[1]), '\t', data, file=sys.stderr)

        output = queryparser(query)
        # print(output)

        reply = json.dumps(output, ensure_ascii=False) + '&&&'
        connection.sendall(reply.encode('utf-8'))
        break

    # came out of loop
    connection.close()


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
        (i, reader.select_title_by_id(i), list(reader.select_cluster_author_by_common_id(i)),
         reader.select_year_by_id(i),
         reader.select_conference_by_id(i), reader.select_url_by_id(i), list(reader.select_aff_clusters_by_id(i)),
         reader.select_abstract_by_id(i)[:300] + '...', similarities[i]) for i in neighbors]
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
    if q.strip().isdigit():
        q = reader.select_alias_name_by_author_cluster(int(q))
    if q in authorsindex:
        results = set(reader.select_articles_of_author(q))
    else:
        for q_author in authorsindex:
            if fnmatch.fnmatch(q_author.lower(), q.lower()):
                results = results.union(set(reader.select_articles_of_author(q_author)))
    return results


def f_affiliation(q):
    if q.strip().isdigit():
        q = reader.select_affiliation_by_cluster(int(q))
    aff_id = reader.select_aff_cluster_by_affiliation(q)
    results = set(reader.select_articles_by_cluster(aff_id))
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
        results = [(i, reader.select_title_by_id(i), list(reader.select_cluster_author_by_common_id(i)),
                    reader.select_year_by_id(i),
                    reader.select_conference_by_id(i), reader.select_url_by_id(i),
                    list(reader.select_aff_clusters_by_id(i)), reader.select_abstract_by_id(i)[:300] + '...') for i in
                   valid]
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
        output = {'neighbors': operations[operation](q_vector, article_id, number),
                  'meta': {'title': reader.select_title_by_id(article_id),
                           'author': list(reader.select_cluster_author_by_common_id(article_id)),
                           'year': reader.select_year_by_id(article_id),
                           'conference': reader.select_conference_by_id(article_id),
                           'affiliation': list(reader.select_aff_clusters_by_id(article_id)),
                           'abstract': reader.select_abstract_by_id(article_id)[:300] + '...',
                           'url': reader.select_url_by_id(article_id)},
                  'topics': {}
                  }
        output['meta']['filename'] = article_id
    else:
        output = {'topics': {}, 'neighbors': operations[operation](searchstring, number)}
    if operation < 3:
        for n in output['neighbors']:
            text_vector = text_vectors[n[0]]
            candidates = [(topic, nlpub_terms[topic]['url']) for topic in nlpub_terms if
                          cossim(text_vector, nlpub_terms[topic]['terms']) > 0.03]
            if candidates:
                output['topics'][n[0]] = candidates
    return output


def ids2names(query, number):
    ids = query['ids']
    field = query['field']
    if field == 'author':
        names = {int(identifier): reader.select_alias_name_by_author_cluster(identifier) for identifier in ids}
    elif field == 'affiliation':
        names = {int(identifier): reader.select_affiliation_by_cluster(identifier) for identifier in ids}
    else:
        names = None
    return names


def stats(query, number):
    statistics = reader.get_statistics().to_dict()
    return statistics

def descriptions(query, number):
    entity = query['field']
    ids = query['ids']
    if entity == 'conference':
        descr = reader.get_dict_of_conference_description(ids[0])
    else:
        descr = None
    return descr


if __name__ == "__main__":
    operations = {1: find_nearest, 2: finder, 3: ids2names, 4: stats, 5: descriptions}

    config = configparser.RawConfigParser()
    config.read('rusnlp.cfg')

    root = config.get('Files and directories', 'root')
    HOST = config.get('Sockets', 'host')  # Symbolic name meaning all available interfaces
    PORT = config.getint('Sockets', 'port')  # Arbitrary non-privileged port

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

    databasefile = config.get('Files and directories', 'database')
    metadatafile = config.get('Files and directories', 'database_meta')
    nlpubfile = config.get('Files and directories', 'nlpub_file')

    print('Loading database from', databasefile, file=sys.stderr)

    bd_m = DBaseRusNLP(path.join('data', databasefile),
                       path.join('data', metadatafile))
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

    nlpub_terms = {}
    with open(nlpubfile, 'r') as csvfile:
        csvreader = csv.DictReader(csvfile, delimiter='\t')
        for row in csvreader:
            nlpub_terms[row['description']] = {}
            nlpub_terms[row['description']]['terms'] = model[dictionary.doc2bow(row['terms'].strip().split())]
            nlpub_terms[row['description']]['url'] = row['url'].strip()

    id_index = text_vectors.keys()
    authorsindex = set()
    for el in id_index:
        cur_authors = reader.select_author_by_id(el)
        authorsindex |= set(cur_authors)
    titlesindex = {reader.select_title_by_id(ident): ident for ident in id_index}

    maxthreads = 2  # Maximum number of threads
    threadLimiter = threading.BoundedSemaphore(maxthreads)

    # Bind socket to local host and port

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print('Socket created with max number of active threads set to', maxthreads, file=sys.stderr)

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
        # wait to accept a connection
        conn, addr = s.accept()

        # start new thread takes 1st argument as a function name to be run,
        # second is the tuple of arguments to the function.
        thread = SrvThread(conn, addr)
        thread.start()
