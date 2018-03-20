#!/usr/bin/python3

import sys
import json

data = open(sys.argv[1]).read()

similarities = json.loads(data)

clusters = set()

for key in similarities:
    if len(similarities[key]) == 0:
        clusters.add(frozenset([key]))
    else:
        cluster = set()
        cluster.add(key)
        for similar in similarities[key]:
            cluster.add(similar)
            cluster.update(similarities[similar])
        cluster = frozenset(cluster)
        clusters.add(cluster)

for cluster in clusters:
    if len(cluster) > 1:
        print('\t'.join(cluster))

for cluster in clusters:
    if len(cluster) == 1:
       print('\t'.join(cluster))
