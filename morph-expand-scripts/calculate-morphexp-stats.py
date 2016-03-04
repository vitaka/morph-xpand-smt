import sys,codecs, gzip, argparse, itertools
from morphExpansionUtils import PhraseTable, Lexicon
from multiprocessing import Process, Queue
ENCODING="utf-8"


def check_matching_level_subset(lines,phrasedict, queue, useLemmatized):
		pt=PhraseTable()
		pt.phrasedict=phrasedict
		numline=0
		for linelist in lines:
			numline+=1
			slline=linelist[0].rstrip("\n")
			if useLemmatized:
				trueLen=len(linelist[1:])/2
				tllines=[line.rstrip("\n") for line in linelist[1:1+trueLen] ]
				tllines_lem=[ line.rstrip("\n") for line in linelist[1+trueLen:] ]
				if len(tllines) != len(tllines_lem):
					print >> sys.stderr, "Super error"
					exit(1)
			else:
				tllines=[line.rstrip("\n") for line in linelist[1:] ]
				tllines_lem=None
			pt.count_coverage(slline.split(u" "),[tlline.split(u" ") for tlline in tllines], [ [ tok.split(u"|")[0] for tok in tlline.split(u" ")  ] for tlline in  tllines_lem ], [ [ tok.split(u"|")[1] for tok in tlline.split(u" ")  ] for tlline in  tllines_lem ])
			print >> sys.stderr, str(numline)
		pt.phrasedict=None
		queue.put(pt)


parser=argparse.ArgumentParser(description="calculate stats about best options for morhp expansion")
parser.add_argument("--lexicon")
parser.add_argument("--lemmatized_devtl")
parser.add_argument("devsl")
parser.add_argument("devtl",help='multiple references can be separated by ;')
parser.add_argument("phrasetable")
args = parser.parse_args()

lexicon=None
if args.lexicon:
	myreader=codecs.getreader(ENCODING)
	lexicon=Lexicon(myreader(gzip.open(args.lexicon,'rb')))


print >> sys.stderr, "Loading phrase table ..."
myreader=codecs.getreader(ENCODING)
pt = PhraseTable(myreader(gzip.open(args.phrasetable,'rb')),lexicon)
print >> sys.stderr, "... done"

filesToRead=[]
filesToRead.append(codecs.open(args.devsl,'r',ENCODING))
for onedevtl in args.devtl.split(";"):
	filesToRead.append(codecs.open(onedevtl,'r',ENCODING))

if args.lemmatized_devtl:
	for onedevtl in args.lemmatized_devtl.split(";"):
		filesToRead.append(codecs.open(onedevtl,'r',ENCODING))

NUMTHREADS=32
linegroups=[]
for i in range(NUMTHREADS):
	linegroups.append([])


numline=0
for linelist in itertools.izip(*filesToRead):
	linegroups[numline % NUMTHREADS].append(linelist)
	numline+=1

q=Queue()
print >> sys.stderr, "Starting threads"
for i in xrange(NUMTHREADS):
	t=Process(target=check_matching_level_subset, args=(linegroups[i],pt.phrasedict,q, args.lemmatized_devtl != None))
	t.start()

print >> sys.stderr, "Waiting and gathering results"
for i in xrange(NUMTHREADS):
	localpt=q.get()
	pt.add_results(localpt)

#print results of couting coverage
for statsline in pt.summary_coverage():
	print statsline.encode(ENCODING)
