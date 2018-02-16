import spacy
import argparse
import re
from spacy import displacy
from spacy.lang.es import Spanish

parser = argparse.ArgumentParser(description='Process text files and recognize named entities.')
parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='an input file to be processed')
parser.add_argument('--concordance', dest='concordance', action='store_const', const=1, default=0, help='return concordances for the named entities (default: output HTML annotations)')

args = parser.parse_args()
nlp = spacy.load('es')

concordance_context = 5

for filename in args.files:
    document = open(filename,encoding='utf8').read()
    document = nlp(document)
    if args.concordance == 0:
        html = displacy.render(document, style='ent', page=True)
        html = html.replace("<title>displaCy</title>", "<title>displaCy</title><meta charset='UTF-8'>",1)
        html_file = open(filename + ".html", "w",encoding='utf8')
        html_file.write(html)
        html_file.close()
    elif args.concordance == 1:
        text = str(document.text)
        text_file = open(filename + ".concordance", "w",encoding='utf8')
        for e in document.ents:
            entity = re.sub('[\s+]', ' ', e.string).strip()
            if len(entity) == 0: continue
            start = e.start_char
            end = e.end_char            
            while ( start > 0 and len(re.sub('[\s+]', ' ', text[start:e.end_char]).strip().split()) < concordance_context + 1): start = start - 1
            while ( end < len(text) and len(re.sub('[\s+]', ' ', text[e.end_char:end]).strip().split()) < concordance_context + 1 ): end = end + 1
            if start < e.start_char: start = start + 1
            if end > e.end_char: end = end - 1
            label = e.label_
            concordance = re.sub('[\s+]', ' ', text[start:end]).strip()
            text_file.write(label + "\t\t" + entity + "\t\t" + concordance + "\n")
        text_file.close()
#    else:
#        labels = set([w.label_ for w in document.ents]) 
#        for label in labels: 
#            entities = [cleanup(e.string, lower=False) for e in document.ents if label==e.label_] 
#            entities = list(set(entities)) 
#            print(label,entities)
#        for np in doc.noun_chunks:
#            print(np.text, np.root.dep_, np.root.head.text)

