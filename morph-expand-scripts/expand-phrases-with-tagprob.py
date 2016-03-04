import sys,codecs, gzip, argparse
from morphExpansionUtils import TagGroups,Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--lexicon")
parser.add_argument("--tag_groups")
parser.add_argument("--tag_freqs")
parser.add_argument("--join_same_surface", action='store_true')
args = parser.parse_args()

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 1)
tagGroups=TagGroups(codecs.open(args.tag_groups,'r',ENCODING))
tagGroups.buildProbs(codecs.open(args.tag_freqs,'r',ENCODING))

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#parts[1] is TL side of phrase table
	tltokens=parts[1].split(" ")
	#we will only modify first token
	firsttokenparts=tltokens[0].split(u"|")
	lemma=firsttokenparts[0]
	morphTags=firsttokenparts[1].split(u"__")
	originalphraseprobs=[float(p) for p in parts[2].split(" ")]
	originalphraseCounts=[float(p) for p in parts[4].split(" ")]
	originalTLLexCount=float(parts[5].split(u" ")[1])
	if not args.join_same_surface:
		for morphTag in morphTags:
			surface_l=lexicon.getSurface(lemma,morphTag)
			if surface_l != None:
				for surface in surface_l:
					if surface != None:
						tagProb=tagGroups.getProb(morphTag)
						tltokens[0]=surface+u"|"+morphTag
						parts[1]=u" ".join(tltokens)
						parts[2]=u" ".join([ unicode(originalphraseprobs[0]), unicode(originalphraseprobs[1]), unicode(originalphraseprobs[2]*tagProb), unicode(originalphraseprobs[3]*tagProb) ])
						parts[4]=u" ".join([ unicode(originalphraseCounts[0]) , unicode(originalphraseCounts[1]*tagProb), unicode(originalphraseCounts[2]*tagProb) ])
						#multiply tl lex count by prob of tag
						parts[5]=u"0.0 "+unicode(originalTLLexCount*tagProb)
						if originalphraseprobs[0] > 0 and originalphraseprobs[1] > 0 and originalphraseprobs[2]*tagProb > 0 and originalphraseprobs[3]*tagProb > 0:
							print u"\t".join(parts).encode(ENCODING)
	else:
		tltokens=[t.split(u"|")[0] for t in tltokens]
		surfaceToSumTagProbs=dict()
		for morphTag in morphTags:
			surface=lexicon.getSurface(lemma,morphTag)
			if surface != None:
				tagProb=tagGroups.getProb(morphTag)
				if not surface in surfaceToSumTagProbs:
					surfaceToSumTagProbs[surface]=0.0
				surfaceToSumTagProbs[surface]=surfaceToSumTagProbs[surface]+tagProb
		for surface in surfaceToSumTagProbs:
			tagProb=surfaceToSumTagProbs[surface]
			tltokens[0]=surface
			parts[1]=u" ".join(tltokens)
			parts[2]=u" ".join([ unicode(originalphraseprobs[0]), unicode(originalphraseprobs[1]), unicode(originalphraseprobs[2]*tagProb), unicode(originalphraseprobs[3]*tagProb) ])
			parts[4]=u" ".join([ unicode(originalphraseCounts[0]) , unicode(originalphraseCounts[1]*tagProb), unicode(originalphraseCounts[2]*tagProb) ])
			#multiply tl lex count by prob of tag
			parts[5]=u"0.0 "+unicode(originalTLLexCount*tagProb)

			#print only if all the phrase probs > 0:
			if originalphraseprobs[0] > 0 and originalphraseprobs[1] > 0 and originalphraseprobs[2]*tagProb > 0 and originalphraseprobs[3]*tagProb > 0:
				print u"\t".join(parts).encode(ENCODING)
