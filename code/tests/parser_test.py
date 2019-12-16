import unittest
import os
from code.backend.preprocessing.parser.parser import Parser


class ParserTest(unittest.TestCase):
    def test(self):
        p = Parser()
        p.parse('/Users/amir/Documents/projects/rusnlp/rusnlp/code/tests/data/dataset_test/conferences')
        print(p.result)
