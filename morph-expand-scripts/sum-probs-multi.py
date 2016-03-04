import sys, codecs, argparse
ENCODING="utf-8"

#Sum the probs of all the entries with the same SL and TL side
#each element of the input contains:
#0: sl phrase
#1: lemmatized tl phrase
#2: original tl phrase
#3: following probs split by space: p(sl|tl) p_lex(sl|tl) p(tl|sl) p_lex(tl|sl)
#4: aligments
#5: phrase counts: count_tl count_sl count_cooc
#6: empty? lex counts?
#7: empty
#
# Values of the resulting entry will be
# 0: input sl phrase
# 1: lemmatized tl phrase
# 2: probs, computed as follows:
#	- p(sl|tl): (sum of all count_cooc )/(sum of all count_tl)
#	- p_lex(sl|tl): product, for each SL word s:  p(s|NULL) if not aligned else: sum_for_each_tl_aligned( 1/numtlaligned * sum_for_each_line( p_lex( s|tl ) * count( tl)  )/sum_for_each_line(count(tl))  )
#	- p(tl|sl): sum of all p(tl|sl)
#	- p_lex(tl|sl): product, for each TL word (include null alignments), of {  1/(num sl words aligned) * sum(lex.f2e for all tls being combined)  }
# 3: alignments, from the first line
# 4: phrase counts, computed as follows:
#	- count_tl: sum of all count_tl
#	- count_sl: same as last line
#	- count_cooc: sum of all count_cooc
# 5: empty at the moment
# 6: empty
#


#This is how lexical translation probability is originally computed by Moses
#// lexical translation probability
#  double lexScore = 1.0;
#  int null = vcbS.getWordID("NULL");
#  // all target words have to be explained
#  for(size_t ti=0; ti<alignmentTargetToSource->size(); ti++) {
#    const set< size_t > & srcIndices = alignmentTargetToSource->at(ti);
#    if (srcIndices.empty()) {
#      // explain unaligned word by NULL
#      lexScore *= lexTable.permissiveLookup( null, phraseTarget->at(ti) );
#    } else {
#      // go through all the aligned words to compute average
#      double thisWordScore = 0;
#      for (set< size_t >::const_iterator p(srcIndices.begin()); p != srcIndices.end(); ++p) {
#        thisWordScore += lexTable.permissiveLookup( phraseSource->at(*p), phraseTarget->at(ti) );
#      }
#      lexScore *= thisWordScore / (double)srcIndices.size();
#    }
 # }
  #return lexScore;

def processList(mylist,lexcountsDict,lexcountsSlDict,lexf2eDict, lexe2fDict):
	if lexcountsDict == None:
		for i in xrange(len(mylist)):
			mylist[i]=mylist[i][0:2]+[u""]+mylist[i][2:]

	sumCountTL=0.0
	sumCountCooc=0.0
	countSL=0.0

	sumProbDirect=0.0
	sumProbDirectLex=0.0

	#parse alogignments
	alignments=[]
	for alstr in mylist[0][4].split(" "):
		splitbyhyphen=alstr.split("-")
		alignments.append((int(splitbyhyphen[0]), int(splitbyhyphen[1]) ))

	#one for alignment: intialised right now
	alslwords=[]
	allslwords=mylist[0][0].split(u" ")
	for al in alignments:
		alslwords.append( allslwords[al[0]]  )

	#a list per alignment: empty intialised
	altlwords=[]
	for al in alignments:
		altlwords.append([])

	#List, that contains as many elements as TL words
	#For each TL word, contains a list. Each element of the list represents the aligned words in one line being combined
	#the aligned words in one line is also a list
	alignedWithTLWords=[]
	for i in range(len(mylist[0][2].split(" "))):
		alignedWithTLWords.append([])

	#List indexes aligned with each SL word (we will look only at alignments of first phrase being combined)
	alignedWithSLWordsIndexes=[]
	for i in range(len(allslwords)):
		alignedWithSLWordsIndexes.append([])
	for sli,tli in alignments:
		alignedWithSLWordsIndexes[sli].append(tli)

	#list of lists: each element is a position in the tl phrase. Each element contains a list of tl words, one for each phrase table entry being combined
	tlwordsmatrix=[]
	for i in range(len(mylist[0][2].split(" "))):
		tlwordsmatrix.append([])

	for element in mylist:
		parts=element
		ptprobs=[float(p) for p in parts[3].split(u" ")]
		ptcounts=[float(c) for c in parts[5].split(u" ")]

		sumCountTL+=ptcounts[0]
		countSL=ptcounts[1]
		sumCountCooc+=ptcounts[2]

		sumProbDirect+=ptprobs[2]
		sumProbDirectLex+=ptprobs[2]

		#add corresponding tl words to altlwords
		alltlwords=parts[2].split(" ")
		for i,al in enumerate(alignments):
			altlwords[i].append(alltlwords[al[1]])

		for i in range(len(alltlwords)):
			tlwordsmatrix[i].append(alltlwords[i])

		alsIndexedByTL=dict()
		for alstr in parts[4].split(" "):
			splitbyhyphen=alstr.split("-")
			slindex=int(splitbyhyphen[0])
			tlindex=int(splitbyhyphen[1])
			if tlindex not in alsIndexedByTL:
				alsIndexedByTL[tlindex]=[]
			alsIndexedByTL[tlindex].append(slindex)

		#fill alignedWithTLWords data structure
		for index,tlword in enumerate(alltlwords):
			slwordsAlignedWithMe=[]
			if index in alsIndexedByTL:
				for slindex in alsIndexedByTL[index]:
					slwordsAlignedWithMe.append(allslwords[slindex])
			else:
				slwordsAlignedWithMe.append(u"NULL")
			alignedWithTLWords[index].append(slwordsAlignedWithMe)

	#compute lexical translation probabilities as explained above

	#OLD: product, for each alignment point, of {  sum(lex.f2e for all tls being combined)*slcount/sum tls_count  }
	#product, for each SL word s:  p(s|NULL) if not aligned else: sum_for_each_tl_aligned( 1/numtlaligned * sum_for_each_line( p_lex( s|tl ) * count( tl)  )/sum_for_each_line(count(tl))  )
	inverseLexProb_factors=[]
	if False:
		for i in range(len(alignments)):
			sumLexCountTL=0.0
			sumOflexf2e=0.0
			lexcountSL=0.0

			slword=alslwords[i]
			if slword in lexcountsSlDict:
				lexcountSL=lexcountsSlDict[slword]
			for tlword in altlwords[i]:
				if tlword in lexcountsDict:
					sumLexCountTL+=lexcountsDict[tlword]
				if (slword,tlword) in lexf2eDict:
					sumOflexf2e+=lexf2eDict[(slword,tlword)]
			estimatedProb=0.0
			if sumLexCountTL > 0.0:
				estimatedProb=sumOflexf2e*lexcountSL/sumLexCountTL
			inverseLexProb_factors.append(estimatedProb)
	for i in range(len(allslwords)):
		estimatedProb=0.0
		slword=allslwords[i]
		if len(alignedWithSLWordsIndexes[i]) == 0:
			estimatedProb=lexe2fDict[(u"NULL",slword)]
		else:
			numtlaligned=len(alignedWithSLWordsIndexes[i])
			num=0.0
			den=0.0
			for tlindex in alignedWithSLWordsIndexes[i]:
				num+=(1.0/numtlaligned)* sum(  (lexe2fDict[(tlword,slword)] if (tlword,slword) in lexe2fDict else 0.0) *lexcountsDict[tlword] for tlword in tlwordsmatrix[tlindex])
				den+=sum(lexcountsDict[tlword] for tlword in tlwordsmatrix[tlindex])
			if den > 0.0:
				estimatedProb=num/den
		inverseLexProb_factors.append(estimatedProb)
	inverseLexProb=reduce(lambda x, y: x*y, inverseLexProb_factors)

	#product, for each TL word (include null alignments), of {  sum(  1/(num sl words aligned) lex.f2e for all tls being combined)  }
	directLexProb_factors=[]
	for i in range(len(alltlwords)):
		sumOflexf2e=0.0
		slwords_ll=alignedWithTLWords[i]
		for lineindex,slwordsInOnePosition in enumerate(slwords_ll):
			tlword=tlwordsmatrix[i][lineindex]
			for alignedSLWord in slwordsInOnePosition:
				sumOflexf2e+=lexf2eDict[(alignedSLWord,tlword)]/1.0*len(slwordsInOnePosition)
		directLexProb_factors.append(sumOflexf2e)
	directLexProb=reduce(lambda x, y: x*y, directLexProb_factors)


	output=[]
	output.append(mylist[0][0])
	output.append(mylist[0][1])
	output.append(u" ".join([ unicode(sumCountCooc/sumCountTL) , unicode(inverseLexProb) , unicode(sumProbDirect) , unicode(directLexProb)  ]) )
	output.append(mylist[0][4])
	output.append(u" ".join([ unicode(sumCountTL), unicode(countSL), unicode(sumCountCooc) ]))
	output.append(u"0.0 "+unicode(0.0)) #we print TL sum of lexical counts: we will need them later
	output.append(u" ".join(  u"__".join(listposition)    for listposition in tlwordsmatrix  ))
	print u"\t".join(output).encode(ENCODING)

# if lexcounts arguments is provided,
# an additional field after TL phrase is used together with the lexcounts file to obtain the final lexcounts TL used for computing probs
# if not, the field after phrase counts is assumed to contain tl lexcounts
#
parser=argparse.ArgumentParser(description="sum probabilities")
parser.add_argument("--lexcounts")
parser.add_argument("--lexcountssl")
parser.add_argument("--lexf2e")
parser.add_argument("--lexe2f")
args = parser.parse_args()

lexcountsDict=None
lexcountsSlDict=None
lexf2eDict=None
lexe2fDict=None
if args.lexcountssl:
	lexcountsSlDict=dict()
	for line in codecs.open(args.lexcountssl,'r',ENCODING):
		line=line.rstrip(u"\n")
		parts=line.split("\t")
		lexcountsSlDict[parts[1]]=int(parts[0])

if args.lexcounts:
	lexcountsDict=dict()
	for line in codecs.open(args.lexcounts,'r',ENCODING):
		line=line.rstrip(u"\n")
		parts=line.split("\t")
		lexcountsDict[parts[1]]=int(parts[0])

if args.lexf2e:
	lexf2eDict=dict()
	for line in codecs.open(args.lexf2e,'r',ENCODING):
		line=line.rstrip(u"\n")
		parts=line.split(" ")
		lexf2eDict[(parts[1],parts[0])]=float(parts[2])

if args.lexe2f:
	lexe2fDict=dict()
	for line in codecs.open(args.lexe2f,'r',ENCODING):
		line=line.rstrip(u"\n")
		parts=line.split(" ")
		lexe2fDict[(parts[1],parts[0])]=float(parts[2])

curList=[]
curKey=None

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split(u"\t")
	key=(parts[0],parts[1])
	if key != curKey:
		if len(curList) > 0:
			processList(curList,lexcountsDict,lexcountsSlDict,lexf2eDict, lexe2fDict)
		curKey=key
		curList=[]
	curList.append(parts)
if len(curList) > 0:
	processList(curList,lexcountsDict,lexcountsSlDict,lexf2eDict, lexe2fDict)
