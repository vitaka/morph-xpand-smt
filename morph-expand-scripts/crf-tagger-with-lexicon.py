import sys
from train_tagger import extract_features_msd
import cPickle as pickle
import pycrfsuite
import argparse, codecs, gzip
from morphExpansionUtils import Lexicon
import itertools
import kenlm

ENCODING="utf-8"
UNKTAG="Unk"
SPECIALTAGS=set(['X','Xf','Y','Z'])

parser=argparse.ArgumentParser(description="Tag hr corpus with crf tagger. Tag as unknown words not found in the lexicon. Do not tag words present in the lexicon with different tags. Corpus should be truecased")
parser.add_argument("--lexicon", default='/home/vmsanchez/zagreb-2016/morphological-expansion/linguistic-data/apertium-hbs.hbs_HR_purist.mte.gz')
parser.add_argument("--tagger_model", default='/home/nikola/tools/tagger/hr/hr.msd.model')
parser.add_argument("--trie", default='/home/nikola/tools/tagger/hr/hr.marisa')
parser.add_argument("--ngram_model", default='/home/vmsanchez/zagreb-2016/morphological-expansion/re-tagging/ngram-model-for-constraining/model.blm')
parser.add_argument("--debug", action='store_true')
parser.add_argument("--disable_unk", action='store_true')
args = parser.parse_args()

myreader=codecs.getreader(ENCODING)
lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')), 2)
numTokensRetagged=0
tagger=pycrfsuite.Tagger()
tagger.open(args.tagger_model)
trie=pickle.load(open(args.trie))

lm= kenlm.LanguageModel(args.ngram_model)

labels=set(tagger.labels())

for line in sys.stdin:
	inputTokens=line.decode(ENCODING).strip().split(' ')
	predictedTags=tagger.tag(extract_features_msd(inputTokens,trie))
	tagsByLexicon=[]
	for token in inputTokens:
		analyses=lexicon.getLemmaTag(token)
		tags=set()
		if analyses != None:
			for lemma,tag in analyses:
				tags.add(tag)
		tagsByLexicon.append(tags)
	positionsWithMultipleTags=[]
	valuesOfMultipleTags=[]

	for i in xrange(len(inputTokens)):
		if predictedTags[i] not in tagsByLexicon[i] and len(tagsByLexicon[i]) > 0 and predictedTags[i] not in SPECIALTAGS:
			filteredTagsByLexicon=[tag for tag in tagsByLexicon[i] if tag in labels]
			tagsByLexicon[i]=filteredTagsByLexicon
			if len(filteredTagsByLexicon) > 0:
				positionsWithMultipleTags.append(i)
				valuesOfMultipleTags.append(tagsByLexicon[i])
				if args.debug:
					print >>sys.stderr, (u"WARNING: tag "+predictedTags[i]+" for token "+inputTokens[i]+" at postion "+unicode(i)+" of sentence "+u" ".join(inputTokens)+" not found in lexicon ("+u",".join(tagsByLexicon[i])+u")").encode(ENCODING)
	if len(positionsWithMultipleTags) == 0:
		chosenTags=predictedTags
	else:
		chosenTags=list(predictedTags)
		#we have to re-interrogate the model with all the possible combinations
		for i in xrange(len(positionsWithMultipleTags)):
			numTokensRetagged+=1
			position=positionsWithMultipleTags[i]
			possibleTags=valuesOfMultipleTags[i]
			hypothesesToScore=[]
			for tag in possibleTags:
				hyp=list(chosenTags)
				hyp[position]=tag
				hypothesesToScore.append(hyp)
			scoredHyps=[]
			for hyp in hypothesesToScore:
				prob=lm.score(u" ".join(hyp))
				scoredHyps.append((prob,hyp))
			sortedHyps=sorted(scoredHyps, key=lambda h: h[0], reverse=True)
			chosenTag=sortedHyps[0][1][position]
			chosenTags[position]=chosenTag
		if args.debug:
			print >>sys.stderr, "Sentence original: "+ u" ".join( e[0]+u"|"+e[1] for e in zip(inputTokens,predictedTags) ).encode(ENCODING)
			print >>sys.stderr, "Sentence lexiconf: "+ u" ".join( e[0]+u"|"+e[1] for e in zip(inputTokens,chosenTags) ).encode(ENCODING)

	if not args.disable_unk:
		for i in xrange(len(inputTokens)):
			if len(tagsByLexicon[i]) == 0 and predictedTags[i] not in SPECIALTAGS:
				chosenTags[i]=UNKTAG
	print ' '.join(chosenTags)

print >> sys.stderr, "Number of tokens retagged:	"+str(numTokensRetagged)
