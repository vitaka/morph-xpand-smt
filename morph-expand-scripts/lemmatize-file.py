import sys,codecs, gzip, argparse, itertools
from morphExpansionUtils import Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="Lemmatize text file. INput is made of 2 files surface forms and tags")
parser.add_argument("--lexicon")
parser.add_argument("surface_f")
parser.add_argument("tagged_f")
args = parser.parse_args()

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')))

for linelist in itertools.izip(codecs.open(args.surface_f,'r',ENCODING),codecs.open(args.tagged_f,'r',ENCODING)):
	linesf=linelist[0].rstrip(u"\n")
	linetag=linelist[1].rstrip(u"\n")
	sftokens=linesf.split(u" ")
	tags=linetag.split(u" ")
	outToks=[]
	for sf,tag in zip(sftokens,tags):
		lemma=lexicon.getLemma(sf,tag)
		if lemma == None:
			lemma=u"Unk"
		outToks.append(lemma+u"|"+tag)
	print u" ".join(outToks).encode(ENCODING)
