import spacy
import argparse
import re
import itertools
from spacy import displacy
from spacy.lang.es import Spanish

parser = argparse.ArgumentParser(description='Process text files and recognize named entities.')
parser.add_argument('files', metavar='FILE', type=str, nargs='+', help='an input file to be processed')
parser.add_argument('--concordance', dest='concordance', action='store_const', const=1, default=0, help='return concordances for the named entities (default: output HTML annotations)')

args = parser.parse_args()
nlp = spacy.load('es')

concordance_context = 5

def noun_chunks(doc, drop_determiners=True, min_freq=1):
    """
    Extract an ordered sequence of noun chunks from a spacy-parsed doc, optionally filtering by frequency and dropping leading determiners.
    Args:
        doc (``textacy.Doc`` or ``spacy.Doc``)
        drop_determiners (bool): remove leading determiners (e.g. "the") from phrases (e.g. "the quick brown fox" => "quick brown fox")
        min_freq (int): remove chunks that occur in `doc` fewer than min_freq` times
    Yields:
        ``spacy.Span``: the next noun chunk from ``doc`` in order of appearance in the document
    """
    if hasattr(doc, 'spacy_doc'): ncs = doc.spacy_doc.noun_chunks
    else: ncs = doc.noun_chunks
    if drop_determiners is True:
        ncs = (nc if nc[0].pos != DET else nc[1:] for nc in ncs)
    if min_freq > 1:
        ncs = list(ncs)
        freqs = itertoolz.frequencies(nc.lower_ for nc in ncs)
        ncs = (nc for nc in ncs if freqs[nc.lower_] >= min_freq)
    for nc in ncs: yield nc

def semistructured_statements(doc, entity, cue='be', ignore_entity_case=True, min_n_words=1, max_n_words=20):
    """
    Extract "semi-structured statements" from a spacy-parsed doc, each as a (entity, cue, fragment) triple. This is similar to subject-verb-object triples.
    Args:
        doc (``textacy.Doc`` or ``spacy.Doc``)
        entity (str): a noun or noun phrase of some sort (e.g. "President Obama", "global warming", "Python")
        cue (str): verb lemma with which `entity` is associated (e.g. "talk about", "have", "write")
        ignore_entity_case (bool): if True, entity matching is case-independent
        min_n_words (int): min number of tokens allowed in a matching fragment
        max_n_words (int): max number of tokens allowed in a matching fragment
    Yields:
        (``spacy.Span`` or ``spacy.Token``, ``spacy.Span`` or ``spacy.Token``, ``spacy.Span``): where each element is a matching (entity, cue, fragment) triple
    Notes:
        Inspired by N. Diakopoulos, A. Zhang, A. Salway. Visual Analytics of Media Frames in Online News and Blogs. IEEE InfoVis Workshop on Text Visualization. October, 2013.
    """
    if ignore_entity_case is True:
        entity_toks = entity.lower().split(' ')
        get_tok_text = lambda x: x.lower_
    else:
        entity_toks = entity.split(' ')
        get_tok_text = lambda x: x.text
    first_entity_tok = entity_toks[0]
    n_entity_toks = len(entity_toks)
    cue = cue.lower()
    cue_toks = cue.split(' ')
    n_cue_toks = len(cue_toks)
    def is_good_last_tok(tok):
        if tok.is_punct: return False
        if tok.pos in {CONJ, DET}: return False
        return True
    for sent in doc.sents:
        for tok in sent:
            if get_tok_text(tok) != first_entity_tok: continue
            if n_entity_toks == 1:
                the_entity = tok
                the_entity_root = the_entity
            if tok.i + n_cue_toks >= len(doc): continue
            elif all(get_tok_text(tok.nbor(i=i + 1)) == et for i, et in enumerate(entity_toks[1:])):
                the_entity = doc[tok.i: tok.i + n_entity_toks]
                the_entity_root = the_entity.root
            else: continue
            terh = the_entity_root.head
            if terh.lemma_ != cue_toks[0]: continue
            if n_cue_toks == 1:
                min_cue_i = terh.i
                max_cue_i = terh.i + n_cue_toks
                the_cue = terh
            elif all(terh.nbor(i=i + 1).lemma_ == ct for i, ct in enumerate(cue_toks[1:])):
                min_cue_i = terh.i
                max_cue_i = terh.i + n_cue_toks
                the_cue = doc[terh.i: max_cue_i]
            else: continue
            if the_entity_root in the_cue.rights: continue
            try: min_cue_i = min(left.i for left in itertools.takewhile( lambda x: x.dep_ in {'aux', 'neg'}, reversed(list(the_cue.lefts))))
            except ValueError: pass
            try: max_cue_i = max(right.i for right in itertools.takewhile( lambda x: x.dep_ in {'aux', 'neg'}, the_cue.rights))
            except ValueError: pass
            if max_cue_i - min_cue_i > 1: the_cue = doc[min_cue_i: max_cue_i]
            else: the_cue = doc[min_cue_i]
            try:
                min_frag_i = min(right.left_edge.i for right in the_cue.rights)
                max_frag_i = max(right.right_edge.i for right in the_cue.rights)
            except ValueError: continue
            while is_good_last_tok(doc[max_frag_i]) is False: max_frag_i -= 1
            n_fragment_toks = max_frag_i - min_frag_i
            if n_fragment_toks <= 0 or n_fragment_toks < min_n_words or n_fragment_toks > max_n_words: continue
            if min_frag_i == max_cue_i - 1: min_frag_i += 1
            the_fragment = doc[min_frag_i: max_frag_i + 1]
            yield (the_entity, the_cue, the_fragment)


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
        text_file = open(filename + ".concordance.html", "w",encoding='utf8')
        text_file.write("<html>")
        text_file.write("<head><meta charset='UTF-8' /></head>")
        text_file.write("<body>")
        text_file.write("<div id='concordances'>")
        text_file.write("<input class='search' placeholder='Search' />")
        text_file.write("<button class='sort' data-sort='entity'>Sort</button>")
        text_file.write("<button class='sort' data-sort='type'>Sort</button>")
        text_file.write("<ul style='list-style: none;' class='list'>")
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
            concordance1 = re.sub('[\s+]', ' ', text[start:e.start_char]).strip()
            concordance2 = re.sub('[\s+]', ' ', text[e.end_char:end]).strip()
            text_file.write("<li>")
            text_file.write("<span style='float:left; width:25%;'>" + concordance1 + "</span>")
            text_file.write("<span style='float:left; width:25%; border: thin solid black' class='entity'>" + entity + "</span>")
            text_file.write("<span style='float:left; width:25%; border: thin solid black' class='type'>" + label + "</span>")
            text_file.write("<span style='float:left; width:25%;'>" + concordance2 + "</span>")
            text_file.write("</li>")
        text_file.write("</ul>")
        text_file.write("<br/>")
        text_file.write("<ul style='list-style: none;' class='pagination'></ul>")
        text_file.write("</div>")
        text_file.write("<script src='../list.min.js'></script>")
        text_file.write("<script type='text/javascript'>")
        text_file.write("var opts = { valueNames: [ 'entity', 'type' ], page: 25, pagination: true };")
        text_file.write("var userList = new List('concordances', opts);")
        text_file.write("</script>")
        text_file.write("</body>")
        text_file.write("</html>")
        text_file.close()
#    else:
#        labels = set([w.label_ for w in document.ents]) 
#        for label in labels: 
#            entities = [cleanup(e.string, lower=False) for e in document.ents if label==e.label_] 
#            entities = list(set(entities)) 
#            print(label,entities)
#        for np in doc.noun_chunks:
#            print(np.text, np.root.dep_, np.root.head.text)

