#!/usr/bin/python3

import sys

for line in sys.stdin:
    res = line.strip().split('\t')
    if len(res) > 0:
        variants = set(res)
        print('\t'.join(variants))
