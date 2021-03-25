#!/usr/bin/env python3
# coding: utf-8

import requests
import json
import argparse
from smart_open import open


def tag_ud(port, text='Do not forget to pass some text as a string!'):
    # UDPipe tagging for any language you have a model for.
    # Requries UDPipe REST server (https://ufal.mff.cuni.cz/udpipe/users-manual#udpipe_server)
    # running on a pre-defined port
    # Start the server with something like:
    # udpipe_server --daemon 46666 MyModel MyModel /opt/my.model UD

    # Sending user query to the server:
    ud_reply = requests.post('http://localhost:%s/process' % port,
                             data={'tokenizer': '', 'tagger': '', 'data': text}).content

    # Getting the result in the CONLLU format:
    processed = json.loads(ud_reply.decode('utf-8'))['result']
    return processed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    arg = parser.add_argument
    arg(
        "--file2process",
        "-f",
        help="Path to a text file to process",
        type=str,
        required=True,
    )
    arg(
        "--port",
        "-p",
        help="UDPipe server port",
        type=int,
        default=46666,
    )
    args = parser.parse_args()

    file2process = args.file2process

    data = open(file2process)
    text2process = data.read()
    data.close()
    tagged = tag_ud(args.port, text2process)

    outfile = file2process.replace('.txt', '.conllu')
    out = open(outfile, 'w')
    out.write(tagged)
    out.close()
