import sys
import requests
import json


def tag_ud(port, text='Do not forget to pass some text as a string!'):
    # UDPipe tagging for any language you have a model for.
    # Demands UDPipe REST server (https://ufal.mff.cuni.cz/udpipe/users-manual#udpipe_server)
    # running on a port defined in webvectors.cfg
    # Start the server with something like:
    # udpipe_server --daemon 66666 MyModel MyModel /opt/my.model UD

    # Sending user query to the server:
    ud_reply = requests.post('http://localhost:%s/process' % port,
                             data={'tokenizer': '', 'tagger': '', 'data': text}).content

    # Getting the result in the CONLLU format:
    processed = json.loads(ud_reply.decode('utf-8'))['result']
    return processed


file2process = sys.argv[1]

data = open(file2process)
text2process = data.read()
data.close()
tagged = tag_ud(66666, text2process)

outfile = file2process.replace('.txt', '.conll')
out = open(outfile, 'w')
out.write(tagged)
out.close()
