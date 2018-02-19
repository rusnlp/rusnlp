#!/bin/bash

for i in ../../prepared-data/pickles/group_by_data/years/*en.pickle 
do
    ./years.py ${i} ../../prepared-data/texts-en-lemma-udpipe > ${i}.txt
done

