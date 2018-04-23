#!/usr/bin/python3
# coding: utf-8

import configparser
import json
import logging
import socket
import sys
from flask import render_template, Blueprint
from flask import request, Response

config = configparser.RawConfigParser()
config.read('rusnlp.cfg')
root = config.get('Files and directories', 'root')

url = config.get('Other', 'url')

# Establishing connection to model server
host = config.get('Sockets', 'host')
port = config.getint('Sockets', 'port')
try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    # could not resolve
    print('Hostname could not be resolved. Exiting', file=sys.stderr)
    sys.exit()


def serverquery(message):
    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print('Failed to create socket', file=sys.stderr)
        return None

    # Connect to remote server
    s.connect((remote_ip, port))
    # Now receive initial data
    initial_reply = s.recv(1024)

    # Send some data to remote server
    message = json.dumps(message, ensure_ascii=False)
    try:
        s.sendall(message.encode('utf-8'))
    except socket.error:
        # Send failed
        print('Send failed', file=sys.stderr)
        s.close()
        return None
    # Now receive data
    reply = ''
    while '&&&' not in reply:
        reply += s.recv(32768).decode('utf-8')
    s.close()
    reply = reply[:-3]
    return reply


logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

nlpsearch = Blueprint('nlpsearch', __name__, template_folder='templates')


@nlpsearch.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        conference = request.form.getlist('conf_query')
        year_min = request.form['year_query_min']
        if year_min:
            year_min = int(year_min)
        year_max = request.form['year_query_max']
        if year_max:
            year_max = int(year_max)
        year = (year_min, year_max)
        author = request.form['author_query'].strip()
        if year[0] and year[1]:
            if year[0] > year[1]:
                return render_template('rusnlp.html', error="Проверьте даты!", url=url)
        title = request.form['query'].strip()
        # query = {'f_author': author, 'f_year': year, "f_conf": conference, "f_title": title}
        query = {'f_author': author, "f_conf": conference, "f_title": title}
        message = [2, query, 10]
        results = json.loads(serverquery(message))
        if len(results) == 0:
            return render_template('rusnlp.html', conf_query=conference, year_query=year, author_query=author,
                                   error='Поиск не дал результатов.', search=True, url=url,
                                   query=title)
        return render_template('rusnlp.html', result=results, conf_query=conference, author_query=author,
                               year_query=year, search=True, url=url, query=title)
    return render_template('rusnlp.html', search=True, url=url)


@nlpsearch.route('/publ/<fname>', methods=['GET', 'POST'])
def paper(fname):
    query = fname.strip()
    topn = 10
    threshold = 0.95
    if request.method == 'POST':
        try:
            threshold = float(request.form['threshold'])
        except ValueError:
            pass
        try:
            topn = int(request.form['topn'])
        except ValueError:
            pass

        if not fname:
            print('Error!', file=sys.stderr)
            return render_template('rusnlp_paper.html', error="Something wrong with your query!", url=url)

    message = [1, query, topn, True]
    message = json.dumps(message, ensure_ascii=False)
    message = message.encode('utf-8')
    results = json.loads(serverquery(message))
    metadata = results['meta']

    if 'not found' in metadata or 'unknown to the model' in results['cyberleninka_content']:
        return render_template('rusnlp_paper.html',
                               query=query,
                               error='Статья с таким идентификатором не найдена в модели',
                               search=True,
                               url=url,
                               threshold=threshold, topn=topn)

    else:
        return render_template('rusnlp_paper.html',
                               result=results,
                               query=query,
                               metadata=metadata,
                               search=True,
                               url=url,
                               threshold=threshold, topn=topn)


@nlpsearch.route('/api/<title>/<num>', methods=['GET'])
def dissernet_api(title, num):
    mime = 'application/json'
    query = title.strip().lower().replace('__', ' ')
    number = int(num)
    if number > 100:
        number = 100
    message = "1;" + query + ";" + str(number)
    results = json.loads(serverquery(message))
    output = json.dumps(results, ensure_ascii=False)
    return Response(output.encode('utf-8'), mimetype=mime,
                    headers={"Content-Disposition": "attachment;filename=rusnlp.json"})
