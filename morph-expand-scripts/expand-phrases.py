import sys,codecs, gzip, argparse
from morphExpansionUtils import TagGroups,Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--lexicon")
parser.add_argument("--join_same_surface", action='store_true')
args = parser.parse_args()

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 1)

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#parts[1] is TL side of phrase table
	tltokens=parts[1].split(" ")
	#we will only modify first token
	firsttokenparts=tltokens[0].split(u"|")
	lemma=firsttokenparts[0]
	morphTags=firsttokenparts[1].split(u"__")
	generatedSurfaces=set()
	for morphTag in morphTags:
		surface=lexicon.getSurface(lemma,morphTag)
		if surface != None and (args.join_same_surface == False or surface not in generatedSurfaces):
			tltokens[0]=surface+u"|"+morphTag
			if args.join_same_surface:
				parts[1]=u" ".join(token.split(u"|")[0] for token in tltokens)
			else:
				parts[1]=u" ".join(tltokens)
			#We print TL lex count sum, the same for all entries
			print u"\t".join(parts).encode(ENCODING)
			generatedSurfaces.add(surface)
