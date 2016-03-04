import sys, argparse, codecs, gzip
from collections import defaultdict
from morphExpansionUtils import Lexicon
ENCODING="utf-8"
ENTRYSEPARATOR=u" ||| "


def process_group(lines, lexicon, tagFreqs):
	#2. just print multi-word entries in the TL
	multiwordEntries=[ line for line in lines if len(line[1].split(u" ") ) > 1 ]
	for mwEntry in multiwordEntries:
		print ENTRYSEPARATOR.join(mwEntry).encode(ENCODING)

	#3. group entries with the same TL lemma
	monowordEntries=[ line for line in lines if len(line[1].split(u" ") ) == 1 ]
	entriesByTLLemma=defaultdict(list)
	for monowordEntry in monowordEntries:
		tlsideparts=monowordEntry[1].split(u"|")
		lemma=lexicon.getLemma(tlsideparts[0],tlsideparts[1])
		if lemma != None:
			entriesByTLLemma[lemma].append(monowordEntry)
		else:
			print ENTRYSEPARATOR.join(monowordEntry).encode(ENCODING)

	#4. re-assign probs for each group
	for lemma in entriesByTLLemma:
		entries=entriesByTLLemma[lemma]
		tags=[]
		probs=[]
		for entry in entries:
			probs.append([ float(n) for n in entry[2].split(u" ") ] )
			tags.append(entry[1].split(u"|")[1])

		totalPhraseProb=sum( prob[2] for prob in probs )
		totalLexProb=sum(prob[3] for prob in probs )
		totalTagFreq=sum([ tagFreqs[tag] for tag in tags if tag in tagFreqs ])

		if totalTagFreq == 0:
			#just print
			for entry in entries:
				print ENTRYSEPARATOR.join(entry).encode(ENCODING)
		else:
			#actual prob reassignment
			for i in range(len(entries)):
				tag=tags[i]
				tagFreq=0
				if tag in tagFreqs:
					tagFreq=tagFreqs[tag]
				proportion=tagFreq*1.0/totalTagFreq
				phraseProb=proportion*totalPhraseProb
				lexProb=proportion*totalLexProb
				if phraseProb > 0 and lexProb > 0:
					#print line after prob reassignment
					entry=entries[i]
					probs[i][2]=phraseProb
					probs[i][3]=lexProb
					entry[2]=u" ".join( [ unicode(p) for p in probs[i] ] )
					print ENTRYSEPARATOR.join(entry).encode(ENCODING)


parser=argparse.ArgumentParser(description="recalculate direct probs accroding to tag frequency")
parser.add_argument("--lexicon")
parser.add_argument("--debug",action='store_true')
parser.add_argument("--tag_freqs")
args = parser.parse_args()

#load lexicon and tag freqs
myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 0)

tagFreqs=dict()
for line in open(args.tag_freqs):
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split(u"\t")
	freq=int(parts[0])
	tag=parts[1]
	tagFreqs[tag]=freq

#1. we group entries with the same SL side
#2. just print multi-word entries in the TL
#3. group entries with the same TL lemma
#4. re-assign probs for each group

curSL=None
curList=[]

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split(ENTRYSEPARATOR)

	lineSL=line[0]
	if lineSL != curSL:
		if len(curList) > 0:
			process_group(curList, lexicon, tagFreqs)
		curList=[]
	curList.append(parts)
	curSL=lineSL
if len(curList) > 0:
	process_group(curList, lexicon, tagFreqs)
