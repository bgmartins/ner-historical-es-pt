from __future__ import unicode_literals

import nltk
import sys
import os
import spacy
import argparse
import re
import itertools
import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.text import Text

parser = argparse.ArgumentParser(description='a simple command line script to process concordance queries')
parser.add_argument('query', metavar='QUERY', type=str, nargs='+', help='list of query terms')
parser.add_argument('-i','--input', help='input file name', required=True)
parser.add_argument('-o','--output', help='output file name', default="stdout")
parser.add_argument('-l','--left-margin', help='left context length', default=5)
parser.add_argument('-r','--right-margin', help='right context length', default=5)

def n_concordance_tokenised(text,phrase,left_margin=1,right_margin=1):
    phraseList=phrase.split(' ')
    c = nltk.ConcordanceIndex(text.tokens, key = lambda s: s.lower())
    offsets=[c.offsets(x) for x in phraseList]
    offsets_norm=[]
    for i in range(len(phraseList)): offsets_norm.append([x-i for x in offsets[i]])
    intersects=set(offsets_norm[0]).intersection(*offsets_norm[1:])
    outputs = intersects
    for offset in intersects:
        concordance_txt_left = [ ]
        concordance_txt_right = [ ]
        concordance_txt_middle = [ ]
        start_offset = offset - left_margin if (offset - left_margin) > 0 else 0
        end_offset = offset + len(phraseList) + right_margin
        for x in range(start_offset,offset): concordance_txt_left += [ text.tokens[x] ]
        for x in range(offset + len(phraseList) ,end_offset): concordance_txt_right += [ text.tokens[x] ]
        for x in range(offset , offset + len(phraseList)): concordance_txt_middle += [ text.tokens[x] ]        
        yield ' '.join(concordance_txt_left), ' '.join(concordance_txt_middle), ' '.join(concordance_txt_right)

def n_concordance(txt,phrase,left_margin=5,right_margin=5):
    tokens = nltk.word_tokenize(txt)
    text = nltk.Text(tokens)
    return n_concordance_tokenised(text,phrase,left_margin=left_margin,right_margin=right_margin)

def main():
    args = parser.parse_args()
    args.query = ' '.join(args.query)
    #nlp = spacy.load('es')
    text = open(args.input, "r").read()
    tokens = word_tokenize(text)
    textList = Text(tokens)
    result =  n_concordance_tokenised(textList, args.query, left_margin=args.left_margin,right_margin=args.right_margin)
    if args.output == "stdout": 
        for r in result: print(r)
    else:
        output = open(args.output, "w")
        pd.DataFrame(result).to_excel(args.output)

if __name__ == '__main__':
    main()
