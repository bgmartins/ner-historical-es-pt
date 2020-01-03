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
parser.add_argument('file', metavar='FILE', type=str, nargs='+', help='An input text file to be processed')
parser.add_argument('query', metavar='QUERY', type=str, nargs='+', help='An input text file to be processed')
parser.add_argument('--concordance', dest='concordance', action='store_const', const=1, default=0, help='return concordances for the named entities (default: output HTML annotations)')

def n_concordance_tokenised(text,phrase,left_margin=5,right_margin=5):
    phraseList=phrase.split(' ')
    c = nltk.ConcordanceIndex(text.tokens, key = lambda s: s.lower())
    offsets=[c.offsets(x) for x in phraseList]
    offsets_norm=[]
    for i in range(len(phraseList)): offsets_norm.append([x-i for x in offsets[i]])
    intersects=set(offsets_norm[0]).intersection(*offsets_norm[1:])
    concordance_txt = ([text.tokens[map(lambda x: x-left_margin if (x-left_margin) > 0 else 0,[offset])[0]:offset+len(phraseList)+right_margin] for offset in intersects])
    outputs=[''.join([x+' ' for x in con_sub]) for con_sub in concordance_txt]
    return outputs

def n_concordance(txt,phrase,left_margin=5,right_margin=5):
    tokens = nltk.word_tokenize(txt)
    text = nltk.Text(tokens)
    return n_concordance_tokenised(text,phrase,left_margin=left_margin,right_margin=right_margin)

def main():
    args = parser.parse_args()
    nlp = spacy.load('es')
    text = open(args.FILE, "r").read()
    tokens = word_tokenize(text)
    textList = Text(tokens)
    result =  n_concordance_tokenised(textList, args.QUERY)
    print(result)
    
if __name__ == '__main__':
    main()