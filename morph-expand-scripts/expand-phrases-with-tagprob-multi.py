import sys,codecs, gzip, argparse, itertools
from morphExpansionUtils import TagGroupsMulti,Lexicon
ENCODING="utf-8"

parser=argparse.ArgumentParser(description="replace inflected forms with lemmas and set of possible tags")
parser.add_argument("--lexicon")
parser.add_argument("--tag_groups")
parser.add_argument("--tag_freqs")
parser.add_argument("--join_same_surface", action='store_true')
parser.add_argument("--use_cond_prob", action='store_true')
args = parser.parse_args()

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 1)
tagGroups=TagGroupsMulti(codecs.open(args.tag_groups,'r',ENCODING))
tagGroups.buildProbs(codecs.open(args.tag_freqs,'r',ENCODING))

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split("\t")
	#parts[1] is TL side of phrase table
	#parts[1] is TL side of phrase table
	tltokens=parts[1].split(" ")
	tltokensSplit=[t.split("|") for t in tltokens]
	lemma_l=[t[0] for t in tltokensSplit]

	#this is a list of lists of the same length.
	morphTag_l=[t[1].split(u"__") for t in tltokensSplit]

	#we will only modify first token
	#firsttokenparts=tltokens[0].split(u"|")
	#lemma=firsttokenparts[0]
	#morphTags=firsttokenparts[1].split(u"__")

	originalphraseprobs=[float(p) for p in parts[2].split(" ")]
	originalphraseCounts=[float(p) for p in parts[4].split(" ")]
	originalTLLexCount=float(parts[5].split(u" ")[1])
	if not args.join_same_surface:
		for altSequenceIndex in range(len(morphTag_l[0])):
			morphTagseq=[ ml[altSequenceIndex] for ml in morphTag_l ]
			surface_l=[lexicon.getSurface(lemma,morphTag) for lemma,morphTag in zip(lemma_l,morphTagseq) ]
			if all(surface != None for surface in surface_l):
				tagProb=tagGroups.getProb(morphTagseq)
				if args.use_cond_prob:
					initialTagProb=tagProb
					tagProbOfObserved=0.0
					originPhrases = parts[-1]
					originPhrasesWords=originPhrases.split(" ")
					originTags_ll = []
					for word in originPhrasesWords:
						originTags_ll.append( [w.split("|")[1] for w in word.split("__")] )
					originTagSeqs=[]
					for i in range(len(originTags_ll[0])):
						originTagSeqs.append([ tagl[i] for tagl in originTags_ll  ])
					for originTagSeq in originTagSeqs:
						tagProbOfObserved+=tagGroups.getProb(originTagSeq)
					# tp observed = 0.4
					# tp generated = 0.2
					#  prob observed = 0.33
					#  prob generated = 0.33 * 0.2/0.4 = 0.165
					tagProb=initialTagProb/tagProbOfObserved

				if originalphraseprobs[0] > 0 and originalphraseprobs[1] > 0 and originalphraseprobs[2]*tagProb > 0 and originalphraseprobs[3]*tagProb > 0:
					parts[2]=u" ".join([ unicode(originalphraseprobs[0]), unicode(originalphraseprobs[1]), unicode(min(1.0,originalphraseprobs[2]*tagProb)), unicode(min(1.0,originalphraseprobs[3]*tagProb)) ])
					parts[4]=u" ".join([ unicode(originalphraseCounts[0]) , unicode( min(1.0,originalphraseCounts[1]*tagProb)), unicode( min(1.0,originalphraseCounts[2]*tagProb)) ])
					#multiply tl lex count by prob of tag
					parts[5]=u"0.0 "+unicode(originalTLLexCount*tagProb)
					#Cartesian product, since we may obtain more than one surface form
					for aSurface_l in itertools.product(*surface_l):
						for i in range(len(aSurface_l)):
							tltokens[i]=aSurface_l[i]+u"|"+morphTagseq[i]
						parts[1]=u" ".join(tltokens)
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
