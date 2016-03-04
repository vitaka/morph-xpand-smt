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
#	- p_lex(sl|tl): (sum of all lexcount_tl*p_lex(sl|tl))/(sum of all lexcount_tl)
#	- p(tl|sl): sum of all p(tl|sl)
#	- p_lex(tl|sl): sum of all p_lex(tl|sl)
# 3: alignments, from the first line
# 4: phrase counts, computed as follows:
#	- count_tl: sum of all count_tl
#	- count_sl: same as last line
#	- count_cooc: sum of all count_cooc
# 5: empty at the moment
# 6: empty
#
def processList(mylist,lexcountsDict):
	if lexcountsDict == None:
		for i in xrange(len(mylist)):
			mylist[i]=mylist[i][0:2]+[u""]+mylist[i][2:]

	sumCountTL=0.0
	sumCountCooc=0.0
	countSL=0.0

	sumProbDirect=0.0
	sumProbDirectLex=0.0
	sumLexCountTL=0.0
	sumLexCountTLProdProbInverseLex=0.0
	for element in mylist:
		parts=element
		ptprobs=[float(p) for p in parts[3].split(u" ")]
		ptcounts=[float(c) for c in parts[5].split(u" ")]
		if lexcountsDict == None:
			lexcountTL=float(parts[6].split(u" ")[1])
		else:
			lexcountTL=lexcountsDict[parts[2].split(" ")[0]]

		sumCountTL+=ptcounts[0]
		countSL=ptcounts[1]
		sumCountCooc+=ptcounts[2]

		sumProbDirect+=ptprobs[2]
		sumProbDirectLex+=ptprobs[2]
		sumLexCountTL+=lexcountTL
		sumLexCountTLProdProbInverseLex+=(lexcountTL*ptprobs[1])

	output=[]
	output.append(mylist[0][0])
	output.append(mylist[0][1])
	output.append(u" ".join([ unicode(sumCountCooc/sumCountTL) , unicode((sumLexCountTLProdProbInverseLex/sumLexCountTL) if sumLexCountTL > 0.0 else 0.0) , unicode(sumProbDirect) , unicode(sumProbDirectLex)  ]) )
	output.append(mylist[0][4])
	output.append(u" ".join([ unicode(sumCountTL), unicode(countSL), unicode(sumCountCooc) ]))
	output.append(u"0.0 "+unicode(sumLexCountTL)) #we print TL sum of lexical counts: we will need them later
	output.append(u"")
	print u"\t".join(output).encode(ENCODING)

# if lexcounts arguments is provided,
# an additional field after TL phrase is used together with the lexcounts file to obtain the final lexcounts TL used for computing probs
# if not, the field after phrase counts is assumed to contain tl lexcounts
#
parser=argparse.ArgumentParser(description="sum probabilities")
parser.add_argument("--lexcounts")
args = parser.parse_args()

lexcountsDict=None
if args.lexcounts:
	lexcountsDict=dict()
	for line in codecs.open(args.lexcounts,'r',ENCODING):
		line=line.rstrip(u"\n")
		parts=line.split("\t")
		lexcountsDict[parts[1]]=int(parts[0])

curList=[]
curKey=None

for line in sys.stdin:
	line=line.rstrip("\n").decode(ENCODING)
	parts=line.split(u"\t")
	key=(parts[0],parts[1])
	if key != curKey:
		if len(curList) > 0:
			processList(curList,lexcountsDict)
		curKey=key
		curList=[]
	curList.append(parts)
if len(curList) > 0:
	processList(curList,lexcountsDict)
