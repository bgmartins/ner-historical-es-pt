from __future__ import unicode_literals

import sys
import os
import spacy
import argparse
import re
import itertools
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.text import Text

parser = argparse.ArgumentParser(description='Process concordance queries.')
parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='An input text file to be processed')
parser.add_argument('--concordance', dest='concordance', action='store_const', const=1, default=0, help='return concordances for the named entities (default: output HTML annotations)')

def main():
    if not sys.argv[1]: return
    # read text
    text = open(sys.argv[1], "r").read()
    tokens = word_tokenize(text)
    textList = Text(tokens)
    textList.concordance('is')
    print(tokens)

if __name__ == '__main__':
    main()
