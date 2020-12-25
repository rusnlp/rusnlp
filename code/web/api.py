#!/usr/bin/env python3
# coding: utf-8

import configparser
import json
import logging
import socket
import sys
from nlp import *
from flasgger import swag_from
from flask import render_template, Blueprint, redirect
from flask import request, Response
from flask import g
from strings_reader import language_dicts


config = configparser.RawConfigParser()
config.read("rusnlp.cfg")
root = config.get("Files and directories", "root")
languages_list = config.get("Languages", "interface_languages").split(",")
languages = "/".join(list(language_dicts.keys())).upper()
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
        print(reply)
        reply += s.recv(65536)
    s.close()
    reply = reply.decode("utf-8")[:-3]
    return reply



api_bp = Blueprint("api", __name__, template_folder="templates")

@nlpsearch.route("/" + "<lang:lang>/" + "/api", methods=["GET"])
def ap_doc(lang):
    g.lang = lang
    s = {lang}
    other_lang = list(set(language_dicts.keys()) - s)[0]  # works only for two languages
    g.strings = language_dicts[lang]
    return render_template('swagger.html', languages=languages)


@api_bp.after_request
def per_request_callbacks(response):
    for func in getattr(g, "call_after_request", ()):
        response = func(response)
    return response


@api_bp.route("/api/get_statistics", methods=["GET"])
def api_get_statistics():
    query = {"dummy": "dummy"}
    message = [4, query, 10]
    # results = json.loads(serverquery(message))
    return serverquery(message)

@api_bp.route("/api/keywords", methods=["GET", "POST"])
def api_search_keywords():
    query_string = request.data.decode()
    query = json.loads(query_string)
    message = [2, query, 10]
    return serverquery(message)