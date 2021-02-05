#!/usr/bin/env python3
# coding: utf-8

import configparser
import json
import logging
import socket
import sys
from flask import render_template, Blueprint, redirect
from flask import request, Response
from flask import g
from strings_reader import language_dicts

config = configparser.RawConfigParser()
config.read("rusnlp.cfg")
root = config.get("Files and directories", "root")
languages_list = config.get("Languages", "interface_languages").split(",")
languages = "/".join(list(language_dicts.keys())).upper()
year_dict = {
    'maxmin_min': config.getint('Maxmin years', 'year_min'),
    'maxmin_max': config.getint('Maxmin years', 'year_max'),
    'default_min': config.getint('Default years', 'year_min'),
    'default_max': config.getint('Default years', 'year_max')
    }
url = config.get("Other", "url")

# Establishing connection to model server
host = config.get("Sockets", "host")
port = config.getint("Sockets", "port")
try:
    remote_ip = socket.gethostbyname(host)
except socket.gaierror:
    # could not resolve
    print("Hostname could not be resolved. Exiting", file=sys.stderr)
    sys.exit()


def serverquery(message):
    # create an INET, STREAMing socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print("Failed to create socket", file=sys.stderr)
        return None

    # Connect to remote server
    s.connect((remote_ip, port))
    # Now receive initial data
    _ = s.recv(1024)

    # Send some data to remote server
    message = json.dumps(message, ensure_ascii=False)
    try:
        s.sendall(message.encode("utf-8"))
    except socket.error:
        # Send failed
        print("Send failed", file=sys.stderr)
        s.close()
        return None
    # Now receive data
    reply = b""
    while b"&&&" not in reply:
        reply += s.recv(65536)
    s.close()
    reply = reply.decode("utf-8")[:-3]
    return reply


logging.basicConfig(
    format="%(asctime)s : %(levelname)s : %(message)s", level=logging.INFO
)

nlpsearch = Blueprint("nlpsearch", __name__, template_folder="templates")


def after_this_request(func):
    if not hasattr(g, "call_after_request"):
        g.call_after_request = []
    g.call_after_request.append(func)
    return func


@nlpsearch.after_request
def per_request_callbacks(response):
    for func in getattr(g, "call_after_request", ()):
        response = func(response)
    return response


@nlpsearch.route(
    "/" + "<lang:lang>/",
    defaults={
        "conference": "",
        "year": "",
        "author": "",
        "affiliation": "",
        "keywords": "",
    },
    methods=["GET", "POST"],
)
@nlpsearch.route(
    "/" + "<lang:lang>/" + "conf/<conference>",
    defaults={"year": "", "author": "", "affiliation": "", "keywords": ""},
    methods=["GET", "POST"],
)
@nlpsearch.route(
    "/" + "<lang:lang>/" + "year/<year>",
    defaults={"conference": "", "author": "", "affiliation": "", "keywords": ""},
    methods=["GET", "POST"],
)
@nlpsearch.route(
    "/" + "<lang:lang>/" + "author/<author>",
    defaults={"conference": "", "year": "", "affiliation": "", "keywords": ""},
    methods=["GET", "POST"],
)
@nlpsearch.route(
    "/" + "<lang:lang>/" + "affiliation/<affiliation>",
    defaults={"conference": "", "year": "", "author": "", "keywords": ""},
    methods=["GET", "POST"],
)
@nlpsearch.route(
    "/" + "<lang:lang>/" + "kw/<keywords>",
    defaults={"conference": "", "year": "", "author": "", "affiliation": ""},
    methods=["GET", "POST"],
)
def homepage(lang, conference, year, author, affiliation, keywords):
    # pass all required variables to template
    # repeated within each @nlpsearch.route function
    g.lang = lang
    s = {lang}
    other_lang = list(set(language_dicts.keys()) - s)[0]  # works only for two languages
    g.strings = language_dicts[lang]

    descriptions = {}

    if (
        conference
        or year
        or author
        or affiliation
        or keywords
        or request.method == "POST"
    ):
        if request.method == "POST":
            keywords = request.form["keywords"].strip().lower().split()
            author = request.form["author_query"].strip()
            affiliation = request.form["affiliation_query"].strip()
            title = request.form["query"].strip()
            conference = request.form.getlist("conf_query")
            if conference:
                query = {"field": "conference", "ids": conference}
                message = [5, query, 10]
                descriptions["conferences"] = json.loads(serverquery(message))[
                    "neighbors"
                ]
            year_min = request.form["year_query_min"]
            if year_min:
                year_min = int(year_min)
            year_max = request.form["year_query_max"]
            if year_max:
                year_max = int(year_max)
        else:
            title = ""
            if keywords:
                keywords = keywords.strip().lower().split("+")
            if conference:
                conference = [conference]
                query = {"field": "conference", "ids": conference}
                message = [5, query, 10]
                descriptions["conferences"] = json.loads(serverquery(message))[
                    "neighbors"
                ]
            year_min = year
            year_max = year
        year = (year_min, year_max)
        if year[0] and year[1]:
            if year[0] > year[1]:
                return render_template(
                    "rusnlp.html",
                    error="Проверьте даты!",
                    url=url,
                    other_lang=other_lang,
                    languages=languages,
                    search=True,
                    years=year_dict
                )
        if len(conference) == 0:
            conference = ["Dialogue", "AIST", "AINL"]
        query = {
            "f_author": author,
            "f_year": year,
            "f_conf": conference,
            "f_title": title,
            "f_affiliation": affiliation,
            "keywords": keywords,
        }
        if (
            query["f_author"] == ""
            and query["f_affiliation"] == ""
            and query["f_title"] == ""
            # если будут добавляться конференции, надо будет не забыть переделать
            and len(query["f_conf"]) == 3
            and query["keywords"] == []
            and query["f_year"] == (config.getint('Default years', 'year_min'),
                                    config.getint('Default years', 'year_max'))
        ):
            return render_template(
                "rusnlp.html",
                error="Введите какой-нибудь запрос!",
                url=url,
                other_lang=other_lang,
                languages=languages,
                search=True,
                years=year_dict
            )
        message = [2, query, 10]
        results = json.loads(serverquery(message))
        if len(results["neighbors"]) == 0:
            return render_template(
                "rusnlp.html",
                conf_query=conference,
                year_query=year,
                author_query=author,
                error="Поиск не дал результатов.",
                search=True,
                url=url,
                affiliation_query=affiliation,
                query=title,
                keywords=" ".join(keywords),
                other_lang=other_lang,
                languages=languages,
                years=year_dict
            )
        author_ids = set()
        for res in results["neighbors"]:
            r_authors = res[2]
            author_ids |= set(r_authors)
        query = {"field": "author", "ids": list(author_ids)}
        message = [3, query, 10]
        author_map = json.loads(serverquery(message))["neighbors"]
        if author.strip().isdigit():
            author = author_map[author]

        affiliation_ids = set()
        for res in results["neighbors"]:
            r_affiliations = res[6]
            affiliation_ids |= set(r_affiliations)
        query = {"field": "affiliation", "ids": list(affiliation_ids)}
        message = [3, query, 10]
        aff_map = json.loads(serverquery(message))["neighbors"]
        if affiliation.strip().isdigit():
            affiliation = aff_map[affiliation]

        return render_template(
            "rusnlp.html",
            result=results["neighbors"],
            conf_query=conference,
            author_query=author,
            year_query=year,
            search=True,
            url=url,
            query=title,
            affiliation_query=affiliation,
            descriptions=descriptions,
            topics=results["topics"],
            aff_map=aff_map,
            keywords=" ".join(keywords),
            author_map=author_map,
            other_lang=other_lang,
            languages=languages,
            years=year_dict
        )
    return render_template(
        "rusnlp.html",
        search=True,
        url=url,
        other_lang=other_lang,
        languages=languages,
        years=year_dict
    )


@nlpsearch.route("/" + "<lang:lang>/" + "publ/<fname>", methods=["GET", "POST"])
def paper(lang, fname):
    # pass all required variables to template
    # repeated within each @nlpsearch.route function
    g.lang = lang
    s = {lang}
    other_lang = list(set(language_dicts.keys()) - s)[0]  # works only for two languages
    g.strings = language_dicts[lang]

    if "." in fname or not fname:
        print("Error!", file=sys.stderr)
        return render_template(
            "rusnlp_paper.html",
            error="С вашим запросом что-то не так!",
            url=url,
            other_lang=other_lang,
            languages=languages,
        )

    query = fname.strip()
    topn = 10
    if request.method == "POST":
        try:
            topn = int(request.form["topn"])
        except ValueError:
            pass

    message = [1, query, topn]
    results = json.loads(serverquery(message))
    metadata = results["meta"]

    if "not found" in metadata or "unknown to the model" in results:
        return render_template(
            "rusnlp_paper.html",
            error="Статья с таким идентификатором не найдена в модели",
            search=True,
            url=url,
            topn=topn,
            other_lang=other_lang,
            languages=languages,
            metadata=metadata
        )

    else:
        author_ids = set(metadata["author"])
        for res in results["neighbors"]:
            r_authors = res[2]
            author_ids |= set(r_authors)
        query = {"field": "author", "ids": list(author_ids)}
        message = [3, query, 10]
        author_map = json.loads(serverquery(message))["neighbors"]

        affiliation_ids = set(metadata["affiliation"])
        for res in results["neighbors"]:
            r_affiliations = res[6]
            affiliation_ids |= set(r_affiliations)
        query = {"field": "affiliation", "ids": list(affiliation_ids)}
        message = [3, query, 10]
        aff_map = json.loads(serverquery(message))["neighbors"]

        topics = results["topics"]
        return render_template(
            "rusnlp_paper.html",
            aff_map=aff_map,
            result=results["neighbors"],
            metadata=metadata,
            search=True,
            url=url,
            author_map=author_map,
            topn=topn,
            topics=topics,
            other_lang=other_lang,
            languages=languages,
        )


@nlpsearch.route("/" + "<lang:lang>/" + "topical/")
def topical_page(lang):
    # pass all required variables to template
    # repeated within each @nlpsearch.route function
    g.lang = lang
    s = {lang}
    other_lang = list(set(language_dicts.keys()) - s)[0]  # works only for two languages
    g.strings = language_dicts[lang]

    return render_template(
        "/topical.html", url=url, other_lang=other_lang, languages=languages
    )


@nlpsearch.route("/" + "<lang:lang>/" + "about/")
def about_page(lang):
    # pass all required variables to template
    # repeated within each @nlpsearch.route function
    g.lang = lang
    s = {lang}
    other_lang = list(set(language_dicts.keys()) - s)[0]  # works only for two languages
    g.strings = language_dicts[lang]

    query = {"dummy": "dummy"}
    message = [4, query, 10]
    stats = json.loads(serverquery(message))["neighbors"]
    return render_template(
        "/about.html", url=url, other_lang=other_lang, languages=languages, stats=stats
    )


@nlpsearch.route("/poll/")
def poll_page():
    # pass all required variables to template
    # repeated within each @nlpsearch.route function
    g.lang = "ru"
    g.strings = language_dicts["ru"]
    return render_template("/poll.html", url=url, other_lang="ru", languages=languages)


# redirecting requests with no lang:
@nlpsearch.route(url, methods=["GET", "POST"], defaults={"path": ""})
@nlpsearch.route(url + "publ/<path:path>", methods=["GET", "POST"])
def redirect_main(path):
    req = request.path.split("/")[-2]
    if path:
        req += "/" + path
    if len(req) == 0:
        req = "/"
    else:
        # if req[-1] != '/':
        #    req += '/'
        if req[0] != "/":
            req = "/" + req
    return redirect(url + "ru" + req)


@nlpsearch.route("/api/<title>/<num>", methods=["GET"])
def nlp_api(title, num):
    mime = "application/json"
    query = title.strip().lower().replace("__", " ")
    number = int(num)
    if number > 100:
        number = 100
    message = "1;" + query + ";" + str(number)
    results = json.loads(serverquery(message))
    output = json.dumps(results, ensure_ascii=False)
    return Response(
        output.encode("utf-8"),
        mimetype=mime,
        headers={"Content-Disposition": "attachment;filename=rusnlp.json"},
    )
