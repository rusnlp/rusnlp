#!/bin/bash

for i in ${1}/*.txt
do
    echo ${i}
    python3 lemmatize_udpipe_server.py -f ${i}
done