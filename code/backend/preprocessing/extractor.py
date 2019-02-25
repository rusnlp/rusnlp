from os import walk, path, makedirs
from shutil import copyfile
from pickle import dump, load
from platform import system
from hashlib import sha1
import json
import sys

path_to_dataset = sys.argv[1]



for root, dirs, files in walk(path_to_dataset):
    if root == './':
        continue
    print(root,dirs,files, file=sys.stderr)
    for f in sorted(files):
        if f == 'common.json':
            metadata = json.loads(open(path.join(root, f)).read())
            h = metadata['hash']
        elif f == 'text.txt':
            copyfile(path.join(root, f), path.join('./texts/', h + '.txt'))
